"""Tests for the shared ingestion pipeline (verdandi.ingest)."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.core.interfaces import InboundMessage, StorageInterface
from nornweave.models.inbox import Inbox
from nornweave.models.message import Message, MessageDirection
from nornweave.verdandi.ingest import IngestResult, ingest_message

if TYPE_CHECKING:
    from nornweave.models.thread import Thread


def _make_inbound(
    *,
    from_address: str = "sender@example.com",
    to_address: str = "inbox@nornweave.dev",
    subject: str = "Test subject",
    body_plain: str = "Hello, this is a test.",
    message_id: str | None = "<test-msg-001@example.com>",
    in_reply_to: str | None = None,
    references: list[str] | None = None,
) -> InboundMessage:
    """Build a minimal InboundMessage for testing."""
    return InboundMessage(
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body_plain=body_plain,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references or [],
        timestamp=datetime(2026, 2, 6, 12, 0, 0, tzinfo=UTC),
    )


def _make_inbox(
    inbox_id: str = "inbox-001",
    email_address: str = "inbox@nornweave.dev",
) -> Inbox:
    """Build a minimal Inbox for testing."""
    return Inbox(id=inbox_id, email_address=email_address, name="Test Inbox")


def _make_settings(
    *,
    inbound_domain_allowlist: str = "",
    inbound_domain_blocklist: str = "",
) -> MagicMock:
    """Build a mock Settings object with sensible defaults."""
    settings = MagicMock()
    settings.attachment_storage_backend = "local"
    settings.attachment_local_path = "/tmp/test-attachments"
    settings.inbound_domain_allowlist = inbound_domain_allowlist
    settings.inbound_domain_blocklist = inbound_domain_blocklist
    return settings


def _make_storage(
    *,
    inbox: Inbox | None = None,
    existing_message: Message | None = None,
) -> AsyncMock:
    """Build a mock StorageInterface.

    Args:
        inbox: Inbox to return from get_inbox_by_email. None = no inbox found.
        existing_message: Message to return from get_message_by_provider_id
                          (simulates duplicate). None = no duplicate.
    """
    storage = AsyncMock(spec=StorageInterface)
    storage.get_inbox_by_email = AsyncMock(return_value=inbox)
    storage.get_message_by_provider_id = AsyncMock(return_value=existing_message)

    # Thread creation returns a Thread with an id
    async def _create_thread(thread: Thread) -> Thread:
        return thread

    storage.create_thread = AsyncMock(side_effect=_create_thread)
    storage.get_thread = AsyncMock(return_value=None)
    storage.update_thread = AsyncMock()

    # Message creation returns the message as-is (with id set)
    async def _create_message(message: Message) -> Message:
        return message

    storage.create_message = AsyncMock(side_effect=_create_message)

    return storage


# ---------------------------------------------------------------------------
# Successful ingestion
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_success_creates_message() -> None:
    """Successful ingestion should create a message and return 'received'."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings()
    inbound = _make_inbound()

    with patch("nornweave.verdandi.ingest.generate_thread_summary", new_callable=AsyncMock):
        result = await ingest_message(inbound, storage, settings)

    assert isinstance(result, IngestResult)
    assert result.status == "received"
    assert result.message_id != ""
    assert result.thread_id != ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_success_calls_storage() -> None:
    """Ingestion should call storage.create_thread and storage.create_message."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings()
    inbound = _make_inbound()

    with patch("nornweave.verdandi.ingest.generate_thread_summary", new_callable=AsyncMock):
        await ingest_message(inbound, storage, settings)

    storage.get_inbox_by_email.assert_awaited_once_with("inbox@nornweave.dev")
    storage.create_thread.assert_awaited_once()
    storage.create_message.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_success_message_fields() -> None:
    """Created message should carry correct fields from inbound."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings()
    inbound = _make_inbound(
        from_address="alice@example.com",
        subject="Important update",
        body_plain="The update content.",
    )

    with patch("nornweave.verdandi.ingest.generate_thread_summary", new_callable=AsyncMock):
        await ingest_message(inbound, storage, settings)

    # Inspect the Message passed to create_message
    created_msg: Message = storage.create_message.call_args[0][0]
    assert created_msg.from_address == "alice@example.com"
    assert created_msg.subject == "Important update"
    assert created_msg.text == "The update content."
    assert created_msg.direction == MessageDirection.INBOUND
    assert created_msg.inbox_id == "inbox-001"


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_duplicate_returns_duplicate_status() -> None:
    """If message_id already exists, ingestion returns 'duplicate'."""
    inbox = _make_inbox()
    existing = Message(
        message_id="existing-msg-001",
        thread_id="existing-thread-001",
        inbox_id="inbox-001",
        direction=MessageDirection.INBOUND,
    )
    storage = _make_storage(inbox=inbox, existing_message=existing)
    settings = _make_settings()
    inbound = _make_inbound(message_id="<duplicate@example.com>")

    result = await ingest_message(inbound, storage, settings)

    assert result.status == "duplicate"
    assert result.message_id == "existing-msg-001"
    assert result.thread_id == "existing-thread-001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_duplicate_does_not_create_message() -> None:
    """Duplicate should not call create_message or create_thread."""
    inbox = _make_inbox()
    existing = Message(
        message_id="existing-msg-001",
        thread_id="existing-thread-001",
        inbox_id="inbox-001",
        direction=MessageDirection.INBOUND,
    )
    storage = _make_storage(inbox=inbox, existing_message=existing)
    settings = _make_settings()
    inbound = _make_inbound(message_id="<duplicate@example.com>")

    await ingest_message(inbound, storage, settings)

    storage.create_message.assert_not_awaited()
    storage.create_thread.assert_not_awaited()


