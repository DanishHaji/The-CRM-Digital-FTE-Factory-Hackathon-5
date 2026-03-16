"""Gmail webhook endpoint (Google Pub/Sub)."""

import base64
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request
from api.models.requests import GmailWebhookPayload
from api.models.responses import AsyncProcessingResponse
from kafka.producer import publish_message
from kafka.topics import TOPIC_INCOMING, TOPIC_GMAIL, create_ticket_message
from utils.logger import get_logger

router = APIRouter(prefix="/api/webhooks", tags=["gmail"])
logger = get_logger(__name__)


@router.post(
    "/gmail",
    response_model=AsyncProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Gmail Pub/Sub webhook",
    description="Receive Gmail notifications via Google Cloud Pub/Sub",
)
async def handle_gmail_webhook(
    payload: GmailWebhookPayload,
    request: Request,
) -> AsyncProcessingResponse:
    """
    Handle Gmail webhook from Google Cloud Pub/Sub.

    Process:
    1. Decode Pub/Sub message (base64)
    2. Extract Gmail message ID
    3. Fetch full email using Gmail API (in worker)
    4. Publish to Kafka for agent processing

    Note: This endpoint must respond within 10 seconds for Pub/Sub.
    Actual email fetching happens asynchronously in worker.

    Args:
        payload: Google Pub/Sub webhook payload
        request: FastAPI request (for headers/validation)

    Returns:
        AsyncProcessingResponse confirming message queued

    Raises:
        HTTPException: 400 for invalid payload, 500 for system errors
    """

    try:
        # Decode Pub/Sub message data (base64 encoded)
        message_data = payload.message.get("data", "")
        if not message_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidPayload",
                    "message": "Missing message data in Pub/Sub payload",
                }
            )

        # Decode base64
        try:
            decoded_data = base64.b64decode(message_data).decode("utf-8")
            gmail_notification = json.loads(decoded_data)
        except Exception as decode_exc:
            logger.error(
                "gmail_webhook_decode_failed",
                error_message=str(decode_exc),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "DecodingError",
                    "message": "Failed to decode Pub/Sub message data",
                }
            )

        # Extract Gmail message ID and history ID
        gmail_message_id = gmail_notification.get("emailAddress")
        history_id = gmail_notification.get("historyId")

        if not gmail_message_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidPayload",
                    "message": "Missing Gmail message ID",
                }
            )

        # Generate ticket ID
        ticket_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())

        # Create Kafka message for Gmail channel
        # Note: Full email will be fetched by worker using Gmail API
        kafka_message = create_ticket_message(
            ticket_id=ticket_id,
            conversation_id=conversation_id,
            customer_id="",  # Will be resolved after fetching email
            channel="email",
            message="",  # Will be populated by worker
            channel_message_id=gmail_message_id,
        )

        # Add Gmail-specific metadata
        kafka_message["metadata"] = {
            "gmail_message_id": gmail_message_id,
            "history_id": history_id,
            "pubsub_message_id": payload.message.get("messageId"),
            "pubsub_publish_time": payload.message.get("publishTime"),
            "subscription": payload.subscription,
        }

        # Publish to both unified and channel-specific topics
        await publish_message(
            topic=TOPIC_GMAIL,
            key=ticket_id,
            value=kafka_message,
        )

        logger.info(
            "gmail_webhook_received",
            ticket_id=ticket_id,
            gmail_message_id=gmail_message_id,
            history_id=history_id,
        )

        # Return 200 OK immediately (required by Pub/Sub)
        return AsyncProcessingResponse(
            status="processing",
            message="Gmail notification received and queued for processing",
            ticket_id=ticket_id,
        )

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
        return AsyncProcessingResponse(
            status="error",
            message="Gmail notification processing failed",
            ticket_id=None,
        )


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
        "timestamp": datetime.utcnow().isoformat(),
    }
