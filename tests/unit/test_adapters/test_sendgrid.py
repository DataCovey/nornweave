"""Unit tests for SendGridAdapter."""

import base64
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.adapters.sendgrid import SendGridAdapter, SendGridWebhookError
from nornweave.models.attachment import AttachmentDisposition

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "webhooks"


def load_fixture(filename: str) -> dict:
    """Load JSON fixture file."""
    with (FIXTURES_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


class TestSendGridAdapterInit:
    """Tests for SendGridAdapter initialization."""

    def test_init_with_api_key_only(self) -> None:
        """Test initialization with just API key."""
        adapter = SendGridAdapter(api_key="SG.test123")
        assert adapter._api_key == "SG.test123"
        assert adapter._webhook_public_key == ""

    def test_init_with_webhook_public_key(self) -> None:
        """Test initialization with both API key and webhook public key."""
        adapter = SendGridAdapter(
            api_key="SG.test123",
            webhook_public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQc...",
        )
        assert adapter._api_key == "SG.test123"
        assert adapter._webhook_public_key == "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQc..."


class TestParseInboundWebhook:
    """Tests for parse_inbound_webhook method."""

    def test_parse_simple_email(self) -> None:
        """Test parsing a simple email webhook."""
        payload = load_fixture("sendgrid_simple.json")
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "alice@gmail.com"
        assert inbound.to_address == "support@mycompany.com"
        assert inbound.subject == "Question about pricing"
        assert "pricing for the enterprise plan" in inbound.body_plain
        assert inbound.body_html is not None
        assert "enterprise plan" in inbound.body_html
        assert inbound.message_id == "<CADfE8z+abc123@mail.gmail.com>"
        assert len(inbound.attachments) == 0
        assert inbound.spf_result == "pass"
        assert inbound.dkim_result == "{@gmail.com : pass}"

    def test_parse_email_with_inline_image(self) -> None:
        """Test parsing email with inline image attachment."""
        payload = load_fixture("sendgrid_inline_image.json")
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "bob@gmail.com"
        assert inbound.to_address == "feedback@mycompany.com"
        assert inbound.subject == "New logo design"
        assert len(inbound.attachments) == 1

        # Check inline attachment
        att = inbound.attachments[0]
        assert att.filename == "logo.png"
        assert att.content_type == "image/png"
        assert att.disposition == AttachmentDisposition.INLINE
        assert att.content_id == "ii_logo123"
        assert att.provider_id == "attachment1"

        # Check content_id_map
        assert "ii_logo123" in inbound.content_id_map
        assert inbound.content_id_map["ii_logo123"] == "attachment1"

    def test_parse_sender_name_email_format(self) -> None:
        """Test that 'Name <email>' format is parsed correctly."""
        payload = {
            "from": "John Doe <john.doe@example.com>",
            "to": "inbox@company.com",
            "subject": "Test",
            "text": "Hello",
        }
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "john.doe@example.com"

    def test_parse_headers_string(self) -> None:
        """Test parsing headers from newline-separated string."""
        payload = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test",
            "text": "Hello",
            "headers": (
                "Message-ID: <test123@example.com>\n"
                "In-Reply-To: <parent@example.com>\n"
                "References: <ref1@example.com> <ref2@example.com>\n"
                "Date: Sat, 31 Jan 2026 10:30:00 -0500"
            ),
        }
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.message_id == "<test123@example.com>"
        assert inbound.in_reply_to == "<parent@example.com>"
        assert inbound.references == ["<ref1@example.com>", "<ref2@example.com>"]

    def test_parse_cc_from_headers(self) -> None:
        """Test parsing CC addresses from headers."""
        payload = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test",
            "text": "Hello",
            "headers": "Cc: cc1@example.com, cc2@example.com\nFrom: sender@example.com",
        }
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.cc_addresses == ["cc1@example.com", "cc2@example.com"]


class TestGetEventType:
    """Tests for get_event_type static method."""

    def test_returns_inbound_for_any_payload(self) -> None:
        """Test that get_event_type always returns 'inbound' for Inbound Parse."""
        payload = load_fixture("sendgrid_simple.json")
        assert SendGridAdapter.get_event_type(payload) == "inbound"

    def test_returns_inbound_for_empty_payload(self) -> None:
        """Test that get_event_type returns 'inbound' even for minimal payload."""
        assert SendGridAdapter.get_event_type({}) == "inbound"


