"""WhatsApp webhook endpoint (Twilio)."""

import base64
import uuid
import hmac
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Form, Header
from api.models.requests import WhatsAppWebhookPayload
from api.models.responses import AsyncProcessingResponse
from kafka.producer import publish_message
from kafka.topics import TOPIC_INCOMING, TOPIC_WHATSAPP, create_ticket_message
from utils.config import settings
from utils.logger import get_logger

router = APIRouter(prefix="/api/webhooks", tags=["whatsapp"])
logger = get_logger(__name__)


def validate_twilio_signature(
    url: str,
    params: dict,
    signature: str,
    auth_token: str,
) -> bool:
    """
    Validate Twilio webhook signature for security.

    Args:
        url: Full webhook URL
        params: POST parameters
        signature: X-Twilio-Signature header value
        auth_token: Twilio auth token

    Returns:
        True if signature is valid, False otherwise
    """

    # Sort parameters
    sorted_params = sorted(params.items())

    # Concatenate: URL + sorted params
    data = url + "".join(f"{k}{v}" for k, v in sorted_params)

    # Compute HMAC-SHA256
    computed_signature = base64.b64encode(
        hmac.new(
            auth_token.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256
        ).digest()
    ).decode("utf-8")

    # Compare signatures (constant-time comparison)
    return hmac.compare_digest(computed_signature, signature)


@router.post(
    "/whatsapp",
    response_model=AsyncProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="WhatsApp (Twilio) webhook",
    description="Receive WhatsApp messages via Twilio webhook",
)
async def handle_whatsapp_webhook(
    request: Request,
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form(default="0"),
    ProfileName: Optional[str] = Form(default=None),
    WaId: Optional[str] = Form(default=None),
    x_twilio_signature: Optional[str] = Header(default=None, alias="X-Twilio-Signature"),
) -> AsyncProcessingResponse:
    """
    Handle WhatsApp message from Twilio webhook.

    Process:
    1. Validate Twilio signature (security)
    2. Extract message details
    3. Normalize phone number
    4. Publish to Kafka for agent processing

    Args:
        Form parameters from Twilio webhook
        x_twilio_signature: Twilio signature header for validation

    Returns:
        AsyncProcessingResponse (must return 200 OK to Twilio)

    Note: Twilio expects 200 OK within 15 seconds
    """

    try:
        # Validate Twilio signature (if configured)
        if settings.twilio_auth_token and x_twilio_signature:
            form_data = await request.form()
            params = dict(form_data)

            is_valid = validate_twilio_signature(
                url=str(request.url),
                params=params,
                signature=x_twilio_signature,
                auth_token=settings.twilio_auth_token,
            )

            if not is_valid:
                logger.warning(
                    "twilio_signature_validation_failed",
                    message_sid=MessageSid,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "InvalidSignature",
                        "message": "Twilio signature validation failed",
                    }
                )

        # Extract WhatsApp number (remove 'whatsapp:' prefix)
        whatsapp_number = From.replace("whatsapp:", "")

        # Generate ticket ID
        ticket_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Create Kafka message
        kafka_message = create_ticket_message(
            ticket_id=ticket_id,
            conversation_id=conversation_id,
            customer_id="",  # Will be resolved by agent
            channel="whatsapp",
            message=Body,
            channel_message_id=MessageSid,
        )

        # Add WhatsApp-specific metadata
        kafka_message["metadata"] = {
            "message_sid": MessageSid,
            "account_sid": AccountSid,
            "from_number": whatsapp_number,
            "to_number": To.replace("whatsapp:", ""),
            "profile_name": ProfileName,
            "wa_id": WaId,
            "num_media": int(NumMedia),
        }

        # Publish to both unified and channel-specific topics
        await publish_message(
            topic=TOPIC_WHATSAPP,
            key=ticket_id,
            value=kafka_message,
        )

        await publish_message(
            topic=TOPIC_INCOMING,
            key=ticket_id,
            value=kafka_message,
        )

        logger.info(
            "whatsapp_message_received",
            ticket_id=ticket_id,
            message_sid=MessageSid,
            from_number=whatsapp_number,
            message_length=len(Body),
        )

        # Return 200 OK to Twilio (required)
        return AsyncProcessingResponse(
            status="processing",
            message="WhatsApp message received and queued for processing",
            ticket_id=ticket_id,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "whatsapp_webhook_processing_failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
            message_sid=MessageSid if 'MessageSid' in locals() else None,
            exc_info=True,
        )

        # Return 200 OK to prevent Twilio retries on transient errors
        return AsyncProcessingResponse(
            status="error",
            message="WhatsApp message processing failed",
            ticket_id=None,
        )


@router.get(
    "/whatsapp/health",
    summary="WhatsApp webhook health check",
    description="Verify WhatsApp webhook endpoint is accessible",
)
async def whatsapp_webhook_health() -> dict:
    """Health check for WhatsApp webhook (for Twilio verification)."""

    return {
        "status": "healthy",
        "webhook": "whatsapp",
        "timestamp": datetime.utcnow().isoformat(),
    }
