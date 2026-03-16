"""
Digital FTE Customer Success Agent - Kafka Consumer
Async Kafka consumer with consumer group and offset management
"""

import json
import asyncio
from typing import Callable, Dict, Any, Optional
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MessageConsumer:
    """
    Kafka consumer for processing messages from topics.
    Supports consumer groups and offset management.
    """

    def __init__(
        self,
        topics: list[str],
        group_id: str = None,
        auto_commit: bool = True
    ):
        """
        Initialize message consumer.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID (default: from settings)
            auto_commit: Whether to auto-commit offsets
        """
        self.topics = topics
        self.group_id = group_id or settings.kafka_consumer_group
        self.auto_commit = auto_commit
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False

    async def start(self) -> None:
        """Start the Kafka consumer."""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.kafka_broker,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                enable_auto_commit=self.auto_commit,
                auto_offset_reset='earliest',  # Start from beginning if no offset
                max_poll_records=10,  # Process in small batches
            )

            await self.consumer.start()
            self.running = True

            logger.info(
                f"Kafka consumer started",
                topics=self.topics,
                group_id=self.group_id
            )

        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer gracefully."""
        self.running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(
        self,
        message_handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Consume messages from Kafka and process with handler.

        Args:
            message_handler: Async function that processes messages
                             Should return True on success, False on failure
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        logger.info("Starting message consumption loop")

        try:
            async for msg in self.consumer:
                if not self.running:
                    logger.info("Consumer stopped, exiting consumption loop")
                    break

                logger.info(
                    f"Received message from Kafka",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset,
                    key=msg.key.decode('utf-8') if msg.key else None
                )

                try:
                    # Process message
                    success = await message_handler(msg.value)

                    if success:
                        logger.info(
                            f"Message processed successfully",
                            topic=msg.topic,
                            offset=msg.offset
                        )

                        # Manually commit offset if auto_commit is disabled
                        if not self.auto_commit:
                            await self.consumer.commit()

                    else:
                        logger.error(
                            f"Message processing failed",
                            topic=msg.topic,
                            offset=msg.offset
                        )
                        # Note: Not committing offset means message will be reprocessed

                except Exception as e:
                    logger.error(
                        f"Error processing message",
                        error=str(e),
                        topic=msg.topic,
                        offset=msg.offset
                    )
                    # Don't commit offset on error - message will be reprocessed

        except KafkaError as e:
            logger.error(f"Kafka error in consumption loop: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in consumption loop: {e}")
            raise

    async def get_lag(self) -> Dict[str, int]:
        """
        Get consumer lag (messages behind) for each partition.

        Returns:
            Dict[str, int]: Mapping of topic-partition to lag
        """
        if not self.consumer:
            return {}

        lag = {}

        try:
            # Get assigned partitions
            partitions = self.consumer.assignment()

            for tp in partitions:
                # Get current position
                position = await self.consumer.position(tp)

                # Get end offset (high watermark)
                end_offsets = await self.consumer.end_offsets([tp])
                end_offset = end_offsets[tp]

                # Calculate lag
                partition_lag = end_offset - position
                lag[f"{tp.topic}-{tp.partition}"] = partition_lag

            logger.info(f"Consumer lag calculated", lag=lag)

        except Exception as e:
            logger.error(f"Failed to calculate consumer lag: {e}")

        return lag
