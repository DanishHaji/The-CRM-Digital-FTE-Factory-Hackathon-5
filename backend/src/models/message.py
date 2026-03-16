"""
Digital FTE Customer Success Agent - Message Pydantic Models
Message models with channel, direction, role tracking
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..utils.validators import channel_validator


class MessageBase(BaseModel):
    """Base message model with common fields."""
    conversation_id: UUID = Field(..., description="Conversation UUID")
    channel: str = Field(..., description="Message channel")
    direction: str = Field(..., description="Message direction: inbound or outbound")
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    channel_message_id: Optional[str] = Field(None, description="Channel-specific message ID for deduplication")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific metadata")

    _validate_channel = validator('channel', allow_reuse=True)(channel_validator)

    @validator('direction')
    def validate_direction(cls, v):
        """Validate message direction."""
        allowed = ['inbound', 'outbound']
        if v not in allowed:
            raise ValueError(f"direction must be one of: {', '.join(allowed)}")
        return v

    @validator('role')
    def validate_role(cls, v):
        """Validate message role."""
        allowed = ['user', 'assistant']
        if v not in allowed:
            raise ValueError(f"role must be one of: {', '.join(allowed)}")
        return v


class MessageCreate(MessageBase):
    """Model for creating a new message."""
    pass


class Message(MessageBase):
    """Complete message model with database fields."""
    message_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
