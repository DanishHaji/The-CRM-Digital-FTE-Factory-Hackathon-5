"""
Phone number normalization utilities for cross-channel customer identification.
Handles various phone formats and international numbers.
"""

import re
from typing import Optional


def normalize_phone_number(phone: str, default_country: str = "US") -> str:
    """
    Normalize phone number to E.164 format (+[country][number]).

    Args:
        phone: Phone number in any format
        default_country: Default country code if not provided (default: US)

    Returns:
        Normalized phone number in E.164 format (e.g., "+14155238886")

    Raises:
        ValueError: If phone number is invalid

    Examples:
        >>> normalize_phone_number("(415) 523-8886")
        '+14155238886'
        >>> normalize_phone_number("+1-415-523-8886")
        '+14155238886'
        >>> normalize_phone_number("whatsapp:+14155238886")
        '+14155238886'
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")

    # Remove WhatsApp prefix if present
    phone = phone.replace("whatsapp:", "").strip()

    # Remove all whitespace, dashes, parentheses, dots
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

    # Extract digits and + sign
    digits_only = re.sub(r'[^\d+]', '', cleaned)

    # Handle different formats
    if digits_only.startswith('+'):
        # Already has country code
        normalized = digits_only

    elif digits_only.startswith('00'):
        # International format: 00 country code
        normalized = '+' + digits_only[2:]

    elif len(digits_only) == 10 and default_country == "US":
        # US number without country code: 10 digits
        normalized = '+1' + digits_only

    elif len(digits_only) == 11 and digits_only.startswith('1') and default_country == "US":
        # US number with country code but no +
        normalized = '+' + digits_only

    elif len(digits_only) > 10:
        # Assume it has country code, just missing +
        normalized = '+' + digits_only

    else:
        # Unknown format - try to add default country code
        if default_country == "US":
            normalized = '+1' + digits_only
        else:
            raise ValueError(f"Unable to normalize phone number: {phone}")

    # Validate final format
    if not re.match(r'^\+\d{10,15}$', normalized):
        raise ValueError(f"Invalid phone number format after normalization: {phone} -> {normalized}")

    return normalized


def extract_country_code(phone: str) -> Optional[str]:
    """
    Extract country code from normalized phone number.

    Args:
        phone: Normalized phone number (E.164 format)

    Returns:
        Country code (e.g., "1" for US, "44" for UK) or None if not found

    Example:
        >>> extract_country_code("+14155238886")
        '1'
        >>> extract_country_code("+442071234567")
        '44'
    """
    if not phone.startswith('+'):
        return None

    # Common country codes (1-3 digits)
    # Try 3 digits first, then 2, then 1
    for length in [3, 2, 1]:
        potential_code = phone[1:1+length]
        if potential_code.isdigit():
            # Validate common codes
            if length == 1 and potential_code == '1':
                return '1'  # US/Canada
            elif length == 2 and potential_code in ['44', '33', '49', '39', '34', '61', '81', '86', '91']:
                return potential_code  # UK, France, Germany, Italy, Spain, Australia, Japan, China, India
            elif length == 3:
                # Could be valid, return it
                return potential_code

    return None


def is_valid_phone_format(phone: str) -> bool:
    """
    Check if phone number is in valid E.164 format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid E.164 format, False otherwise

    Example:
        >>> is_valid_phone_format("+14155238886")
        True
        >>> is_valid_phone_format("(415) 523-8886")
        False
    """
    # E.164 format: +[1-3 digit country code][4-14 digit phone number]
    return bool(re.match(r'^\+\d{10,15}$', phone))


def format_phone_display(phone: str) -> str:
    """
    Format phone number for display (human-readable).

    Args:
        phone: Normalized phone number (E.164 format)

    Returns:
        Formatted phone number for display

    Example:
        >>> format_phone_display("+14155238886")
        '+1 (415) 523-8886'
        >>> format_phone_display("+442071234567")
        '+44 20 7123 4567'
    """
    if not is_valid_phone_format(phone):
        return phone  # Return as-is if not valid

    country_code = extract_country_code(phone)

    if country_code == '1' and len(phone) == 12:
        # US/Canada format: +1 (XXX) XXX-XXXX
        return f"+1 ({phone[2:5]}) {phone[5:8]}-{phone[8:]}"

    elif country_code == '44' and len(phone) == 13:
        # UK format: +44 XX XXXX XXXX
        return f"+44 {phone[3:5]} {phone[5:9]} {phone[9:]}"

    else:
        # Generic international format: +XX XXXX XXXX...
        # Group digits in chunks of 4
        digits = phone[1:]
        chunks = [digits[i:i+4] for i in range(0, len(digits), 4)]
        return f"+{country_code} {' '.join(chunks[1:]) if len(chunks) > 1 else chunks[0]}"


def phones_match(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers match (after normalization).

    Args:
        phone1: First phone number
        phone2: Second phone number

    Returns:
        True if phone numbers match after normalization, False otherwise

    Example:
        >>> phones_match("+1 (415) 523-8886", "4155238886")
        True
        >>> phones_match("+14155238886", "+14155239999")
        False
    """
    try:
        norm1 = normalize_phone_number(phone1)
        norm2 = normalize_phone_number(phone2)
        return norm1 == norm2
    except ValueError:
        return False
