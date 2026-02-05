"""Integration tests for LLM thread summarization."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nornweave.models.message import Message, MessageDirection
from nornweave.verdandi.llm.base import SummaryResult
from nornweave.verdandi.summarize import generate_thread_summary


@pytest.mark.integration
class TestSummarizationIngestion:
    """Integration tests for summarization during ingestion flow."""

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_ingest_populates_thread_summary(
        self, mock_provider_fn: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Ingestion with LLM enabled populates thread summary."""
        mock_settings.return_value = MagicMock(
            llm_daily_token_limit=1_000_000,
            llm_model="gpt-4o-mini",
        )

        mock_provider = AsyncMock()
        mock_provider.summarize.return_value = SummaryResult(
            summary="Alice asked about contract terms. Bob reviewed section 3.",
            input_tokens=200,
            output_tokens=30,
            total_tokens=230,
            model="gpt-4o-mini",
        )
        mock_provider_fn.return_value = mock_provider

        from nornweave.models.thread import Thread

        mock_thread = MagicMock(spec=Thread)
        mock_thread.summary = None

        storage = AsyncMock()
        storage.get_token_usage.return_value = 0
        storage.list_messages_for_thread.return_value = [
            Message(
                message_id="msg-1",
                thread_id="thread-1",
                inbox_id="inbox-1",
                direction=MessageDirection.INBOUND,
                extracted_text="Can we discuss contract terms?",
                from_address="alice@example.com",
                timestamp=datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
                to=["bob@example.com"],
            ),
            Message(
                message_id="msg-2",
                thread_id="thread-1",
                inbox_id="inbox-1",
                direction=MessageDirection.INBOUND,
                extracted_text="Sure, I've reviewed section 3.",
                from_address="bob@example.com",
                timestamp=datetime(2026, 1, 15, 14, 22, tzinfo=UTC),
                to=["alice@example.com"],
            ),
        ]
        storage.get_thread.return_value = mock_thread

        await generate_thread_summary(storage, "thread-1")

        # Verify the summary was set on the thread
        assert mock_thread.summary == "Alice asked about contract terms. Bob reviewed section 3."
        storage.update_thread.assert_called_once_with(mock_thread)

        # Verify the text sent to provider had message headers
        call_args = mock_provider.summarize.call_args[0][0]
        assert "[2026-01-15 10:30] alice@example.com:" in call_args
        assert "[2026-01-15 14:22] bob@example.com:" in call_args


@pytest.mark.integration
class TestTokenUsageTracking:
    """Integration tests for token usage tracking and budget enforcement."""

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_token_counter_increments(
        self, mock_provider_fn: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Token counter increments after each summarization."""
        mock_settings.return_value = MagicMock(
            llm_daily_token_limit=1_000_000,
            llm_model="gpt-4o-mini",
        )

        mock_provider = AsyncMock()
        mock_provider.summarize.return_value = SummaryResult(
            summary="Summary 1",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="gpt-4o-mini",
        )
        mock_provider_fn.return_value = mock_provider

        from nornweave.models.thread import Thread

        storage = AsyncMock()
        storage.get_token_usage.return_value = 0
        storage.list_messages_for_thread.return_value = [
            Message(
                message_id="msg-1",
                thread_id="thread-1",
                inbox_id="inbox-1",
                direction=MessageDirection.INBOUND,
                extracted_text="Hello!",
                from_address="alice@example.com",
                timestamp=datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
                to=["bob@example.com"],
            ),
        ]
        storage.get_thread.return_value = MagicMock(spec=Thread)

        # First call
        await generate_thread_summary(storage, "thread-1")
        storage.record_token_usage.assert_called_once()
        call_args = storage.record_token_usage.call_args
        assert call_args[0][1] == 150  # total_tokens

    @pytest.mark.asyncio
    @patch("nornweave.verdandi.summarize.get_settings")
    @patch("nornweave.verdandi.summarize.get_summary_provider")
    async def test_budget_gate_stops_summarization(
        self, mock_provider_fn: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Summarization is skipped when budget is exhausted."""
        mock_settings.return_value = MagicMock(
            llm_daily_token_limit=100,
            llm_model="gpt-4o-mini",
        )

        mock_provider = AsyncMock()
        mock_provider_fn.return_value = mock_provider

        storage = AsyncMock()
        storage.get_token_usage.return_value = 200  # Over budget

        await generate_thread_summary(storage, "thread-1")

        # Provider should never be called
        mock_provider.summarize.assert_not_called()
        storage.update_thread.assert_not_called()
