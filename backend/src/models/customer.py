"""
Digital FTE Customer Success Agent - Customer Pydantic Models
Customer and CustomerIdentifier models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..utils.validators import email_validator, phone_validator


class CustomerBase(BaseModel):
    """Base customer model with common fields."""
    email: str = Field(..., description="Customer email (primary identifier)")
    name: Optional[str] = Field(None, description="Customer name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific metadata")

    _validate_email = validator('email', allow_reuse=True)(email_validator)


class CustomerCreate(CustomerBase):
    """Model for creating a new customer."""
    pass


class CustomerUpdate(BaseModel):
    """Model for updating customer information."""
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Customer(CustomerBase):
    """Complete customer model with database fields."""
    customer_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerIdentifierBase(BaseModel):
    """Base customer identifier model."""
    identifier_type: str = Field(..., description="Type: email, phone, whatsapp_id")
    identifier_value: str = Field(..., description="Identifier value")
    verified: bool = Field(default=False, description="Whether identifier is verified")

    @validator('identifier_type')
    def validate_identifier_type(cls, v):
        """Validate identifier type."""
        allowed = ['email', 'phone', 'whatsapp_id']
        if v not in allowed:
            raise ValueError(f"identifier_type must be one of: {', '.join(allowed)}")
        return v

    @validator('identifier_value')
    def validate_identifier_value(cls, v, values):
        """Validate identifier value based on type."""
        identifier_type = values.get('identifier_type')

        if identifier_type == 'email':
            return email_validator(cls, v)
        elif identifier_type in ['phone', 'whatsapp_id']:
            return phone_validator(cls, v)

        return v


class CustomerIdentifierCreate(CustomerIdentifierBase):
    """Model for creating a new customer identifier."""
    customer_id: UUID


class CustomerIdentifier(CustomerIdentifierBase):
    """Complete customer identifier model with database fields."""
    identifier_id: UUID
    customer_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerProfile(BaseModel):
    """
    Customer profile with all identifiers.
    Used for cross-channel customer identification.
    """
    customer_id: UUID
    email: str
    name: Optional[str]
    identifiers: list[CustomerIdentifier] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
