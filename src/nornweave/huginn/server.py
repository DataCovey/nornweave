"""MCP server setup (Huginn & Muninn).

This module provides the FastMCP server that exposes NornWeave email capabilities
to AI agents via the Model Context Protocol.

Supports three transports:
- stdio: For Claude Desktop, Cursor, and local CLI usage (default)
- sse: For web-based MCP clients and browser integrations
- http: For remote/cloud deployments and LangChain integration
"""

from typing import Any, Literal

from fastmcp import FastMCP

from nornweave.huginn.client import NornWeaveClient
from nornweave.huginn.resources import get_recent_threads, get_thread_content
from nornweave.muninn.tools import (
    create_inbox,
    get_attachment_content,
    list_attachments,
    list_messages,
    search_email,
    send_email,
    send_email_with_attachments,
    wait_for_reply,
)

# Create the FastMCP server
mcp = FastMCP(
    name="nornweave",
    version="0.1.3",
    instructions="Email capabilities for AI agents - create inboxes, send emails, search messages",
)

# Global client instance (created on first use)
_client: NornWeaveClient | None = None


def _get_client() -> NornWeaveClient:
    """Get or create the NornWeave API client."""
    global _client
    if _client is None:
        _client = NornWeaveClient()
    return _client


# -----------------------------------------------------------------------------
# Resources (Read-only data access)
# -----------------------------------------------------------------------------


@mcp.resource("email://inbox/{inbox_id}/recent")
async def resource_recent_threads(inbox_id: str) -> str:
    """Get recent threads for an inbox.

    Returns the 10 most recent thread summaries with id, subject,
    last_message_at, message_count, and participants.
    """
    client = _get_client()
    return await get_recent_threads(client, inbox_id)


@mcp.resource("email://thread/{thread_id}")
async def resource_thread_content(thread_id: str) -> str:
    """Get thread content in Markdown format.

    Returns the full thread conversation formatted as Markdown,
    optimized for LLM context windows.
    """
    client = _get_client()
    return await get_thread_content(client, thread_id)


@mcp.tool()
async def tool_create_inbox(name: str, username: str) -> dict[str, Any]:
    """Create a new inbox.

    Provision a new email address for the agent.

    Args:
        name: Display name for the inbox (e.g., "Support Bot")
        username: Local part of email address (e.g., "support" becomes support@yourdomain.com)

    Returns:
        Created inbox with id, email_address, and name.
    """
    client = _get_client()
    return await create_inbox(client, name=name, username=username)


