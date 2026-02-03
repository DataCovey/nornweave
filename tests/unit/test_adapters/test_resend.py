"""Unit tests for ResendAdapter."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.adapters.resend import ResendAdapter, ResendWebhookError
from nornweave.models.attachment import AttachmentDisposition

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "webhooks"


def load_fixture(filename: str) -> dict:
    """Load JSON fixture file."""
    with (FIXTURES_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


class TestResendAdapterInit:
    """Tests for ResendAdapter initialization."""

    def test_init_with_api_key_only(self) -> None:
        """Test initialization with just API key."""
        adapter = ResendAdapter(api_key="re_test123")
        # Using protected members is acceptable in tests to verify internal state
        assert adapter._api_key == "re_test123"
        assert adapter._webhook_secret == ""

    def test_init_with_webhook_secret(self) -> None:
        """Test initialization with both API key and webhook secret."""
        adapter = ResendAdapter(api_key="re_test123", webhook_secret="whsec_test456")
        # Using protected members is acceptable in tests to verify internal state
        assert adapter._api_key == "re_test123"
        assert adapter._webhook_secret == "whsec_test456"


class TestParseInboundWebhook:
    """Tests for parse_inbound_webhook method."""

    def test_parse_simple_email(self) -> None:
        """Test parsing a simple email webhook."""
        payload = load_fixture("resend_simple.json")
        adapter = ResendAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "bob@gmail.com"
        assert inbound.to_address == "sales@mycompany.com"
        assert inbound.subject == "Demo request"
        assert "schedule a demo" in inbound.body_plain
        assert inbound.message_id == "<CABob123xyz@mail.gmail.com>"
        assert len(inbound.attachments) == 0
        assert inbound.cc_addresses == []
        assert inbound.bcc_addresses == []

    def test_parse_email_with_attachments(self) -> None:
        """Test parsing email with multiple attachments."""
        payload = load_fixture("resend_with_attachments.json")
        adapter = ResendAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "carol@gmail.com"
        assert inbound.to_address == "reports@mycompany.com"
        assert inbound.subject == "Q4 Report Files"
        assert len(inbound.attachments) == 3
        assert inbound.cc_addresses == ["team@mycompany.com"]

        # Check attachment metadata
        pdf_att = inbound.attachments[0]
        assert pdf_att.filename == "q4-summary.pdf"
        assert pdf_att.content_type == "application/pdf"
        assert pdf_att.disposition == AttachmentDisposition.ATTACHMENT
        assert pdf_att.provider_id == "att-uuid-001"

        # Check inline attachment
        inline_att = inbound.attachments[2]
        assert inline_att.filename == "chart.png"
        assert inline_att.disposition == AttachmentDisposition.INLINE
        assert inline_att.content_id == "chart001"

    def test_parse_data_object_directly(self) -> None:
        """Test parsing when only data object is provided (not full webhook)."""
        payload = load_fixture("resend_simple.json")
        adapter = ResendAdapter(api_key="test")

        # Pass just the data object
        inbound = adapter.parse_inbound_webhook(payload["data"])

        assert inbound.from_address == "bob@gmail.com"
        assert inbound.subject == "Demo request"

    def test_parse_email_extracts_address_from_name_format(self) -> None:
        """Test that 'Name <email>' format is parsed correctly."""
        payload = {
            "type": "email.received",
            "created_at": "2026-01-31T17:30:00.000Z",
            "data": {
                "email_id": "test-123",
                "from": "John Doe <john.doe@example.com>",
                "to": ["inbox@company.com"],
                "subject": "Test",
            },
        }
        adapter = ResendAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "john.doe@example.com"

    def test_parse_timestamp(self) -> None:
        """Test timestamp parsing from ISO 8601 format."""
        payload = load_fixture("resend_simple.json")
        adapter = ResendAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.timestamp.year == 2026
        assert inbound.timestamp.month == 1
        assert inbound.timestamp.day == 31


class TestGetEventType:
    """Tests for get_event_type static method."""

    def test_get_received_event_type(self) -> None:
        """Test getting event type for received email."""
        payload = load_fixture("resend_simple.json")
        assert ResendAdapter.get_event_type(payload) == "email.received"

    def test_get_sent_event_type(self) -> None:
        """Test getting event type for sent email."""
        payload = load_fixture("resend_sent.json")
        assert ResendAdapter.get_event_type(payload) == "email.sent"

    def test_get_bounced_event_type(self) -> None:
        """Test getting event type for bounced email."""
        payload = load_fixture("resend_bounced.json")
        assert ResendAdapter.get_event_type(payload) == "email.bounced"

    def test_get_unknown_event_type(self) -> None:
        """Test handling unknown event type."""
        payload = {"data": {}}
        assert ResendAdapter.get_event_type(payload) == "unknown"


class TestIsInboundEvent:
    """Tests for is_inbound_event static method."""

    def test_is_inbound_for_received(self) -> None:
        """Test that email.received returns True."""
        payload = load_fixture("resend_simple.json")
        assert ResendAdapter.is_inbound_event(payload) is True

    def test_is_not_inbound_for_sent(self) -> None:
        """Test that email.sent returns False."""
        payload = load_fixture("resend_sent.json")
        assert ResendAdapter.is_inbound_event(payload) is False

    def test_is_not_inbound_for_bounced(self) -> None:
        """Test that email.bounced returns False."""
        payload = load_fixture("resend_bounced.json")
        assert ResendAdapter.is_inbound_event(payload) is False


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature method."""

    def test_raises_error_when_secret_not_configured(self) -> None:
        """Test that verification fails when secret is not set."""
        adapter = ResendAdapter(api_key="test", webhook_secret="")

        with pytest.raises(ResendWebhookError, match="Webhook secret not configured"):
            adapter.verify_webhook_signature(b'{"test": true}', {})

    def test_raises_error_when_headers_missing(self) -> None:
        """Test that verification fails when Svix headers are missing."""
        adapter = ResendAdapter(api_key="test", webhook_secret="whsec_test123")

        with pytest.raises(ResendWebhookError, match="Missing required Svix headers"):
            adapter.verify_webhook_signature(b'{"test": true}', {})

    @patch("nornweave.adapters.resend.Webhook")
    def test_successful_verification(self, mock_webhook_class: MagicMock) -> None:
        """Test successful webhook signature verification."""
        mock_wh = MagicMock()
        mock_wh.verify.return_value = {"type": "email.received", "data": {}}
        mock_webhook_class.return_value = mock_wh

        adapter = ResendAdapter(api_key="test", webhook_secret="whsec_test123")

        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": "1614265330",
            "svix-signature": "v1,signature123",
        }
        payload = b'{"type": "email.received"}'

        result = adapter.verify_webhook_signature(payload, headers)

        assert result == {"type": "email.received", "data": {}}
        mock_webhook_class.assert_called_once_with("whsec_test123")
        mock_wh.verify.assert_called_once()

    def test_verification_failure(self) -> None:
        """Test webhook signature verification failure with invalid signature."""
        # Use a valid base64-encoded secret (Resend/Svix expects base64)
        # whsec_ prefix is stripped, remaining must be valid base64
        valid_base64_secret = "whsec_MIIBkDCB+gYJKoZIhvcNAQcCoIIB6zCCAecCAQExDTA="
        adapter = ResendAdapter(api_key="test", webhook_secret=valid_base64_secret)

        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": "1614265330",
            "svix-signature": "v1,invalid_signature_that_will_fail",
        }

        # This should fail with a real invalid signature
        with pytest.raises(ResendWebhookError, match="Signature verification failed"):
            adapter.verify_webhook_signature(b'{"test": true}', headers)


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_simple_email(self) -> None:
        """Test sending a simple email."""
        adapter = ResendAdapter(api_key="re_test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "email-id-123"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await adapter.send_email(
                to=["recipient@example.com"],
                subject="Test Subject",
                body="Hello, World!",
                from_address="sender@example.com",
            )

            assert result == "email-id-123"
            mock_client.post.assert_called_once()

            # Check the call arguments
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://api.resend.com/emails"
            assert call_args[1]["headers"]["Authorization"] == "Bearer re_test123"

            json_data = call_args[1]["json"]
            assert json_data["to"] == ["recipient@example.com"]
            assert json_data["subject"] == "Test Subject"
            assert json_data["from"] == "sender@example.com"

    @pytest.mark.asyncio
    async def test_send_email_with_threading_headers(self) -> None:
        """Test sending email with threading headers."""
        adapter = ResendAdapter(api_key="re_test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "email-id-456"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await adapter.send_email(
                to=["recipient@example.com"],
                subject="Re: Original Subject",
                body="This is a reply",
                from_address="sender@example.com",
                message_id="<custom-message-id@example.com>",
                in_reply_to="<original-id@example.com>",
                references=["<ref1@example.com>", "<ref2@example.com>"],
            )

            assert result == "email-id-456"

            json_data = mock_client.post.call_args[1]["json"]
            assert json_data["headers"]["Message-ID"] == "<custom-message-id@example.com>"
            assert json_data["headers"]["In-Reply-To"] == "<original-id@example.com>"
            assert json_data["headers"]["References"] == "<ref1@example.com> <ref2@example.com>"

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self) -> None:
        """Test sending email with CC and BCC."""
        adapter = ResendAdapter(api_key="re_test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "email-id-789"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await adapter.send_email(
                to=["recipient@example.com"],
                subject="Test",
                body="Test body",
                from_address="sender@example.com",
                cc=["cc1@example.com", "cc2@example.com"],
                bcc=["bcc@example.com"],
            )

            json_data = mock_client.post.call_args[1]["json"]
            assert json_data["cc"] == ["cc1@example.com", "cc2@example.com"]
            assert json_data["bcc"] == ["bcc@example.com"]


