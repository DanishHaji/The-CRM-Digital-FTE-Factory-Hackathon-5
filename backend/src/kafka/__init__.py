"""Kafka package"""

from .topics import (
    TOPIC_INCOMING,
    TOPIC_GMAIL,
    TOPIC_WHATSAPP,
    TOPIC_WEB,
    create_ticket_message,
    get_channel_topic
)
from .producer import create_producer, close_producer, get_producer, send_message, send_batch
from .consumer import MessageConsumer

__all__ = [
    'TOPIC_INCOMING',
    'TOPIC_GMAIL',
    'TOPIC_WHATSAPP',
    'TOPIC_WEB',
    'create_ticket_message',
    'get_channel_topic',
    'create_producer',
    'close_producer',
    'get_producer',
    'send_message',
    'send_batch',
    'MessageConsumer'
]
