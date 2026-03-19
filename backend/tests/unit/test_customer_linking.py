"""
Unit tests for customer linking utilities.
Tests email matching, phone normalization, and fuzzy matching logic.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestPhoneNormalization:
    """Test phone number normalization."""

    def test_normalize_us_phone_various_formats(self):
        """Test normalization of US phone numbers in various formats."""
        from backend.src.utils.phone_normalizer import normalize_phone_number

        test_cases = [
            ("+1 (415) 523-8886", "+14155238886"),
            ("+1-415-523-8886", "+14155238886"),
            ("(415) 523-8886", "+14155238886"),
            ("415-523-8886", "+14155238886"),
            ("4155238886", "+14155238886"),
            ("+14155238886", "+14155238886"),
        ]

        for input_phone, expected in test_cases:
            result = normalize_phone_number(input_phone, default_country="US")
            assert result == expected, f"Failed for input: {input_phone}"

    def test_normalize_international_phone(self):
        """Test normalization of international phone numbers."""
        from backend.src.utils.phone_normalizer import normalize_phone_number

        test_cases = [
            ("+44 20 7123 4567", "+442071234567"),  # UK
            ("+91 98765 43210", "+919876543210"),   # India
            ("+33 1 23 45 67 89", "+33123456789"),  # France
        ]

        for input_phone, expected in test_cases:
            result = normalize_phone_number(input_phone)
            assert result == expected

    def test_normalize_whatsapp_prefix_removal(self):
        """Test removal of WhatsApp prefix."""
        from backend.src.utils.phone_normalizer import normalize_phone_number

        result = normalize_phone_number("whatsapp:+14155238886")
        assert result == "+14155238886"
        assert "whatsapp:" not in result

    def test_normalize_invalid_phone(self):
        """Test handling of invalid phone numbers."""
        from backend.src.utils.phone_normalizer import normalize_phone_number

        invalid_phones = [
            "not_a_phone",
            "123",  # Too short
            "abcdefghij",
        ]

        for invalid in invalid_phones:
            with pytest.raises(ValueError):
                normalize_phone_number(invalid)

    def test_normalize_strip_whitespace_and_special_chars(self):
        """Test that spaces, dashes, parentheses are removed."""
        from backend.src.utils.phone_normalizer import normalize_phone_number

        input_phone = " ( 415 ) - 523 - 8886 "
        result = normalize_phone_number(input_phone, default_country="US")

        # Should remove all non-digit characters except leading +
        assert " " not in result
        assert "(" not in result
        assert ")" not in result
        assert "-" not in result
        assert result == "+14155238886"


class TestFuzzyMatching:
    """Test fuzzy matching for customer identification."""

    def test_fuzzy_match_similar_phones(self):
        """Test fuzzy matching of similar phone numbers."""
        from backend.src.utils.fuzzy_matcher import fuzzy_match_phone

        # Same number, different formats
        phone1 = "+14155238886"
        phone2 = "(415) 523-8886"

        similarity = fuzzy_match_phone(phone1, phone2)
        assert similarity >= 0.95  # Should be very high match

    def test_fuzzy_match_different_phones(self):
        """Test that different phone numbers don't match."""
        from backend.src.utils.fuzzy_matcher import fuzzy_match_phone

        phone1 = "+14155238886"
        phone2 = "+14155239999"

        similarity = fuzzy_match_phone(phone1, phone2)
        assert similarity < 0.8  # Should be low match

    def test_fuzzy_match_email_case_insensitive(self):
        """Test fuzzy matching of emails (case-insensitive)."""
        from backend.src.utils.fuzzy_matcher import fuzzy_match_email

        email1 = "Alice@Example.com"
        email2 = "alice@example.com"

        similarity = fuzzy_match_email(email1, email2)
        assert similarity == 1.0  # Exact match after normalization

    def test_fuzzy_match_email_similar(self):
        """Test fuzzy matching of similar emails (typos)."""
        from backend.src.utils.fuzzy_matcher import fuzzy_match_email

        email1 = "alice@example.com"
        email2 = "allice@example.com"  # Typo: extra 'l'

        similarity = fuzzy_match_email(email1, email2)
        assert 0.8 <= similarity < 1.0  # Similar but not exact

    def test_fuzzy_match_email_different(self):
        """Test that different emails don't match."""
        from backend.src.utils.fuzzy_matcher import fuzzy_match_email

        email1 = "alice@example.com"
        email2 = "bob@different.com"

        similarity = fuzzy_match_email(email1, email2)
        assert similarity < 0.5  # Should be low match


