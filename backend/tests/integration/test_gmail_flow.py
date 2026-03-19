"""
Integration test for Gmail flow: webhook → agent → Gmail API send
Tests the complete E2E flow for Gmail channel.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import base64
import json

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
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%test@example.com%'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%test@example.com%')")
        await conn.execute("DELETE FROM customers WHERE email LIKE '%test@example.com%'")

    yield

    # Cleanup after test
    async with get_connection() as conn:
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%test@example.com%'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email LIKE '%test@example.com%')")
        await conn.execute("DELETE FROM customers WHERE email LIKE '%test@example.com%'")


@pytest.mark.asyncio
async def test_gmail_webhook_to_response_flow(test_client, clean_database):
    """
    Test complete Gmail flow:
    1. Gmail Pub/Sub webhook receives message
    2. Handler parses email
    3. Agent processes with Groq
    4. Response sent via Gmail API
    5. Database records created
    """

    # Mock Gmail Pub/Sub message
    email_content = """From: test@example.com
To: support@company.com
Subject: Need help with password reset

Hi, I forgot my password and need help resetting it. Can you guide me through the process?

Thanks,
John Doe"""

    # Base64 encode the message data
    message_data = base64.b64encode(email_content.encode()).decode()

    pubsub_payload = {
        "message": {
            "data": message_data,
            "messageId": "2070443601311540",
            "publishTime": "2024-03-17T10:00:00.000Z"
        },
        "subscription": "projects/test-project/subscriptions/gmail-push-sub"
    }

    # Mock Gmail API send function
    with patch('backend.src.channels.gmail_handler.send_gmail_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {
            "success": True,
            "message_id": "mock_gmail_message_id_123"
        }

        # Send webhook request
        response = test_client.post(
            "/api/webhooks/gmail",
            json=pubsub_payload,
            headers={"Content-Type": "application/json"}
        )

        # Assert webhook accepted
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "received"
        assert "ticket_id" in response_data

        # Wait for async processing
        await asyncio.sleep(2)

        # Verify Gmail API send was called
        assert mock_send.called
        call_args = mock_send.call_args
        assert "test@example.com" in str(call_args)

    # Verify database records
    async with get_connection() as conn:
        # Check customer created
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1",
            "test@example.com"
        )
        assert customer is not None
        assert customer["name"] == "John Doe"

        # Check conversation created
        conversation = await conn.fetchrow(
            "SELECT * FROM conversations WHERE customer_id = $1",
            customer["customer_id"]
        )
        assert conversation is not None
        assert conversation["initial_channel"] == "email"

        # Check messages (inbound + outbound)
        messages = await conn.fetch(
            "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at",
            conversation["conversation_id"]
        )
        assert len(messages) >= 1  # At least inbound message
        assert messages[0]["direction"] == "inbound"
        assert messages[0]["channel"] == "email"
        assert "password reset" in messages[0]["content"].lower()


@pytest.mark.asyncio
async def test_gmail_webhook_duplicate_message_handling(test_client, clean_database):
    """
    Test that duplicate Gmail messages (same message_id) are handled idempotently.
    """

    email_content = """From: duplicate@example.com
To: support@company.com
Subject: Duplicate test

This is a duplicate message test."""

    message_data = base64.b64encode(email_content.encode()).decode()

    pubsub_payload = {
        "message": {
            "data": message_data,
            "messageId": "duplicate_message_id_456",
            "publishTime": "2024-03-17T10:00:00.000Z"
        },
        "subscription": "projects/test-project/subscriptions/gmail-push-sub"
    }

    with patch('backend.src.channels.gmail_handler.send_gmail_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True, "message_id": "mock_123"}

        # Send first time
        response1 = test_client.post("/api/webhooks/gmail", json=pubsub_payload)
        assert response1.status_code == 200

        await asyncio.sleep(1)

        # Send duplicate
        response2 = test_client.post("/api/webhooks/gmail", json=pubsub_payload)
        assert response2.status_code == 200

        # Gmail API should only be called once (not twice)
        assert mock_send.call_count == 1


@pytest.mark.asyncio
async def test_gmail_formal_formatting(test_client, clean_database):
    """
    Test that Gmail responses use formal formatting:
    - Greeting: "Dear {name},"
    - Formal tone
    - Signature: "Best regards, Customer Success Team"
    """

    email_content = """From: formal@example.com
To: support@company.com
Subject: Account question

I have a question about my account settings."""

    message_data = base64.b64encode(email_content.encode()).decode()

    pubsub_payload = {
        "message": {
            "data": message_data,
            "messageId": "formal_test_789",
            "publishTime": "2024-03-17T10:00:00.000Z"
        },
        "subscription": "projects/test-project/subscriptions/gmail-push-sub"
    }

    with patch('backend.src.channels.gmail_handler.send_gmail_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True, "message_id": "mock_456"}

        response = test_client.post("/api/webhooks/gmail", json=pubsub_payload)
        assert response.status_code == 200

        await asyncio.sleep(2)

        # Check that sent message has formal formatting
        assert mock_send.called
        sent_email = mock_send.call_args[1]["body"]

        # Should contain formal greeting
        assert "Dear" in sent_email or "Hello" in sent_email

        # Should contain signature
        assert "Best regards" in sent_email or "Sincerely" in sent_email
        assert "Customer Success Team" in sent_email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
