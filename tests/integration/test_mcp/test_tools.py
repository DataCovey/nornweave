"""Integration tests for MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest

from nornweave.muninn.tools import create_inbox, search_email, send_email

if TYPE_CHECKING:
    from starlette.testclient import TestClient


class MockClient:
    """A mock NornWeave client that uses TestClient for ASGI transport."""

    def __init__(self, test_client: TestClient) -> None:
        self._client = test_client

    async def create_inbox(self, name: str, email_username: str) -> dict[str, Any]:
        """Create an inbox."""
        response = self._client.post(
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
        )
        if response.status_code == 409:
            raise httpx.HTTPStatusError(
                "Conflict",
                request=httpx.Request("POST", "/v1/inboxes"),
                response=httpx.Response(409),
            )
        response.raise_for_status()
        return response.json()

    async def send_message(
        self,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message."""
        payload: dict[str, Any] = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = self._client.post("/v1/messages", json=payload)
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("POST", "/v1/messages"),
                response=httpx.Response(404),
            )
        response.raise_for_status()
        return response.json()

    async def search_messages(
        self,
        query: str,
        inbox_id: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search messages."""
        response = self._client.post(
            "/v1/search",
            json={"query": query, "inbox_id": inbox_id, "limit": limit},
        )
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("POST", "/v1/search"),
                response=httpx.Response(404),
            )
        response.raise_for_status()
        return response.json()


@pytest.fixture
def client(test_client: TestClient) -> MockClient:
    """Create a mock client for testing."""
    return MockClient(test_client)


class TestCreateInboxTool:
    """Tests for create_inbox tool."""

    async def test_create_inbox_success(self, client: MockClient) -> None:
        """Test creating a new inbox."""
        result = await create_inbox(client, name="Support Bot", username="support")

        assert "id" in result
        assert "email_address" in result
        assert "name" in result
        assert result["name"] == "Support Bot"
        assert "support@" in result["email_address"]

    async def test_create_inbox_duplicate_username(self, client: MockClient) -> None:
        """Test creating inbox with duplicate username fails."""
        # Create first inbox
        await create_inbox(client, name="First", username="duplicate")

        # Try to create second with same username
        with pytest.raises(Exception, match="already exists"):
            await create_inbox(client, name="Second", username="duplicate")


class TestSendEmailTool:
    """Tests for send_email tool."""

    async def test_send_email_new_thread(self, client: MockClient) -> None:
        """Test sending email that creates a new thread."""
        result = await send_email(
            client,
            inbox_id="ibx_test",
            recipient="user@example.com",
            subject="Hello",
            body="This is a test email.",
        )

        assert "message_id" in result
        assert "thread_id" in result
        assert "status" in result
        assert result["status"] == "sent"

    async def test_send_email_reply(self, client: MockClient) -> None:
        """Test sending email as reply to existing thread."""
        result = await send_email(
            client,
            inbox_id="ibx_test",
            recipient="user@example.com",
            subject="Re: Test Thread",
            body="This is a reply.",
            thread_id="th_test",
        )

        assert "message_id" in result
        assert result["thread_id"] == "th_test"

    async def test_send_email_invalid_inbox(self, client: MockClient) -> None:
        """Test sending email from non-existent inbox fails."""
        with pytest.raises(Exception, match="not found"):
            await send_email(
                client,
                inbox_id="ibx_nonexistent",
                recipient="user@example.com",
                subject="Test",
                body="Test",
            )


class TestSearchEmailTool:
    """Tests for search_email tool."""

    async def test_search_email_with_matches(self, client: MockClient) -> None:
        """Test searching for emails with matching content."""
        result = await search_email(
            client,
            query="test",
            inbox_id="ibx_test",
            limit=10,
        )

        assert "query" in result
        assert "count" in result
        assert "messages" in result
        assert result["query"] == "test"
        assert isinstance(result["messages"], list)

    async def test_search_email_no_matches(self, client: MockClient) -> None:
        """Test searching for emails with no matches."""
        result = await search_email(
            client,
            query="nonexistentquery12345",
            inbox_id="ibx_test",
            limit=10,
        )

        assert result["count"] == 0
        assert result["messages"] == []

    async def test_search_email_invalid_inbox(self, client: MockClient) -> None:
        """Test searching in non-existent inbox fails."""
        with pytest.raises(Exception, match="not found"):
            await search_email(
                client,
                query="test",
                inbox_id="ibx_nonexistent",
            )

    async def test_search_email_respects_limit(self, client: MockClient) -> None:
        """Test that search respects the limit parameter."""
        result = await search_email(
            client,
            query="message",
            inbox_id="ibx_test",
            limit=1,
        )

        assert len(result["messages"]) <= 1
