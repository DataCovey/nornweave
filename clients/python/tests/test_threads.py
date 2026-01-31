"""Tests for threads resource."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nornweave_client import NornWeave
from nornweave_client._types import ThreadDetail, ThreadSummary


class TestThreadsResource:
    """Test synchronous thread operations."""

    def test_list_threads(self, sample_thread_list: dict[str, Any]) -> None:
        """Test listing threads for an inbox."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_list

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.threads.list(inbox_id="inbox-123")

            threads = list(pager)
            assert len(threads) == 1
            assert isinstance(threads[0], ThreadSummary)
            assert threads[0].id == "thread-456"
            assert threads[0].subject == "Test Thread"
            assert threads[0].message_count == 3

            # Verify inbox_id was passed
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["params"]["inbox_id"] == "inbox-123"

    def test_get_thread(self, sample_thread_detail: dict[str, Any]) -> None:
        """Test getting a thread with messages."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_detail

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            thread = client.threads.get("thread-456")

            assert isinstance(thread, ThreadDetail)
            assert thread.id == "thread-456"
            assert thread.subject == "Test Thread"
            assert len(thread.messages) == 2

            # Check message format is LLM-ready
            assert thread.messages[0].role == "user"
            assert thread.messages[0].author == "user@example.com"
            assert thread.messages[1].role == "assistant"

    def test_get_thread_with_pagination(self, sample_thread_detail: dict[str, Any]) -> None:
        """Test getting thread with message pagination."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_detail

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            _ = client.threads.get("thread-456", limit=50, offset=10)

            # Verify pagination params were passed
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["params"]["limit"] == 50
            assert call_args.kwargs["params"]["offset"] == 10

    def test_get_thread_with_raw_response(
        self, sample_thread_detail: dict[str, Any]
    ) -> None:
        """Test getting thread with raw response access."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_detail
        mock_response.headers = httpx.Headers({"content-type": "application/json"})

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            raw_response = client.threads.with_raw_response.get("thread-456")

            assert raw_response.status_code == 200
            assert raw_response.data.id == "thread-456"
            assert len(raw_response.data.messages) == 2


class TestAsyncThreadsResource:
    """Test asynchronous thread operations."""

    @pytest.mark.asyncio
    async def test_async_list_threads(self, sample_thread_list: dict[str, Any]) -> None:
        """Test async thread listing."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_list

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            pager = client.threads.list(inbox_id="inbox-123")

            threads = await pager.to_list()
            assert len(threads) == 1
            assert threads[0].id == "thread-456"

    @pytest.mark.asyncio
    async def test_async_get_thread(self, sample_thread_detail: dict[str, Any]) -> None:
        """Test async getting thread with messages."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_thread_detail

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            thread = await client.threads.get("thread-456")

            assert isinstance(thread, ThreadDetail)
            assert thread.id == "thread-456"
            assert len(thread.messages) == 2
