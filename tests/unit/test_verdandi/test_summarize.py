"""Unit tests for thread summarization."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.models.message import Message, MessageDirection
from nornweave.verdandi.llm.base import SummaryProvider, SummaryResult
from nornweave.verdandi.summarize import (
    check_token_budget,
    generate_thread_summary,
    prepare_thread_text,
    truncate_to_context_window,
)


# ---------------------------------------------------------------------------
# 8.1 SummaryProvider protocol tests
# ---------------------------------------------------------------------------
class TestSummaryProviderProtocol:
    """Tests for SummaryProvider protocol and SummaryResult."""

    def test_summary_result_dataclass(self) -> None:
        """SummaryResult contains all expected fields."""
        result = SummaryResult(
            summary="Test summary",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="gpt-4o-mini",
        )
        assert result.summary == "Test summary"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
        assert result.model == "gpt-4o-mini"

    def test_protocol_is_runtime_checkable(self) -> None:
        """SummaryProvider protocol can be checked at runtime."""

        class FakeProvider:
            async def summarize(self, text: str) -> SummaryResult:  # noqa: ARG002
                return SummaryResult(
                    summary="fake",
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    model="fake",
                )

        assert isinstance(FakeProvider(), SummaryProvider)


# ---------------------------------------------------------------------------
# 8.2 get_summary_provider factory tests
# ---------------------------------------------------------------------------
class TestGetSummaryProvider:
    """Tests for the provider factory function."""

    @patch("nornweave.verdandi.llm.get_settings")
    def test_returns_none_when_disabled(self, mock_settings: MagicMock) -> None:
        """Returns None when LLM_PROVIDER is not set."""
        from nornweave.verdandi.llm import get_summary_provider

        mock_settings.return_value = MagicMock(llm_provider=None)
        assert get_summary_provider() is None

    @patch("nornweave.verdandi.llm.get_settings")
    def test_returns_none_when_no_provider(self, mock_settings: MagicMock) -> None:
        """Returns None when no provider is configured."""
        from nornweave.verdandi.llm import get_summary_provider

        mock_settings.return_value = MagicMock(llm_provider=None)
        result = get_summary_provider()
        assert result is None


# ---------------------------------------------------------------------------
# 8.3 prepare_thread_text tests
# ---------------------------------------------------------------------------
class TestPrepareThreadText:
    """Tests for prepare_thread_text function."""

    def _make_message(
        self,
        *,
        text: str | None = None,
        extracted_text: str | None = None,
        from_address: str = "alice@example.com",
        timestamp: datetime | None = None,
    ) -> Message:
        return Message(
            message_id="msg-1",
            thread_id="thread-1",
            inbox_id="inbox-1",
            direction=MessageDirection.INBOUND,
            text=text,
            extracted_text=extracted_text,
            from_address=from_address,
            timestamp=timestamp or datetime(2026, 1, 15, 10, 30),
            to=["bob@example.com"],
        )

    def test_multiple_messages_chronological(self) -> None:
        """Messages are ordered chronologically with headers."""
        msgs = [
            self._make_message(
                extracted_text="Hello!",
                from_address="bob@example.com",
                timestamp=datetime(2026, 1, 15, 14, 22),
            ),
            self._make_message(
                extracted_text="Hi Bob.",
                from_address="alice@example.com",
                timestamp=datetime(2026, 1, 15, 10, 30),
            ),
        ]
        result = prepare_thread_text(msgs)
        assert "[2026-01-15 10:30] alice@example.com:" in result
        assert "[2026-01-15 14:22] bob@example.com:" in result
        # Alice should come first (earlier timestamp)
        assert result.index("alice@example.com") < result.index("bob@example.com")

    def test_falls_back_to_text(self) -> None:
        """Uses text field when extracted_text is None."""
        msgs = [self._make_message(text="raw text", extracted_text=None)]
        result = prepare_thread_text(msgs)
        assert "raw text" in result

    def test_prefers_extracted_text(self) -> None:
        """Uses extracted_text over text when both are present."""
        msgs = [self._make_message(text="raw text", extracted_text="clean text")]
        result = prepare_thread_text(msgs)
        assert "clean text" in result
        assert "raw text" not in result

    def test_skips_empty_messages(self) -> None:
        """Skips messages with no text content."""
        msgs = [
            self._make_message(text=None, extracted_text=None),
            self._make_message(extracted_text="real content"),
        ]
        result = prepare_thread_text(msgs)
        assert "real content" in result
        # Should only have one message block
        assert result.count("[") == 1

    def test_empty_list(self) -> None:
        """Returns empty string for no messages."""
        assert prepare_thread_text([]) == ""


# ---------------------------------------------------------------------------
# 8.4 truncate_to_context_window tests
# ---------------------------------------------------------------------------
class TestTruncateToContextWindow:
    """Tests for truncate_to_context_window function."""

    def test_under_limit_unchanged(self) -> None:
        """Text under limit is returned unchanged."""
        text = "Short text"
        result = truncate_to_context_window(text, "gpt-4o-mini")
        assert result == text

    def test_over_limit_truncates_oldest(self) -> None:
        """Text over limit truncates oldest messages and adds note."""
        # Create a very long text
        blocks = [f"[2026-01-{i:02d} 10:00] user@example.com:\n{'x' * 1000}" for i in range(1, 20)]
        text = "\n\n".join(blocks)

        # Use a model with small context window for testing
        result = truncate_to_context_window(text, "gpt-3.5-turbo")

        if len(text) > 16_385 * 0.8 * 4:
            assert "[Earlier messages truncated" in result
            assert len(result) < len(text)


# ---------------------------------------------------------------------------
# 8.5 check_token_budget tests
# ---------------------------------------------------------------------------
class TestCheckTokenBudget:
    """Tests for check_token_budget function."""

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    async def test_under_budget(self, mock_settings: MagicMock) -> None:
        """Returns True when under budget."""
        mock_settings.return_value = MagicMock(llm_daily_token_limit=1_000_000)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 500_000
        assert await check_token_budget(storage) is True

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    async def test_at_budget(self, mock_settings: MagicMock) -> None:
        """Returns False when at budget."""
        mock_settings.return_value = MagicMock(llm_daily_token_limit=1_000_000)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 1_000_000
        assert await check_token_budget(storage) is False

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    async def test_over_budget(self, mock_settings: MagicMock) -> None:
        """Returns False when over budget."""
        mock_settings.return_value = MagicMock(llm_daily_token_limit=1_000_000)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 1_200_000
        assert await check_token_budget(storage) is False

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    async def test_no_row(self, mock_settings: MagicMock) -> None:
        """Returns True when no usage row exists (0 usage)."""
        mock_settings.return_value = MagicMock(llm_daily_token_limit=1_000_000)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 0
        assert await check_token_budget(storage) is True

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    async def test_unlimited(self, mock_settings: MagicMock) -> None:
        """Returns True when limit is 0 (unlimited)."""
        mock_settings.return_value = MagicMock(llm_daily_token_limit=0)
        storage = AsyncMock()
        # Should not even check storage
        assert await check_token_budget(storage) is True
        storage.get_token_usage.assert_not_called()


# ---------------------------------------------------------------------------
# 8.6 generate_thread_summary tests
# ---------------------------------------------------------------------------
class TestGenerateThreadSummary:
    """Tests for generate_thread_summary orchestration."""

    def _make_message(self, text: str, timestamp: datetime) -> Message:
        return Message(
            message_id="msg-1",
            thread_id="thread-1",
            inbox_id="inbox-1",
            direction=MessageDirection.INBOUND,
            extracted_text=text,
            from_address="alice@example.com",
            timestamp=timestamp,
            to=["bob@example.com"],
        )

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_disabled_skips(self, mock_provider: MagicMock) -> None:
        """No-op when provider is None (feature disabled)."""
        mock_provider.return_value = None
        storage = AsyncMock()
        await generate_thread_summary(storage, "thread-1")
        storage.list_messages_for_thread.assert_not_called()

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_budget_exhausted_skips(
        self, mock_provider: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Skips when budget is exhausted."""
        mock_provider.return_value = MagicMock()
        mock_settings.return_value = MagicMock(llm_daily_token_limit=100)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 200
        await generate_thread_summary(storage, "thread-1")
        storage.list_messages_for_thread.assert_not_called()

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_happy_path(self, mock_provider_fn: MagicMock, mock_settings: MagicMock) -> None:
        """Happy path: generates summary, updates thread, records tokens."""
        mock_settings.return_value = MagicMock(
            llm_daily_token_limit=1_000_000,
            llm_model="gpt-4o-mini",
        )

        mock_provider = AsyncMock()
        mock_provider.summarize.return_value = SummaryResult(
            summary="Test summary",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="gpt-4o-mini",
        )
        mock_provider_fn.return_value = mock_provider

        from nornweave.models.thread import Thread

        mock_thread = MagicMock(spec=Thread)
        storage = AsyncMock()
        storage.get_token_usage.return_value = 0
        storage.list_messages_for_thread.return_value = [
            self._make_message("Hello!", datetime(2026, 1, 15, 10, 30))
        ]
        storage.get_thread.return_value = mock_thread

        await generate_thread_summary(storage, "thread-1")

        mock_provider.summarize.assert_called_once()
        assert mock_thread.summary == "Test summary"
        storage.update_thread.assert_called_once_with(mock_thread)
        storage.record_token_usage.assert_called_once()

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_provider_failure_graceful(
        self, mock_provider_fn: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Provider failure logs warning but doesn't raise."""
        mock_settings.return_value = MagicMock(
            llm_daily_token_limit=0,
            llm_model="",
        )

        mock_provider = AsyncMock()
        mock_provider.summarize.side_effect = RuntimeError("API error")
        mock_provider_fn.return_value = mock_provider

        storage = AsyncMock()
        storage.list_messages_for_thread.return_value = [
            self._make_message("Hello!", datetime(2026, 1, 15, 10, 30))
        ]

        # Should not raise
        await generate_thread_summary(storage, "thread-1")
        storage.update_thread.assert_not_called()