# ---------------------------------------------------------------------------
# No matching inbox
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_no_inbox_returns_no_inbox_status() -> None:
    """When no inbox matches the recipient, return 'no_inbox'."""
    storage = _make_storage(inbox=None)
    settings = _make_settings()
    inbound = _make_inbound(to_address="unknown@nornweave.dev")

    result = await ingest_message(inbound, storage, settings)

    assert result.status == "no_inbox"
    assert result.message_id == ""
    assert result.thread_id == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_no_inbox_does_not_create_anything() -> None:
    """No inbox should not trigger any create operations."""
    storage = _make_storage(inbox=None)
    settings = _make_settings()
    inbound = _make_inbound(to_address="unknown@nornweave.dev")

    await ingest_message(inbound, storage, settings)

    storage.create_message.assert_not_awaited()
    storage.create_thread.assert_not_awaited()


# ---------------------------------------------------------------------------
# Inbound domain filtering
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_blocked_sender_domain_returns_domain_blocked() -> None:
    """Inbound email from a blocklisted sender domain returns 'domain_blocked'."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(inbound_domain_blocklist=r"blocked\.org")
    inbound = _make_inbound(from_address="spammer@blocked.org")

    result = await ingest_message(inbound, storage, settings)

    assert result.status == "domain_blocked"
    assert result.message_id == ""
    assert result.thread_id == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_blocked_sender_does_not_create_anything() -> None:
    """Blocked sender should not trigger any create operations."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(inbound_domain_blocklist=r"blocked\.org")
    inbound = _make_inbound(from_address="spammer@blocked.org")

    await ingest_message(inbound, storage, settings)

    storage.create_message.assert_not_awaited()
    storage.create_thread.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_allowed_sender_domain_proceeds() -> None:
    """Inbound email from an allowlisted sender domain is processed normally."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(inbound_domain_allowlist=r"allowed\.com")
    inbound = _make_inbound(from_address="partner@allowed.com")

    with patch("nornweave.verdandi.ingest.generate_thread_summary", new_callable=AsyncMock):
        result = await ingest_message(inbound, storage, settings)

    assert result.status == "received"
    assert result.message_id != ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ingest_unlisted_domain_rejected_when_allowlist_active() -> None:
    """Sender domain not on the allowlist is rejected when allowlist is set."""
    inbox = _make_inbox()
    storage = _make_storage(inbox=inbox)
    settings = _make_settings(inbound_domain_allowlist=r"allowed\.com")
    inbound = _make_inbound(from_address="stranger@unknown.com")

    result = await ingest_message(inbound, storage, settings)

    assert result.status == "domain_blocked"
    storage.create_message.assert_not_awaited()
    storage.create_thread.assert_not_awaited()
