"""
Digital FTE Customer Success Agent - OpenAI Agents SDK Tools
Production tools with @function_tool decorators and Pydantic validation
"""

from agents import function_tool
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from uuid import uuid4
from openai import AsyncOpenAI

from ..database.connection import get_transaction, get_connection
from ..utils.validators import validate_email, normalize_phone
from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Initialize OpenAI client for embeddings
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


# =============================================================================
# Tool Input Schemas (Pydantic BaseModels)
# =============================================================================

class CreateTicketInput(BaseModel):
    """Input schema for create_ticket tool with validation."""
    customer_email: str = Field(..., description="Customer's email address (primary identifier)")
    customer_name: str = Field(..., description="Customer's name")
    message: str = Field(..., description="Customer's support request message")
    channel: str = Field(..., description="Source channel: email, whatsapp, or web")
    channel_message_id: str = Field(..., description="Channel-specific message ID for deduplication")
    phone: Optional[str] = Field(None, description="Phone number (required for WhatsApp)")

    @validator('customer_email')
    def validate_email_field(cls, v):
        return validate_email(v)

    @validator('channel')
    def validate_channel_field(cls, v):
        if v not in ['email', 'whatsapp', 'web']:
            raise ValueError(f"Invalid channel: {v}. Must be email, whatsapp, or web")
        return v

    @validator('phone')
    def validate_phone_field(cls, v, values):
        if values.get('channel') == 'whatsapp' and not v:
            raise ValueError("Phone number required for WhatsApp channel")
        if v:
            return normalize_phone(v)
        return v


class GetCustomerHistoryInput(BaseModel):
    """Input schema for get_customer_history tool."""
    customer_id: str = Field(..., description="Customer UUID from create_ticket response")


class SearchKnowledgeBaseInput(BaseModel):
    """Input schema for search_knowledge_base tool."""
    query: str = Field(..., description="Customer's question to search in knowledge base")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to return")


class SendResponseInput(BaseModel):
    """Input schema for send_response tool."""
    conversation_id: str = Field(..., description="Conversation UUID from create_ticket response")
    channel: str = Field(..., description="Target channel: email, whatsapp, or web")
    response_text: str = Field(..., description="Response content (will be formatted per channel)")

    @validator('channel')
    def validate_channel_field(cls, v):
        if v not in ['email', 'whatsapp', 'web']:
            raise ValueError(f"Invalid channel: {v}")
        return v


class EscalateToHumanInput(BaseModel):
    """Input schema for escalate_to_human tool."""
    ticket_id: str = Field(..., description="Ticket UUID from create_ticket response")
    reason: str = Field(..., description="Escalation reason: pricing, refund, legal, sentiment, knowledge_gap, customer_request")
    context: str = Field(default="", description="Additional context for human agent")


# =============================================================================
# Tool Implementations with @function_tool decorator
# =============================================================================

