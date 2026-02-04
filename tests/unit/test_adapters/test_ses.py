"""Unit tests for SESAdapter."""

import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.adapters.ses import (
    SESAdapter,
    SESWebhookError,
    SNS_TYPE_NOTIFICATION,
    SNS_TYPE_SUBSCRIPTION_CONFIRMATION,
)

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "webhooks"


def load_fixture(filename: str) -> dict:
    """Load JSON fixture file."""
    with (FIXTURES_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


class TestSESAdapterInit:
    """Tests for SESAdapter initialization."""

    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )
        assert adapter._access_key_id == "AKIATEST123"
        assert adapter._secret_access_key == "secretkey123"
        assert adapter._region == "us-east-1"
        assert adapter._configuration_set is None

    def test_init_with_custom_region(self) -> None:
        """Test initialization with custom region."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
            region="eu-west-1",
        )
        assert adapter._region == "eu-west-1"
        assert adapter._api_host == "email.eu-west-1.amazonaws.com"

    def test_init_with_configuration_set(self) -> None:
        """Test initialization with configuration set."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
            configuration_set="my-tracking-set",
        )
        assert adapter._configuration_set == "my-tracking-set"


class TestSigV4Signing:
    """Tests for AWS Signature Version 4 signing."""

    def test_sign_request_adds_authorization_header(self) -> None:
        """Test that _sign_request adds Authorization header."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
            region="us-east-1",
        )

        headers = {"Content-Type": "application/json"}
        signed = adapter._sign_request("POST", "/v2/email/outbound-emails", headers, b'{"test": true}')

        assert "Authorization" in signed
        assert signed["Authorization"].startswith("AWS4-HMAC-SHA256")
        assert "Credential=AKIATEST123" in signed["Authorization"]

    def test_sign_request_adds_date_header(self) -> None:
        """Test that _sign_request adds X-Amz-Date header."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )

        headers = {"Content-Type": "application/json"}
        signed = adapter._sign_request("POST", "/v2/email/outbound-emails", headers, b'{}')

        assert "X-Amz-Date" in signed
        # Format: 20260131T123456Z
        assert len(signed["X-Amz-Date"]) == 16
        assert signed["X-Amz-Date"].endswith("Z")


class TestSNSMessageHelpers:
    """Tests for SNS message helper methods."""

    def test_get_sns_message_type_notification(self) -> None:
        """Test get_sns_message_type for Notification."""
        payload = {"Type": SNS_TYPE_NOTIFICATION}
        assert SESAdapter.get_sns_message_type(payload) == SNS_TYPE_NOTIFICATION

    def test_get_sns_message_type_subscription_confirmation(self) -> None:
        """Test get_sns_message_type for SubscriptionConfirmation."""
        payload = {"Type": SNS_TYPE_SUBSCRIPTION_CONFIRMATION}
        assert SESAdapter.get_sns_message_type(payload) == SNS_TYPE_SUBSCRIPTION_CONFIRMATION

    def test_get_sns_message_type_missing(self) -> None:
        """Test get_sns_message_type when Type is missing."""
        payload = {}
        assert SESAdapter.get_sns_message_type(payload) is None

    def test_is_inbound_event_for_valid_notification(self) -> None:
        """Test is_inbound_event for valid inbound email notification."""
        payload = load_fixture("ses_sns_simple.json")
        assert SESAdapter.is_inbound_event(payload) is True

    def test_is_inbound_event_for_non_notification(self) -> None:
        """Test is_inbound_event for non-Notification type."""
        payload = {"Type": SNS_TYPE_SUBSCRIPTION_CONFIRMATION}
        assert SESAdapter.is_inbound_event(payload) is False

    def test_is_inbound_event_for_empty_message(self) -> None:
        """Test is_inbound_event when Message is empty."""
        payload = {"Type": SNS_TYPE_NOTIFICATION, "Message": ""}
        assert SESAdapter.is_inbound_event(payload) is False

    def test_get_event_type_for_received_email(self) -> None:
        """Test get_event_type returns 'inbound' for received emails."""
        payload = load_fixture("ses_sns_simple.json")
        assert SESAdapter.get_event_type(payload) == "inbound"

    def test_get_event_type_for_empty_message(self) -> None:
        """Test get_event_type returns 'unknown' for empty message."""
        payload = {"Type": SNS_TYPE_NOTIFICATION, "Message": ""}
        assert SESAdapter.get_event_type(payload) == "unknown"


