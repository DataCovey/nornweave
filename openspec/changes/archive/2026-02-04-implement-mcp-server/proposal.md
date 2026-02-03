## Why

NornWeave's core value proposition is enabling AI agents to interact with email. While the REST API serves traditional integrations, MCP (Model Context Protocol) is becoming the standard interface for Claude, Cursor, LangChain, and other agent frameworks. The MCP server is documented but not implemented (Phase 2 placeholder), blocking adoption by the primary target audience. Publishing to MCP registries (Smithery.ai, mcp-get.com, glama.ai) will make NornWeave discoverable where developers search for agent tools.

## What Changes

- **Implement MCP server** in `src/nornweave/huginn/server.py` using FastMCP, exposing 2 resources and 4 tools
- **Add MCP resources** (read-only data access):
  - `email://inbox/{inbox_id}/recent` - Recent thread summaries
  - `email://thread/{thread_id}` - Full thread content in Markdown
- **Add MCP tools** (actions):
  - `create_inbox` - Provision new email address
  - `send_email` - Send email with Markdown body
  - `search_email` - Find relevant messages
  - `wait_for_reply` - Block until reply arrives (experimental)
- **Add CLI entry point** `nornweave mcp` for running the server standalone
- **Create registry metadata** for Smithery.ai, mcp-get.com, and glama.ai/mcp publication
- **Add integration tests** for MCP server functionality

## Capabilities

### New Capabilities

- `mcp-server`: MCP server implementation with FastMCP, exposing email resources and tools for AI agent integration. Includes stdio transport, API client for backend communication, and registry metadata for publication.

### Modified Capabilities

None. The MCP server is a new integration layer over existing REST APIs.

## Impact

- **Code**: New implementation in `huginn/server.py`, `huginn/resources.py`, `muninn/tools.py`; CLI command in `yggdrasil/`
- **Dependencies**: `mcp>=1.0.0` moves from optional to recommended; `fastmcp` added
- **APIs**: No REST API changes; MCP server calls existing `/v1/` endpoints internally
- **Documentation**: Update `web/content/docs/api/mcp.md` with actual usage examples; add registry links
- **CI/CD**: Add workflow for publishing to MCP registries on release
- **Testing**: New integration tests in `tests/integration/test_mcp/`
