"""Huginn: MCP read tools (Thought).

This module provides MCP resources (read-only data access) for AI agents.
Named after Odin's raven of thought.
"""

from nornweave.huginn.client import NornWeaveClient
from nornweave.huginn.config import MCPSettings, get_mcp_settings

__all__ = ["MCPSettings", "NornWeaveClient", "get_mcp_settings"]
