"""Muninn: MCP write tools (Memory).

This module provides MCP tools (actions) for AI agents.
Named after Odin's raven of memory.
"""

from nornweave.muninn.tools import (
    create_inbox,
    search_email,
    send_email,
    wait_for_reply,
)

__all__ = ["create_inbox", "search_email", "send_email", "wait_for_reply"]
