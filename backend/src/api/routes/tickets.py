"""Ticket status query endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from api.models.responses import TicketStatusResponse, TicketStatus
from database.connection import get_connection
from utils.logger import get_logger

router = APIRouter(prefix="/api/tickets", tags=["tickets"])
logger = get_logger(__name__)


@router.get(
    "/{ticket_id}/status",
    response_model=TicketStatusResponse,
    summary="Get ticket status",
    description="Query the current status and response for a support ticket",
)
async def get_ticket_status(ticket_id: str) -> TicketStatusResponse:
    """
    Get ticket status by ID.

    Retrieves:
    - Current ticket status (pending, processing, responded, escalated, closed)
    - Customer information
    - Agent response (if available)
    - Creation and update timestamps
    - Escalation reason (if applicable)

    Args:
        ticket_id: UUID of the ticket

    Returns:
        TicketStatusResponse with complete ticket information

    Raises:
        HTTPException: 404 if ticket not found, 500 for system errors
    """

    try:
        async with get_connection() as conn:
            # Query ticket with customer and response info
            row = await conn.fetchrow("""
                SELECT
                    t.ticket_id,
                    t.status,
                    t.channel,
                    t.created_at,
                    t.updated_at,
                    t.escalation_reason,
                    c.email AS customer_email,
                    c.name AS customer_name,
                    (
                        SELECT m.content
                        FROM messages m
                        WHERE m.conversation_id = t.conversation_id
                          AND m.sender_type = 'agent'
                        ORDER BY m.created_at DESC
                        LIMIT 1
                    ) AS response
                FROM tickets t
                JOIN conversations conv ON t.conversation_id = conv.conversation_id
                JOIN customers c ON conv.customer_id = c.customer_id
                WHERE t.ticket_id = $1
            """, ticket_id)

            if not row:
                logger.warning(
                    "ticket_not_found",
                    ticket_id=ticket_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "TicketNotFound",
                        "message": f"Ticket with ID {ticket_id} not found",
                    }
                )

            logger.info(
                "ticket_status_retrieved",
                ticket_id=ticket_id,
                status=row["status"],
            )

            return TicketStatusResponse(
                ticket_id=row["ticket_id"],
                status=TicketStatus(row["status"]),
                channel=row["channel"],
                customer_email=row["customer_email"],
                customer_name=row["customer_name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                response=row["response"],
                escalation_reason=row["escalation_reason"],
            )

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(
            "ticket_status_query_failed",
            ticket_id=ticket_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve ticket status",
            }
        )


@router.get(
    "/",
    summary="List customer tickets",
    description="Get all tickets for a customer by email",
)
async def list_customer_tickets(
    email: str = Query(..., description="Customer email address"),
    limit: int = Query(10, ge=1, le=100, description="Max number of tickets to return"),
) -> dict:
    """
    List all tickets for a customer.

    Args:
        email: Customer email address
        limit: Maximum number of tickets (1-100)

    Returns:
        List of tickets with status and response info
    """

    try:
        async with get_connection() as conn:
            rows = await conn.fetch("""
                SELECT
                    t.ticket_id,
                    t.status,
                    t.channel,
                    t.created_at,
                    t.updated_at,
                    (
                        SELECT m.content
                        FROM messages m
                        WHERE m.conversation_id = t.conversation_id
                          AND m.sender_type = 'customer'
                        ORDER BY m.created_at ASC
                        LIMIT 1
                    ) AS original_message,
                    (
                        SELECT m.content
                        FROM messages m
                        WHERE m.conversation_id = t.conversation_id
                          AND m.sender_type = 'agent'
                        ORDER BY m.created_at DESC
                        LIMIT 1
                    ) AS last_response
                FROM tickets t
                JOIN conversations conv ON t.conversation_id = conv.conversation_id
                JOIN customers c ON conv.customer_id = c.customer_id
                WHERE c.email = $1
                ORDER BY t.created_at DESC
                LIMIT $2
            """, email.lower().strip(), limit)

            tickets = [
                {
                    "ticket_id": row["ticket_id"],
                    "status": row["status"],
                    "channel": row["channel"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                    "original_message": row["original_message"],
                    "last_response": row["last_response"],
                }
                for row in rows
            ]

            logger.info(
                "customer_tickets_retrieved",
                customer_email=email,
                ticket_count=len(tickets),
            )

            return {
                "customer_email": email,
                "total_tickets": len(tickets),
                "tickets": tickets,
            }

    except Exception as exc:
        logger.error(
            "customer_tickets_query_failed",
            customer_email=email,
            error_type=type(exc).__name__,
            error_message=str(exc),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "Failed to retrieve customer tickets",
            }
        )
