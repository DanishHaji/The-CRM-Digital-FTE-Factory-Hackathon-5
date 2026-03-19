"""
Integration test for cross-channel customer continuity.
Tests that customers are correctly linked across email, WhatsApp, and web form channels.
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
        await conn.execute("DELETE FROM customer_identifiers WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com')")
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com')")
        await conn.execute("DELETE FROM customers WHERE email = 'alice@example.com'")

    yield

    # Cleanup after test
    async with get_connection() as conn:
        await conn.execute("DELETE FROM customer_identifiers WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com')")
        await conn.execute("DELETE FROM messages WHERE conversation_id IN (SELECT conversation_id FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com'))")
        await conn.execute("DELETE FROM conversations WHERE customer_id IN (SELECT customer_id FROM customers WHERE email = 'alice@example.com')")
        await conn.execute("DELETE FROM customers WHERE email = 'alice@example.com'")


@pytest.mark.asyncio
async def test_cross_channel_email_to_whatsapp_linking(test_client, clean_database):
    """
    Test that customer is correctly linked when they contact via email first,
    then via WhatsApp with the same email and phone.

    Scenario:
    1. Customer submits web form with email alice@example.com
    2. Same customer sends WhatsApp message from +14155238886
    3. System should link both channels to same customer_id
    4. Customer history should include both conversations
    """

    # Step 1: Customer submits web form
    web_payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "message": "I need help with my account settings"
    }

    response = test_client.post("/webhooks/web", json=web_payload)
    assert response.status_code == 201

    await asyncio.sleep(2)

    # Verify customer created via web
    async with get_connection() as conn:
        customer = await conn.fetchrow(
            "SELECT customer_id, email, name FROM customers WHERE email = $1",
            "alice@example.com"
        )
        assert customer is not None
        customer_id_web = customer["customer_id"]

    # Step 2: Same customer sends WhatsApp message
    whatsapp_payload = {
        "MessageSid": "SMtest123",
        "AccountSid": "ACtest",
        "From": "whatsapp:+14155238886",
        "To": "whatsapp:+15558675310",
        "Body": "Hi, I also need help with password reset",
        "ProfileName": "Alice Johnson",
        "NumMedia": "0",
        "WaId": "14155238886"
    }

    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "message_sid": "SMmock"}

            response = test_client.post(
                "/webhooks/whatsapp",
                data=whatsapp_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert response.status_code == 200

            await asyncio.sleep(2)

    # Step 3: Verify cross-channel linking
    async with get_connection() as conn:
        # Check that phone identifier was added to same customer
        identifiers = await conn.fetch(
            "SELECT identifier_type, identifier_value FROM customer_identifiers WHERE customer_id = $1",
            customer_id_web
        )

        identifier_dict = {row["identifier_type"]: row["identifier_value"] for row in identifiers}

        # Should have email identifier
        assert "email" in identifier_dict
        assert identifier_dict["email"] == "alice@example.com"

        # Should have phone identifier
        assert "phone" in identifier_dict
        assert "+14155238886" in identifier_dict["phone"]

        # Check that conversations from both channels belong to same customer
        conversations = await conn.fetch(
            "SELECT initial_channel FROM conversations WHERE customer_id = $1 ORDER BY created_at",
            customer_id_web
        )

        assert len(conversations) == 2
        assert conversations[0]["initial_channel"] == "web"
        assert conversations[1]["initial_channel"] == "whatsapp"


@pytest.mark.asyncio
async def test_cross_channel_gmail_to_web_linking(test_client, clean_database):
    """
    Test that customer is correctly linked when they email first,
    then submit web form with same email.
    """

    # Step 1: Customer sends email via Gmail
    import base64
    email_content = """From: alice@example.com
To: support@company.com
Subject: Account question

I have a question about my account.

