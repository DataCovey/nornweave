"""HTTP client for NornWeave API.

This module provides an async HTTP client for the MCP server to communicate
with the NornWeave REST API.
"""

from typing import Any, cast

import httpx

from nornweave.huginn.config import get_mcp_settings


class NornWeaveClient:
    """Async HTTP client for NornWeave REST API."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_url: Base URL for the NornWeave API. Defaults to NORNWEAVE_API_URL env var.
            api_key: API key for authentication. Defaults to NORNWEAVE_API_KEY env var.
        """
        settings = get_mcp_settings()
        self.api_url = (api_url or settings.api_url).rstrip("/")
        self.api_key = api_key or settings.api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers: dict[str, str] = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> NornWeaveClient:
        """Enter async context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context."""
        await self.close()

    # -------------------------------------------------------------------------
    # Inbox Operations
    # -------------------------------------------------------------------------

    async def create_inbox(self, name: str, email_username: str) -> dict[str, Any]:
        """Create a new inbox.

        Args:
            name: Display name for the inbox.
            email_username: Local part of the email address.

        Returns:
            Created inbox with id, email_address, name.
        """
        client = await self._get_client()
        response = await client.post(
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def get_inbox(self, inbox_id: str) -> dict[str, Any]:
        """Get an inbox by ID.

        Args:
            inbox_id: The inbox ID.

        Returns:
            Inbox data.
        """
        client = await self._get_client()
        response = await client.get(f"/v1/inboxes/{inbox_id}")
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def list_inboxes(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all inboxes.

        Args:
            limit: Maximum number of inboxes to return.
            offset: Number of inboxes to skip.

        Returns:
            List response with items and count.
        """
        client = await self._get_client()
        response = await client.get(
            "/v1/inboxes",
            params={"limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    # -------------------------------------------------------------------------
    # Thread Operations
    # -------------------------------------------------------------------------

    async def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Get a thread with messages.

        Args:
            thread_id: The thread ID.

        Returns:
            Thread data with messages in LLM-ready format.
        """
        client = await self._get_client()
        response = await client.get(f"/v1/threads/{thread_id}")
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def list_threads(
        self,
        inbox_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List threads for an inbox.

        Args:
            inbox_id: The inbox ID.
            limit: Maximum number of threads to return.
            offset: Number of threads to skip.

        Returns:
            List response with thread summaries.
        """
        client = await self._get_client()
        response = await client.get(
            "/v1/threads",
            params={"inbox_id": inbox_id, "limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    # -------------------------------------------------------------------------
    # Message Operations
    # -------------------------------------------------------------------------

    async def get_message(self, message_id: str) -> dict[str, Any]:
        """Get a message by ID.

        Args:
            message_id: The message ID.

        Returns:
            Message data.
        """
        client = await self._get_client()
        response = await client.get(f"/v1/messages/{message_id}")
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def list_messages(
        self,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List messages for an inbox.

        Args:
            inbox_id: The inbox ID.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip.

        Returns:
            List response with messages.
        """
        client = await self._get_client()
        response = await client.get(
            "/v1/messages",
            params={"inbox_id": inbox_id, "limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def send_message(
        self,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send an outbound message.

        Args:
            inbox_id: The inbox ID to send from.
            to: List of recipient email addresses.
            subject: Email subject.
            body: Markdown body content.
            reply_to_thread_id: Thread ID if this is a reply.

        Returns:
            Send response with message_id, thread_id, status.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = await client.post("/v1/messages", json=payload)
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    # -------------------------------------------------------------------------
    # Search Operations
    # -------------------------------------------------------------------------

    async def search_messages(
        self,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search messages by content.

        Args:
            query: Search query.
            inbox_id: Inbox to search in.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Search response with matching messages.
        """
        client = await self._get_client()
        response = await client.post(
            "/v1/search",
            json={
                "query": query,
                "inbox_id": inbox_id,
                "limit": limit,
                "offset": offset,
            },
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    # -------------------------------------------------------------------------
    # Polling for wait_for_reply
    # -------------------------------------------------------------------------

    async def get_thread_message_count(self, thread_id: str) -> int:
        """Get the current message count for a thread.

        Args:
            thread_id: The thread ID.

        Returns:
            Number of messages in the thread.
        """
        thread = await self.get_thread(thread_id)
        return len(thread.get("messages", []))

    async def get_latest_message(self, thread_id: str) -> dict[str, Any] | None:
        """Get the latest message in a thread.

        Args:
            thread_id: The thread ID.

        Returns:
            The latest message or None if thread is empty.
        """
        thread = await self.get_thread(thread_id)
        messages = thread.get("messages", [])
        if not messages:
            return None
        return cast("dict[str, Any]", messages[-1])

    # -------------------------------------------------------------------------
    # Attachment Operations
    # -------------------------------------------------------------------------

    async def list_attachments(
        self,
        message_id: str | None = None,
        thread_id: str | None = None,
        inbox_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List attachments filtered by message, thread, or inbox.

        Args:
            message_id: Filter by message ID.
            thread_id: Filter by thread ID.
            inbox_id: Filter by inbox ID.
            limit: Maximum number of attachments to return.
            offset: Number of attachments to skip.

        Returns:
            List response with attachment metadata.
        """
        client = await self._get_client()
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if message_id:
            params["message_id"] = message_id
        elif thread_id:
            params["thread_id"] = thread_id
        elif inbox_id:
            params["inbox_id"] = inbox_id

        response = await client.get("/v1/attachments", params=params)
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def get_attachment(self, attachment_id: str) -> dict[str, Any]:
        """Get attachment metadata.

        Args:
            attachment_id: The attachment ID.

        Returns:
            Attachment metadata with download_url.
        """
        client = await self._get_client()
        response = await client.get(f"/v1/attachments/{attachment_id}")
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def get_attachment_content(
        self,
        attachment_id: str,
        response_format: str = "base64",
    ) -> dict[str, Any]:
        """Get attachment content.

        Args:
            attachment_id: The attachment ID.
            response_format: Response format - "binary" or "base64" (default: base64).

        Returns:
            For base64: {"content": "...", "content_type": "...", "filename": "..."}
            For binary: raw bytes (handled by httpx)
        """
        client = await self._get_client()
        response = await client.get(
            f"/v1/attachments/{attachment_id}/content",
            params={"format": response_format},
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    async def send_message_with_attachments(
        self,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[dict[str, str]],
        reply_to_thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send an outbound message with attachments.

        Args:
            inbox_id: The inbox ID to send from.
            to: List of recipient email addresses.
            subject: Email subject.
            body: Markdown body content.
            attachments: List of attachment dicts with filename, content_type, content (base64).
            reply_to_thread_id: Thread ID if this is a reply.

        Returns:
            Send response with message_id, thread_id, status.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
            "attachments": [
                {
                    "filename": att["filename"],
                    "content_type": att["content_type"],
                    "content_base64": att["content"],
                }
                for att in attachments
            ],
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = await client.post("/v1/messages", json=payload)
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())
