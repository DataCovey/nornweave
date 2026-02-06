"""Unit tests for ImapReceiver.

Tests UID search/fetch, UIDVALIDITY change detection, mark-as-read,
delete-after-fetch, and connection failure handling — all with aioimaplib mocked.
"""

import sys
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.adapters.smtp_imap import ImapReceiver


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------
@dataclass
class FakeResponse:
    """Minimal mock of aioimaplib response objects."""

    result: str = "OK"
    lines: list = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.lines is None:
            self.lines = []


def _make_mock_client(
    *,
    uid_search_lines: list | None = None,
    uid_fetch_lines: list | None = None,
    select_lines: list | None = None,
) -> MagicMock:
    """Build a mock IMAP client with configurable responses."""
    client = MagicMock()
    client.wait_hello_from_server = AsyncMock()
    client.login = AsyncMock()
    client.logout = AsyncMock()

    _select_lines = select_lines or ["OK [UIDVALIDITY 12345] selected"]
    client.select = AsyncMock(return_value=FakeResponse(result="OK", lines=_select_lines))

    _search_lines = uid_search_lines if uid_search_lines is not None else [""]
    client.uid_search = AsyncMock(return_value=FakeResponse(result="OK", lines=_search_lines))

    _fetch_lines = uid_fetch_lines if uid_fetch_lines is not None else []
    client.uid = AsyncMock(return_value=FakeResponse(result="OK", lines=_fetch_lines))

    client.expunge = AsyncMock()

    return client


def _mock_aioimaplib() -> MagicMock:
    """Create a mock aioimaplib module."""
    mock = MagicMock()
    return mock


def _receiver(**kwargs) -> ImapReceiver:
    defaults: dict = {
        "host": "imap.test.com",
        "port": 993,
        "username": "user@test.com",
        "password": "secret",
        "use_ssl": True,
        "mailbox": "INBOX",
        "mark_as_read": True,
        "delete_after_fetch": False,
    }
    defaults.update(kwargs)
    return ImapReceiver(**defaults)


# ===========================================================================
# UID Search
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverUidSearch:
    """UID SEARCH behaviour."""

    @pytest.mark.asyncio
    async def test_fetch_new_messages_always_searches_all(self) -> None:
        """Always uses ALL search for max IMAP server compatibility."""
        client = _make_mock_client(uid_search_lines=["42 43 44"])
        client.uid = AsyncMock(
            return_value=FakeResponse(result="OK", lines=[b"* 1 FETCH", bytearray(b"raw"), b")"])
        )
        receiver = _receiver()
        receiver._client = client

        await receiver.fetch_new_messages(last_uid=42)

        client.uid_search.assert_awaited_once_with("ALL")

    @pytest.mark.asyncio
    async def test_fetch_all_when_last_uid_is_zero(self) -> None:
        client = _make_mock_client(uid_search_lines=[""])
        receiver = _receiver()
        receiver._client = client

        await receiver.fetch_new_messages(last_uid=0)

        client.uid_search.assert_awaited_once_with("ALL")

    @pytest.mark.asyncio
    async def test_returns_empty_when_search_fails(self) -> None:
        client = _make_mock_client()
        client.uid_search = AsyncMock(
            return_value=FakeResponse(result="NO", lines=["NO search failed"])
        )
        receiver = _receiver()
        receiver._client = client

        result = await receiver.fetch_new_messages(last_uid=10)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_new_uids(self) -> None:
        client = _make_mock_client(uid_search_lines=[""])
        receiver = _receiver()
        receiver._client = client

        result = await receiver.fetch_new_messages(last_uid=99)

        assert result == []

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self) -> None:
        receiver = _receiver()
        receiver._client = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await receiver.fetch_new_messages(last_uid=0)


