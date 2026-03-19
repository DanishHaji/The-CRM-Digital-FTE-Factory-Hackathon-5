"""WhatsApp webhook endpoint (Twilio) - Direct Processing."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Request, Form, Header
from fastapi.responses import PlainTextResponse

from ...channels.whatsapp_handler import handle_whatsapp_webhook
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/whatsapp",
    status_code=status.HTTP_200_OK,
    summary="WhatsApp (Twilio) webhook",
    description="Receive WhatsApp messages via Twilio webhook and process with Digital FTE agent",
    response_class=PlainTextResponse
)
async def whatsapp_webhook_endpoint(
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
):
    """
    Handle WhatsApp message from Twilio webhook.

    Process:
    1. Validate Twilio signature (security)
    2. Parse WhatsApp message
    3. Process with Digital FTE agent
    4. Send concise response via Twilio API (with splitting if > 1600 chars)

    Args:
        Form parameters from Twilio webhook
        x_twilio_signature: Twilio signature header for validation

    Returns:
        Empty TwiML response (Twilio expects 200 OK)

    Note: Twilio expects 200 OK within 15 seconds.
    Processing happens inline (no Kafka) for MVP simplicity.
    """

    try:
        # Build payload from form data
        payload = {
            "MessageSid": MessageSid,
            "AccountSid": AccountSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": NumMedia,
            "ProfileName": ProfileName,
            "WaId": WaId
        }

        # Get full URL for signature validation
        url = str(request.url)

        # Get signature (default to empty if not provided)
        signature = x_twilio_signature or ""

        # Process webhook (validate signature, parse, run agent, send response)
        result = await handle_whatsapp_webhook(payload, signature, url)

        logger.info(
            "whatsapp_webhook_success",
            ticket_id=result.get("ticket_id"),
            status=result.get("status"),
            message_sid=MessageSid
        )

        # Return empty TwiML response (Twilio expects this)
        return PlainTextResponse(content="", status_code=200)

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

        # Check if it's a signature validation error
        if "Invalid Twilio signature" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "InvalidSignature",
                    "message": "Twilio signature validation failed"
                }
            )

        # Return 200 OK to prevent Twilio retries on transient errors
        # Twilio will not retry if we return 200
        return PlainTextResponse(content="", status_code=200)


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
        "channel": "whatsapp",
        "timestamp": datetime.utcnow().isoformat(),
    }
