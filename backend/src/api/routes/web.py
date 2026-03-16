"""Web form webhook endpoint - Simplified without Kafka."""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from ..models.requests import WebFormSubmission
from ..models.responses import TicketResponse
from ...agent.customer_success_agent import DigitalFTEAgent
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/web",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit web support form",
    description="Receive customer support request from web form - Direct processing with Groq AI",
)
async def handle_web_submission(submission: WebFormSubmission) -> TicketResponse:
    """
    Handle web form submission - Direct agent processing (no Kafka).

    Process:
    1. Validate form data (automatic via Pydantic)
    2. Process with Groq AI agent directly
    3. Save to database
    4. Return response

    Args:
        submission: Web form data (name, email, message)

    Returns:
        TicketResponse with ticket_id, status, and AI response

    Raises:
        HTTPException: 422 for validation errors, 500 for system errors
    """

    try:
        # Generate unique ticket ID
        ticket_id = str(uuid.uuid4())
        channel_message_id = f"web_{ticket_id}"

        logger.info(
            "web_form_submission_received",
            customer_email=submission.email,
            customer_name=submission.name,
            message_length=len(submission.message),
        )

        # Create agent and process request directly
        agent = DigitalFTEAgent(channel="web")

        result = await agent.handle_customer_request(
            customer_email=submission.email,
            customer_name=submission.name,
            message=submission.message,
            channel_message_id=channel_message_id,
        )

        if not result["success"]:
            logger.error("agent_processing_failed", error=result.get("error"))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process your request. Please try again.",
            )

        # Return response to customer
        response_message = result["response"]
        escalated = result.get("escalated", False)

        logger.info(
            "web_form_submission_processed",
            ticket_id=ticket_id,
            processing_time_ms=result["processing_time_ms"],
            escalated=escalated,
        )

        return TicketResponse(
            ticket_id=ticket_id,
            status="escalated" if escalated else "resolved",
            message=response_message,
            estimated_response_time="Immediate (AI-powered response)",
            created_at=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "web_form_submission_error",
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System error: {str(exc)}",
        )