# ===========================================================================
# UID Fetch
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverUidFetch:
    """UID FETCH and message retrieval."""

    @pytest.mark.asyncio
    async def test_fetches_raw_bytes_for_each_uid(self) -> None:
        raw_email = bytearray(b"From: a@b.com\r\nSubject: Hi\r\n\r\nHello")
        client = _make_mock_client(uid_search_lines=["50 51"])
        client.uid = AsyncMock(
            return_value=FakeResponse(
                result="OK",
                lines=[b"1 FETCH (RFC822 {35})", raw_email, b")", b"FETCH completed"],
            )
        )

        receiver = _receiver()
        receiver._client = client

        result = await receiver.fetch_new_messages(last_uid=49)

        assert len(result) == 2
        assert result[0] == (50, bytes(raw_email))
        assert result[1] == (51, bytes(raw_email))

    @pytest.mark.asyncio
    async def test_skips_uid_on_fetch_failure(self) -> None:
        raw_email = bytearray(b"From: a@b.com\r\nSubject: Hi\r\n\r\nHello")
        client = _make_mock_client(uid_search_lines=["60 61"])

        call_count = 0

        async def uid_side_effect(*_args: object, **_kwargs: object) -> FakeResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("network error")
            return FakeResponse(
                result="OK",
                lines=[b"1 FETCH (RFC822 {35})", raw_email, b")", b"FETCH completed"],
            )

        client.uid = AsyncMock(side_effect=uid_side_effect)
        receiver = _receiver()
        receiver._client = client

        result = await receiver.fetch_new_messages(last_uid=59)

        # First UID (60) fails, second (61) succeeds
        assert len(result) == 1
        assert result[0][0] == 61

    @pytest.mark.asyncio
    async def test_filters_out_old_uids_from_search(self) -> None:
        # Search ALL returns all UIDs; client-side filtering removes old ones
        raw_email = bytearray(b"From: a@b.com\r\nSubject: Hi\r\n\r\nHello")
        client = _make_mock_client(uid_search_lines=["42 43 44"])
        client.uid = AsyncMock(
            return_value=FakeResponse(
                result="OK",
                lines=[b"1 FETCH (RFC822 {35})", raw_email, b")", b"FETCH completed"],
            )
        )
        receiver = _receiver()
        receiver._client = client

        result = await receiver.fetch_new_messages(last_uid=42)

        # UID 42 should be filtered out, only 43 and 44 fetched
        assert len(result) == 2
        assert result[0][0] == 43
        assert result[1][0] == 44


# ===========================================================================
# UIDVALIDITY
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverUidValidity:
    """UIDVALIDITY parsing."""

    @pytest.mark.asyncio
    async def test_parses_uid_validity_from_select(self) -> None:
        client = _make_mock_client(
            select_lines=["* FLAGS (\\Seen)", "OK [UIDVALIDITY 99887766] selected"]
        )
        receiver = _receiver()
        receiver._client = client

        result = await receiver.get_uid_validity()

        assert result == 99887766

    @pytest.mark.asyncio
    async def test_returns_zero_when_not_found(self) -> None:
        client = _make_mock_client(select_lines=["OK selected"])
        receiver = _receiver()
        receiver._client = client

        result = await receiver.get_uid_validity()

        assert result == 0

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self) -> None:
        receiver = _receiver()
        receiver._client = None

        with pytest.raises(RuntimeError, match="Not connected"):
            await receiver.get_uid_validity()


# ===========================================================================
# Mark-as-read
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverMarkAsRead:
    """\\Seen flag management."""

    @pytest.mark.asyncio
    async def test_sets_seen_flag_when_enabled(self) -> None:
        client = _make_mock_client()
        receiver = _receiver(mark_as_read=True)
        receiver._client = client

        await receiver.mark_as_read(uid=50)

        client.uid.assert_awaited_once_with("store", "50", "+FLAGS", "(\\Seen)")

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        client = _make_mock_client()
        receiver = _receiver(mark_as_read=False)
        receiver._client = client

        await receiver.mark_as_read(uid=50)

        client.uid.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_not_connected(self) -> None:
        receiver = _receiver(mark_as_read=True)
        receiver._client = None

        # Should not raise
        await receiver.mark_as_read(uid=50)

    @pytest.mark.asyncio
    async def test_swallows_exception(self) -> None:
        client = _make_mock_client()
        client.uid = AsyncMock(side_effect=ConnectionError("gone"))
        receiver = _receiver(mark_as_read=True)
        receiver._client = client

        # Should not raise
        await receiver.mark_as_read(uid=50)


