"""
Gmail channel handler for Digital FTE Customer Success Agent.
Handles Gmail Pub/Sub webhooks, email parsing, and Gmail API integration.
"""

import base64
import json
import re
import time
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.validators import validate_email
from ..agent.customer_success_agent import DigitalFTEAgent

settings = get_settings()
logger = get_logger(__name__)


def parse_pubsub_message(pubsub_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Gmail Pub/Sub push notification message.

    Args:
        pubsub_payload: Pub/Sub message payload from Gmail webhook

    Returns:
        Dict with parsed email fields: from_email, from_name, to_email, subject, body, message_id

    Raises:
        ValueError: If message format is invalid or required fields missing
    """
    try:
        # Extract base64-encoded message data
        message_data = pubsub_payload.get("message", {}).get("data", "")
        message_id = pubsub_payload.get("message", {}).get("messageId", "")

        if not message_data:
            raise ValueError("Missing message data in Pub/Sub payload")

        # Decode base64
        try:
            decoded_data = base64.b64decode(message_data).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decode base64 message data: {e}")

        # Parse email content
        email_message = email.message_from_string(decoded_data)

        # Extract fields
        from_field = email_message.get("From", "")
        to_field = email_message.get("To", "")
        subject = email_message.get("Subject", "(No Subject)")

        if not from_field:
            raise ValueError("Email missing 'From' field")

        # Extract sender email and name
        from_email, from_name = extract_sender_info(from_field)
        to_email = extract_email_address(to_field) if to_field else settings.support_email

        # Extract body (prefer plain text, fallback to HTML)
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                elif content_type == "text/html" and not body:
                    # Fallback to HTML if no plain text
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    body = strip_html_tags(html_body)
        else:
            body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

        # Clean up body
        body = body.strip()

        if not body:
            raise ValueError("Email body is empty")

        return {
            "from_email": from_email,
            "from_name": from_name,
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "message_id": message_id,
            "received_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error("gmail_parse_error", error=str(e), exc_info=True)
        raise


def extract_sender_info(from_field: str) -> Tuple[str, Optional[str]]:
    """
    Extract email address and name from From field.

    Args:
        from_field: From header field (e.g., "Alice Smith <alice@example.com>")

    Returns:
        Tuple of (email_address, name) - name can be None

    Raises:
        ValueError: If email format is invalid
    """
    # Pattern: "Name" <email@domain.com> or just email@domain.com
    match = re.match(r'^(?:"?([^"<]+)"?\s*)?<?([^>]+@[^>]+)>?$', from_field.strip())

    if not match:
        raise ValueError(f"Invalid From field format: {from_field}")

    name = match.group(1).strip() if match.group(1) else None
    email_addr = match.group(2).strip()

    # Validate email
    email_addr = validate_email(email_addr)

    return email_addr, name


def extract_email_address(email_field: str) -> str:
    """
    Extract email address from email field (handles <email@domain.com> format).

    Args:
        email_field: Email field string

    Returns:
        Email address
    """
    match = re.search(r'([^<\s]+@[^>\s]+)', email_field)
    if match:
        return validate_email(match.group(1))
    return validate_email(email_field.strip())


def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags from string (simple implementation).

    Args:
        html: HTML string

    Returns:
        Plain text
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    return text.strip()


def format_email_response(response_text: str, customer_name: Optional[str] = None, max_words: int = 500) -> str:
    """
    Format AI response for email channel with formal greeting and signature.

    Args:
        response_text: AI-generated response text
        customer_name: Customer's name for greeting
        max_words: Maximum words in response (default 500 for email)

    Returns:
        Formatted email body with greeting and signature
    """
    # Formal greeting
    if customer_name:
        greeting = f"Dear {customer_name},"
    else:
        greeting = "Hello,"

    # Truncate response if too long
    words = response_text.split()
    if len(words) > max_words:
        response_text = ' '.join(words[:max_words]) + "..."
        logger.warning("email_response_truncated", original_words=len(words), max_words=max_words)

    # Formal signature
    signature = """

Best regards,
Digital FTE Customer Success Team

---
This is an automated response powered by AI. If you need further assistance, please reply to this email and a human agent will help you."""

    # Combine
    formatted = f"{greeting}\n\n{response_text}{signature}"

    return formatted


def get_gmail_service():
    """
    Create Gmail API service instance with authentication.

    Returns:
        Gmail API service object

    Raises:
        Exception: If authentication fails
    """
    try:
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            settings.gmail_credentials_file,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )

        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)

        return service

    except Exception as e:
        logger.error("gmail_auth_error", error=str(e), exc_info=True)
        raise


async def send_gmail_message(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email via Gmail API.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (plain text)
        from_email: Sender email (defaults to settings.support_email)

    Returns:
        Dict with success status and message_id

    Raises:
        Exception: If Gmail API call fails
    """
    try:
        if not from_email:
            from_email = settings.support_email

        # Create MIME message
        message = MIMEText(body, 'plain', 'utf-8')
        message['to'] = to_email
        message['from'] = from_email
        message['subject'] = subject

        # Encode for Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send via Gmail API
        service = get_gmail_service()

        # Execute send (run in thread pool since it's blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        )

        logger.info(
            "gmail_message_sent",
            to_email=to_email,
            subject=subject,
            message_id=result['id']
        )

        return {
            "success": True,
            "message_id": result['id']
        }

    except HttpError as e:
        error_detail = json.loads(e.content.decode('utf-8'))
        error_message = error_detail.get('error', {}).get('message', str(e))

        logger.error(
            "gmail_api_error",
            status_code=e.resp.status,
            error=error_message,
            to_email=to_email
        )

        # Check for quota exceeded
        if e.resp.status == 429:
            raise Exception(f"Gmail API quota exceeded: {error_message}")

        raise Exception(f"Gmail API error: {error_message}")

    except Exception as e:
        logger.error("gmail_send_error", error=str(e), to_email=to_email, exc_info=True)
        raise


async def send_gmail_message_with_retry(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Send Gmail message with exponential backoff retry.

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Email body
        from_email: Sender email
        max_retries: Maximum retry attempts

    Returns:
        Dict with success status and message_id
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await send_gmail_message(to_email, subject, body, from_email)

            if attempt > 0:
                logger.info("gmail_retry_success", attempt=attempt + 1)

            return result

        except Exception as e:
            last_error = e

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                logger.warning(
                    "gmail_send_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_seconds=wait_time,
                    error=str(e)
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "gmail_send_failed_all_retries",
                    attempts=max_retries,
                    error=str(e)
                )

    raise last_error


async def handle_gmail_webhook(pubsub_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Gmail Pub/Sub webhook notification.

    Args:
        pubsub_payload: Pub/Sub message payload

    Returns:
        Dict with processing status and ticket_id
    """
    try:
        # Parse email from Pub/Sub message
        email_data = parse_pubsub_message(pubsub_payload)

        logger.info(
            "gmail_webhook_received",
            from_email=email_data["from_email"],
            from_name=email_data["from_name"],
            subject=email_data["subject"],
            message_id=email_data["message_id"]
        )

        # Create agent for email channel
        agent = DigitalFTEAgent(channel="email")

        # Process with agent
        result = await agent.handle_customer_request(
            customer_email=email_data["from_email"],
            customer_name=email_data["from_name"] or email_data["from_email"].split('@')[0],
            message=f"Subject: {email_data['subject']}\n\n{email_data['body']}",
            channel_message_id=f"gmail_{email_data['message_id']}"
        )

        if not result["success"]:
            raise Exception("Agent processing failed")

        # Format response for email
        formatted_response = format_email_response(
            result["response"],
            email_data["from_name"]
        )

        # Send email response with retry
        await send_gmail_message_with_retry(
            to_email=email_data["from_email"],
            subject=f"Re: {email_data['subject']}",
            body=formatted_response,
            from_email=settings.support_email
        )

        logger.info(
            "gmail_webhook_processed",
            from_email=email_data["from_email"],
            escalated=result.get("escalated", False),
            processing_time_ms=result.get("processing_time_ms", 0)
        )

        return {
            "status": "received",
            "ticket_id": email_data["message_id"],
            "processed": True
        }

    except Exception as e:
        logger.error(
            "gmail_webhook_error",
            error=str(e),
            exc_info=True
        )
        raise