class TestParseInboundWebhook:
    """Tests for parse_inbound_webhook method."""

    def test_parse_simple_email(self) -> None:
        """Test parsing a simple email from SNS notification."""
        payload = load_fixture("ses_sns_simple.json")
        adapter = SESAdapter(
            access_key_id="test",
            secret_access_key="test",
        )

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.from_address == "alice@gmail.com"
        assert inbound.to_address == "support@mycompany.com"
        assert inbound.subject == "Question about pricing"
        assert "pricing for the enterprise plan" in inbound.body_plain
        assert inbound.message_id == "<CADfE8z+abc123@mail.gmail.com>"
        assert inbound.spf_result == "PASS"
        assert inbound.dkim_result == "PASS"
        assert inbound.dmarc_result == "PASS"

    def test_parse_extracts_verification_verdicts(self) -> None:
        """Test that verification verdicts are extracted from receipt."""
        payload = load_fixture("ses_sns_simple.json")
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert inbound.spf_result == "PASS"
        assert inbound.dkim_result == "PASS"
        assert inbound.dmarc_result == "PASS"

    def test_parse_extracts_headers_dict(self) -> None:
        """Test that headers are parsed into dictionary."""
        payload = load_fixture("ses_sns_simple.json")
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        assert "Message-ID" in inbound.headers
        assert inbound.headers["Message-ID"] == "<CADfE8z+abc123@mail.gmail.com>"

    def test_parse_handles_display_name_in_from(self) -> None:
        """Test parsing sender with display name."""
        # The fixture has "Alice Smith <alice@gmail.com>" in commonHeaders.from
        payload = load_fixture("ses_sns_simple.json")
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        # Should extract just the email
        assert inbound.from_address == "alice@gmail.com"

    def test_parse_raises_for_missing_message(self) -> None:
        """Test that parsing raises for missing Message field."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        with pytest.raises(SESWebhookError, match="Missing Message field"):
            adapter.parse_inbound_webhook({"Type": "Notification"})

    def test_parse_raises_for_invalid_json_in_message(self) -> None:
        """Test that parsing raises for invalid JSON in Message."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        with pytest.raises(SESWebhookError, match="Invalid JSON in Message field"):
            adapter.parse_inbound_webhook({
                "Type": "Notification",
                "Message": "not valid json"
            })


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature method."""

    def test_raises_for_missing_signature(self) -> None:
        """Test that verification raises for missing Signature."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        with pytest.raises(SESWebhookError, match="Missing Signature field"):
            adapter.verify_webhook_signature({
                "Type": "Notification",
                "SigningCertURL": "https://sns.us-east-1.amazonaws.com/cert.pem"
            })

    def test_raises_for_missing_signing_cert_url(self) -> None:
        """Test that verification raises for missing SigningCertURL."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        with pytest.raises(SESWebhookError, match="Missing SigningCertURL field"):
            adapter.verify_webhook_signature({
                "Type": "Notification",
                "Signature": "test-signature"
            })

    def test_raises_for_invalid_signing_cert_url(self) -> None:
        """Test that verification raises for non-AWS SigningCertURL."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        with pytest.raises(SESWebhookError, match="Invalid SigningCertURL"):
            adapter.verify_webhook_signature({
                "Type": "Notification",
                "Signature": "test-signature",
                "SigningCertURL": "https://evil.com/cert.pem"
            })

    def test_validates_signing_cert_url_pattern(self) -> None:
        """Test SigningCertURL validation for various URLs."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        # Valid URLs
        assert adapter._validate_signing_cert_url(
            "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-xxx.pem"
        ) is True
        assert adapter._validate_signing_cert_url(
            "https://sns.eu-west-1.amazonaws.com/cert.pem"
        ) is True
        assert adapter._validate_signing_cert_url(
            "https://sns.cn-north-1.amazonaws.com.cn/cert.pem"
        ) is True

        # Invalid URLs
        assert adapter._validate_signing_cert_url(
            "https://evil.com/cert.pem"
        ) is False
        assert adapter._validate_signing_cert_url(
            "http://sns.us-east-1.amazonaws.com/cert.pem"  # http not https
        ) is False


class TestSubscriptionConfirmation:
    """Tests for SNS subscription confirmation handling."""

    @pytest.mark.asyncio
    async def test_handle_subscription_confirmation_success(self) -> None:
        """Test successful subscription confirmation."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        payload = {
            "Type": SNS_TYPE_SUBSCRIPTION_CONFIRMATION,
            "TopicArn": "arn:aws:sns:us-east-1:123456789:test-topic",
            "SubscribeURL": "https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription&Token=xxx"
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await adapter.handle_subscription_confirmation(payload)

            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_confirmation_missing_url(self) -> None:
        """Test subscription confirmation with missing SubscribeURL."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        payload = {
            "Type": SNS_TYPE_SUBSCRIPTION_CONFIRMATION,
            "TopicArn": "arn:aws:sns:us-east-1:123456789:test-topic"
        }

        result = await adapter.handle_subscription_confirmation(payload)
        assert result is False


class TestSendEmail:
    """Tests for send_email method."""

    @pytest.mark.asyncio
    async def test_send_simple_email(self) -> None:
        """Test sending a simple email."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"MessageId": "ses-msg-id-123"}
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

            assert result == "ses-msg-id-123"
            mock_client.post.assert_called_once()

            call_args = mock_client.post.call_args
            # Check URL
            assert "/v2/email/outbound-emails" in call_args[0][0]

            # Check auth headers
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("AWS4-HMAC-SHA256")

    @pytest.mark.asyncio
    async def test_send_email_with_threading_headers(self) -> None:
        """Test sending email with threading headers."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"MessageId": "ses-msg-456"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await adapter.send_email(
                to=["recipient@example.com"],
                subject="Re: Original Subject",
                body="This is a reply",
                from_address="sender@example.com",
                message_id="<custom-id@example.com>",
                in_reply_to="<original-id@example.com>",
                references=["<ref1@example.com>", "<ref2@example.com>"],
            )

            # Parse the JSON payload
            call_args = mock_client.post.call_args
            payload = json.loads(call_args[1]["content"])

            # Check headers array
            headers = payload["Content"]["Simple"]["Headers"]
            header_dict = {h["Name"]: h["Value"] for h in headers}

            assert header_dict["Message-ID"] == "<custom-id@example.com>"
            assert header_dict["In-Reply-To"] == "<original-id@example.com>"
            assert header_dict["References"] == "<ref1@example.com> <ref2@example.com>"

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self) -> None:
        """Test sending email with CC and BCC."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"MessageId": "ses-msg-789"}
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

            call_args = mock_client.post.call_args
            payload = json.loads(call_args[1]["content"])

            assert payload["Destination"]["CcAddresses"] == ["cc1@example.com", "cc2@example.com"]
            assert payload["Destination"]["BccAddresses"] == ["bcc@example.com"]

    @pytest.mark.asyncio
    async def test_send_email_with_configuration_set(self) -> None:
        """Test sending email with configuration set."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
            configuration_set="my-tracking-set",
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"MessageId": "ses-msg-config"}
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            await adapter.send_email(
                to=["recipient@example.com"],
                subject="Test",
                body="Test body",
                from_address="sender@example.com",
            )

            call_args = mock_client.post.call_args
            payload = json.loads(call_args[1]["content"])

            assert payload["ConfigurationSetName"] == "my-tracking-set"

    @pytest.mark.asyncio
    async def test_send_email_api_error(self) -> None:
        """Test handling API errors."""
        adapter = SESAdapter(
            access_key_id="AKIATEST123",
            secret_access_key="secretkey123",
        )

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


class TestMIMEParsing:
    """Tests for MIME content parsing."""

    def test_parse_simple_text_mime(self) -> None:
        """Test parsing simple text MIME content."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        mime_content = (
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
            "Hello, this is a test email."
        )

        body_plain, body_html, attachments, content_id_map = adapter._parse_mime_content(
            mime_content.encode("utf-8")
        )

        assert "Hello, this is a test email" in body_plain
        assert body_html is None
        assert len(attachments) == 0

    def test_parse_multipart_mime(self) -> None:
        """Test parsing multipart MIME content."""
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        mime_content = (
            "Content-Type: multipart/alternative; boundary=boundary123\r\n"
            "\r\n"
            "--boundary123\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "\r\n"
            "Plain text version\r\n"
            "--boundary123\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            "<p>HTML version</p>\r\n"
            "--boundary123--"
        )

        body_plain, body_html, attachments, content_id_map = adapter._parse_mime_content(
            mime_content.encode("utf-8")
        )

        assert "Plain text version" in body_plain
        assert body_html is not None
        assert "<p>HTML version</p>" in body_html


class TestAllSESFixtures:
    """Test that all SES fixtures parse correctly."""

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "ses_sns_simple.json",
        ],
    )
    def test_fixture_parses_successfully(self, fixture_name: str) -> None:
        """Test that each fixture parses without error."""
        payload = load_fixture(fixture_name)
        adapter = SESAdapter(access_key_id="test", secret_access_key="test")

        inbound = adapter.parse_inbound_webhook(payload)

        # Basic validation
        assert inbound.from_address != ""
        assert inbound.to_address != ""
        assert inbound.subject != ""
