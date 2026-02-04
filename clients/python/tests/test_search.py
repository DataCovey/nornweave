"""Tests for search resource."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nornweave_client import NornWeave
from nornweave_client._types import SearchResponse, SearchResultItem


class TestSearchResource:
    """Test synchronous search operations."""

    def test_search_query(self, sample_search_response: dict[str, Any]) -> None:
        """Test searching messages."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.search.query(query="invoice", inbox_id="inbox-123")

            results = list(pager)
            assert len(results) == 1
            assert isinstance(results[0], SearchResultItem)
            assert "invoice" in results[0].content_clean

            # Verify request body
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["json"]["query"] == "invoice"
            assert call_args.kwargs["json"]["inbox_id"] == "inbox-123"

    def test_search_query_raw(self, sample_search_response: dict[str, Any]) -> None:
        """Test searching with full response object."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            result = client.search.query_raw(query="invoice", inbox_id="inbox-123")

            assert isinstance(result, SearchResponse)
            assert result.query == "invoice"
            assert result.count == 1
            assert len(result.items) == 1

    def test_search_with_pagination(self, sample_search_response: dict[str, Any]) -> None:
        """Test search with custom pagination."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.search.query(query="invoice", inbox_id="inbox-123", limit=25, offset=10)

            # Access items to trigger fetch
            _ = pager.items

            # Verify pagination params
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["json"]["limit"] == 25
            assert call_args.kwargs["json"]["offset"] == 10

    def test_search_with_raw_response(self, sample_search_response: dict[str, Any]) -> None:
        """Test search with raw response access."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response
        mock_response.headers = httpx.Headers({"content-type": "application/json"})

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            raw_response = client.search.with_raw_response.query_raw(
                query="invoice", inbox_id="inbox-123"
            )

            assert raw_response.status_code == 200
            assert raw_response.data.query == "invoice"


class TestAsyncSearchResource:
    """Test asynchronous search operations."""

    @pytest.mark.asyncio
    async def test_async_search_query(self, sample_search_response: dict[str, Any]) -> None:
        """Test async search."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            pager = client.search.query(query="invoice", inbox_id="inbox-123")

            results = await pager.to_list()
            assert len(results) == 1
            assert "invoice" in results[0].content_clean

    @pytest.mark.asyncio
    async def test_async_search_query_raw(self, sample_search_response: dict[str, Any]) -> None:
        """Test async search with full response."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_response

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            result = await client.search.query_raw(query="invoice", inbox_id="inbox-123")

            assert isinstance(result, SearchResponse)
            assert result.query == "invoice"
