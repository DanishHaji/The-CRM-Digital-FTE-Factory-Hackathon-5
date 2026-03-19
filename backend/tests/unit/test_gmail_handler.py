"""
Unit tests for Gmail handler module.
Tests Pub/Sub message parsing, email formatting, and signature validation.
"""

import pytest
import base64
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


@pytest.fixture
def sample_gmail_pubsub_message():
    """Sample Gmail Pub/Sub message payload."""
    email_content = """From: customer@example.com
To: support@company.com
Subject: Product Question
Message-ID: <abc123@mail.gmail.com>

Hi,

I need help with setting up my account.

Thanks,
Alice Smith"""

    message_data = base64.b64encode(email_content.encode()).decode()

    return {
        "message": {
            "data": message_data,
            "messageId": "test_message_id_123",
            "publishTime": "2024-03-17T10:30:00.000Z",
            "attributes": {
                "emailAddress": "support@company.com",
                "historyId": "1234567"
            }
        },
        "subscription": "projects/test-project/subscriptions/gmail-push-sub"
    }


class TestGmailPubSubParsing:
    """Test Gmail Pub/Sub message parsing."""

    def test_parse_pubsub_message_success(self, sample_gmail_pubsub_message):
        """Test successful parsing of Pub/Sub message."""
        from backend.src.channels.gmail_handler import parse_pubsub_message

        result = parse_pubsub_message(sample_gmail_pubsub_message)

        assert result is not None
        assert result["from_email"] == "customer@example.com"
        assert result["to_email"] == "support@company.com"
        assert result["subject"] == "Product Question"
        assert "setting up my account" in result["body"]
        assert result["from_name"] == "Alice Smith"
        assert result["message_id"] == "test_message_id_123"

    def test_parse_pubsub_message_invalid_base64(self):
        """Test handling of invalid base64 data."""
        from backend.src.channels.gmail_handler import parse_pubsub_message

        invalid_message = {
            "message": {
                "data": "invalid_base64!!!",
                "messageId": "test_123"
            }
        }

        with pytest.raises(ValueError):
            parse_pubsub_message(invalid_message)

    def test_parse_pubsub_message_missing_from(self):
        """Test handling of email without From field."""
        from backend.src.channels.gmail_handler import parse_pubsub_message

        email_content = """To: support@company.com
Subject: No sender

This email has no sender."""

        message_data = base64.b64encode(email_content.encode()).decode()

        message = {
            "message": {
                "data": message_data,
                "messageId": "test_456"
            }
        }

        with pytest.raises(ValueError, match="missing.*from"):
            parse_pubsub_message(message)


class TestEmailFormatting:
    """Test email response formatting."""

    def test_format_email_response_formal_greeting(self):
        """Test that email responses include formal greeting."""
        from backend.src.channels.gmail_handler import format_email_response

        response_text = "Here's how to reset your password: Go to Settings > Security."
        customer_name = "John Doe"

        formatted = format_email_response(response_text, customer_name)

        # Should start with formal greeting
        assert formatted.startswith("Dear John Doe,") or formatted.startswith("Hello John Doe,")

        # Should contain the response text
        assert "reset your password" in formatted

        # Should end with signature
        assert "Best regards" in formatted or "Sincerely" in formatted
        assert "Customer Success Team" in formatted

    def test_format_email_response_max_length(self):
        """Test that email responses respect max length (500 words)."""
        from backend.src.channels.gmail_handler import format_email_response

        # Generate long response
        long_response = " ".join(["word"] * 600)  # 600 words
        customer_name = "Jane Smith"

        formatted = format_email_response(long_response, customer_name)

        # Count words (excluding greeting and signature)
        words = formatted.split()
        assert len(words) <= 550  # Allow some buffer for greeting/signature

    def test_format_email_response_preserves_formatting(self):
        """Test that email formatting preserves line breaks and structure."""
        from backend.src.channels.gmail_handler import format_email_response

        response_text = """Here are the steps:

1. Go to Settings
2. Click on Security
3. Select Reset Password

Let me know if you need help!"""

        customer_name = "Bob Wilson"

        formatted = format_email_response(response_text, customer_name)

        # Should preserve line breaks
        assert "\n\n" in formatted
        # Should preserve numbered list
        assert "1." in formatted
        assert "2." in formatted


