"""
Digital FTE Customer Success Agent - Kafka Topic Definitions
All Kafka topics with schemas and configuration
"""

from typing import Dict, Any
from ..utils.config import get_settings


settings = get_settings()


# =============================================================================
# Topic Names
# =============================================================================

TOPIC_INCOMING = settings.kafka_topic_incoming  # Unified topic for all channels
TOPIC_GMAIL = settings.kafka_topic_gmail  # Channel-specific for analytics
TOPIC_WHATSAPP = settings.kafka_topic_whatsapp  # Channel-specific for analytics
TOPIC_WEB = settings.kafka_topic_web  # Channel-specific for analytics


# =============================================================================
# Topic Configurations
# =============================================================================

TOPIC_CONFIGS: Dict[str, Dict[str, Any]] = {
    TOPIC_INCOMING: {
        "num_partitions": 10,
        "replication_factor": 3,
        "config": {
            "retention.ms": 604800000,  # 7 days
            "compression.type": "snappy",
            "max.message.bytes": 1048576,  # 1MB
        }
    },
    TOPIC_GMAIL: {
        "num_partitions": 3,
        "replication_factor": 3,
        "config": {
            "retention.ms": 2592000000,  # 30 days (for analytics)
            "compression.type": "snappy",
        }
    },
    TOPIC_WHATSAPP: {
        "num_partitions": 3,
        "replication_factor": 3,
        "config": {
            "retention.ms": 2592000000,  # 30 days
            "compression.type": "snappy",
        }
    },
    TOPIC_WEB: {
        "num_partitions": 3,
        "replication_factor": 3,
        "config": {
            "retention.ms": 2592000000,  # 30 days
            "compression.type": "snappy",
        }
    },
}


# =============================================================================
# Message Schema
# =============================================================================

def create_ticket_message(
    ticket_id: str,
    conversation_id: str,
    customer_id: str,
    channel: str,
    message: str,
    channel_message_id: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized ticket message for Kafka.

    Args:
        ticket_id: Ticket UUID
        conversation_id: Conversation UUID
        customer_id: Customer UUID
        channel: Channel name (email, whatsapp, web)
        message: Customer message content
        channel_message_id: Channel-specific message ID for deduplication
        metadata: Additional channel-specific metadata

    Returns:
        Dict[str, Any]: Standardized message schema
    """
    import time

    return {
        "ticket_id": ticket_id,
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "channel": channel,
        "message": message,
        "channel_message_id": channel_message_id,
        "timestamp": int(time.time() * 1000),  # Milliseconds since epoch
        "metadata": metadata or {}
    }


def get_channel_topic(channel: str) -> str:
    """
    Get the channel-specific topic for analytics.

    Args:
        channel: Channel name (email, whatsapp, web)

    Returns:
        str: Topic name
    """
    mapping = {
        "email": TOPIC_GMAIL,
        "whatsapp": TOPIC_WHATSAPP,
        "web": TOPIC_WEB,
    }
    return mapping.get(channel, TOPIC_INCOMING)
