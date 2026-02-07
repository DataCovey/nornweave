"""Tests for outbound domain filtering in the send_message route."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.core.interfaces import StorageInterface
from nornweave.models.inbox import Inbox
from nornweave.yggdrasil.routes.v1.messages import SendMessageRequest, send_message

if TYPE_CHECKING:
    from nornweave.models.thread import Thread


def _make_settings(
    *,
    outbound_domain_allowlist: str = "",
    outbound_domain_blocklist: str = "",
) -> MagicMock:
    """Build a mock Settings with domain filter fields."""
    settings = MagicMock()
    settings.outbound_domain_allowlist = outbound_domain_allowlist
    settings.outbound_domain_blocklist = outbound_domain_blocklist
    settings.attachment_storage_backend = "local"
    settings.attachment_local_path = "/tmp/test-attachments"
    return settings


def _make_storage(*, inbox: Inbox | None = None) -> AsyncMock:
    """Build a mock StorageInterface for send tests."""
    storage = AsyncMock(spec=StorageInterface)
    storage.get_inbox = AsyncMock(return_value=inbox)

    async def _create_thread(thread: Thread) -> Thread:
        return thread

    storage.create_thread = AsyncMock(side_effect=_create_thread)
    storage.get_thread = AsyncMock(return_value=None)
    storage.update_thread = AsyncMock()
    storage.create_message = AsyncMock(
        side_effect=lambda msg: msg,
    )
    storage.create_attachment = AsyncMock()
    return storage


def _make_inbox(
    inbox_id: str = "inbox-001",
    email_address: str = "bot@nornweave.dev",
) -> Inbox:
    return Inbox(id=inbox_id, email_address=email_address, name="Test Inbox")


def _make_email_provider() -> AsyncMock:
    provider = AsyncMock()
    provider.send_email = AsyncMock(return_value="provider-msg-id-001")
    return provider


# ---------------------------------------------------------------------------
# Outbound domain filtering — blocked
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_blocked_recipient_returns_403() -> None:
    """Sending to a blocklisted recipient domain returns HTTP 403."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(outbound_domain_blocklist=r"blocked\.org")
    provider = _make_email_provider()
    payload = SendMessageRequest(
        inbox_id="inbox-001",
        to=["user@blocked.org"],
        subject="Hello",
        body="Test body",
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await send_message(payload, storage, provider, settings)

    assert exc_info.value.status_code == 403
    assert "blocked.org" in str(exc_info.value.detail)
    provider.send_email.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_mixed_recipients_blocked_returns_403() -> None:
    """If any recipient domain is blocked, the entire send is rejected."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(outbound_domain_blocklist=r"blocked\.org")
    provider = _make_email_provider()
    payload = SendMessageRequest(
        inbox_id="inbox-001",
        to=["user@ok.com", "user@blocked.org"],
        subject="Hello",
        body="Test body",
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await send_message(payload, storage, provider, settings)

    assert exc_info.value.status_code == 403
    assert "blocked.org" in str(exc_info.value.detail)
    provider.send_email.assert_not_awaited()


# ---------------------------------------------------------------------------
# Outbound domain filtering — allowed
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_allowed_recipient_proceeds() -> None:
    """Sending to an allowlisted recipient domain proceeds normally."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(outbound_domain_allowlist=r"partner\.com")
    provider = _make_email_provider()
    payload = SendMessageRequest(
        inbox_id="inbox-001",
        to=["user@partner.com"],
        subject="Hello",
        body="Test body",
    )

    with patch(
        "nornweave.yggdrasil.routes.v1.messages.generate_thread_summary",
        new_callable=AsyncMock,
    ):
        result = await send_message(payload, storage, provider, settings)

    assert result.status == "sent"
    provider.send_email.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_no_filter_configured_proceeds() -> None:
    """When no domain filter is configured, all sends proceed."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings()  # empty lists
    provider = _make_email_provider()
    payload = SendMessageRequest(
        inbox_id="inbox-001",
        to=["anyone@anywhere.com"],
        subject="Hello",
        body="Test body",
    )

    with patch(
        "nornweave.yggdrasil.routes.v1.messages.generate_thread_summary",
        new_callable=AsyncMock,
    ):
        result = await send_message(payload, storage, provider, settings)

    assert result.status == "sent"
    provider.send_email.assert_awaited_once()