# ===========================================================================
# Delete-after-fetch
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverDeleteAfterFetch:
    """\\Deleted flag + EXPUNGE management."""

    @pytest.mark.asyncio
    async def test_deletes_and_expunges_when_enabled(self) -> None:
        client = _make_mock_client()
        receiver = _receiver(delete_after_fetch=True)
        receiver._client = client

        await receiver.delete_message(uid=50)

        assert client.uid.await_count == 1
        client.uid.assert_awaited_once_with("store", "50", "+FLAGS", "(\\Deleted)")
        client.expunge.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        client = _make_mock_client()
        receiver = _receiver(delete_after_fetch=False)
        receiver._client = client

        await receiver.delete_message(uid=50)

        client.uid.assert_not_awaited()
        client.expunge.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_not_connected(self) -> None:
        receiver = _receiver(delete_after_fetch=True)
        receiver._client = None

        await receiver.delete_message(uid=50)

    @pytest.mark.asyncio
    async def test_swallows_exception(self) -> None:
        client = _make_mock_client()
        client.uid = AsyncMock(side_effect=ConnectionError("gone"))
        receiver = _receiver(delete_after_fetch=True)
        receiver._client = client

        # Should not raise
        await receiver.delete_message(uid=50)


# ===========================================================================
# Connection
# ===========================================================================
@pytest.mark.unit
class TestImapReceiverConnection:
    """Connect / disconnect behaviour."""

    @pytest.mark.asyncio
    async def test_connect_ssl(self) -> None:
        receiver = _receiver(use_ssl=True)
        mock_lib = _mock_aioimaplib()
        mock_client = _make_mock_client()
        mock_lib.IMAP4_SSL = MagicMock(return_value=mock_client)

        with patch.dict(sys.modules, {"aioimaplib": mock_lib}):
            await receiver.connect()

        mock_lib.IMAP4_SSL.assert_called_once_with(host="imap.test.com", port=993)
        mock_client.wait_hello_from_server.assert_awaited_once()
        mock_client.login.assert_awaited_once_with("user@test.com", "secret")
        mock_client.select.assert_awaited_once_with("INBOX")

    @pytest.mark.asyncio
    async def test_connect_plaintext(self) -> None:
        receiver = _receiver(use_ssl=False)
        mock_lib = _mock_aioimaplib()
        mock_client = _make_mock_client()
        mock_lib.IMAP4 = MagicMock(return_value=mock_client)

        with patch.dict(sys.modules, {"aioimaplib": mock_lib}):
            await receiver.connect()

        mock_lib.IMAP4.assert_called_once_with(host="imap.test.com", port=993)

    @pytest.mark.asyncio
    async def test_disconnect_calls_logout(self) -> None:
        client = _make_mock_client()
        receiver = _receiver()
        receiver._client = client

        await receiver.disconnect()

        client.logout.assert_awaited_once()
        assert receiver._client is None

    @pytest.mark.asyncio
    async def test_disconnect_swallows_exception(self) -> None:
        client = _make_mock_client()
        client.logout = AsyncMock(side_effect=ConnectionError("already closed"))
        receiver = _receiver()
        receiver._client = client

        # Should not raise
        await receiver.disconnect()

        assert receiver._client is None

    @pytest.mark.asyncio
    async def test_disconnect_noop_when_not_connected(self) -> None:
        receiver = _receiver()
        receiver._client = None

        # Should not raise
        await receiver.disconnect()
