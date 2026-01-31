"""Tests for NornWeave client initialization."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from nornweave_client import AsyncNornWeave, NornWeave


class TestNornWeaveClient:
    """Test synchronous NornWeave client."""

    def test_client_initialization(self) -> None:
        """Test client initializes with default values."""
        with patch("httpx.Client"):
            client = NornWeave(base_url="http://localhost:8000")
            assert client.base_url == "http://localhost:8000"

    def test_client_custom_timeout(self) -> None:
        """Test client accepts custom timeout."""
        with patch("httpx.Client"):
            client = NornWeave(base_url="http://localhost:8000", timeout=30.0)
            assert client._base_client.timeout == 30.0

    def test_client_custom_max_retries(self) -> None:
        """Test client accepts custom max retries."""
        with patch("httpx.Client"):
            client = NornWeave(base_url="http://localhost:8000", max_retries=5)
            assert client._base_client.max_retries == 5

    def test_client_custom_httpx_client(self) -> None:
        """Test client accepts custom httpx client."""
        custom_client = MagicMock(spec=httpx.Client)
        client = NornWeave(base_url="http://localhost:8000", httpx_client=custom_client)
        assert client._base_client._client is custom_client
        assert not client._base_client._owns_client

    def test_client_has_resources(self) -> None:
        """Test client has all resource attributes."""
        with patch("httpx.Client"):
            client = NornWeave(base_url="http://localhost:8000")
            assert hasattr(client, "inboxes")
            assert hasattr(client, "messages")
            assert hasattr(client, "threads")
            assert hasattr(client, "search")

    def test_client_context_manager(self) -> None:
        """Test client works as context manager."""
        mock_httpx = MagicMock(spec=httpx.Client)
        with patch("httpx.Client", return_value=mock_httpx):
            with NornWeave(base_url="http://localhost:8000") as client:
                assert client is not None
            mock_httpx.close.assert_called_once()

    def test_client_health_check(self, health_response: dict[str, Any]) -> None:
        """Test health check endpoint."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = health_response

        mock_httpx = MagicMock(spec=httpx.Client)
        mock_httpx.request.return_value = mock_response

        with patch("httpx.Client", return_value=mock_httpx):
            client = NornWeave(base_url="http://localhost:8000")
            result = client.health()
            assert result.status == "ok"

    def test_client_strips_trailing_slash(self) -> None:
        """Test client strips trailing slash from base URL."""
        with patch("httpx.Client"):
            client = NornWeave(base_url="http://localhost:8000/")
            assert client.base_url == "http://localhost:8000"


class TestAsyncNornWeaveClient:
    """Test asynchronous NornWeave client."""

    def test_async_client_initialization(self) -> None:
        """Test async client initializes with default values."""
        with patch("httpx.AsyncClient"):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            assert client.base_url == "http://localhost:8000"

    def test_async_client_custom_timeout(self) -> None:
        """Test async client accepts custom timeout."""
        with patch("httpx.AsyncClient"):
            client = AsyncNornWeave(base_url="http://localhost:8000", timeout=30.0)
            assert client._base_client.timeout == 30.0

    def test_async_client_custom_httpx_client(self) -> None:
        """Test async client accepts custom httpx async client."""
        custom_client = MagicMock(spec=httpx.AsyncClient)
        client = AsyncNornWeave(base_url="http://localhost:8000", httpx_client=custom_client)
        assert client._base_client._client is custom_client
        assert not client._base_client._owns_client

    def test_async_client_has_resources(self) -> None:
        """Test async client has all resource attributes."""
        with patch("httpx.AsyncClient"):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            assert hasattr(client, "inboxes")
            assert hasattr(client, "messages")
            assert hasattr(client, "threads")
            assert hasattr(client, "search")

    @pytest.mark.asyncio
    async def test_async_client_context_manager(self) -> None:
        """Test async client works as async context manager."""
        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        with patch("httpx.AsyncClient", return_value=mock_httpx):
            async with AsyncNornWeave(base_url="http://localhost:8000") as client:
                assert client is not None
            mock_httpx.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_client_health_check(self, health_response: dict[str, Any]) -> None:
        """Test async health check endpoint."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = health_response

        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_httpx.request = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx):
            client = AsyncNornWeave(base_url="http://localhost:8000")
            result = await client.health()
            assert result.status == "ok"