class TestFetchEmailContent:
    """Tests for fetch_email_content method."""

    @pytest.mark.asyncio
    async def test_fetch_email_content_success(self) -> None:
        """Test successful email content fetch."""
        adapter = ResendAdapter(api_key="re_test123")

        expected_response = {
            "id": "email-123",
            "html": "<p>Email body</p>",
            "text": "Email body",
            "headers": {"in-reply-to": "<parent@example.com>"},
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await adapter.fetch_email_content("email-123")

            assert result == expected_response
            mock_client.get.assert_called_once()
            call_url = mock_client.get.call_args[0][0]
            assert "emails/receiving/email-123" in call_url


class TestAllEventTypes:
    """Test that all event type fixtures are valid."""

    @pytest.mark.parametrize(
        "fixture_name,expected_type",
        [
            ("resend_simple.json", "email.received"),
            ("resend_with_attachments.json", "email.received"),
            ("resend_sent.json", "email.sent"),
            ("resend_delivered.json", "email.delivered"),
            ("resend_bounced.json", "email.bounced"),
            ("resend_complained.json", "email.complained"),
            ("resend_failed.json", "email.failed"),
            ("resend_opened.json", "email.opened"),
            ("resend_clicked.json", "email.clicked"),
            ("resend_delivery_delayed.json", "email.delivery_delayed"),
            ("resend_scheduled.json", "email.scheduled"),
            ("resend_suppressed.json", "email.suppressed"),
        ],
    )
    def test_fixture_has_correct_type(self, fixture_name: str, expected_type: str) -> None:
        """Test that each fixture has the correct event type."""
        payload = load_fixture(fixture_name)
        assert payload.get("type") == expected_type
        assert "data" in payload
        assert "email_id" in payload["data"] or "created_at" in payload["data"]