@function_tool
async def create_ticket(input: CreateTicketInput) -> Dict[str, Any]:
    """
    Create support ticket with channel metadata. MUST be called FIRST in workflow.

    This tool:
    1. Creates/updates customer record by email (primary identifier)
    2. Links channel identifier (phone/whatsapp_id) via customer_identifiers table
    3. Creates conversation with initial_channel tracking
    4. Creates inbound message record with channel, direction='inbound', role='user'
    5. Creates ticket with source_channel and status='pending'

    Returns:
        Dict with ticket_id, conversation_id, customer_id, status
    """
    try:
        async with get_transaction() as conn:
            # 1. Create or get existing customer
            existing_customer = await conn.fetchrow(
                "SELECT customer_id FROM customers WHERE email = $1",
                input.customer_email
            )

            if existing_customer:
                customer_id = existing_customer['customer_id']
                await conn.execute(
                    "UPDATE customers SET name = $1, updated_at = CURRENT_TIMESTAMP WHERE customer_id = $2",
                    input.customer_name, customer_id
                )
                logger.info(f"Using existing customer: {customer_id}")
            else:
                customer_id = uuid4()
                await conn.execute("""
                    INSERT INTO customers (customer_id, email, name)
                    VALUES ($1, $2, $3)
                """, customer_id, input.customer_email, input.customer_name)
                logger.info(f"Created new customer: {customer_id}")

            # 2. Link customer identifiers
            await conn.execute("""
                INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified)
                VALUES ($1, 'email', $2, true)
                ON CONFLICT (identifier_type, identifier_value) DO NOTHING
            """, customer_id, input.customer_email)

            if input.phone:
                identifier_type = 'whatsapp_id' if input.channel == 'whatsapp' else 'phone'
                await conn.execute("""
                    INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified)
                    VALUES ($1, $2, $3, false)
                    ON CONFLICT (identifier_type, identifier_value) DO NOTHING
                """, customer_id, identifier_type, input.phone)

            # 3. Create conversation
            conversation_id = uuid4()
            await conn.execute("""
                INSERT INTO conversations (conversation_id, customer_id, initial_channel, status)
                VALUES ($1, $2, $3, 'open')
            """, conversation_id, customer_id, input.channel)

            # 4. Create inbound message
            message_id = uuid4()
            metadata = {'customer_name': input.customer_name}
            if input.phone:
                metadata['phone'] = input.phone

            await conn.execute("""
                INSERT INTO messages (
                    message_id, conversation_id, channel, direction, role,
                    content, channel_message_id, metadata
                )
                VALUES ($1, $2, $3, 'inbound', 'user', $4, $5, $6)
            """, message_id, conversation_id, input.channel, input.message,
                input.channel_message_id, metadata)

            # 5. Create ticket
            ticket_id = uuid4()
            await conn.execute("""
                INSERT INTO tickets (ticket_id, conversation_id, source_channel, priority, status)
                VALUES ($1, $2, $3, 'medium', 'pending')
            """, ticket_id, conversation_id, input.channel)

            logger.info(
                f"Ticket created successfully",
                ticket_id=str(ticket_id),
                customer_id=str(customer_id),
                channel=input.channel
            )

            return {
                "success": True,
                "ticket_id": str(ticket_id),
                "conversation_id": str(conversation_id),
                "customer_id": str(customer_id),
                "message_id": str(message_id),
                "status": "pending",
                "channel": input.channel
            }

    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def get_customer_history(input: GetCustomerHistoryInput) -> Dict[str, Any]:
    """
    Retrieve complete customer history across ALL channels (email, WhatsApp, web).
    MUST be called AFTER create_ticket, BEFORE generating response.

    This demonstrates cross-channel continuity - customer history is preserved
    regardless of which channel they use.

    Returns:
        Dict with customer info, conversations across all channels, channels used
    """
    try:
        async with get_connection() as conn:
            # Get customer info
            customer = await conn.fetchrow("""
                SELECT customer_id, email, name, created_at
                FROM customers
                WHERE customer_id = $1
            """, input.customer_id)

            if not customer:
                return {
                    "success": False,
                    "error": f"Customer not found: {input.customer_id}"
                }

            # Get all conversations with messages
            conversations = await conn.fetch("""
                SELECT
                    c.conversation_id,
                    c.initial_channel,
                    c.status,
                    c.created_at,
                    json_agg(
                        json_build_object(
                            'channel', m.channel,
                            'direction', m.direction,
                            'role', m.role,
                            'content', m.content,
                            'created_at', m.created_at
                        )
                        ORDER BY m.created_at ASC
                    ) AS messages
                FROM conversations c
                LEFT JOIN messages m ON c.conversation_id = m.conversation_id
                WHERE c.customer_id = $1
                GROUP BY c.conversation_id, c.initial_channel, c.status, c.created_at
                ORDER BY c.created_at DESC
            """, input.customer_id)

            channels_used = set()
            conversation_list = []

            for conv in conversations:
                channels_used.add(conv['initial_channel'])
                messages = conv['messages'] if conv['messages'] else []

                conversation_list.append({
                    "conversation_id": str(conv['conversation_id']),
                    "initial_channel": conv['initial_channel'],
                    "status": conv['status'],
                    "created_at": conv['created_at'].isoformat(),
                    "message_count": len([m for m in messages if m is not None]),
                    "messages": [m for m in messages if m is not None]
                })

            return {
                "success": True,
                "customer_id": str(customer['customer_id']),
                "email": customer['email'],
                "name": customer['name'],
                "customer_since": customer['created_at'].isoformat(),
                "conversations": conversation_list,
                "total_conversations": len(conversation_list),
                "channels_used": list(channels_used),
                "has_history": len(conversation_list) > 0,
                "cross_channel_customer": len(channels_used) > 1
            }

    except Exception as e:
        logger.error(f"Failed to get customer history: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def search_knowledge_base(input: SearchKnowledgeBaseInput) -> Dict[str, Any]:
    """
    Search product documentation using pgvector semantic similarity.
    Use when customer asks product questions, troubleshooting, account issues.

    This uses OpenAI embeddings + PostgreSQL pgvector for semantic search.
    Returns top_k most relevant entries with similarity scores.

    Returns:
        Dict with search results sorted by similarity, best_match
    """
    try:
        # Generate embedding for query
        logger.info(f"Generating embedding for query: {input.query[:50]}...")
        response = await openai_client.embeddings.create(
            model=settings.openai_embedding_model,
            input=input.query
        )
        query_embedding = response.data[0].embedding

        # Search knowledge base using pgvector cosine similarity
        async with get_connection() as conn:
            results = await conn.fetch("""
                SELECT
                    entry_id,
                    title,
                    content,
                    category,
                    source_url,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM knowledge_base
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, query_embedding, input.top_k)

            result_list = [
                {
                    "entry_id": str(row['entry_id']),
                    "title": row['title'],
                    "content": row['content'],
                    "category": row['category'],
                    "source_url": row['source_url'],
                    "similarity": float(row['similarity'])
                }
                for row in results
            ]

            logger.info(
                f"Knowledge base search completed",
                query=input.query[:50],
                results_found=len(result_list),
                best_similarity=result_list[0]['similarity'] if result_list else 0
            )

            return {
                "success": True,
                "query": input.query,
                "results": result_list,
                "total_results": len(result_list),
                "has_results": len(result_list) > 0,
                "best_match": result_list[0] if result_list else None,
                "similarity_threshold_met": result_list[0]['similarity'] > 0.6 if result_list else False
            }

    except Exception as e:
        logger.error(f"Failed to search knowledge base: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": input.query,
            "results": [],
            "total_results": 0,
            "has_results": False
        }


@function_tool
async def send_response(input: SendResponseInput) -> Dict[str, Any]:
    """
    Format and deliver response to appropriate channel. MUST be called LAST in workflow.

    Channel-specific formatting:
    - Email: Formal greeting, body, signature (max 500 words)
    - WhatsApp: Concise, conversational (max 300 chars preferred), split if > 1600
    - Web: Semi-formal, helpful (max 300 words), send email notification

    Returns:
        Dict with message_id, delivery_status, formatted_response
    """
    try:
        async with get_transaction() as conn:
            # Get conversation and customer info
            conv = await conn.fetchrow("""
                SELECT c.conversation_id, c.customer_id, cust.name, cust.email
                FROM conversations c
                JOIN customers cust ON c.customer_id = cust.customer_id
                WHERE c.conversation_id = $1
            """, input.conversation_id)

            if not conv:
                return {
                    "success": False,
                    "error": f"Conversation not found: {input.conversation_id}"
                }

            customer_name = conv['name'] or "Valued Customer"

            # Apply channel-specific formatting
            if input.channel == "email":
                formatted_response = f"""Dear {customer_name},

{input.response_text}

If you have any further questions, please don't hesitate to reach out.

Best regards,
Customer Success Team"""

            elif input.channel == "whatsapp":
                # Keep concise for WhatsApp
                if len(input.response_text) > 300:
                    formatted_response = input.response_text[:280] + "..."
                else:
                    formatted_response = input.response_text

            else:  # web
                formatted_response = input.response_text

            # Create outbound message record
            message_id = uuid4()
            await conn.execute("""
                INSERT INTO messages (
                    message_id, conversation_id, channel, direction, role,
                    content, metadata
                )
                VALUES ($1, $2, $3, 'outbound', 'assistant', $4, $5)
            """, message_id, input.conversation_id, input.channel, formatted_response,
                {'original_response': input.response_text, 'formatted': True})

            # Update ticket status to 'responded'
            await conn.execute("""
                UPDATE tickets
                SET status = 'responded', updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = $1 AND status IN ('pending', 'processing')
            """, input.conversation_id)

            logger.info(
                f"Response sent successfully",
                conversation_id=input.conversation_id,
                channel=input.channel,
                message_id=str(message_id)
            )

            return {
                "success": True,
                "message_id": str(message_id),
                "delivery_status": "sent",
                "formatted_response": formatted_response,
                "channel": input.channel,
                "response_length": len(formatted_response),
                "customer_email": conv['email']
            }

    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def escalate_to_human(input: EscalateToHumanInput) -> Dict[str, Any]:
    """
    Escalate ticket to human support with full context.

    MUST escalate when:
    - Customer mentions "lawyer", "legal", "sue", "attorney"
    - Customer asks about pricing or refunds
    - Sentiment score < 0.3 (angry/frustrated)
    - Cannot find relevant information after 2 search attempts
    - Customer explicitly requests human help

    Returns:
        Dict with escalation_id, status, estimated_response_time
    """
    try:
        async with get_transaction() as conn:
            # Get ticket info
            ticket = await conn.fetchrow("""
                SELECT t.ticket_id, t.conversation_id, t.source_channel,
                       c.customer_id, cust.email, cust.name
                FROM tickets t
                JOIN conversations c ON t.conversation_id = c.conversation_id
                JOIN customers cust ON c.customer_id = cust.customer_id
                WHERE t.ticket_id = $1
            """, input.ticket_id)

            if not ticket:
                return {
                    "success": False,
                    "error": f"Ticket not found: {input.ticket_id}"
                }

            # Update ticket status to 'escalated'
            await conn.execute("""
                UPDATE tickets
                SET status = 'escalated',
                    escalation_reason = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = $1
            """, input.ticket_id, input.reason)

            # Update conversation status
            await conn.execute("""
                UPDATE conversations
                SET status = 'escalated',
                    updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = $1
            """, ticket['conversation_id'])

            # Create escalation notification message
            message_id = uuid4()
            escalation_message = f"""Your request has been escalated to a specialist who will review your case.

Reason: {input.reason}
Expected response time: 1-2 business hours

A team member will contact you shortly at {ticket['email']}.

Thank you for your patience."""

            await conn.execute("""
                INSERT INTO messages (
                    message_id, conversation_id, channel, direction, role,
                    content, metadata
                )
                VALUES ($1, $2, $3, 'outbound', 'assistant', $4, $5)
            """, message_id, ticket['conversation_id'], ticket['source_channel'],
                escalation_message, {'escalation': True, 'reason': input.reason})

            logger.info(
                f"Ticket escalated to human",
                ticket_id=input.ticket_id,
                reason=input.reason,
                customer_email=ticket['email']
            )

            return {
                "success": True,
                "escalation_id": str(input.ticket_id),
                "status": "escalated",
                "reason": input.reason,
                "context": input.context,
                "estimated_response_time": "1-2 business hours",
                "customer_notified": True,
                "notification_channel": ticket['source_channel']
            }

    except Exception as e:
        logger.error(f"Failed to escalate ticket: {e}")
        return {
            "success": False,
            "error": str(e)
        }
