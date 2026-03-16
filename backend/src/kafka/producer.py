"""
Digital FTE Customer Success Agent - Kafka Producer
Async Kafka producer with error handling and retry logic
"""

import json
import asyncio
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Global producer instance
_producer: Optional[AIOKafkaProducer] = None


async def create_producer() -> AIOKafkaProducer:
    """
    Create Kafka producer with configuration.

    Returns:
        AIOKafkaProducer: Kafka producer instance
    """
    global _producer

    if _producer is not None:
        logger.warning("Producer already exists")
        return _producer

    try:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy',
            acks='all',  # Wait for all replicas to acknowledge
            retries=5,
            max_in_flight_requests_per_connection=1,  # Ensure ordering
            enable_idempotence=True,  # Prevent duplicates
        )

        await _producer.start()
        logger.info(f"Kafka producer started: {settings.kafka_broker}")
        return _producer

    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        raise


async def close_producer() -> None:
    """Close the Kafka producer gracefully."""
    global _producer

    if _producer is None:
        logger.warning("No producer to close")
        return

    await _producer.stop()
    _producer = None
    logger.info("Kafka producer closed")


async def get_producer() -> AIOKafkaProducer:
    """
    Get the existing producer or create one if it doesn't exist.

    Returns:
        AIOKafkaProducer: Kafka producer instance
    """
    global _producer

    if _producer is None:
        _producer = await create_producer()

    return _producer


async def send_message(
    topic: str,
    message: Dict[str, Any],
    key: Optional[str] = None,
    max_retries: int = 3
) -> bool:
    """
    Send a message to Kafka topic with retry logic.

    Args:
        topic: Kafka topic name
        message: Message payload (will be JSON serialized)
        key: Optional message key for partitioning
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if message sent successfully, False otherwise
    """
    producer = await get_producer()

    for attempt in range(max_retries):
        try:
            # Send message
            future = await producer.send(
                topic,
                value=message,
                key=key.encode('utf-8') if key else None
            )

            # Wait for acknowledgment
            record_metadata = await future

            logger.info(
                f"Message sent to Kafka",
                topic=topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                attempt=attempt + 1
            )
            return True

        except KafkaError as e:
            logger.error(
                f"Kafka error sending message (attempt {attempt + 1}/{max_retries})",
                error=str(e),
                topic=topic
            )

            if attempt < max_retries - 1:
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to send message after {max_retries} attempts")
                return False

        except Exception as e:
            logger.error(
                f"Unexpected error sending message to Kafka",
                error=str(e),
                topic=topic
            )
            return False

    return False


async def send_batch(
    topic: str,
    messages: list[Dict[str, Any]]
) -> int:
    """
    Send a batch of messages to Kafka topic.

    Args:
        topic: Kafka topic name
        messages: List of message payloads

    Returns:
        int: Number of messages sent successfully
    """
    producer = await get_producer()
    sent_count = 0

    try:
        # Send all messages asynchronously
        futures = []
        for msg in messages:
            future = producer.send(topic, value=msg)
            futures.append(future)

        # Wait for all to complete
        results = await asyncio.gather(*futures, return_exceptions=True)

        # Count successes
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send message {i}: {result}")
            else:
                sent_count += 1

        logger.info(
            f"Batch send completed",
            topic=topic,
            total=len(messages),
            sent=sent_count,
            failed=len(messages) - sent_count
        )

    except Exception as e:
        logger.error(f"Batch send failed: {e}")

    return sent_count
