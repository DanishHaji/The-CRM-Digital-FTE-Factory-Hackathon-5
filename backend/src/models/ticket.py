"""
Digital FTE Customer Success Agent - Ticket Pydantic Models
Support ticket models with source_channel and escalation tracking
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..utils.validators import channel_validator, validate_status


class TicketBase(BaseModel):
    """Base ticket model with common fields."""
    conversation_id: UUID = Field(..., description="Conversation UUID")
    source_channel: str = Field(..., description="Channel where ticket originated")
    priority: str = Field(default="medium", description="Ticket priority")
    status: str = Field(default="pending", description="Ticket status")
    assigned_to: Optional[UUID] = Field(None, description="NULL for Digital FTE, user_id for human")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")

    _validate_channel = validator('source_channel', allow_reuse=True)(channel_validator)

    @validator('priority')
    def validate_priority(cls, v):
        """Validate ticket priority."""
        allowed = ['low', 'medium', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f"priority must be one of: {', '.join(allowed)}")
        return v

    @validator('status')
    def validate_status_field(cls, v):
        """Validate ticket status."""
        allowed = ['pending', 'processing', 'responded', 'escalated']
        return validate_status(v, allowed)


class TicketCreate(TicketBase):
    """Model for creating a new ticket."""
    pass


class TicketUpdate(BaseModel):
    """Model for updating ticket information."""
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    escalation_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None

    @validator('priority')
    def validate_priority(cls, v):
        """Validate ticket priority."""
        if v is None:
            return v
        allowed = ['low', 'medium', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f"priority must be one of: {', '.join(allowed)}")
        return v

    @validator('status')
    def validate_status_field(cls, v):
        """Validate ticket status."""
        if v is None:
            return v
        allowed = ['pending', 'processing', 'responded', 'escalated']
        return validate_status(v, allowed)


class Ticket(TicketBase):
    """Complete ticket model with database fields."""
    ticket_id: UUID
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketSummary(BaseModel):
    """
    Ticket summary with customer and conversation information.
    Used for reporting and analytics.
    """
    ticket_id: UUID
    status: str
    priority: str
    source_channel: str
    customer_email: str
    customer_name: Optional[str]
    initial_channel: str
    message_count: int
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
