"""
Integration test for WhatsApp flow: Twilio webhook → agent → Twilio send
Tests the complete E2E flow for WhatsApp channel.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.src.api.main import app
from backend.src.database.connection import get_connection
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def clean_database():
    """Clean database before and after tests."""
    async with get_connection() as conn:
        # Clean test data
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%whatsapp-test%'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%whatsapp-test%')")
        await conn.execute("DELETE FROM customers WHERE email LIKE '%whatsapp-test%'")

    yield

    # Cleanup after test
    async with get_connection() as conn:
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%whatsapp-test%'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%whatsapp-test%')")
        await conn.execute("DELETE FROM customers WHERE email LIKE '%whatsapp-test%'")


@pytest.mark.asyncio
async def test_whatsapp_webhook_to_response_flow(test_client, clean_database):
    """
    Test complete WhatsApp flow:
    1. Twilio webhook receives WhatsApp message
    2. Handler validates signature and parses message
    3. Agent processes with Groq
    4. Response sent via Twilio API (concise format)
    5. Database records created
    """

    # Mock Twilio webhook payload (form-encoded)
    twilio_payload = {
        "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "From": "whatsapp:+14155238886",
        "To": "whatsapp:+15558675310",
        "Body": "Hi, I need help resetting my password. Can you help?",
        "NumMedia": "0",
        "ProfileName": "Alice Johnson",
        "WaId": "14155238886"
    }

    # Mock Twilio signature validation
    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        # Mock Twilio API send function
        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {
                "success": True,
                "message_sid": "SMmock123456"
            }

            # Send webhook request (form-encoded)
            response = test_client.post(
                "/webhooks/whatsapp",
                data=twilio_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            # Assert webhook accepted (Twilio expects 200 with TwiML)
            assert response.status_code == 200
            assert "<?xml version" in response.text or response.text == ""

            # Wait for async processing
            await asyncio.sleep(2)

            # Verify Twilio API send was called
            assert mock_send.called
            call_args = mock_send.call_args

            # Verify message is concise (< 300 chars preferred)
            sent_message = call_args[1]["body"]
            assert len(sent_message) <= 500  # Allow some buffer

    # Verify database records
    async with get_connection() as conn:
        # Check customer created with phone normalization
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE metadata->>'phone' LIKE '%14155238886%'"
        )
        assert customer is not None

        # Check conversation created
        conversation = await conn.fetchrow(
            "SELECT * FROM conversations WHERE customer_id = $1",
            customer["customer_id"]
        )
        assert conversation is not None
        assert conversation["initial_channel"] == "whatsapp"

        # Check messages (inbound + outbound)
        messages = await conn.fetch(
            "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at",
            conversation["conversation_id"]
        )
        assert len(messages) >= 1
        assert messages[0]["direction"] == "inbound"
        assert messages[0]["channel"] == "whatsapp"
        assert "password" in messages[0]["content"].lower()


@pytest.mark.asyncio
async def test_whatsapp_message_splitting_long_response(test_client, clean_database):
    """
    Test that long WhatsApp responses (> 1600 chars) are split into multiple messages.
    """

    twilio_payload = {
        "MessageSid": "SMlong123",
        "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "From": "whatsapp:+14155551234",
        "To": "whatsapp:+15558675310",
        "Body": "Can you explain everything about your product in detail?",
        "NumMedia": "0",
        "ProfileName": "Bob Wilson"
    }

    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        # Mock long response from agent
        with patch('backend.src.agent.customer_success_agent.DigitalFTEAgent.handle_customer_request', new_callable=AsyncMock) as mock_agent:
            # Generate a response longer than 1600 chars
            long_response = "Here's detailed information: " + ("word " * 400)  # ~2400 chars
            mock_agent.return_value = {
                "success": True,
                "response": long_response,
                "escalated": False
            }

            with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = {"success": True, "message_sid": "SMmock"}

                response = test_client.post(
                    "/webhooks/whatsapp",
                    data=twilio_payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                assert response.status_code == 200

                await asyncio.sleep(2)

                # Verify multiple send calls (message was split)
                assert mock_send.call_count >= 2  # At least 2 parts

                # Verify each part is <= 1600 chars
                for call in mock_send.call_args_list:
                    message_body = call[1]["body"]
                    assert len(message_body) <= 1600


@pytest.mark.asyncio
async def test_whatsapp_concise_formatting(test_client, clean_database):
    """
    Test that WhatsApp responses use concise, conversational formatting:
    - No formal greeting
    - Direct and concise
    - Conversational tone
    """

    twilio_payload = {
        "MessageSid": "SMconcise123",
        "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "From": "whatsapp:+14155552222",
        "To": "whatsapp:+15558675310",
        "Body": "How do I change my password?",
        "NumMedia": "0",
        "ProfileName": "Carol"
    }

    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "message_sid": "SMmock"}

            response = test_client.post(
                "/webhooks/whatsapp",
                data=twilio_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == 200

            await asyncio.sleep(2)

            # Check that sent message is concise
            assert mock_send.called
            sent_message = mock_send.call_args[1]["body"]

            # Should NOT contain formal greeting
            assert not sent_message.startswith("Dear")
            assert "Best regards" not in sent_message
            assert "Sincerely" not in sent_message

            # Should be conversational
            assert len(sent_message) < 400  # Reasonable length for WhatsApp


@pytest.mark.asyncio
async def test_whatsapp_escalation_keyword_human(test_client, clean_database):
    """
    Test that WhatsApp-specific escalation keywords trigger escalation.
    Keywords: "human", "agent", "representative"
    """

    twilio_payload = {
        "MessageSid": "SMescalate123",
        "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "From": "whatsapp:+14155553333",
        "To": "whatsapp:+15558675310",
        "Body": "I want to speak to a human agent please",
        "NumMedia": "0",
        "ProfileName": "Dan"
    }

    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "message_sid": "SMmock"}

            response = test_client.post(
                "/webhooks/whatsapp",
                data=twilio_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            assert response.status_code == 200

            await asyncio.sleep(2)

            # Verify escalation message sent
            assert mock_send.called
            sent_message = mock_send.call_args[1]["body"]

            # Should indicate escalation
            assert "connect" in sent_message.lower() or "team" in sent_message.lower()


@pytest.mark.asyncio
async def test_whatsapp_signature_validation_failure(test_client, clean_database):
    """
    Test that invalid Twilio signature is rejected.
    """

    twilio_payload = {
        "MessageSid": "SMinvalid123",
        "From": "whatsapp:+14155554444",
        "Body": "Test message"
    }

    # Mock signature validation to fail
    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=False):
        response = test_client.post(
            "/webhooks/whatsapp",
            data=twilio_payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": "invalid_signature"
            }
        )

        # Should reject with 403 Forbidden
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
