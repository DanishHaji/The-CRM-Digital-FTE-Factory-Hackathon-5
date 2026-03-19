"""
Unit tests for custom validators.
Tests email validation, phone normalization, and other custom validators.
"""

import pytest
from pydantic import ValidationError


class TestEmailValidation:
    """Test email validation utilities."""

    def test_validate_email_valid(self):
        """Test validation of valid email addresses."""
        from backend.src.utils.validators import validate_email

        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@test.com"
        ]

        for email in valid_emails:
            result = validate_email(email)
            assert result.lower() == email.lower()

    def test_validate_email_normalization(self):
        """Test that emails are normalized to lowercase."""
        from backend.src.utils.validators import validate_email

        result = validate_email("TEST@EXAMPLE.COM")
        assert result == "test@example.com"

    def test_validate_email_invalid(self):
        """Test that invalid emails raise ValueError."""
        from backend.src.utils.validators import validate_email

        invalid_emails = [
            "not_an_email",
            "@example.com",
            "user@",
            "user @example.com",  # Space
            "",
        ]

        for invalid in invalid_emails:
            with pytest.raises(ValueError):
                validate_email(invalid)

    def test_validate_email_strip_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        from backend.src.utils.validators import validate_email

        result = validate_email("  test@example.com  ")
        assert result == "test@example.com"


class TestPhoneNormalization:
    """Test phone normalization utilities."""

    def test_normalize_phone_us_formats(self):
        """Test normalization of US phone formats."""
        from backend.src.utils.validators import normalize_phone

        test_cases = [
            ("+1 (415) 523-8886", "+14155238886"),
            ("+1-415-523-8886", "+14155238886"),
            ("(415) 523-8886", "+14155238886"),
            ("415-523-8886", "+14155238886"),
            ("4155238886", "+14155238886"),
        ]

        for input_phone, expected in test_cases:
            result = normalize_phone(input_phone)
            assert result == expected, f"Failed for {input_phone}"

    def test_normalize_phone_whatsapp_prefix(self):
        """Test removal of WhatsApp prefix."""
        from backend.src.utils.validators import normalize_phone

        result = normalize_phone("whatsapp:+14155238886")
        assert result == "+14155238886"
        assert "whatsapp:" not in result

    def test_normalize_phone_international(self):
        """Test normalization of international numbers."""
        from backend.src.utils.validators import normalize_phone

        test_cases = [
            ("+44 20 7123 4567", "+442071234567"),  # UK
            ("+91 98765 43210", "+919876543210"),   # India
        ]

        for input_phone, expected in test_cases:
            result = normalize_phone(input_phone)
            assert result.replace(" ", "") == expected.replace(" ", "")

    def test_normalize_phone_invalid(self):
        """Test that invalid phone numbers raise ValueError."""
        from backend.src.utils.validators import normalize_phone

        invalid_phones = [
            "not_a_phone",
            "123",  # Too short
            "abcdefghij",
        ]

        for invalid in invalid_phones:
            with pytest.raises(ValueError):
                normalize_phone(invalid)


class TestRequestModels:
    """Test request model validation."""

    def test_web_form_submission_valid(self):
        """Test valid web form submission."""
        from backend.src.api.models.requests import WebFormSubmission

        submission = WebFormSubmission(
            name="Alice Johnson",
            email="alice@example.com",
            message="I need help with my account settings"
        )

        assert submission.name == "Alice Johnson"
        assert submission.email == "alice@example.com"
        assert len(submission.message) >= 10

    def test_web_form_submission_name_too_short(self):
        """Test that name must be at least 2 characters."""
        from backend.src.api.models.requests import WebFormSubmission

        with pytest.raises(ValidationError):
            WebFormSubmission(
                name="A",  # Too short
                email="alice@example.com",
                message="Test message here"
            )

    def test_web_form_submission_message_too_short(self):
        """Test that message must be at least 10 characters."""
        from backend.src.api.models.requests import WebFormSubmission

        with pytest.raises(ValidationError):
            WebFormSubmission(
                name="Alice Johnson",
                email="alice@example.com",
                message="Short"  # Less than 10 chars
            )

    def test_web_form_submission_invalid_email(self):
        """Test that invalid email is rejected."""
        from backend.src.api.models.requests import WebFormSubmission

        with pytest.raises(ValidationError):
            WebFormSubmission(
                name="Alice Johnson",
                email="not_an_email",
                message="Test message here"
            )

    def test_web_form_submission_name_strip_whitespace(self):
        """Test that name whitespace is stripped."""
        from backend.src.api.models.requests import WebFormSubmission

        submission = WebFormSubmission(
            name="  Alice Johnson  ",
            email="alice@example.com",
            message="Test message here"
        )

        assert submission.name == "Alice Johnson"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
