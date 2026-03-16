"""
Digital FTE Customer Success Agent - Conversation Pydantic Models
Conversation models with channel and status tracking
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..utils.validators import channel_validator, validate_status


class ConversationBase(BaseModel):
    """Base conversation model with common fields."""
    customer_id: UUID = Field(..., description="Customer UUID")
    initial_channel: str = Field(..., description="Channel where conversation started")
    status: str = Field(default="open", description="Conversation status")

    _validate_channel = validator('initial_channel', allow_reuse=True)(channel_validator)

    @validator('status')
    def validate_status_field(cls, v):
        """Validate conversation status."""
        allowed = ['open', 'resolved', 'escalated']
        return validate_status(v, allowed)


class ConversationCreate(ConversationBase):
    """Model for creating a new conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Model for updating conversation information."""
    status: Optional[str] = None

    @validator('status')
    def validate_status_field(cls, v):
        """Validate conversation status."""
        if v is None:
            return v
        allowed = ['open', 'resolved', 'escalated']
        return validate_status(v, allowed)


class Conversation(ConversationBase):
    """Complete conversation model with database fields."""
    conversation_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