class TestCustomerLookup:
    """Test customer lookup and creation logic."""

    @pytest.mark.asyncio
    async def test_get_or_create_customer_new_email(self):
        """Test creating a new customer with email."""
        from backend.src.utils.customer_linking import get_or_create_customer

        with patch('backend.src.database.connection.get_connection') as mock_conn:
            # Mock: No existing customer
            mock_db = AsyncMock()
            mock_db.fetchrow.return_value = None  # Customer doesn't exist

            # Mock: Insert new customer
            mock_db.fetchrow.side_effect = [
                None,  # Customer lookup returns None
                {"customer_id": "uuid-123", "email": "new@example.com"}  # Insert returns new customer
            ]

            mock_conn.return_value.__aenter__.return_value = mock_db

            result = await get_or_create_customer(
                email="new@example.com",
                name="New Customer"
            )

            assert result["customer_id"] == "uuid-123"
            assert result["is_new"] is True

    @pytest.mark.asyncio
    async def test_get_or_create_customer_existing_email(self):
        """Test retrieving existing customer by email."""
        from backend.src.utils.customer_linking import get_or_create_customer

        with patch('backend.src.database.connection.get_connection') as mock_conn:
            # Mock: Existing customer found
            mock_db = AsyncMock()
            mock_db.fetchrow.return_value = {
                "customer_id": "uuid-existing",
                "email": "existing@example.com",
                "name": "Existing Customer"
            }

            mock_conn.return_value.__aenter__.return_value = mock_db

            result = await get_or_create_customer(
                email="existing@example.com",
                name="Existing Customer"
            )

            assert result["customer_id"] == "uuid-existing"
            assert result["is_new"] is False

    @pytest.mark.asyncio
    async def test_link_customer_identifier_phone(self):
        """Test linking phone identifier to customer."""
        from backend.src.utils.customer_linking import link_customer_identifier

        with patch('backend.src.database.connection.get_connection') as mock_conn:
            mock_db = AsyncMock()
            mock_conn.return_value.__aenter__.return_value = mock_db

            await link_customer_identifier(
                customer_id="uuid-123",
                identifier_type="phone",
                identifier_value="+14155238886"
            )

            # Verify INSERT was called
            mock_db.execute.assert_called_once()
            call_args = mock_db.execute.call_args[0]

            # Should insert into customer_identifiers
            assert "customer_identifiers" in call_args[0]
            assert "uuid-123" in call_args
            assert "phone" in call_args
            assert "+14155238886" in call_args

    @pytest.mark.asyncio
    async def test_find_customer_by_phone(self):
        """Test finding customer by phone number."""
        from backend.src.utils.customer_linking import find_customer_by_phone

        with patch('backend.src.database.connection.get_connection') as mock_conn:
            mock_db = AsyncMock()

            # Mock: Customer found by phone
            mock_db.fetchrow.return_value = {
                "customer_id": "uuid-phone-match",
                "email": "found@example.com"
            }

            mock_conn.return_value.__aenter__.return_value = mock_db

            result = await find_customer_by_phone("+14155238886")

            assert result is not None
            assert result["customer_id"] == "uuid-phone-match"


class TestCustomerIdentityConfirmation:
    """Test customer identity confirmation logic."""

    def test_should_confirm_identity_same_name(self):
        """Test that identity confirmation is suggested when names match."""
        from backend.src.utils.customer_linking import should_confirm_identity

        result = should_confirm_identity(
            existing_name="Alice Johnson",
            new_name="Alice Johnson",
            confidence_score=0.95
        )

        assert result is False  # No confirmation needed - high confidence + same name

    def test_should_confirm_identity_different_name(self):
        """Test that identity confirmation is suggested when names differ."""
        from backend.src.utils.customer_linking import should_confirm_identity

        result = should_confirm_identity(
            existing_name="Alice Johnson",
            new_name="Alicia Johnston",  # Similar but different
            confidence_score=0.85
        )

        assert result is True  # Confirmation needed - moderate confidence + different name

    def test_should_confirm_identity_low_confidence(self):
        """Test that identity confirmation is required for low confidence."""
        from backend.src.utils.customer_linking import should_confirm_identity

        result = should_confirm_identity(
            existing_name="Alice",
            new_name="Alice",
            confidence_score=0.60  # Below threshold
        )

        assert result is True  # Confirmation needed - low confidence


class TestCrossChannelMetadata:
    """Test cross-channel metadata management."""

    @pytest.mark.asyncio
    async def test_get_customer_channels(self):
        """Test retrieving all channels used by customer."""
        from backend.src.utils.customer_linking import get_customer_channels

        with patch('backend.src.database.connection.get_connection') as mock_conn:
            mock_db = AsyncMock()

            # Mock: Customer has used web and email
            mock_db.fetch.return_value = [
                {"initial_channel": "web"},
                {"initial_channel": "email"}
            ]

            mock_conn.return_value.__aenter__.return_value = mock_db

            channels = await get_customer_channels("uuid-123")

            assert "web" in channels
            assert "email" in channels
            assert len(channels) == 2

    @pytest.mark.asyncio
    async def test_is_cross_channel_customer(self):
        """Test checking if customer has used multiple channels."""
        from backend.src.utils.customer_linking import is_cross_channel_customer

        with patch('backend.src.utils.customer_linking.get_customer_channels', new_callable=AsyncMock) as mock_channels:
            # Mock: Customer has used 2 channels
            mock_channels.return_value = ["web", "email"]

            result = await is_cross_channel_customer("uuid-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_is_not_cross_channel_customer(self):
        """Test that single-channel customer returns False."""
        from backend.src.utils.customer_linking import is_cross_channel_customer

        with patch('backend.src.utils.customer_linking.get_customer_channels', new_callable=AsyncMock) as mock_channels:
            # Mock: Customer has used only 1 channel
            mock_channels.return_value = ["web"]

            result = await is_cross_channel_customer("uuid-123")

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
