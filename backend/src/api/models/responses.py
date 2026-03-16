"""Response models for API endpoints."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketResponse(BaseModel):
    """Response after creating a support ticket."""

    ticket_id: str = Field(..., description="Unique ticket identifier (UUID)")
    status: str = Field(..., description="Current ticket status")
    message: str = Field(..., description="AI response or success message")
    estimated_response_time: str = Field(..., description="Estimated response time")
    created_at: str = Field(..., description="Ticket creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
                "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
                "customer_id": "770e8400-e29b-41d4-a716-446655440002",
                "status": "pending",
                "channel": "web",
                "message": "Support ticket created successfully. Our team will respond within 24 hours.",
                "created_at": "2026-03-16T10:30:00Z"
            }
        }


class TicketStatusResponse(BaseModel):
    """Response for ticket status query."""

    ticket_id: str = Field(..., description="Ticket identifier")
    status: TicketStatus = Field(..., description="Current status")
    channel: str = Field(..., description="Support channel")
    customer_email: str = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    created_at: datetime = Field(..., description="Ticket creation time")
    updated_at: datetime = Field(..., description="Last update time")
    response: Optional[str] = Field(None, description="Agent's response (if available)")
    escalation_reason: Optional[str] = Field(None, description="Escalation reason (if escalated)")

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "responded",
                "channel": "web",
                "customer_email": "john.doe@example.com",
                "customer_name": "John Doe",
                "created_at": "2026-03-16T10:30:00Z",
                "updated_at": "2026-03-16T10:35:00Z",
                "response": "Thank you for contacting us! To reset your password, please follow these steps: 1. Go to the login page...",
                "escalation_reason": None
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server time")
    database: str = Field(..., description="Database connection status")
    kafka: str = Field(..., description="Kafka connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-03-16T10:30:00Z",
                "database": "connected",
                "kafka": "connected"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid email format",
                "detail": {
                    "field": "email",
                    "value": "invalid-email"
                },
                "request_id": "req_1234567890"
            }
        }


class AsyncProcessingResponse(BaseModel):
    """Response for async processing (webhooks)."""

    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    ticket_id: Optional[str] = Field(None, description="Ticket ID if created")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "processing",
                "message": "Message received and queued for processing",
                "ticket_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
