"""
Digital FTE Customer Success Agent - Groq AI Implementation
Production agent with multi-channel support using Groq (Free & Fast)
"""

from groq import Groq
from typing import Dict, Any, Optional
import time
import json

from .prompts import get_system_prompt, should_escalate
from ..utils.config import get_settings
from ..utils.logger import get_logger, bind_context
from ..database.connection import get_connection

logger = get_logger(__name__)
settings = get_settings()


class DigitalFTEAgent:
    """
    Digital FTE Customer Success Agent using Groq AI.
    Handles customer support across email, WhatsApp, and web channels.
    """

    def __init__(self, channel: str = "web"):
        """
        Initialize Digital FTE agent for specific channel.

        Args:
            channel: Channel name (email, whatsapp, web)
        """
        self.channel = channel
        self.logger = logger

        # Initialize Groq client
        if settings.ai_provider == "groq":
            self.client = Groq(api_key=settings.groq_api_key)
            self.model = settings.groq_model
            self.logger.info(
                f"Digital FTE Agent initialized with Groq",
                channel=channel,
                model=self.model
            )
        else:
            raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")

    async def search_knowledge_base_simple(self, query: str) -> str:
        """Simple knowledge base search without embeddings."""
        async with get_connection() as conn:
            # Simple text search
            results = await conn.fetch("""
                SELECT title, content, category
                FROM knowledge_base
                WHERE content ILIKE $1 OR title ILIKE $1
                LIMIT 3
            """, f"%{query}%")

            if results:
                kb_text = "\n\n".join([
                    f"**{r['title']}** ({r['category']})\n{r['content']}"
                    for r in results
                ])
                return f"Found relevant information:\n{kb_text}"
            return "No specific documentation found."

    async def handle_customer_request(
        self,
        customer_email: str,
        customer_name: str,
        message: str,
        channel_message_id: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle complete customer support request using Groq AI.

        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            message: Customer's message/question
            channel_message_id: Channel-specific message ID for deduplication
            phone: Phone number (required for WhatsApp)

        Returns:
            Dict with result, response, and metadata
        """
        start_time = time.time()

        # Bind context for logging
        context_logger = bind_context(
            self.logger,
            channel=self.channel,
            customer_email=customer_email
        )

        context_logger.info("Processing customer request", message=message[:100])

        try:
            # Pre-check for immediate escalation triggers
            should_esc, esc_reason = should_escalate(message)

            if should_esc:
                response = f"I understand you need assistance with {esc_reason}. Let me connect you with a human agent who can better help you with this matter."
                escalated = True
            else:
                # Search knowledge base
                kb_info = await self.search_knowledge_base_simple(message)

                # Build prompt for Groq
                system_prompt = get_system_prompt(self.channel)
                user_prompt = f"""Customer: {customer_name} ({customer_email})
Channel: {self.channel}
Question: {message}

Knowledge Base Information:
{kb_info}

Please provide a helpful response to the customer's question."""

                # Call Groq API
                context_logger.info("Calling Groq API...")
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=500 if self.channel == "email" else 300,
                )

                response = chat_completion.choices[0].message.content
                escalated = False

            # Save to database
            async with get_connection() as conn:
                # Create or get customer
                customer = await conn.fetchrow("""
                    INSERT INTO customers (email, name, metadata)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (email) DO UPDATE SET name = $2
                    RETURNING customer_id
                """, customer_email, customer_name, json.dumps({"phone": phone} if phone else {}))

                customer_id = customer['customer_id']

                # Create conversation
                conversation = await conn.fetchrow("""
                    INSERT INTO conversations (customer_id, initial_channel, status)
                    VALUES ($1, $2, $3)
                    RETURNING conversation_id
                """, customer_id, self.channel, "escalated" if escalated else "resolved")

                conversation_id = conversation['conversation_id']

                # Save customer message
                await conn.execute("""
                    INSERT INTO messages (conversation_id, channel, direction, role, content, channel_message_id)
                    VALUES ($1, $2, 'inbound', 'user', $3, $4)
                """, conversation_id, self.channel, message, channel_message_id)

                # Save agent response
                await conn.execute("""
                    INSERT INTO messages (conversation_id, channel, direction, role, content)
                    VALUES ($1, $2, 'outbound', 'assistant', $3)
                """, conversation_id, self.channel, response)

            processing_time_ms = int((time.time() - start_time) * 1000)

            context_logger.info(
                "Agent execution completed",
                processing_time_ms=processing_time_ms,
                response_length=len(response),
                escalated=escalated
            )

            return {
                "success": True,
                "response": response,
                "processing_time_ms": processing_time_ms,
                "channel": self.channel,
                "customer_email": customer_email,
                "escalated": escalated,
                "escalation_reason": esc_reason if should_esc else None
            }

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            context_logger.error(
                f"Agent execution failed",
                error=str(e),
                processing_time_ms=processing_time_ms
            )

            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": processing_time_ms,
                "channel": self.channel
            }


async def create_agent_for_channel(channel: str) -> DigitalFTEAgent:
    """
    Factory function to create Digital FTE agent for specific channel.

    Args:
        channel: Channel name (email, whatsapp, web)

    Returns:
        DigitalFTEAgent: Configured agent instance
    """
    return DigitalFTEAgent(channel=channel)


async def test_agent():
    """Test the Digital FTE agent with a sample request."""
    from ..database.connection import create_pool, close_pool

    logger.info("="*80)
    logger.info("Testing Digital FTE Agent with Groq AI")
    logger.info("="*80)

    # Initialize database
    await create_pool()

    # Create agent for web channel
    agent = DigitalFTEAgent(channel="web")

    # Test request
    result = await agent.handle_customer_request(
        customer_email="test.customer@example.com",
        customer_name="Test Customer",
        message="How do I contact support via email?",
        channel_message_id="web_test_12345"
    )

    logger.info("="*80)
    logger.info("Test Result:")
    logger.info("="*80)
    logger.info(f"Success: {result['success']}")
    logger.info(f"Processing Time: {result['processing_time_ms']}ms")
    if result['success']:
        logger.info(f"Response: {result['response']}")
    else:
        logger.info(f"Error: {result.get('error')}")

    # Close database
    await close_pool()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())
