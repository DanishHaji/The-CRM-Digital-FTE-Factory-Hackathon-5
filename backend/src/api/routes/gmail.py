"""Gmail webhook endpoint (Google Pub/Sub) - Direct Processing."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request

from ..models.requests import GmailWebhookPayload
from ...channels.gmail_handler import handle_gmail_webhook
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/gmail",
    status_code=status.HTTP_200_OK,
    summary="Gmail Pub/Sub webhook",
    description="Receive Gmail notifications via Google Cloud Pub/Sub and process with Digital FTE agent",
)
async def gmail_webhook_endpoint(
    payload: GmailWebhookPayload,
    request: Request,
):
    """
    Handle Gmail webhook from Google Cloud Pub/Sub.

    Process:
    1. Decode Pub/Sub message (base64)
    2. Parse email content (from, to, subject, body)
    3. Process with Digital FTE agent
    4. Send formatted email response via Gmail API

    Note: This endpoint must respond within 10 seconds for Pub/Sub.
    Processing happens inline (no Kafka) for MVP simplicity.

    Args:
        payload: Google Pub/Sub webhook payload
        request: FastAPI request (for headers/validation)

    Returns:
        Dict with status and ticket_id

    Raises:
        HTTPException: 400 for invalid payload, 500 for system errors
    """

    try:
        # Process webhook (parse email, run agent, send response)
        result = await handle_gmail_webhook(payload.dict())

        logger.info(
            "gmail_webhook_success",
            ticket_id=result.get("ticket_id"),
            status=result.get("status")
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "gmail_webhook_processing_failed",
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True,
        )

        # Return 200 OK even on error to prevent Pub/Sub retries
        # Log error for monitoring/alerting
        return {
            "status": "error",
            "message": "Gmail notification processing failed",
            "ticket_id": None,
        }


@router.get(
    "/gmail/health",
    summary="Gmail webhook health check",
    description="Verify Gmail webhook endpoint is accessible",
)
async def gmail_webhook_health() -> dict:
    """Health check for Gmail webhook (for Google verification)."""

    return {
        "status": "healthy",
        "webhook": "gmail",
        "channel": "email",
        "timestamp": datetime.utcnow().isoformat(),
    }
