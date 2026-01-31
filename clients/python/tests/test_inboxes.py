"""Tests for inbox resource."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nornweave_client import NornWeave
from nornweave_client._types import Inbox


class TestInboxesResource:
    """Test synchronous inbox operations."""

    def test_create_inbox(self, sample_inbox: dict[str, Any]) -> None:
        """Test creating an inbox."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_inbox

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            inbox = client.inboxes.create(name="Support", email_username="support")

            assert isinstance(inbox, Inbox)
            assert inbox.id == "inbox-123"
            assert inbox.name == "Support"
            assert inbox.email_address == "support@example.nornweave.io"

            # Verify request was made correctly
            mock_httpx.request.assert_called_once()
            call_args = mock_httpx.request.call_args
            assert call_args[0][0] == "POST"
            assert "/v1/inboxes" in call_args[0][1]

    def test_get_inbox(self, sample_inbox: dict[str, Any]) -> None:
        """Test getting an inbox by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_inbox

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            inbox = client.inboxes.get("inbox-123")

            assert isinstance(inbox, Inbox)
            assert inbox.id == "inbox-123"

    def test_list_inboxes(self, sample_inbox_list: dict[str, Any]) -> None:
        """Test listing inboxes with pagination."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_inbox_list

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.inboxes.list()

            # Test iteration
            inboxes = list(pager)
            assert len(inboxes) == 1
            assert inboxes[0].id == "inbox-123"

    def test_delete_inbox(self) -> None:
        """Test deleting an inbox."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            # Should not raise
            client.inboxes.delete("inbox-123")

            mock_httpx.request.assert_called_once()
            call_args = mock_httpx.request.call_args
            assert call_args[0][0] == "DELETE"

    def test_create_inbox_with_raw_response(self, sample_inbox: dict[str, Any]) -> None:
        """Test creating inbox with raw response access."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_inbox
        mock_response.headers = httpx.Headers({"content-type": "application/json"})

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            raw_response = client.inboxes.with_raw_response.create(
                name="Support", email_username="support"
            )

            assert raw_response.status_code == 201
            assert raw_response.data.id == "inbox-123"
            assert "content-type" in raw_response.headers

    def test_list_inboxes_with_pagination_params(
        self, sample_inbox_list: dict[str, Any]
    ) -> None:
        """Test listing inboxes with custom pagination parameters."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_inbox_list

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            pager = client.inboxes.list(limit=10, offset=5)

            # Access items to trigger fetch
            _ = pager.items

            # Verify pagination params were passed
            call_args = mock_httpx.request.call_args
            assert call_args.kwargs["params"]["limit"] == 10
            assert call_args.kwargs["params"]["offset"] == 5


class TestAsyncInboxesResource:
    """Test asynchronous inbox operations."""

    @pytest.mark.asyncio
    async def test_async_create_inbox(self, sample_inbox: dict[str, Any]) -> None:
        """Test async inbox creation."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = sample_inbox

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            inbox = await client.inboxes.create(name="Support", email_username="support")

            assert isinstance(inbox, Inbox)
            assert inbox.id == "inbox-123"

    @pytest.mark.asyncio
    async def test_async_list_inboxes(self, sample_inbox_list: dict[str, Any]) -> None:
        """Test async listing inboxes."""
        from nornweave_client import AsyncNornWeave

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = sample_inbox_list

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            pager = client.inboxes.list()

            # Test async iteration
            inboxes = await pager.to_list()
            assert len(inboxes) == 1
            assert inboxes[0].id == "inbox-123"
