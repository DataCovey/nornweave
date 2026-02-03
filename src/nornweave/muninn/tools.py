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
    inbox_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for emails.

    Find relevant messages in an inbox by query text.

    Args:
        client: NornWeave API client.
        query: Search query.
        inbox_id: Inbox to search in.
        limit: Maximum number of results (default: 10).

    Returns:
        Search results with matching messages.

    Raises:
        Exception: If search fails.
    """
    try:
        result = await client.search_messages(
            query=query,
            inbox_id=inbox_id,
            limit=limit,
        )

        # Format results for MCP
        messages = []
        for item in result.get("items", []):
            messages.append(
                {
                    "id": item["id"],
                    "thread_id": item["thread_id"],
                    "content": item.get("content_clean", ""),
                    "created_at": item.get("created_at"),
                }
            )

        return {
            "query": query,
            "count": len(messages),
            "messages": messages,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Inbox '{inbox_id}' not found") from e
        raise Exception(f"Search failed: {e.response.status_code}") from e


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