class TestGmailAPIIntegration:
    """Test Gmail API send functionality."""

    @pytest.mark.asyncio
    async def test_send_gmail_message_success(self):
        """Test successful Gmail API message send."""
        from backend.src.channels.gmail_handler import send_gmail_message

        with patch('backend.src.channels.gmail_handler.get_gmail_service') as mock_service:
            # Mock Gmail API response
            mock_gmail = Mock()
            mock_gmail.users().messages().send().execute.return_value = {
                "id": "sent_message_id_789",
                "labelIds": ["SENT"]
            }
            mock_service.return_value = mock_gmail

            result = await send_gmail_message(
                to_email="customer@example.com",
                subject="Re: Your question",
                body="Here's the answer to your question.",
                from_email="support@company.com"
            )

            assert result["success"] is True
            assert result["message_id"] == "sent_message_id_789"

    @pytest.mark.asyncio
    async def test_send_gmail_message_quota_exceeded(self):
        """Test handling of Gmail API quota exceeded error."""
        from backend.src.channels.gmail_handler import send_gmail_message
        from googleapiclient.errors import HttpError

        with patch('backend.src.channels.gmail_handler.get_gmail_service') as mock_service:
            # Mock quota exceeded error
            mock_gmail = Mock()
            error_response = Mock()
            error_response.status = 429
            mock_gmail.users().messages().send().execute.side_effect = HttpError(
                resp=error_response,
                content=b'{"error": {"message": "Quota exceeded"}}'
            )
            mock_service.return_value = mock_gmail

            # Should raise exception that can be caught for retry
            with pytest.raises(Exception, match="quota"):
                await send_gmail_message(
                    to_email="customer@example.com",
                    subject="Test",
                    body="Test body",
                    from_email="support@company.com"
                )

    @pytest.mark.asyncio
    async def test_send_gmail_message_with_retry(self):
        """Test exponential backoff retry on transient errors."""
        from backend.src.channels.gmail_handler import send_gmail_message_with_retry

        with patch('backend.src.channels.gmail_handler.send_gmail_message', new_callable=AsyncMock) as mock_send:
            # Fail twice, succeed third time
            mock_send.side_effect = [
                Exception("Temporary error"),
                Exception("Temporary error"),
                {"success": True, "message_id": "retry_success_123"}
            ]

            result = await send_gmail_message_with_retry(
                to_email="customer@example.com",
                subject="Retry test",
                body="Test body",
                from_email="support@company.com",
                max_retries=3
            )

            assert result["success"] is True
            assert result["message_id"] == "retry_success_123"
            assert mock_send.call_count == 3


class TestEmailExtraction:
    """Test email address and name extraction."""

    def test_extract_sender_email_and_name(self):
        """Test extraction of sender email and name from From field."""
        from backend.src.channels.gmail_handler import extract_sender_info

        # Test various formats
        test_cases = [
            ("Alice Smith <alice@example.com>", "alice@example.com", "Alice Smith"),
            ("alice@example.com", "alice@example.com", None),
            ("\"Smith, Alice\" <alice@example.com>", "alice@example.com", "Smith, Alice"),
            ("<bob@example.com>", "bob@example.com", None),
        ]

        for from_field, expected_email, expected_name in test_cases:
            email, name = extract_sender_info(from_field)
            assert email == expected_email
            assert name == expected_name

    def test_extract_sender_invalid_format(self):
        """Test handling of invalid From field format."""
        from backend.src.channels.gmail_handler import extract_sender_info

        invalid_inputs = [
            "not an email",
            "",
            "missing@angle.bracket",
        ]

        for invalid in invalid_inputs:
            with pytest.raises(ValueError):
                extract_sender_info(invalid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
