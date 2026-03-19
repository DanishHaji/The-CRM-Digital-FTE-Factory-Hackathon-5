"""
Unit tests for Pydantic models.
Tests validation, edge cases, and data integrity.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestCustomerModel:
    """Test Customer Pydantic model."""

    def test_customer_valid_data(self):
        """Test customer model with valid data."""
        from backend.src.models.customer import Customer

        customer = Customer(
            customer_id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            name="Test User",
            metadata={"source": "web"}
        )

        assert customer.email == "test@example.com"
        assert customer.name == "Test User"
        assert customer.metadata["source"] == "web"

    def test_customer_email_validation(self):
        """Test that invalid emails are rejected."""
        from backend.src.models.customer import Customer

        with pytest.raises(ValidationError):
            Customer(
                email="not_an_email",
                name="Test User"
            )

    def test_customer_email_normalization(self):
        """Test that emails are normalized to lowercase."""
        from backend.src.models.customer import Customer

        customer = Customer(
            email="TEST@EXAMPLE.COM",
            name="Test User"
        )

        # Should be normalized to lowercase
        assert customer.email == "test@example.com"


class TestConversationModel:
    """Test Conversation Pydantic model."""

    def test_conversation_valid_data(self):
        """Test conversation model with valid data."""
        from backend.src.models.conversation import Conversation

        conversation = Conversation(
            conversation_id="550e8400-e29b-41d4-a716-446655440001",
            customer_id="550e8400-e29b-41d4-a716-446655440000",
            initial_channel="web",
            status="open"
        )

        assert conversation.initial_channel == "web"
        assert conversation.status == "open"

    def test_conversation_invalid_channel(self):
        """Test that invalid channels are rejected."""
        from backend.src.models.conversation import Conversation

        with pytest.raises(ValidationError):
            Conversation(
                customer_id="550e8400-e29b-41d4-a716-446655440000",
                initial_channel="invalid_channel",  # Not in enum
                status="open"
            )

    def test_conversation_invalid_status(self):
        """Test that invalid statuses are rejected."""
        from backend.src.models.conversation import Conversation

        with pytest.raises(ValidationError):
            Conversation(
                customer_id="550e8400-e29b-41d4-a716-446655440000",
                initial_channel="web",
                status="invalid_status"  # Not in enum
            )


class TestMessageModel:
    """Test Message Pydantic model."""

    def test_message_valid_data(self):
        """Test message model with valid data."""
        from backend.src.models.message import Message

        message = Message(
            message_id="550e8400-e29b-41d4-a716-446655440002",
            conversation_id="550e8400-e29b-41d4-a716-446655440001",
            channel="web",
            direction="inbound",
            role="user",
            content="Test message content"
        )

        assert message.channel == "web"
        assert message.direction == "inbound"
        assert message.role == "user"
        assert message.content == "Test message content"

    def test_message_content_required(self):
        """Test that message content is required."""
        from backend.src.models.message import Message

        with pytest.raises(ValidationError):
            Message(
                conversation_id="550e8400-e29b-41d4-a716-446655440001",
                channel="web",
                direction="inbound",
                role="user",
                content=""  # Empty content should fail
            )


class TestTicketModel:
    """Test Ticket Pydantic model."""

    def test_ticket_valid_data(self):
        """Test ticket model with valid data."""
        from backend.src.models.ticket import Ticket

        ticket = Ticket(
            ticket_id="550e8400-e29b-41d4-a716-446655440003",
            conversation_id="550e8400-e29b-41d4-a716-446655440001",
            source_channel="web",
            priority="medium",
            status="pending"
        )

        assert ticket.source_channel == "web"
        assert ticket.priority == "medium"
        assert ticket.status == "pending"

    def test_ticket_priority_validation(self):
        """Test that priority must be valid."""
        from backend.src.models.ticket import Ticket

        valid_priorities = ["low", "medium", "high", "urgent"]

        for priority in valid_priorities:
            ticket = Ticket(
                conversation_id="550e8400-e29b-41d4-a716-446655440001",
                source_channel="web",
                priority=priority,
                status="pending"
            )
            assert ticket.priority == priority


class TestKnowledgeBaseModel:
    """Test KnowledgeBase Pydantic model."""

    def test_knowledge_base_valid_data(self):
        """Test knowledge base model with valid data."""
        from backend.src.models.knowledge_base import KnowledgeBaseEntry

        entry = KnowledgeBaseEntry(
            entry_id="550e8400-e29b-41d4-a716-446655440004",
            title="How to reset password",
            content="To reset your password, go to Settings > Security > Reset Password.",
            category="account",
            source_url="https://docs.example.com/reset-password"
        )

        assert entry.title == "How to reset password"
        assert entry.category == "account"
        assert "Reset Password" in entry.content

    def test_knowledge_base_title_required(self):
        """Test that title is required."""
        from backend.src.models.knowledge_base import KnowledgeBaseEntry

        with pytest.raises(ValidationError):
            KnowledgeBaseEntry(
                content="Some content",
                category="account"
            )

    def test_knowledge_base_content_min_length(self):
        """Test that content has minimum length."""
        from backend.src.models.knowledge_base import KnowledgeBaseEntry

        with pytest.raises(ValidationError):
            KnowledgeBaseEntry(
                title="Test",
                content="Too short",  # Less than min length
                category="account"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
