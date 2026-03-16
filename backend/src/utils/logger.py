"""
Digital FTE Customer Success Agent - Structured Logging
JSON format logging with conversation_id, customer_id, channel context
"""

import logging
import structlog
from typing import Optional
import sys

from .config import get_settings


def setup_logging() -> None:
    """
    Configure structured logging with JSON output.
    Includes conversation_id, customer_id, channel in log context.
    """
    settings = get_settings()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        structlog.BoundLogger: Structured logger
    """
    return structlog.get_logger(name)


def bind_context(
    logger: structlog.BoundLogger,
    conversation_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    channel: Optional[str] = None,
    ticket_id: Optional[str] = None,
    **kwargs
) -> structlog.BoundLogger:
    """
    Bind contextual information to logger for all subsequent log calls.

    Args:
        logger: Structured logger instance
        conversation_id: Conversation UUID
        customer_id: Customer UUID
        channel: Channel name (email, whatsapp, web)
        ticket_id: Ticket UUID
        **kwargs: Additional context fields

    Returns:
        structlog.BoundLogger: Logger with bound context
    """
    context = {}

    if conversation_id:
        context["conversation_id"] = conversation_id
    if customer_id:
        context["customer_id"] = customer_id
    if channel:
        context["channel"] = channel
    if ticket_id:
        context["ticket_id"] = ticket_id

    context.update(kwargs)

    return logger.bind(**context)