Alice"""

    message_data = base64.b64encode(email_content.encode()).decode()

    gmail_payload = {
        "message": {
            "data": message_data,
            "messageId": "gmail_test_123",
            "publishTime": "2024-03-17T10:00:00.000Z"
        },
        "subscription": "projects/test/subscriptions/gmail-sub"
    }

    with patch('backend.src.channels.gmail_handler.send_gmail_message_with_retry', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True, "message_id": "gmail_sent_123"}

        response = test_client.post("/webhooks/gmail", json=gmail_payload)
        assert response.status_code == 200

        await asyncio.sleep(2)

    # Get customer_id from email
    async with get_connection() as conn:
        customer = await conn.fetchrow(
            "SELECT customer_id FROM customers WHERE email = $1",
            "alice@example.com"
        )
        assert customer is not None
        customer_id_email = customer["customer_id"]

    # Step 2: Same customer submits web form
    web_payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "message": "I also need help with billing"
    }

    response = test_client.post("/webhooks/web", json=web_payload)
    assert response.status_code == 201

    await asyncio.sleep(2)

    # Step 3: Verify same customer_id used
    async with get_connection() as conn:
        # Should still be only one customer
        customers = await conn.fetch(
            "SELECT customer_id FROM customers WHERE email = $1",
            "alice@example.com"
        )
        assert len(customers) == 1
        assert customers[0]["customer_id"] == customer_id_email

        # Should have 2 conversations for same customer
        conversations = await conn.fetch(
            "SELECT initial_channel FROM conversations WHERE customer_id = $1 ORDER BY created_at",
            customer_id_email
        )

        assert len(conversations) == 2
        assert conversations[0]["initial_channel"] == "email"
        assert conversations[1]["initial_channel"] == "web"


@pytest.mark.asyncio
async def test_cross_channel_all_three_channels(test_client, clean_database):
    """
    Test customer uses all three channels: web → email → WhatsApp.
    All should link to same customer_id.
    """

    # Step 1: Web form
    web_payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "message": "Initial question"
    }

    response = test_client.post("/webhooks/web", json=web_payload)
    assert response.status_code == 201
    await asyncio.sleep(1)

    # Get customer_id
    async with get_connection() as conn:
        customer = await conn.fetchrow(
            "SELECT customer_id FROM customers WHERE email = $1",
            "alice@example.com"
        )
        original_customer_id = customer["customer_id"]

    # Step 2: Gmail
    import base64
    email_content = """From: alice@example.com
To: support@company.com
Subject: Follow up

Following up on my question.

Alice"""

    message_data = base64.b64encode(email_content.encode()).decode()

    gmail_payload = {
        "message": {
            "data": message_data,
            "messageId": "gmail_test_456",
            "publishTime": "2024-03-17T11:00:00.000Z"
        },
        "subscription": "projects/test/subscriptions/gmail-sub"
    }

    with patch('backend.src.channels.gmail_handler.send_gmail_message_with_retry', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"success": True, "message_id": "gmail_sent_456"}

        response = test_client.post("/webhooks/gmail", json=gmail_payload)
        assert response.status_code == 200
        await asyncio.sleep(1)

    # Step 3: WhatsApp
    whatsapp_payload = {
        "MessageSid": "SMtest789",
        "AccountSid": "ACtest",
        "From": "whatsapp:+14155238886",
        "To": "whatsapp:+15558675310",
        "Body": "One more question via WhatsApp",
        "ProfileName": "Alice",
        "NumMedia": "0"
    }

    with patch('backend.src.channels.whatsapp_handler.validate_twilio_signature', return_value=True):
        with patch('backend.src.channels.whatsapp_handler.send_whatsapp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "message_sid": "SMmock"}

            response = test_client.post(
                "/webhooks/whatsapp",
                data=whatsapp_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert response.status_code == 200
            await asyncio.sleep(2)

    # Step 4: Verify all three channels linked to same customer
    async with get_connection() as conn:
        # Should still be only one customer
        customers = await conn.fetch(
            "SELECT customer_id FROM customers WHERE email = $1",
            "alice@example.com"
        )
        assert len(customers) == 1

        # All conversations should belong to original customer_id
        conversations = await conn.fetch(
            "SELECT initial_channel FROM conversations WHERE customer_id = $1 ORDER BY created_at",
            original_customer_id
        )

        assert len(conversations) == 3
        channels = [conv["initial_channel"] for conv in conversations]
        assert "web" in channels
        assert "email" in channels
        assert "whatsapp" in channels


@pytest.mark.asyncio
async def test_cross_channel_customer_history_retrieval(test_client, clean_database):
    """
    Test that agent can retrieve complete customer history across all channels.
    """

    # Create customer with conversations on multiple channels
    web_payload = {"name": "Alice Johnson", "email": "alice@example.com", "message": "Web question"}
    test_client.post("/webhooks/web", json=web_payload)
    await asyncio.sleep(1)

    # Add email conversation
    import base64
    email_content = "From: alice@example.com\nTo: support@company.com\nSubject: Email question\n\nEmail message"
    gmail_payload = {
        "message": {
            "data": base64.b64encode(email_content.encode()).decode(),
            "messageId": "gmail_history_test"
        },
        "subscription": "projects/test/subscriptions/gmail-sub"
    }

    with patch('backend.src.channels.gmail_handler.send_gmail_message_with_retry', new_callable=AsyncMock):
        test_client.post("/webhooks/gmail", json=gmail_payload)
        await asyncio.sleep(1)

    # Verify history includes both channels
    async with get_connection() as conn:
        customer = await conn.fetchrow(
            "SELECT customer_id FROM customers WHERE email = $1",
            "alice@example.com"
        )

        messages = await conn.fetch("""
            SELECT m.channel, m.direction, m.content, c.initial_channel
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.customer_id = $1
            ORDER BY m.created_at
        """, customer["customer_id"])

        # Should have messages from both channels
        channels_in_history = {msg["channel"] for msg in messages}
        assert "web" in channels_in_history
        assert "email" in channels_in_history


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
