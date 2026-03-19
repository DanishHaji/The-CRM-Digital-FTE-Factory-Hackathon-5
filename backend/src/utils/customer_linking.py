"""
Customer linking utilities for cross-channel identification.
Handles customer lookup, creation, and identifier linking.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database.connection import get_connection
from ..utils.logger import get_logger
from .phone_normalizer import normalize_phone_number
from .fuzzy_matcher import fuzzy_match_customer, should_confirm_identity as should_confirm_identity_util

logger = get_logger(__name__)


async def get_or_create_customer(
    email: str,
    name: str,
    phone: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get existing customer by email or create new one.
    Email is the primary identifier for cross-channel linking.

    Args:
        email: Customer email (primary identifier)
        name: Customer name
        phone: Optional phone number
        metadata: Optional metadata dict

    Returns:
        Dict with customer_id, email, name, is_new

    Example:
        >>> customer = await get_or_create_customer("alice@example.com", "Alice Johnson")
        >>> customer["customer_id"]
        'uuid-123'
        >>> customer["is_new"]
        True
    """
    async with get_connection() as conn:
        # Try to find existing customer by email
        existing = await conn.fetchrow(
            "SELECT customer_id, email, name, metadata FROM customers WHERE email = $1",
            email.lower()
        )

        if existing:
            logger.info(
                "customer_found_by_email",
                customer_id=str(existing["customer_id"]),
                email=email
            )

            return {
                "customer_id": str(existing["customer_id"]),
                "email": existing["email"],
                "name": existing["name"],
                "metadata": existing["metadata"] or {},
                "is_new": False
            }

        # Create new customer
        new_customer_id = str(uuid.uuid4())

        # Prepare metadata
        customer_metadata = metadata or {}
        if phone:
            customer_metadata["phone"] = phone

        await conn.execute(
            """
            INSERT INTO customers (customer_id, email, name, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            uuid.UUID(new_customer_id),
            email.lower(),
            name,
            customer_metadata,
            datetime.utcnow(),
            datetime.utcnow()
        )

        logger.info(
            "customer_created",
            customer_id=new_customer_id,
            email=email,
            name=name
        )

        return {
            "customer_id": new_customer_id,
            "email": email.lower(),
            "name": name,
            "metadata": customer_metadata,
            "is_new": True
        }


async def link_customer_identifier(
    customer_id: str,
    identifier_type: str,
    identifier_value: str
) -> None:
    """
    Link an identifier (email, phone) to a customer.

    Args:
        customer_id: Customer UUID
        identifier_type: Type of identifier ('email', 'phone', 'whatsapp_id')
        identifier_value: Identifier value

    Example:
        >>> await link_customer_identifier("uuid-123", "phone", "+14155238886")
    """
    async with get_connection() as conn:
        # Check if identifier already exists
        existing = await conn.fetchrow(
            "SELECT customer_id FROM customer_identifiers WHERE identifier_type = $1 AND identifier_value = $2",
            identifier_type,
            identifier_value
        )

        if existing:
            if str(existing["customer_id"]) == customer_id:
                # Already linked to this customer
                logger.debug("identifier_already_linked", customer_id=customer_id, type=identifier_type)
                return
            else:
                # Linked to different customer - this is a conflict
                logger.warning(
                    "identifier_conflict",
                    customer_id=customer_id,
                    existing_customer_id=str(existing["customer_id"]),
                    identifier_type=identifier_type,
                    identifier_value=identifier_value
                )
                # For now, skip linking (TODO: implement merge logic)
                return

        # Insert new identifier link
        await conn.execute(
            """
            INSERT INTO customer_identifiers (identifier_id, customer_id, identifier_type, identifier_value, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (identifier_type, identifier_value) DO NOTHING
            """,
            uuid.uuid4(),
            uuid.UUID(customer_id),
            identifier_type,
            identifier_value,
            datetime.utcnow()
        )

        logger.info(
            "identifier_linked",
            customer_id=customer_id,
            identifier_type=identifier_type,
            identifier_value=identifier_value
        )


async def find_customer_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """
    Find customer by phone number.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Customer dict if found, None otherwise

    Example:
        >>> customer = await find_customer_by_phone("+14155238886")
        >>> customer["customer_id"] if customer else None
        'uuid-123'
    """
    try:
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone)

        async with get_connection() as conn:
            # Look up in customer_identifiers table
            result = await conn.fetchrow(
                """
                SELECT c.customer_id, c.email, c.name, c.metadata
                FROM customers c
                JOIN customer_identifiers ci ON c.customer_id = ci.customer_id
                WHERE ci.identifier_type = 'phone' AND ci.identifier_value = $1
                """,
                normalized_phone
            )

            if result:
                logger.info("customer_found_by_phone", customer_id=str(result["customer_id"]), phone=normalized_phone)

                return {
                    "customer_id": str(result["customer_id"]),
                    "email": result["email"],
                    "name": result["name"],
                    "metadata": result["metadata"] or {}
                }

            return None

    except ValueError as e:
        logger.error("phone_normalization_failed", phone=phone, error=str(e))
        return None


async def get_customer_channels(customer_id: str) -> List[str]:
    """
    Get list of channels customer has used.

    Args:
        customer_id: Customer UUID

    Returns:
        List of channel names ['web', 'email', 'whatsapp']

    Example:
        >>> channels = await get_customer_channels("uuid-123")
        >>> channels
        ['web', 'email']
    """
    async with get_connection() as conn:
        results = await conn.fetch(
            """
            SELECT DISTINCT initial_channel
            FROM conversations
            WHERE customer_id = $1
            ORDER BY initial_channel
            """,
            uuid.UUID(customer_id)
        )

        return [row["initial_channel"] for row in results]


async def is_cross_channel_customer(customer_id: str) -> bool:
    """
    Check if customer has used multiple channels.

    Args:
        customer_id: Customer UUID

    Returns:
        True if customer has used 2+ channels, False otherwise

    Example:
        >>> await is_cross_channel_customer("uuid-123")
        True
    """
    channels = await get_customer_channels(customer_id)
    return len(channels) >= 2


async def get_customer_history(customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get customer conversation history across all channels.

    Args:
        customer_id: Customer UUID
        limit: Maximum number of messages to return (default 10)

    Returns:
        List of messages with channel, direction, content, created_at

    Example:
        >>> history = await get_customer_history("uuid-123")
        >>> len(history)
        5
        >>> history[0]["channel"]
        'web'
    """
    async with get_connection() as conn:
        results = await conn.fetch(
            """
            SELECT
                m.message_id,
                m.channel,
                m.direction,
                m.role,
                m.content,
                m.created_at,
                c.initial_channel,
                c.conversation_id
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.customer_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
            """,
            uuid.UUID(customer_id),
            limit
        )

        return [
            {
                "message_id": str(row["message_id"]),
                "channel": row["channel"],
                "direction": row["direction"],
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"].isoformat(),
                "initial_channel": row["initial_channel"],
                "conversation_id": str(row["conversation_id"])
            }
            for row in results
        ]


async def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get customer by email address.

    Args:
        email: Customer email

    Returns:
        Customer dict if found, None otherwise
    """
    async with get_connection() as conn:
        result = await conn.fetchrow(
            "SELECT customer_id, email, name, metadata FROM customers WHERE email = $1",
            email.lower()
        )

        if result:
            return {
                "customer_id": str(result["customer_id"]),
                "email": result["email"],
                "name": result["name"],
                "metadata": result["metadata"] or {}
            }

        return None


def should_confirm_identity(existing_name: str, new_name: str, confidence_score: float) -> bool:
    """
    Wrapper for fuzzy_matcher.should_confirm_identity.
    Exported for backwards compatibility.
    """
    return should_confirm_identity_util(existing_name, new_name, confidence_score)