@mcp.tool()
async def tool_send_email(
    inbox_id: str,
    recipient: str,
    subject: str,
    body: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Send an email.

    Send an email from an inbox. The body content should be in Markdown format
    and will be automatically converted to HTML.

    Args:
        inbox_id: The inbox ID to send from
        recipient: Email address to send to
        subject: Email subject line
        body: Email body in Markdown format
        thread_id: Optional thread ID if this is a reply to an existing thread

    Returns:
        Send response with message_id, thread_id, and status.
    """
    client = _get_client()
    return await send_email(
        client,
        inbox_id=inbox_id,
        recipient=recipient,
        subject=subject,
        body=body,
        thread_id=thread_id,
    )


@mcp.tool()
async def tool_search_email(
    query: str,
    inbox_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """Search for emails with flexible filters.

    Find relevant messages by query text. At least one of inbox_id or thread_id must be provided.

    Args:
        query: Search query (searches subject, body, sender, attachment filenames)
        inbox_id: Filter by inbox ID (optional)
        thread_id: Filter by thread ID (optional)
        limit: Maximum number of results (default: 10, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        Search results with matching messages containing full email metadata.
    """
    client = _get_client()
    return await search_email(
        client,
        query=query,
        inbox_id=inbox_id,
        thread_id=thread_id,
        limit=min(limit, 100),
        offset=offset,
    )


@mcp.tool()
async def tool_list_messages(
    inbox_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List messages with flexible filters.

    List messages from an inbox or thread. At least one of inbox_id or thread_id must be provided.

    Args:
        inbox_id: Filter by inbox ID (optional)
        thread_id: Filter by thread ID (optional)
        limit: Maximum number of results (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of messages with full email metadata including subject, from_address, to_addresses, text, etc.
    """
    client = _get_client()
    return await list_messages(
        client,
        inbox_id=inbox_id,
        thread_id=thread_id,
        limit=min(limit, 100),
        offset=offset,
    )


@mcp.tool()
async def tool_wait_for_reply(thread_id: str, timeout_seconds: int = 300) -> dict[str, Any]:
    """Wait for a reply in a thread (experimental).

    Block execution until a new email arrives in the specified thread.
    Useful for synchronous agent workflows that need to wait for responses.

    Args:
        thread_id: Thread ID to wait on
        timeout_seconds: Maximum wait time in seconds (default: 300 / 5 minutes)

    Returns:
        If reply received: {"received": true, "message": {...}}
        If timeout: {"received": false, "timeout": true, "waited_seconds": N}

    Note:
        This is an experimental feature that uses polling. It may not be suitable
        for all use cases and could incur additional API calls.
    """
    client = _get_client()
    return await wait_for_reply(client, thread_id=thread_id, timeout_seconds=timeout_seconds)


@mcp.tool()
async def tool_list_attachments(
    message_id: str | None = None,
    thread_id: str | None = None,
    inbox_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List attachments for a message, thread, or inbox.

    Retrieve metadata for attachments. Exactly one filter must be provided.

    Args:
        message_id: Filter by message ID
        thread_id: Filter by thread ID (all messages in thread)
        inbox_id: Filter by inbox ID (all messages in inbox)
        limit: Maximum number of results (default: 100)

    Returns:
        List of attachment metadata with id, message_id, filename, content_type, size.
    """
    client = _get_client()
    return await list_attachments(
        client,
        message_id=message_id,
        thread_id=thread_id,
        inbox_id=inbox_id,
        limit=limit,
    )


@mcp.tool()
async def tool_get_attachment_content(attachment_id: str) -> dict[str, Any]:
    """Get attachment content as base64.

    Download the binary content of an attachment, returned as base64-encoded data.

    Args:
        attachment_id: The attachment ID to retrieve

    Returns:
        Attachment content with base64-encoded data, content_type, and filename.
    """
    client = _get_client()
    return await get_attachment_content(client, attachment_id=attachment_id)


@mcp.tool()
async def tool_send_email_with_attachments(
    inbox_id: str,
    recipient: str,
    subject: str,
    body: str,
    attachments: list[dict[str, str]],
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Send an email with attachments.

    Send an email with one or more file attachments.

    Args:
        inbox_id: The inbox ID to send from
        recipient: Email address to send to
        subject: Email subject line
        body: Email body in Markdown format
        attachments: List of attachments, each with:
            - filename: Name of the file (e.g., "report.pdf")
            - content_type: MIME type (e.g., "application/pdf")
            - content: Base64-encoded file content
        thread_id: Optional thread ID if this is a reply

    Returns:
        Send response with message_id, thread_id, and status.
    """
    client = _get_client()
    return await send_email_with_attachments(
        client,
        inbox_id=inbox_id,
        recipient=recipient,
        subject=subject,
        body=body,
        attachments=attachments,
        thread_id=thread_id,
    )


# -----------------------------------------------------------------------------
# Server Entry Points
# -----------------------------------------------------------------------------


def serve(
    transport: Literal["stdio", "sse", "http"] = "stdio",
    host: str = "0.0.0.0",
    port: int = 3000,
) -> None:
    """Run the MCP server.

    Args:
        transport: Transport type - "stdio" (default), "sse", or "http"
        host: Host to bind for SSE/HTTP transports (default: 0.0.0.0)
        port: Port for SSE/HTTP transports (default: 3000)
    """
    if transport == "stdio":
        mcp.run()
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "http":
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}")


def serve_stdio() -> None:
    """Run MCP server with stdio transport (for MCP entry point)."""
    serve(transport="stdio")


def serve_sse(host: str = "0.0.0.0", port: int = 3000) -> None:
    """Run MCP server with SSE transport."""
    serve(transport="sse", host=host, port=port)


def serve_http(host: str = "0.0.0.0", port: int = 3000) -> None:
    """Run MCP server with HTTP transport."""
    serve(transport="http", host=host, port=port)


# For MCP entry point discovery
if __name__ == "__main__":
    serve_stdio()
