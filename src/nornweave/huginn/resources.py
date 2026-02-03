"""MCP resources: email://inbox/{id}/recent, email://thread/{id}.

Resources provide read-only data access for AI agents.
"""

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from nornweave.huginn.client import NornWeaveClient


async def get_recent_threads(client: NornWeaveClient, inbox_id: str) -> str:
    """Get recent threads for an inbox.

    Resource URI: email://inbox/{inbox_id}/recent

    Args:
        client: NornWeave API client.
        inbox_id: The inbox ID.

    Returns:
        JSON string with thread summaries.

    Raises:
        Exception: If inbox not found or API error.
    """
    import json

    try:
        # Get threads (limit to 10 most recent)
        threads_response = await client.list_threads(inbox_id, limit=10)
        threads = threads_response.get("items", [])

        # Format thread summaries with message count
        summaries = []
        for thread in threads:
            # Get thread details to count messages
            try:
                thread_detail = await client.get_thread(thread["id"])
                message_count = len(thread_detail.get("messages", []))
                participants = _extract_participants(thread_detail)
            except httpx.HTTPStatusError:
                message_count = 0
                participants = []

            summaries.append(
                {
                    "id": thread["id"],
                    "subject": thread.get("subject", "(no subject)"),
                    "last_message_at": thread.get("last_message_at"),
                    "message_count": message_count,
                    "participants": participants,
                }
            )

        return json.dumps(summaries, indent=2, default=str)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Inbox '{inbox_id}' not found") from e
        raise Exception(f"API error: {e.response.status_code}") from e


def _extract_participants(thread_detail: dict[str, Any]) -> list[str]:
    """Extract unique participant email addresses from thread messages."""
    participants: set[str] = set()
    for message in thread_detail.get("messages", []):
        author = message.get("author")
        if author:
            participants.add(author)
    return sorted(participants)


async def get_thread_content(client: NornWeaveClient, thread_id: str) -> str:
    """Get thread content in Markdown format.

    Resource URI: email://thread/{thread_id}

    Args:
        client: NornWeave API client.
        thread_id: The thread ID.

    Returns:
        Markdown-formatted thread content optimized for LLM context.

    Raises:
        Exception: If thread not found or API error.
    """
    try:
        thread = await client.get_thread(thread_id)
        return format_thread_markdown(thread)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise Exception(f"Thread '{thread_id}' not found") from e
        raise Exception(f"API error: {e.response.status_code}") from e


def format_thread_markdown(thread: dict[str, Any]) -> str:
    """Format thread data as Markdown for LLM context.

    Args:
        thread: Thread data with id, subject, and messages.

    Returns:
        Markdown-formatted thread content.
    """
    lines: list[str] = []

    # Thread subject as heading
    subject = thread.get("subject", "(no subject)")
    lines.append(f"## Thread: {subject}")
    lines.append("")

    messages = thread.get("messages", [])
    if not messages:
        lines.append("*No messages in this thread.*")
        return "\n".join(lines)

    for i, message in enumerate(messages):
        if i > 0:
            lines.append("---")
            lines.append("")

        # Message metadata
        author = message.get("author", "unknown")
        timestamp = message.get("timestamp")
        role = message.get("role", "user")

        # Format date
        date_str = _format_timestamp(timestamp) if timestamp else "unknown date"

        # Role indicator for context
        role_indicator = "→" if role == "assistant" else "←"

        lines.append(f"**From:** {author} {role_indicator}")
        lines.append(f"**Date:** {date_str}")
        lines.append("")

        # Message content
        content = message.get("content", "")
        if content:
            lines.append(content)
        else:
            lines.append("*(empty message)*")

        lines.append("")

    return "\n".join(lines)


def _format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    from datetime import datetime

    try:
        # Handle ISO format with timezone
        if "T" in timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        return timestamp
    except (ValueError, TypeError):
        return str(timestamp)
