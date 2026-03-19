"""
WhatsApp channel handler for Digital FTE Customer Success Agent.
Handles Twilio WhatsApp webhooks, message parsing, and Twilio API integration.
"""

import hashlib
import hmac
import base64
import re
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.validators import normalize_phone
from ..agent.customer_success_agent import DigitalFTEAgent

settings = get_settings()
logger = get_logger(__name__)


def validate_twilio_signature(url: str, params: Dict[str, str], signature: str) -> bool:
    """
    Validate Twilio webhook signature for security.

    Args:
        url: Full webhook URL
        params: POST parameters from webhook
        signature: X-Twilio-Signature header value

    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Skip validation if disabled (for development)
    if not settings.twilio_webhook_validate:
        logger.warning("twilio_signature_validation_disabled")
        return True

    try:
        # Build string to sign: URL + sorted params
        data = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))

        # Compute HMAC-SHA1 signature
        expected_signature = base64.b64encode(
            hmac.new(
                settings.twilio_auth_token.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')

        # Compare signatures
        is_valid = hmac.compare_digest(expected_signature, signature)

        if not is_valid:
            logger.warning(
                "twilio_signature_invalid",
                url=url,
                expected=expected_signature[:10] + "...",
                received=signature[:10] + "..."
            )

        return is_valid

    except Exception as e:
        logger.error("twilio_signature_validation_error", error=str(e), exc_info=True)
        return False


def normalize_whatsapp_phone(phone: str) -> str:
    """
    Normalize WhatsApp phone number (remove 'whatsapp:' prefix).

    Args:
        phone: Phone number (e.g., "whatsapp:+14155238886")

    Returns:
        Normalized phone number (e.g., "+14155238886")
    """
    # Remove 'whatsapp:' prefix
    if phone.startswith('whatsapp:'):
        phone = phone.replace('whatsapp:', '')

    # Use existing normalize_phone utility
    return normalize_phone(phone)


def parse_twilio_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Twilio WhatsApp webhook payload.

    Args:
        payload: Twilio webhook form data

    Returns:
        Dict with parsed fields: from_phone, to_phone, body, profile_name, message_sid, whatsapp_id

    Raises:
        ValueError: If required fields are missing
    """
    try:
        # Extract required fields
        from_field = payload.get("From", "")
        to_field = payload.get("To", "")
        body = payload.get("Body", "")
        message_sid = payload.get("MessageSid", "")

        if not from_field:
            raise ValueError("WhatsApp webhook missing 'From' field")

        if not body:
            raise ValueError("WhatsApp webhook missing 'Body' field")

        # Extract optional fields
        profile_name = payload.get("ProfileName")
        whatsapp_id = payload.get("WaId")  # WhatsApp ID (phone without country code)
        num_media = int(payload.get("NumMedia", "0"))

        # Normalize phone numbers
        from_phone = normalize_whatsapp_phone(from_field)
        to_phone = normalize_whatsapp_phone(to_field) if to_field else settings.twilio_whatsapp_from

        return {
            "from_phone": from_phone,
            "to_phone": to_phone,
            "body": body.strip(),
            "profile_name": profile_name,
            "message_sid": message_sid,
            "whatsapp_id": whatsapp_id,
            "num_media": num_media,
            "received_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error("whatsapp_parse_error", error=str(e), exc_info=True)
        raise


def format_whatsapp_response(response_text: str, max_chars: int = 300) -> str:
    """
    Format AI response for WhatsApp channel (concise, conversational, no formal greeting).

    Args:
        response_text: AI-generated response text
        max_chars: Preferred max characters (default 300)

    Returns:
        Formatted WhatsApp message (concise, direct)
    """
    # WhatsApp should be direct and concise
    # NO formal greeting, NO signature

    # Truncate if too long (prefer short messages)
    if len(response_text) > max_chars:
        response_text = response_text[:max_chars] + "..."
        logger.warning("whatsapp_response_truncated", original_length=len(response_text), max_chars=max_chars)

    # Return as-is (no formatting needed for WhatsApp)
    return response_text.strip()


def split_whatsapp_message(message: str, max_length: int = 1600) -> List[str]:
    """
    Split long WhatsApp message into multiple parts (Twilio limit is 1600 chars).

    Args:
        message: Message to split
        max_length: Maximum characters per message (default 1600)

    Returns:
        List of message parts (each <= max_length)
    """
    # If message fits in one part, return as-is
    if len(message) <= max_length:
        return [message]

    parts = []
    remaining = message

    # Calculate how many parts needed
    num_parts = (len(message) + max_length - 1) // max_length

    # Reserve space for part indicators: "(part X/Y) "
    indicator_length = len(f"(part {num_parts}/{num_parts}) ")
    usable_length = max_length - indicator_length

    part_num = 1
    while remaining:
        # Extract chunk at word boundary
        if len(remaining) <= usable_length:
            chunk = remaining
            remaining = ""
        else:
            # Find last space before limit
            chunk = remaining[:usable_length]
            last_space = chunk.rfind(' ')

            if last_space > 0:
                chunk = remaining[:last_space]
                remaining = remaining[last_space:].strip()
            else:
                # No space found, hard split
                chunk = remaining[:usable_length]
                remaining = remaining[usable_length:]

        # Add part indicator
        part_message = f"(part {part_num}/{num_parts}) {chunk}"
        parts.append(part_message)
        part_num += 1

    return parts


def get_twilio_client() -> Client:
    """
    Create Twilio client instance.

    Returns:
        Twilio Client object

    Raises:
        Exception: If Twilio credentials are invalid
    """
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        return client

    except Exception as e:
        logger.error("twilio_client_error", error=str(e), exc_info=True)
        raise


async def send_whatsapp_message(
    to_phone: str,
    body: str,
    from_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send WhatsApp message via Twilio API.

    Args:
        to_phone: Recipient phone number (e.g., "+14155238886")
        body: Message body (max 1600 chars)
        from_phone: Sender WhatsApp number (defaults to settings.twilio_whatsapp_from)

    Returns:
        Dict with success status and message_sid

    Raises:
        Exception: If Twilio API call fails
    """
    try:
        if not from_phone:
            from_phone = settings.twilio_whatsapp_from

        # Add 'whatsapp:' prefix if not present
        if not to_phone.startswith('whatsapp:'):
            to_phone = f"whatsapp:{to_phone}"

        if not from_phone.startswith('whatsapp:'):
            from_phone = f"whatsapp:{from_phone}"

        # Get Twilio client
        client = get_twilio_client()

        # Send message (run in thread pool since it's blocking)
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                from_=from_phone,
                to=to_phone,
                body=body
            )
        )

        logger.info(
            "whatsapp_message_sent",
            to_phone=to_phone,
            message_sid=message.sid,
            status=message.status
        )

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status
        }

    except TwilioRestException as e:
        logger.error(
            "twilio_api_error",
            status_code=e.status,
            error_code=e.code,
            error_message=e.msg,
            to_phone=to_phone
        )
        raise Exception(f"Twilio API error: {e.msg}")

    except Exception as e:
        logger.error("whatsapp_send_error", error=str(e), to_phone=to_phone, exc_info=True)
        raise


async def send_multiple_whatsapp_messages(
    to_phone: str,
    message_parts: List[str],
    from_phone: Optional[str] = None,
    delay_seconds: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Send multiple WhatsApp messages (for split long messages).

    Args:
        to_phone: Recipient phone number
        message_parts: List of message parts to send
        from_phone: Sender WhatsApp number
        delay_seconds: Delay between messages (default 0.5s)

    Returns:
        List of results for each message
    """
    results = []

    for i, part in enumerate(message_parts):
        try:
            result = await send_whatsapp_message(to_phone, part, from_phone)
            results.append(result)

            # Small delay between messages to ensure order
            if i < len(message_parts) - 1:
                await asyncio.sleep(delay_seconds)

        except Exception as e:
            logger.error(
                "whatsapp_multi_send_error",
                part_number=i + 1,
                total_parts=len(message_parts),
                error=str(e)
            )
            results.append({
                "success": False,
                "error": str(e)
            })

    return results


async def handle_whatsapp_webhook(payload: Dict[str, Any], signature: str, url: str) -> Dict[str, Any]:
    """
    Handle Twilio WhatsApp webhook notification.

    Args:
        payload: Twilio webhook form data
        signature: X-Twilio-Signature header
        url: Full webhook URL for signature validation

    Returns:
        Dict with processing status

    Raises:
        Exception: If signature is invalid or processing fails
    """
    try:
        # Validate Twilio signature
        if not validate_twilio_signature(url, payload, signature):
            raise Exception("Invalid Twilio signature")

        # Parse WhatsApp message
        whatsapp_data = parse_twilio_webhook(payload)

        logger.info(
            "whatsapp_webhook_received",
            from_phone=whatsapp_data["from_phone"],
            profile_name=whatsapp_data["profile_name"],
            message_sid=whatsapp_data["message_sid"]
        )

        # Create agent for WhatsApp channel
        agent = DigitalFTEAgent(channel="whatsapp")

        # Process with agent
        # Use phone as customer identifier, profile_name for name
        customer_email = f"whatsapp-{whatsapp_data['whatsapp_id'] or whatsapp_data['from_phone'].replace('+', '')}@whatsapp.user"
        customer_name = whatsapp_data["profile_name"] or whatsapp_data["from_phone"]

        result = await agent.handle_customer_request(
            customer_email=customer_email,
            customer_name=customer_name,
            message=whatsapp_data["body"],
            channel_message_id=f"whatsapp_{whatsapp_data['message_sid']}",
            phone=whatsapp_data["from_phone"]
        )

        if not result["success"]:
            raise Exception("Agent processing failed")

        # Format response for WhatsApp (concise, conversational)
        formatted_response = format_whatsapp_response(
            result["response"],
            max_chars=settings.channel_whatsapp_max_response_length
        )

        # Check if message needs splitting
        if len(formatted_response) > settings.channel_whatsapp_split_threshold:
            # Split and send multiple messages
            message_parts = split_whatsapp_message(
                formatted_response,
                max_length=settings.channel_whatsapp_split_threshold
            )

            await send_multiple_whatsapp_messages(
                to_phone=whatsapp_data["from_phone"],
                message_parts=message_parts,
                from_phone=settings.twilio_whatsapp_from
            )

            logger.info(
                "whatsapp_message_split",
                from_phone=whatsapp_data["from_phone"],
                num_parts=len(message_parts),
                original_length=len(formatted_response)
            )

        else:
            # Send single message
            await send_whatsapp_message(
                to_phone=whatsapp_data["from_phone"],
                body=formatted_response,
                from_phone=settings.twilio_whatsapp_from
            )

        logger.info(
            "whatsapp_webhook_processed",
            from_phone=whatsapp_data["from_phone"],
            escalated=result.get("escalated", False),
            processing_time_ms=result.get("processing_time_ms", 0)
        )

        return {
            "status": "processed",
            "ticket_id": whatsapp_data["message_sid"],
            "processed": True
        }

    except Exception as e:
        logger.error(
            "whatsapp_webhook_error",
            error=str(e),
            exc_info=True
        )
        raise
