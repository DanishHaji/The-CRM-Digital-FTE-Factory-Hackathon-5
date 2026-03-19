"""
Unit tests for WhatsApp handler module.
Tests Twilio webhook parsing, message splitting, signature validation, and formatting.
"""

import pytest
import hashlib
import hmac
import base64
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


@pytest.fixture
def sample_twilio_webhook_payload():
    """Sample Twilio WhatsApp webhook payload."""
    return {
        "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "MessagingServiceSid": "MGxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "From": "whatsapp:+14155238886",
        "To": "whatsapp:+15558675310",
        "Body": "Hi, I need help with my account settings.",
        "NumMedia": "0",
        "ProfileName": "Alice Smith",
        "WaId": "14155238886"
    }


class TestTwilioSignatureValidation:
    """Test Twilio signature validation."""

    def test_validate_twilio_signature_success(self):
        """Test successful Twilio signature validation."""
        from backend.src.channels.whatsapp_handler import validate_twilio_signature

        # Mock Twilio auth token
        auth_token = "test_auth_token_12345"

        # Create payload
        url = "https://api.example.com/webhooks/whatsapp"
        payload = {
            "MessageSid": "SM123",
            "From": "whatsapp:+14155238886",
            "Body": "Test message"
        }

        # Generate valid signature
        data = url + "".join(f"{k}{v}" for k, v in sorted(payload.items()))
        expected_signature = base64.b64encode(
            hmac.new(
                auth_token.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')

        with patch('backend.src.channels.whatsapp_handler.settings.twilio_auth_token', auth_token):
            result = validate_twilio_signature(url, payload, expected_signature)
            assert result is True

    def test_validate_twilio_signature_failure(self):
        """Test Twilio signature validation failure with wrong signature."""
        from backend.src.channels.whatsapp_handler import validate_twilio_signature

        auth_token = "test_auth_token_12345"
        url = "https://api.example.com/webhooks/whatsapp"
        payload = {"MessageSid": "SM123"}

        invalid_signature = "invalid_signature_xxx"

        with patch('backend.src.channels.whatsapp_handler.settings.twilio_auth_token', auth_token):
            result = validate_twilio_signature(url, payload, invalid_signature)
            assert result is False

    def test_validate_twilio_signature_disabled(self):
        """Test that signature validation can be disabled for development."""
        from backend.src.channels.whatsapp_handler import validate_twilio_signature

        # When validation is disabled, should always return True
        with patch('backend.src.channels.whatsapp_handler.settings.twilio_webhook_validate', False):
            result = validate_twilio_signature("url", {}, "any_signature")
            assert result is True


class TestWhatsAppMessageParsing:
    """Test WhatsApp message parsing from Twilio webhook."""

    def test_parse_twilio_webhook_success(self, sample_twilio_webhook_payload):
        """Test successful parsing of Twilio webhook."""
        from backend.src.channels.whatsapp_handler import parse_twilio_webhook

        result = parse_twilio_webhook(sample_twilio_webhook_payload)

        assert result is not None
        assert result["from_phone"] == "+14155238886"
        assert result["to_phone"] == "+15558675310"
        assert result["body"] == "Hi, I need help with my account settings."
        assert result["profile_name"] == "Alice Smith"
        assert result["message_sid"] == "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert result["whatsapp_id"] == "14155238886"

    def test_parse_twilio_webhook_missing_from(self):
        """Test handling of webhook without From field."""
        from backend.src.channels.whatsapp_handler import parse_twilio_webhook

        invalid_payload = {
            "MessageSid": "SM123",
            "Body": "Test"
        }

        with pytest.raises(ValueError, match="missing.*From"):
            parse_twilio_webhook(invalid_payload)

    def test_parse_twilio_webhook_missing_body(self):
        """Test handling of webhook without message body."""
        from backend.src.channels.whatsapp_handler import parse_twilio_webhook

        invalid_payload = {
            "MessageSid": "SM123",
            "From": "whatsapp:+14155238886"
        }

        with pytest.raises(ValueError, match="missing.*Body"):
            parse_twilio_webhook(invalid_payload)

    def test_parse_phone_number_normalization(self):
        """Test phone number normalization (remove 'whatsapp:' prefix)."""
        from backend.src.channels.whatsapp_handler import normalize_whatsapp_phone

        test_cases = [
            ("whatsapp:+14155238886", "+14155238886"),
            ("+14155238886", "+14155238886"),
            ("whatsapp:+919876543210", "+919876543210"),
        ]

        for input_phone, expected_output in test_cases:
            result = normalize_whatsapp_phone(input_phone)
            assert result == expected_output


class TestWhatsAppMessageFormatting:
    """Test WhatsApp message formatting."""

    def test_format_whatsapp_response_concise(self):
        """Test that WhatsApp responses are concise and conversational."""
        from backend.src.channels.whatsapp_handler import format_whatsapp_response

        response_text = "To reset your password, go to Settings > Security > Reset Password."

        formatted = format_whatsapp_response(response_text)

        # Should NOT have formal greeting
        assert not formatted.startswith("Dear")
        assert not formatted.startswith("Hello")

        # Should NOT have signature
        assert "Best regards" not in formatted
        assert "Sincerely" not in formatted
        assert "Customer Success Team" not in formatted

        # Should be direct
        assert "reset your password" in formatted.lower()

    def test_format_whatsapp_response_max_length(self):
        """Test that WhatsApp responses respect preferred max length (300 chars)."""
        from backend.src.channels.whatsapp_handler import format_whatsapp_response

        long_response = " ".join(["word"] * 100)  # ~500 characters

        formatted = format_whatsapp_response(long_response, max_chars=300)

        # Should truncate to ~300 chars
        assert len(formatted) <= 310  # Allow small buffer

    def test_format_whatsapp_response_preserves_short_messages(self):
        """Test that short messages are not modified unnecessarily."""
        from backend.src.channels.whatsapp_handler import format_whatsapp_response

        short_message = "Hi! I can help with that."

        formatted = format_whatsapp_response(short_message)

        assert formatted == short_message


class TestMessageSplitting:
    """Test WhatsApp message splitting for long messages."""

    def test_split_long_message_under_limit(self):
        """Test that messages under 1600 chars are not split."""
        from backend.src.channels.whatsapp_handler import split_whatsapp_message

        short_message = "This is a short message that doesn't need splitting."

        parts = split_whatsapp_message(short_message, max_length=1600)

        assert len(parts) == 1
        assert parts[0] == short_message

    def test_split_long_message_over_limit(self):
        """Test that messages over 1600 chars are split."""
        from backend.src.channels.whatsapp_handler import split_whatsapp_message

        # Create message > 1600 chars
        long_message = "Part: " + ("word " * 400)  # ~2400 chars

        parts = split_whatsapp_message(long_message, max_length=1600)

        assert len(parts) >= 2  # Should be split into at least 2 parts

        # Each part should be <= 1600 chars
        for part in parts:
            assert len(part) <= 1600

        # Rejoined parts should match original (minus split markers)
        rejoined = "".join([p.replace("(part 1/2)", "").replace("(part 2/2)", "") for p in parts])
        assert long_message.replace(" ", "") in rejoined.replace(" ", "")

    def test_split_message_with_part_indicators(self):
        """Test that split messages include part indicators (1/2, 2/2)."""
        from backend.src.channels.whatsapp_handler import split_whatsapp_message

        long_message = "Message: " + ("word " * 400)

        parts = split_whatsapp_message(long_message, max_length=1600)

        if len(parts) > 1:
            # First part should indicate "1/N"
            assert "(part 1/" in parts[0].lower() or "(1/" in parts[0]
            # Last part should indicate "N/N"
            assert f"({len(parts)}/{len(parts)})" in parts[-1].lower() or f"part {len(parts)}" in parts[-1].lower()

    def test_split_message_at_word_boundaries(self):
        """Test that messages are split at word boundaries, not mid-word."""
        from backend.src.channels.whatsapp_handler import split_whatsapp_message

        # Create message with distinct words
        words = ["word" + str(i) for i in range(500)]
        long_message = " ".join(words)

        parts = split_whatsapp_message(long_message, max_length=1600)

        # Each part should end with complete word (no partial words)
        for part in parts[:-1]:  # Check all except last
            # Should not end with partial word (no letter followed by space in next part)
            assert part[-1] == " " or part[-1].isalpha()


class TestTwilioAPIIntegration:
    """Test Twilio API send functionality."""

    @pytest.mark.asyncio
    async def test_send_whatsapp_message_success(self):
        """Test successful WhatsApp message send via Twilio."""
        from backend.src.channels.whatsapp_handler import send_whatsapp_message

        with patch('backend.src.channels.whatsapp_handler.get_twilio_client') as mock_client:
            # Mock Twilio client response
            mock_twilio = Mock()
            mock_message = Mock()
            mock_message.sid = "SMsent123456"
            mock_message.status = "queued"
            mock_twilio.messages.create.return_value = mock_message
            mock_client.return_value = mock_twilio

            result = await send_whatsapp_message(
                to_phone="+14155238886",
                body="Hi! Here's the answer to your question.",
                from_phone="+15558675310"
            )

            assert result["success"] is True
            assert result["message_sid"] == "SMsent123456"

    @pytest.mark.asyncio
    async def test_send_whatsapp_message_error(self):
        """Test handling of Twilio API error."""
        from backend.src.channels.whatsapp_handler import send_whatsapp_message
        from twilio.base.exceptions import TwilioRestException

        with patch('backend.src.channels.whatsapp_handler.get_twilio_client') as mock_client:
            # Mock Twilio error
            mock_twilio = Mock()
            mock_twilio.messages.create.side_effect = TwilioRestException(
                status=400,
                uri="/Messages",
                msg="Invalid phone number"
            )
            mock_client.return_value = mock_twilio

            with pytest.raises(Exception, match="Twilio.*error"):
                await send_whatsapp_message(
                    to_phone="invalid",
                    body="Test",
                    from_phone="+15558675310"
                )

    @pytest.mark.asyncio
    async def test_send_multiple_whatsapp_messages(self):
        """Test sending multiple WhatsApp messages (for split messages)."""
        from backend.src.channels.whatsapp_handler import send_multiple_whatsapp_messages

        message_parts = [
            "Part 1 of the message (1/2)",
            "Part 2 of the message (2/2)"
        ]

        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "message_sid": "SMmock"}

            results = await send_multiple_whatsapp_messages(
                to_phone="+14155238886",
                message_parts=message_parts,
                from_phone="+15558675310"
            )

            # Should send both parts
            assert mock_send.call_count == 2
            assert len(results) == 2
            assert all(r["success"] for r in results)


class TestPhoneNumberNormalization:
    """Test phone number normalization utilities."""

    def test_normalize_phone_formats(self):
        """Test normalization of various phone formats."""
        from backend.src.channels.whatsapp_handler import normalize_whatsapp_phone

        test_cases = [
            ("whatsapp:+14155238886", "+14155238886"),
            ("+1 (415) 523-8886", "+14155238886"),
            ("+1-415-523-8886", "+14155238886"),
            ("+14155238886", "+14155238886"),
        ]

        for input_phone, expected in test_cases:
            result = normalize_whatsapp_phone(input_phone)
            # Should remove all non-digit characters except leading +
            assert result.startswith("+")
            assert result[1:].isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
