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
from nornweave.muninn.tools import create_inbox, search_email, send_email, wait_for_reply

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
async def tool_search_email(query: str, inbox_id: str, limit: int = 10) -> dict[str, Any]:
    """Search for emails.

    Find relevant messages in an inbox by query text.

    Args:
        query: Search query (e.g., "invoice", "meeting request")
        inbox_id: Inbox to search in
        limit: Maximum number of results (default: 10, max: 100)

    Returns:
        Search results with matching messages containing id, thread_id, content, created_at.
    """
    client = _get_client()
    return await search_email(client, query=query, inbox_id=inbox_id, limit=min(limit, 100))


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
