"""MCP tools: create_inbox, send_email, search_email, wait_for_reply.

Tools provide actions that AI agents can perform.
"""

import asyncio
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from nornweave.huginn.client import NornWeaveClient


async def create_inbox(
    client: NornWeaveClient,
    name: str,
    username: str,
) -> dict[str, Any]:
    """Create a new inbox.

    Provision a new email address for the agent.

    Args:
        client: NornWeave API client.
        name: Display name for the inbox.
        username: Local part of email address (before @).

    Returns:
        Created inbox with id, email_address, name.

    Raises:
        Exception: If inbox creation fails.
    """
    try:
        result = await client.create_inbox(name=name, email_username=username)
        return {
            "id": result["id"],
            "email_address": result["email_address"],
            "name": result.get("name"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            raise Exception(f"Email address with username '{username}' already exists") from e
        if e.response.status_code == 422:
            raise Exception(f"Invalid username: {username}") from e
        raise Exception(f"Failed to create inbox: {e.response.status_code}") from e


async def send_email(
    client: NornWeaveClient,
    inbox_id: str,
    recipient: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Send an email.

    Send an email from an inbox, automatically converting Markdown to HTML.

    Args:
        client: NornWeave API client.
        inbox_id: The inbox to send from.
        recipient: Email address to send to.
        subject: Email subject.
        body: Markdown content for the email body.
        thread_id: Optional thread ID for replies.

    Returns:
        Send response with message_id, thread_id, status.

    Raises:
        Exception: If sending fails.
    """
    try:
        result = await client.send_message(
            inbox_id=inbox_id,
            to=[recipient],
            subject=subject,
            body=body,
            reply_to_thread_id=thread_id,
        )
        return {
            "message_id": result["id"],
            "thread_id": result["thread_id"],
            "status": result.get("status", "sent"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Inbox '{inbox_id}' not found") from e
        raise Exception(f"Failed to send email: {e.response.status_code}") from e


async def search_email(
    client: NornWeaveClient,
    query: str,
    inbox_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """Search for emails with flexible filters.

    Find relevant messages by query text. At least one of inbox_id or thread_id must be provided.

    Args:
        client: NornWeave API client.
        query: Search query (searches subject, body, sender, attachment filenames).
        inbox_id: Filter by inbox ID (optional).
        thread_id: Filter by thread ID (optional).
        limit: Maximum number of results (default: 10).
        offset: Pagination offset (default: 0).

    Returns:
        Search results with matching messages including expanded fields.

    Raises:
        Exception: If search fails or no filter provided.
    """
    if inbox_id is None and thread_id is None:
        raise Exception("At least one filter (inbox_id or thread_id) is required")

    try:
        result = await client.list_messages(
            inbox_id=inbox_id,
            thread_id=thread_id,
            q=query,
            limit=limit,
            offset=offset,
        )

        # Format results for MCP with expanded fields
        messages = []
        for item in result.get("items", []):
            messages.append(_format_message_for_mcp(item))

        return {
            "query": query,
            "count": len(messages),
            "total": result.get("total", len(messages)),
            "messages": messages,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception("Inbox or thread not found") from e
        if e.response.status_code == 422:
            raise Exception("At least one filter (inbox_id or thread_id) is required") from e
        raise Exception(f"Search failed: {e.response.status_code}") from e


async def list_messages(
    client: NornWeaveClient,
    inbox_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List messages with flexible filters.

    List messages from an inbox or thread. At least one of inbox_id or thread_id must be provided.

    Args:
        client: NornWeave API client.
        inbox_id: Filter by inbox ID (optional).
        thread_id: Filter by thread ID (optional).
        limit: Maximum number of results (default: 50).
        offset: Pagination offset (default: 0).

    Returns:
        List of messages with expanded fields.

    Raises:
        Exception: If listing fails or no filter provided.
    """
    if inbox_id is None and thread_id is None:
        raise Exception("At least one filter (inbox_id or thread_id) is required")

    try:
        result = await client.list_messages(
            inbox_id=inbox_id,
            thread_id=thread_id,
            limit=limit,
            offset=offset,
        )

        # Format results for MCP with expanded fields
        messages = []
        for item in result.get("items", []):
            messages.append(_format_message_for_mcp(item))

        return {
            "count": len(messages),
            "total": result.get("total", len(messages)),
            "messages": messages,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception("Inbox or thread not found") from e
        if e.response.status_code == 422:
            raise Exception("At least one filter (inbox_id or thread_id) is required") from e
        raise Exception(f"List messages failed: {e.response.status_code}") from e


def _format_message_for_mcp(item: dict[str, Any]) -> dict[str, Any]:
    """Format a message response for MCP tools with all expanded fields."""
    return {
        "id": item["id"],
        "thread_id": item["thread_id"],
        "inbox_id": item["inbox_id"],
        "direction": item.get("direction"),
        "subject": item.get("subject"),
        "from_address": item.get("from_address"),
        "to_addresses": item.get("to_addresses", []),
        "cc_addresses": item.get("cc_addresses"),
        "text": item.get("text"),
        "content_clean": item.get("content_clean", ""),
        "timestamp": item.get("timestamp"),
        "preview": item.get("preview"),
        "labels": item.get("labels", []),
        "created_at": item.get("created_at"),
    }


async def wait_for_reply(
    client: NornWeaveClient,
    thread_id: str,
    timeout_seconds: int = 300,
    poll_interval: int = 5,
) -> dict[str, Any]:
    """Wait for a reply in a thread (experimental).

    Block execution until a new email arrives in a thread.
    Uses polling to check for new messages.

    Args:
        client: NornWeave API client.
        thread_id: Thread to wait on.
        timeout_seconds: Maximum wait time (default: 300 seconds / 5 minutes).
        poll_interval: Seconds between polls (default: 5).

    Returns:
        The new message content if received, or timeout indicator.

    Raises:
        Exception: If thread not found.
    """
    try:
        # Get initial message count
        initial_count = await client.get_thread_message_count(thread_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Thread '{thread_id}' not found") from e
        raise Exception(f"Failed to access thread: {e.response.status_code}") from e

    elapsed = 0
    while elapsed < timeout_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        try:
            current_count = await client.get_thread_message_count(thread_id)

            if current_count > initial_count:
                # New message arrived
                latest = await client.get_latest_message(thread_id)
                if latest:
                    return {
                        "received": True,
                        "message": {
                            "author": latest.get("author"),
                            "content": latest.get("content", ""),
                            "timestamp": latest.get("timestamp"),
                        },
                    }
        except httpx.HTTPStatusError:
            # Ignore transient errors during polling
            pass

    # Timeout reached
    return {
        "received": False,
        "timeout": True,
        "waited_seconds": timeout_seconds,
    }


async def list_attachments(
    client: NornWeaveClient,
    message_id: str | None = None,
    thread_id: str | None = None,
    inbox_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List attachments for a message, thread, or inbox.

    Retrieve metadata for attachments. Exactly one filter must be provided.

    Args:
        client: NornWeave API client.
        message_id: Filter by message ID.
        thread_id: Filter by thread ID (all messages in thread).
        inbox_id: Filter by inbox ID (all messages in inbox).
        limit: Maximum number of results (default: 100).

    Returns:
        List of attachment metadata objects.

    Raises:
        Exception: If filter is missing or invalid.
    """
    # Validate exactly one filter
    filters = [f for f in [message_id, thread_id, inbox_id] if f is not None]
    if len(filters) == 0:
        raise Exception("Exactly one filter required: message_id, thread_id, or inbox_id")
    if len(filters) > 1:
        raise Exception("Only one filter allowed: message_id, thread_id, or inbox_id")

    try:
        result = await client.list_attachments(
            message_id=message_id,
            thread_id=thread_id,
            inbox_id=inbox_id,
            limit=limit,
        )

        # Format results for MCP
        attachments = []
        for item in result.get("items", []):
            attachments.append(
                {
                    "id": item["id"],
                    "message_id": item["message_id"],
                    "filename": item["filename"],
                    "content_type": item["content_type"],
                    "size": item["size"],
                }
            )

        return {
            "count": len(attachments),
            "attachments": attachments,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            raise Exception(
                "Invalid filter: exactly one of message_id, thread_id, or inbox_id required"
            ) from e
        if e.response.status_code == 404:
            raise Exception("Resource not found") from e
        raise Exception(f"Failed to list attachments: {e.response.status_code}") from e


async def get_attachment_content(
    client: NornWeaveClient,
    attachment_id: str,
) -> dict[str, Any]:
    """Retrieve attachment content as base64.

    Download the binary content of an attachment, encoded as base64.

    Args:
        client: NornWeave API client.
        attachment_id: The attachment ID to retrieve.

    Returns:
        Attachment content with base64-encoded data, content_type, and filename.

    Raises:
        Exception: If attachment not found.
    """
    try:
        result = await client.get_attachment_content(
            attachment_id=attachment_id,
            response_format="base64",
        )
        return {
            "content": result["content"],
            "content_type": result["content_type"],
            "filename": result["filename"],
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Attachment '{attachment_id}' not found") from e
        if e.response.status_code == 401:
            raise Exception("Attachment download URL expired or invalid") from e
        raise Exception(f"Failed to get attachment content: {e.response.status_code}") from e


async def send_email_with_attachments(
    client: NornWeaveClient,
    inbox_id: str,
    recipient: str,
    subject: str,
    body: str,
    attachments: list[dict[str, str]],
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Send an email with attachments.

    Send an email with one or more attachments. Each attachment should include
    filename, content_type, and base64-encoded content.

    Args:
        client: NornWeave API client.
        inbox_id: The inbox to send from.
        recipient: Email address to send to.
        subject: Email subject.
        body: Markdown content for the email body.
        attachments: List of attachment dicts with keys:
            - filename: Name of the file
            - content_type: MIME type (e.g., "application/pdf")
            - content: Base64-encoded file content
        thread_id: Optional thread ID for replies.

    Returns:
        Send response with message_id, thread_id, status.

    Raises:
        Exception: If sending fails or attachments are invalid.
    """
    # Validate attachments
    if not attachments:
        raise Exception(
            "At least one attachment is required. Use send_email for messages without attachments."
        )

    for i, att in enumerate(attachments):
        if not att.get("filename"):
            raise Exception(f"Attachment {i} missing filename")
        if not att.get("content_type"):
            raise Exception(f"Attachment {i} missing content_type")
        if not att.get("content"):
            raise Exception(f"Attachment {i} missing content (base64)")

    try:
        result = await client.send_message_with_attachments(
            inbox_id=inbox_id,
            to=[recipient],
            subject=subject,
            body=body,
            attachments=attachments,
            reply_to_thread_id=thread_id,
        )
        return {
            "message_id": result["id"],
            "thread_id": result["thread_id"],
            "status": result.get("status", "sent"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Inbox '{inbox_id}' not found") from e
        if e.response.status_code == 400:
            raise Exception("Invalid attachment data (check base64 encoding)") from e
        raise Exception(f"Failed to send email: {e.response.status_code}") from e