class TestIsInboundEvent:
    """Tests for is_inbound_event static method."""

    def test_is_inbound_for_valid_payload(self) -> None:
        """Test that valid Inbound Parse payload returns True."""
        payload = load_fixture("sendgrid_simple.json")
        assert SendGridAdapter.is_inbound_event(payload) is True

    def test_is_inbound_for_payload_with_from(self) -> None:
        """Test payload with from field."""
        assert SendGridAdapter.is_inbound_event({"from": "sender@example.com"}) is True

    def test_is_inbound_for_payload_with_to(self) -> None:
        """Test payload with to field."""
        assert SendGridAdapter.is_inbound_event({"to": "recipient@example.com"}) is True

    def test_is_inbound_for_payload_with_subject(self) -> None:
        """Test payload with subject field."""
        assert SendGridAdapter.is_inbound_event({"subject": "Test"}) is True

    def test_is_not_inbound_for_empty_payload(self) -> None:
        """Test that empty payload returns False."""
        assert SendGridAdapter.is_inbound_event({}) is False


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature method."""

    def test_raises_error_when_public_key_not_configured(self) -> None:
        """Test that verification fails when public key is not set."""
        adapter = SendGridAdapter(api_key="test", webhook_public_key="")

        with pytest.raises(SendGridWebhookError, match="Webhook public key not configured"):
            adapter.verify_webhook_signature(b'{"test": true}', {})

    def test_raises_error_when_signature_header_missing(self) -> None:
        """Test that verification fails when signature header is missing."""
        adapter = SendGridAdapter(api_key="test", webhook_public_key="test_key")

        with pytest.raises(SendGridWebhookError, match=r"Missing required header.*Signature"):
            adapter.verify_webhook_signature(
                b'{"test": true}',
                {"X-Twilio-Email-Event-Webhook-Timestamp": "1234567890"},
            )

    def test_raises_error_when_timestamp_header_missing(self) -> None:
        """Test that verification fails when timestamp header is missing."""
        adapter = SendGridAdapter(api_key="test", webhook_public_key="test_key")

        with pytest.raises(SendGridWebhookError, match=r"Missing required header.*Timestamp"):
            adapter.verify_webhook_signature(
                b'{"test": true}',
                {"X-Twilio-Email-Event-Webhook-Signature": "signature"},
            )

    def test_raises_error_when_timestamp_expired(self) -> None:
        """Test that verification fails when timestamp is too old."""
        adapter = SendGridAdapter(api_key="test", webhook_public_key="dGVzdA==")

        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
        with pytest.raises(SendGridWebhookError, match="Timestamp validation failed"):
            adapter.verify_webhook_signature(
                b'{"test": true}',
                {
                    "X-Twilio-Email-Event-Webhook-Signature": base64.b64encode(b"sig").decode(),
                    "X-Twilio-Email-Event-Webhook-Timestamp": old_timestamp,
                },
            )

    def test_raises_error_for_invalid_timestamp_format(self) -> None:
        """Test that verification fails for non-numeric timestamp."""
        adapter = SendGridAdapter(api_key="test", webhook_public_key="dGVzdA==")

        with pytest.raises(SendGridWebhookError, match="Invalid timestamp format"):
            adapter.verify_webhook_signature(
                b'{"test": true}',
                {
                    "X-Twilio-Email-Event-Webhook-Signature": base64.b64encode(b"sig").decode(),
                    "X-Twilio-Email-Event-Webhook-Timestamp": "not-a-number",
                },
            )


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_simple_email(self) -> None:
        """Test sending a simple email."""
        adapter = SendGridAdapter(api_key="SG.test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-id-123"}
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

            assert result == "msg-id-123"
            mock_client.post.assert_called_once()

            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://api.sendgrid.com/v3/mail/send"
            assert call_args[1]["headers"]["Authorization"] == "Bearer SG.test123"

            json_data = call_args[1]["json"]
            assert json_data["personalizations"][0]["to"] == [{"email": "recipient@example.com"}]
            assert json_data["subject"] == "Test Subject"
            assert json_data["from"] == {"email": "sender@example.com"}
            assert len(json_data["content"]) == 2
            assert json_data["content"][0]["type"] == "text/plain"
            assert json_data["content"][1]["type"] == "text/html"

    @pytest.mark.asyncio
    async def test_send_email_with_threading_headers(self) -> None:
        """Test sending email with threading headers."""
        adapter = SendGridAdapter(api_key="SG.test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-id-456"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await adapter.send_email(
                to=["recipient@example.com"],
                subject="Re: Original Subject",
                body="This is a reply",
                from_address="sender@example.com",
                message_id="<custom-message-id@example.com>",
                in_reply_to="<original-id@example.com>",
                references=["<ref1@example.com>", "<ref2@example.com>"],
            )

            json_data = mock_client.post.call_args[1]["json"]
            assert json_data["headers"]["Message-ID"] == "<custom-message-id@example.com>"
            assert json_data["headers"]["In-Reply-To"] == "<original-id@example.com>"
            assert json_data["headers"]["References"] == "<ref1@example.com> <ref2@example.com>"

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self) -> None:
        """Test sending email with CC and BCC."""
        adapter = SendGridAdapter(api_key="SG.test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-id-789"}
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
            personalizations = json_data["personalizations"][0]
            assert personalizations["cc"] == [
                {"email": "cc1@example.com"},
                {"email": "cc2@example.com"},
            ]
            assert personalizations["bcc"] == [{"email": "bcc@example.com"}]

    @pytest.mark.asyncio
    async def test_send_email_with_reply_to(self) -> None:
        """Test sending email with reply-to address."""
        adapter = SendGridAdapter(api_key="SG.test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": "msg-id-reply"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await adapter.send_email(
                to=["recipient@example.com"],
                subject="Test",
                body="Test body",
                from_address="sender@example.com",
                reply_to="replyto@example.com",
            )

            json_data = mock_client.post.call_args[1]["json"]
            assert json_data["reply_to"] == {"email": "replyto@example.com"}

    @pytest.mark.asyncio
    async def test_send_email_api_error(self) -> None:
        """Test handling API errors."""
        adapter = SendGridAdapter(api_key="SG.test123")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.raise_for_status.side_effect = Exception("HTTP 400")
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="HTTP 400"):
                await adapter.send_email(
                    to=["recipient@example.com"],
                    subject="Test",
                    body="Test body",
                    from_address="sender@example.com",
                )


class TestAllSendGridFixtures:
    """Test that all SendGrid fixtures parse correctly."""

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "sendgrid_simple.json",
            "sendgrid_inline_image.json",
        ],
    )
    def test_fixture_parses_successfully(self, fixture_name: str) -> None:
        """Test that each fixture parses without error."""
        payload = load_fixture(fixture_name)
        adapter = SendGridAdapter(api_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        # Basic validation
        assert inbound.from_address != ""
        assert inbound.to_address != ""
        assert inbound.subject != ""
