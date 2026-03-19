"""Channel handlers package for Digital FTE Customer Success Agent."""

from .gmail_handler import (
    handle_gmail_webhook,
    parse_pubsub_message,
    format_email_response,
    send_gmail_message,
    send_gmail_message_with_retry
)

from .whatsapp_handler import (
    handle_whatsapp_webhook,
    parse_twilio_webhook,
    format_whatsapp_response,
    send_whatsapp_message,
    send_multiple_whatsapp_messages,
    split_whatsapp_message,
    validate_twilio_signature
)

__all__ = [
    # Gmail
    'handle_gmail_webhook',
    'parse_pubsub_message',
    'format_email_response',
    'send_gmail_message',
    'send_gmail_message_with_retry',
    # WhatsApp
    'handle_whatsapp_webhook',
    'parse_twilio_webhook',
    'format_whatsapp_response',
    'send_whatsapp_message',
    'send_multiple_whatsapp_messages',
    'split_whatsapp_message',
    'validate_twilio_signature'
]
