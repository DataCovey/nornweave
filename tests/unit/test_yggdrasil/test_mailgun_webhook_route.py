"""Unit tests for Mailgun webhook route verification behavior."""

import hashlib
import hmac
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nornweave.core.config import get_settings
from nornweave.yggdrasil.dependencies import get_storage
from nornweave.yggdrasil.routes.webhooks import mailgun


def _mailgun_signature(signing_key: str, timestamp: int, token: str) -> str:
    signed_payload = f"{timestamp}{token}".encode()
    return hmac.new(signing_key.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()


def _make_app(signing_key: str) -> FastAPI:
    app = FastAPI()
    app.include_router(mailgun.router, prefix="/webhooks")
    app.dependency_overrides[get_storage] = lambda: AsyncMock()
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        mailgun_api_key="key-test",
        mailgun_domain="mail.example.com",
        webhook_secret=signing_key,
    )
    return app


def _mailgun_form(*, signing_key: str, token: str = "token-123", signature: str | None = None) -> dict[str, str]:
    timestamp = int(time.time())
    signed = signature or _mailgun_signature(signing_key, timestamp, token)
    return {
        "sender": "alice@gmail.com",
        "from": "Alice Smith <alice@gmail.com>",
        "recipient": "support@example.com",
        "subject": "Test subject",
        "body-plain": "Hello",
        "timestamp": str(timestamp),
        "token": token,
        "signature": signed,
    }


@pytest.mark.unit
class TestMailgunWebhookRouteVerification:
    """Ensure webhook verification is enforced before parsing and ingestion."""

    def test_rejects_invalid_signature_before_parse_and_ingest(self) -> None:
        app = _make_app("mailgun-signing-key")
        client = TestClient(app)
        form_data = _mailgun_form(signing_key="mailgun-signing-key", signature="invalid-signature")

        with patch(
            "nornweave.yggdrasil.routes.webhooks.mailgun.MailgunAdapter.parse_inbound_webhook"
        ) as mock_parse, patch(
            "nornweave.yggdrasil.routes.webhooks.mailgun.ingest_message",
            new_callable=AsyncMock,
        ) as mock_ingest:
            response = client.post("/webhooks/mailgun", data=form_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "Signature verification failed"
        mock_parse.assert_not_called()
        mock_ingest.assert_not_awaited()

    def test_rejects_when_signing_key_not_configured(self) -> None:
        app = _make_app("")
        client = TestClient(app)
        form_data = _mailgun_form(signing_key="fallback-key")

        with patch(
            "nornweave.yggdrasil.routes.webhooks.mailgun.MailgunAdapter.parse_inbound_webhook"
        ) as mock_parse, patch(
            "nornweave.yggdrasil.routes.webhooks.mailgun.ingest_message",
            new_callable=AsyncMock,
        ) as mock_ingest:
            response = client.post("/webhooks/mailgun", data=form_data)

        assert response.status_code == 503
        assert response.json()["detail"] == "Mailgun webhook verification is not configured"
        mock_parse.assert_not_called()
        mock_ingest.assert_not_awaited()

    def test_accepts_valid_signature_and_processes_webhook(self) -> None:
        app = _make_app("mailgun-signing-key")
        client = TestClient(app)
        form_data = _mailgun_form(signing_key="mailgun-signing-key")

        with patch(
            "nornweave.yggdrasil.routes.webhooks.mailgun.ingest_message",
            new_callable=AsyncMock,
        ) as mock_ingest:
            mock_ingest.return_value = SimpleNamespace(
                status="received",
                message_id="msg-123",
                thread_id="th-456",
            )

            response = client.post("/webhooks/mailgun", data=form_data)

        assert response.status_code == 200
        assert response.json() == {
            "status": "received",
            "message_id": "msg-123",
            "thread_id": "th-456",
        }
        mock_ingest.assert_awaited_once()
