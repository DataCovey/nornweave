"""Integration tests for MCP resources."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest

from nornweave.huginn.resources import get_recent_threads, get_thread_content

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class MockClient:
    """A mock NornWeave client that uses TestClient for ASGI transport."""

    def __init__(self, test_client: TestClient) -> None:
        self._client = test_client

    async def list_threads(self, inbox_id: str, limit: int = 10) -> dict[str, Any]:
        """List threads for an inbox."""
        response = self._client.get(f"/v1/threads?inbox_id={inbox_id}&limit={limit}")
        response.raise_for_status()
        return response.json()

    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Get a thread with messages."""
        response = self._client.get(f"/v1/threads/{thread_id}")
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", f"/v1/threads/{thread_id}"),
                response=httpx.Response(404),
            )
        response.raise_for_status()
        return response.json()


@pytest.fixture
def client(test_client: TestClient) -> MockClient:
    """Create a mock client for testing."""
    return MockClient(test_client)


class TestRecentThreadsResource:
    """Tests for email://inbox/{inbox_id}/recent resource."""

    async def test_get_recent_threads_valid_inbox(self, client: MockClient) -> None:
        """Test fetching recent threads for a valid inbox."""
        result = await get_recent_threads(client, "ibx_test")

        # Should return JSON array
        threads = json.loads(result)
        assert isinstance(threads, list)
        assert len(threads) >= 1

        # Each thread should have required fields
        thread = threads[0]
        assert "id" in thread
        assert "subject" in thread
        assert "last_message_at" in thread
        assert "message_count" in thread
        assert "participants" in thread

    async def test_get_recent_threads_invalid_inbox(self, client: MockClient) -> None:
        """Test fetching recent threads for non-existent inbox."""
        with pytest.raises(Exception, match="not found"):
            await get_recent_threads(client, "ibx_nonexistent")


class TestThreadContentResource:
    """Tests for email://thread/{thread_id} resource."""

    async def test_get_thread_content_valid_thread(self, client: MockClient) -> None:
        """Test fetching thread content for a valid thread."""
        result = await get_thread_content(client, "th_test")

        # Should return Markdown content
        assert isinstance(result, str)
        assert "## Thread:" in result
        assert "**From:**" in result
        assert "**Date:**" in result

    async def test_get_thread_content_invalid_thread(self, client: MockClient) -> None:
        """Test fetching thread content for non-existent thread."""
        with pytest.raises(Exception, match="not found"):
            await get_thread_content(client, "th_nonexistent")

    async def test_thread_content_markdown_format(self, client: MockClient) -> None:
        """Test that thread content is properly formatted as Markdown."""
        result = await get_thread_content(client, "th_test")

        # Should have thread subject as heading
        assert "Test Thread" in result

        # Should have message separators
        lines = result.split("\n")
        assert any("---" in line for line in lines)
