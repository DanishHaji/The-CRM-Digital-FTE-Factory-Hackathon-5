"""Request models for API endpoints."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, validator
from ...utils.validators import validate_email, normalize_phone


class WebFormSubmission(BaseModel):
    """Web support form submission request."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Customer's full name"
    )
    email: EmailStr = Field(
        ...,
        description="Customer's email address (primary identifier)"
    )
    message: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Customer's support request message"
    )

    @validator('email')
    def validate_email_format(cls, v):
        """Validate and normalize email."""
        return validate_email(v)

    @validator('name')
    def validate_name_format(cls, v):
        """Validate name is not empty after stripping."""
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters")
        return cleaned

    @validator('message')
    def validate_message_content(cls, v):
        """Validate message is meaningful."""
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Message must be at least 10 characters")
        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "message": "I need help resetting my password. I've tried the forgot password link but haven't received an email."
            }
        }


class GmailMessage(BaseModel):
    """Gmail message metadata."""

    id: str = Field(..., description="Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    from_email: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender name")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text or HTML)")
    received_at: datetime = Field(..., description="Message received timestamp")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")

    @validator('from_email')
    def validate_from_email(cls, v):
        """Validate sender email."""
        return validate_email(v)


class GmailWebhookPayload(BaseModel):
    """Gmail Pub/Sub webhook payload."""

    message: Dict[str, Any] = Field(..., description="Pub/Sub message")
    subscription: str = Field(..., description="Pub/Sub subscription name")

    class Config:
        json_schema_extra = {
            "example": {
                "message": {
                    "data": "eyJlbWFpbElkIjogIjE4YzM1...",
                    "messageId": "2070443601311540",
                    "publishTime": "2021-02-26T19:13:55.749Z"
                },
                "subscription": "projects/myproject/subscriptions/gmail-subscription"
            }
        }


class WhatsAppMessage(BaseModel):
    """WhatsApp message from Twilio."""

    MessageSid: str = Field(..., description="Twilio message SID")
    From: str = Field(..., description="Sender WhatsApp number (whatsapp:+1234567890)")
    To: str = Field(..., description="Recipient WhatsApp number")
    Body: str = Field(..., description="Message body")
    ProfileName: Optional[str] = Field(None, description="Sender's WhatsApp profile name")
    NumMedia: int = Field(0, description="Number of media attachments")

    @validator('From')
    def validate_whatsapp_number(cls, v):
        """Extract and normalize WhatsApp phone number."""
        # WhatsApp format: whatsapp:+1234567890
        if v.startswith('whatsapp:'):
            phone = v.replace('whatsapp:', '')
            return normalize_phone(phone)
        return normalize_phone(v)


class WhatsAppWebhookPayload(BaseModel):
    """Twilio WhatsApp webhook payload (form-encoded)."""

    MessageSid: str
    AccountSid: str
    MessagingServiceSid: Optional[str] = None
    From: str  # whatsapp:+1234567890
    To: str
    Body: str
    NumMedia: str = "0"  # Twilio sends as string
    ProfileName: Optional[str] = None
    WaId: Optional[str] = None  # WhatsApp ID

    class Config:
        json_schema_extra = {
            "example": {
                "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "From": "whatsapp:+14155238886",
                "To": "whatsapp:+15558675310",
                "Body": "Hello, I need help with my order #12345",
                "NumMedia": "0",
                "ProfileName": "John Doe",
                "WaId": "14155238886"
            }
        }
