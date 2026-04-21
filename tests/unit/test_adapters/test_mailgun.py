"""Unit tests for MailgunAdapter."""

import hashlib
import hmac
import time

import pytest

from nornweave.adapters.mailgun import MailgunAdapter, MailgunWebhookError


def _mailgun_signature(signing_key: str, timestamp: int, token: str) -> str:
    signed_payload = f"{timestamp}{token}".encode()
    return hmac.new(signing_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()


class TestVerifyWebhookSignature:
    """Tests for Mailgun webhook verification."""

    def test_raises_when_signing_key_not_configured(self) -> None:
        """Verification should fail closed without webhook signing key."""
        adapter = MailgunAdapter(api_key="test", domain="mail.example.com")

        with pytest.raises(MailgunWebhookError, match="Webhook signing key not configured"):
            adapter.verify_webhook_signature(
                {
                    "timestamp": str(int(time.time())),
                    "token": "token-123",
                    "signature": "any-signature",
                }
            )

    def test_raises_when_required_fields_missing(self) -> None:
        """Verification should fail when required webhook fields are missing."""
        adapter = MailgunAdapter(
            api_key="test",
            domain="mail.example.com",
            webhook_signing_key="signing-key",
        )

        with pytest.raises(
            MailgunWebhookError, match="Missing required webhook fields: timestamp, token, signature"
        ):
            adapter.verify_webhook_signature({"timestamp": str(int(time.time())), "token": "token-123"})

    def test_raises_for_invalid_timestamp_format(self) -> None:
        """Verification should fail for non-numeric timestamps."""
        adapter = MailgunAdapter(
            api_key="test",
            domain="mail.example.com",
            webhook_signing_key="signing-key",
        )

        with pytest.raises(MailgunWebhookError, match="Invalid timestamp format"):
            adapter.verify_webhook_signature(
                {
                    "timestamp": "not-a-number",
                    "token": "token-123",
                    "signature": "abcdef",
                }
            )

    def test_raises_for_expired_timestamp(self) -> None:
        """Verification should fail when timestamp is outside tolerance."""
        signing_key = "signing-key"
        token = "token-123"
        old_timestamp = int(time.time()) - 3600
        signature = _mailgun_signature(signing_key, old_timestamp, token)
        adapter = MailgunAdapter(
            api_key="test",
            domain="mail.example.com",
            webhook_signing_key=signing_key,
        )

        with pytest.raises(MailgunWebhookError, match="Timestamp validation failed"):
            adapter.verify_webhook_signature(
                {
                    "timestamp": str(old_timestamp),
                    "token": token,
                    "signature": signature,
                }
            )

    def test_raises_for_invalid_signature(self) -> None:
        """Verification should fail when HMAC signature does not match."""
        adapter = MailgunAdapter(
            api_key="test",
            domain="mail.example.com",
            webhook_signing_key="signing-key",
        )

        with pytest.raises(MailgunWebhookError, match="Signature verification failed"):
            adapter.verify_webhook_signature(
                {
                    "timestamp": str(int(time.time())),
                    "token": "token-123",
                    "signature": "not-a-valid-signature",
                }
            )

    def test_verifies_valid_signature(self) -> None:
        """Verification should pass for a valid timestamp/token/signature."""
        signing_key = "signing-key"
        token = "token-123"
        timestamp = int(time.time())
        signature = _mailgun_signature(signing_key, timestamp, token)
        adapter = MailgunAdapter(
            api_key="test",
            domain="mail.example.com",
            webhook_signing_key=signing_key,
        )

        adapter.verify_webhook_signature(
            {
                "timestamp": str(timestamp),
                "token": token,
                "signature": signature,
            }
        )
