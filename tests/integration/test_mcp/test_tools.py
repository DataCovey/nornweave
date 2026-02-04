"""Integration tests for MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest

from nornweave.muninn.tools import (
    create_inbox,
    get_attachment_content,
    list_attachments,
    search_email,
    send_email,
    send_email_with_attachments,
)

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

    async def list_attachments(
        self,
        message_id: str | None = None,
        thread_id: str | None = None,
        inbox_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List attachments for a message, thread, or inbox."""
        params: dict[str, Any] = {"limit": limit}
        if message_id:
            params["message_id"] = message_id
        if thread_id:
            params["thread_id"] = thread_id
        if inbox_id:
            params["inbox_id"] = inbox_id

        response = self._client.get("/v1/attachments", params=params)
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", "/v1/attachments"),
                response=httpx.Response(404),
            )
        if response.status_code == 400:
            raise ValueError(response.json().get("detail", "Bad request"))
        response.raise_for_status()
        return response.json()

    async def get_attachment(self, attachment_id: str) -> dict[str, Any]:
        """Get attachment metadata."""
        response = self._client.get(f"/v1/attachments/{attachment_id}")
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", f"/v1/attachments/{attachment_id}"),
                response=httpx.Response(404),
            )
        response.raise_for_status()
        return response.json()

    async def get_attachment_content(
        self,
        attachment_id: str,
        response_format: str = "base64",
    ) -> dict[str, Any] | bytes:
        """Get attachment content."""
        params: dict[str, Any] = {"format": response_format}

        response = self._client.get(
            f"/v1/attachments/{attachment_id}/content",
            params=params,
        )
        if response.status_code == 404:
            raise httpx.HTTPStatusError(
                "Not found",
                request=httpx.Request("GET", f"/v1/attachments/{attachment_id}/content"),
                response=httpx.Response(404),
            )
        if response.status_code in (401, 403):
            raise httpx.HTTPStatusError(
                "Unauthorized",
                request=httpx.Request("GET", f"/v1/attachments/{attachment_id}/content"),
                response=httpx.Response(response.status_code),
            )
        response.raise_for_status()
        if response_format == "base64":
            return response.json()
        return response.content

    async def send_message_with_attachments(
        self,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[dict[str, str]],
        reply_to_thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message with attachments."""
        # Transform attachments: content -> content_base64 (matching the API model)
        api_attachments = [
            {
                "filename": att["filename"],
                "content_type": att["content_type"],
                "content_base64": att["content"],
            }
            for att in attachments
        ]

        payload: dict[str, Any] = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
            "attachments": api_attachments,
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
        if response.status_code == 400:
            raise ValueError(response.json().get("detail", "Bad request"))
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


class TestListAttachmentsTool:
    """Tests for list_attachments tool."""

    async def test_list_attachments_by_message(self, client: MockClient) -> None:
        """Test listing attachments for a message."""
        result = await list_attachments(client, message_id="msg_with_attachments")

        assert "attachments" in result
        assert isinstance(result["attachments"], list)

    async def test_list_attachments_by_thread(self, client: MockClient) -> None:
        """Test listing attachments for a thread."""
        result = await list_attachments(client, thread_id="th_test")

        assert "attachments" in result
        assert isinstance(result["attachments"], list)

    async def test_list_attachments_by_inbox(self, client: MockClient) -> None:
        """Test listing attachments for an inbox."""
        result = await list_attachments(client, inbox_id="ibx_test")

        assert "attachments" in result
        assert isinstance(result["attachments"], list)

    async def test_list_attachments_requires_filter(self, client: MockClient) -> None:
        """Test that list_attachments requires a filter parameter."""
        with pytest.raises(Exception, match="filter required"):
            await list_attachments(client)

    async def test_list_attachments_invalid_message(self, client: MockClient) -> None:
        """Test listing attachments for non-existent message fails."""
        with pytest.raises(Exception, match="not found"):
            await list_attachments(client, message_id="msg_nonexistent")


class TestGetAttachmentContentTool:
    """Tests for get_attachment_content tool."""

    async def test_get_attachment_content_base64(self, client: MockClient) -> None:
        """Test getting attachment content as base64.

        Note: The MCP tool always returns base64 (no format parameter).
        """
        result = await get_attachment_content(
            client,
            attachment_id="att_test",
        )

        assert "content" in result
        assert "content_type" in result
        assert "filename" in result
        # Content should be base64 encoded
        assert isinstance(result["content"], str)

    async def test_get_attachment_content_not_found(self, client: MockClient) -> None:
        """Test getting content for non-existent attachment fails."""
        with pytest.raises(Exception, match="not found"):
            await get_attachment_content(client, attachment_id="att_nonexistent")


class TestSendEmailWithAttachmentsTool:
    """Tests for send_email_with_attachments tool."""

    async def test_send_email_with_single_attachment(self, client: MockClient) -> None:
        """Test sending email with a single attachment."""
        import base64

        # Create a simple text file attachment
        content = base64.b64encode(b"Hello, World!").decode("ascii")

        result = await send_email_with_attachments(
            client,
            inbox_id="ibx_test",
            recipient="user@example.com",
            subject="Email with attachment",
            body="Please see attached file.",
            attachments=[
                {
                    "filename": "hello.txt",
                    "content_type": "text/plain",
                    "content": content,
                }
            ],
        )

        assert "message_id" in result
        assert "thread_id" in result
        assert "status" in result

    async def test_send_email_with_multiple_attachments(self, client: MockClient) -> None:
        """Test sending email with multiple attachments."""
        import base64

        content1 = base64.b64encode(b"File 1 content").decode("ascii")
        content2 = base64.b64encode(b"File 2 content").decode("ascii")

        result = await send_email_with_attachments(
            client,
            inbox_id="ibx_test",
            recipient="user@example.com",
            subject="Email with attachments",
            body="Please see attached files.",
            attachments=[
                {
                    "filename": "file1.txt",
                    "content_type": "text/plain",
                    "content": content1,
                },
                {
                    "filename": "file2.txt",
                    "content_type": "text/plain",
                    "content": content2,
                },
            ],
        )

        assert "message_id" in result
        assert "status" in result

    async def test_send_email_with_invalid_base64(self, client: MockClient) -> None:
        """Test sending email with invalid base64 content fails."""
        with pytest.raises(ValueError, match="base64"):
            await send_email_with_attachments(
                client,
                inbox_id="ibx_test",
                recipient="user@example.com",
                subject="Invalid attachment",
                body="This should fail.",
                attachments=[
                    {
                        "filename": "invalid.txt",
                        "content_type": "text/plain",
                        "content": "not-valid-base64!!!",
                    }
                ],
            )
