"""Unit tests for POST /v1/inboxes/{inbox_id}/sync.

Tests the sync endpoint with mocked dependencies: storage, settings, and poller.
Covers: successful sync, wrong provider, missing inbox, IMAP failure, poller not running.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from nornweave.core.config import get_settings
from nornweave.models.inbox import Inbox
from nornweave.yggdrasil.dependencies import get_storage
from nornweave.yggdrasil.routes.v1.inboxes import router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with just the inbox router."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/v1")
    return test_app


def _mock_settings(provider: str = "imap-smtp") -> MagicMock:
    settings = MagicMock()
    settings.email_provider = provider
    return settings


def _mock_storage(inbox: Inbox | None = None) -> AsyncMock:
    storage = AsyncMock()
    storage.get_inbox = AsyncMock(return_value=inbox)
    return storage


def _test_inbox() -> Inbox:
    return Inbox(
        id="inbox-123",
        email_address="test@example.com",
        name="Test Inbox",
        provider_config={},
    )


# ===========================================================================
# Successful sync
# ===========================================================================
@pytest.mark.unit
class TestSyncEndpointSuccess:
    """Successful manual IMAP sync."""

    def test_returns_200_with_sync_result(self) -> None:
        app = _make_app()
        inbox = _test_inbox()
        mock_poller = MagicMock()
        mock_poller.sync_inbox = AsyncMock(return_value=3)

        app.dependency_overrides[get_storage] = lambda: _mock_storage(inbox)
        app.dependency_overrides[get_settings] = lambda: _mock_settings("imap-smtp")

        with patch("nornweave.yggdrasil.app.get_imap_poller", return_value=mock_poller):
            client = TestClient(app)
            response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert data["new_messages"] == 3

    def test_returns_zero_messages_when_none_found(self) -> None:
        app = _make_app()
        inbox = _test_inbox()
        mock_poller = MagicMock()
        mock_poller.sync_inbox = AsyncMock(return_value=0)

        app.dependency_overrides[get_storage] = lambda: _mock_storage(inbox)
        app.dependency_overrides[get_settings] = lambda: _mock_settings("imap-smtp")

        with patch("nornweave.yggdrasil.app.get_imap_poller", return_value=mock_poller):
            client = TestClient(app)
            response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 200
        assert response.json()["new_messages"] == 0


# ===========================================================================
# Wrong provider
# ===========================================================================
@pytest.mark.unit
class TestSyncEndpointWrongProvider:
    """Sync returns 404 when provider is not imap-smtp."""

    def test_returns_404_for_mailgun_provider(self) -> None:
        app = _make_app()

        app.dependency_overrides[get_storage] = lambda: _mock_storage(_test_inbox())
        app.dependency_overrides[get_settings] = lambda: _mock_settings("mailgun")

        client = TestClient(app)
        response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 404
        assert "imap-smtp" in response.json()["detail"]

    def test_returns_404_for_resend_provider(self) -> None:
        app = _make_app()

        app.dependency_overrides[get_storage] = lambda: _mock_storage(_test_inbox())
        app.dependency_overrides[get_settings] = lambda: _mock_settings("resend")

        client = TestClient(app)
        response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 404


# ===========================================================================
# Missing inbox
# ===========================================================================
@pytest.mark.unit
class TestSyncEndpointMissingInbox:
    """Sync returns 404 when inbox doesn't exist."""

    def test_returns_404_for_unknown_inbox(self) -> None:
        app = _make_app()

        app.dependency_overrides[get_storage] = lambda: _mock_storage(inbox=None)
        app.dependency_overrides[get_settings] = lambda: _mock_settings("imap-smtp")

        client = TestClient(app)
        response = client.post("/v1/inboxes/nonexistent/sync")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


# ===========================================================================
# IMAP failure
# ===========================================================================
@pytest.mark.unit
class TestSyncEndpointImapFailure:
    """Sync returns 502 on IMAP connection failure."""

    def test_returns_502_on_connection_error(self) -> None:
        app = _make_app()
        inbox = _test_inbox()
        mock_poller = MagicMock()
        mock_poller.sync_inbox = AsyncMock(side_effect=ConnectionError("IMAP server down"))

        app.dependency_overrides[get_storage] = lambda: _mock_storage(inbox)
        app.dependency_overrides[get_settings] = lambda: _mock_settings("imap-smtp")

        with patch("nornweave.yggdrasil.app.get_imap_poller", return_value=mock_poller):
            client = TestClient(app)
            response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 502
        assert "IMAP connection failure" in response.json()["detail"]

    def test_returns_404_when_poller_not_running(self) -> None:
        app = _make_app()
        inbox = _test_inbox()

        app.dependency_overrides[get_storage] = lambda: _mock_storage(inbox)
        app.dependency_overrides[get_settings] = lambda: _mock_settings("imap-smtp")

        with patch("nornweave.yggdrasil.app.get_imap_poller", return_value=None):
            client = TestClient(app)
            response = client.post("/v1/inboxes/inbox-123/sync")

        assert response.status_code == 404
        assert "poller" in response.json()["detail"].lower()
