"""
Digital FTE Customer Success Agent - Custom Pydantic Validators
Email, phone, channel enum validators
"""

import re
from typing import Any
from pydantic import validator


# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Phone number normalization regex (removes all non-digits)
PHONE_REGEX = re.compile(r'\D')


def validate_email(email: str) -> str:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        str: Validated email (lowercase)

    Raises:
        ValueError: If email format is invalid
    """
    email = email.strip().lower()

    if not EMAIL_REGEX.match(email):
        raise ValueError(f"Invalid email format: {email}")

    return email


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number by removing all non-digit characters.
    Handles international formats like +1-234-567-8900 → +12345678900

    Args:
        phone: Phone number in any format

    Returns:
        str: Normalized phone number (digits and + only)

    Example:
        normalize_phone("+1 (234) 567-8900") → "+12345678900"
        normalize_phone("234-567-8900") → "2345678900"
    """
    phone = phone.strip()

    # Preserve leading + for international numbers
    has_plus = phone.startswith('+')

    # Remove all non-digit characters
    digits = PHONE_REGEX.sub('', phone)

    # Add + back if it was present
    return f"+{digits}" if has_plus else digits


def validate_channel(channel: str) -> str:
    """
    Validate channel name.

    Args:
        channel: Channel name

    Returns:
        str: Validated channel (lowercase)

    Raises:
        ValueError: If channel is not one of: email, whatsapp, web
    """
    channel = channel.strip().lower()

    if channel not in ['email', 'whatsapp', 'web']:
        raise ValueError(f"Invalid channel: {channel}. Must be one of: email, whatsapp, web")

    return channel


def validate_status(status: str, allowed_values: list[str]) -> str:
    """
    Validate status against allowed values.

    Args:
        status: Status value
        allowed_values: List of allowed status values

    Returns:
        str: Validated status (lowercase)

    Raises:
        ValueError: If status is not in allowed_values
    """
    status = status.strip().lower()

    if status not in allowed_values:
        raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(allowed_values)}")

    return status


# Pydantic validator decorators for reuse in models

def email_validator(cls, v: str) -> str:
    """Pydantic validator for email fields."""
    return validate_email(v)


def phone_validator(cls, v: str) -> str:
    """Pydantic validator for phone fields."""
    return normalize_phone(v)


def channel_validator(cls, v: str) -> str:
    """Pydantic validator for channel fields."""
    return validate_channel(v)
