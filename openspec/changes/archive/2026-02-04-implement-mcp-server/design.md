## Context

NornWeave provides email capabilities via a REST API (`/v1/` endpoints). The MCP server will expose these capabilities through the Model Context Protocol, enabling AI agents (Claude, Cursor, LangChain) to interact with email using natural language.

**Current state:**
- REST API fully functional with 4 routers: inboxes, threads, messages, search
- MCP entry point stubbed in `pyproject.toml` (`nornweave.huginn.server:serve`)
- Placeholder files exist in `huginn/` and `muninn/` modules
- Documentation at `web/content/docs/api/mcp.md` describes expected interface

**Constraints:**
- Must communicate with NornWeave API over HTTP (not direct DB access)
- Keep MCP server stateless; all state lives in the API

## Goals / Non-Goals

**Goals:**
- Implement MCP server with FastMCP exposing 2 resources and 4 tools
- Support multiple transports: stdio (Claude Desktop, Cursor), SSE, and HTTP (remote/cloud deployments)
- Create registry metadata for Smithery.ai, mcp-get.com, glama.ai publication
- Provide CLI command `nornweave mcp` for standalone operation with transport selection

**Non-Goals:**
- Direct database access (MCP server is an API client)
- Authentication within MCP (relies on API key passed to underlying REST calls)
- Streaming responses (tools return complete results)

## Decisions

### Decision 1: Use FastMCP over raw MCP SDK

**Choice:** FastMCP (high-level wrapper)

**Rationale:** FastMCP provides decorator-based tool/resource definitions, automatic schema generation, and built-in stdio support. Reduces boilerplate significantly compared to raw MCP SDK.

**Alternatives considered:**
- Raw MCP SDK: More control but 3x more code for same functionality
- Custom implementation: No benefit, MCP SDK is well-maintained

### Decision 2: MCP server as HTTP client to REST API

**Choice:** MCP server calls NornWeave REST API via httpx

**Rationale:**
- Decouples MCP layer from storage implementation
- Allows MCP server to run on different host than API
- API key authentication works consistently
- No code duplication between REST and MCP paths

**Alternatives considered:**
- Direct storage access: Tighter coupling, requires database connection in MCP process
- Shared service layer: Would require significant refactoring of yggdrasil

### Decision 3: Configuration via environment variables

**Choice:** `NORNWEAVE_API_URL` and `NORNWEAVE_API_KEY` environment variables

**Rationale:**
- Consistent with MCP server conventions (env vars in mcpServers config)
- Simple to configure in Claude Desktop / Cursor settings
- No file-based config needed

**Alternatives considered:**
- CLI arguments: Less flexible for MCP client configuration
- Config file: Overkill for 2 settings

### Decision 4: Module structure preserves Norse naming

**Choice:**
- `huginn/server.py` - MCP server entry point and FastMCP app
- `huginn/resources.py` - Resource definitions (read-only)
- `muninn/tools.py` - Tool definitions (actions)
- `huginn/client.py` - HTTP client for API calls

**Rationale:** Maintains existing architecture. Huginn (thought/reading) for resources, Muninn (memory/actions) for tools.

### Decision 5: Support all three MCP transports

**Choice:** Implement stdio, SSE, and streamable HTTP transports

**Rationale:**
- **stdio**: Required for Claude Desktop, Cursor, and local CLI usage
- **SSE (Server-Sent Events)**: Enables web-based MCP clients and browser integrations
- **HTTP (Streamable)**: Best for remote/cloud deployments, load balancing, and LangChain integration

**Implementation:**
- CLI flag `--transport [stdio|sse|http]` (default: stdio)
- SSE/HTTP modes bind to `--host` and `--port` (default: 0.0.0.0:3000)
- FastMCP natively supports all three transports

**Alternatives considered:**
- stdio only: Limits cloud deployment and web integration use cases
- WebSocket: Not part of MCP spec, would require custom protocol

### Decision 6: wait_for_reply uses polling

**Choice:** Implement via polling with configurable interval and timeout

**Rationale:**
- Simple to implement across all transports
- Acceptable for experimental feature
- Client can set reasonable timeout (default 300s)

**Alternatives considered:**
- Push notifications: Would require additional infrastructure beyond MCP

### Decision 7: Registry metadata in repository root

**Choice:** Create `smithery.yaml`, `mcp-get.json`, `glama.json` in repo root

**Rationale:**
- Standard locations expected by registry crawlers
- Easy to maintain alongside package metadata
- CI can validate these files exist and are valid

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Polling for wait_for_reply is inefficient** | Mark as experimental, document limitations, set reasonable default timeout (5min) |
| **API latency adds to MCP response time** | API runs locally in typical setup; document that remote API adds latency |
| **Registry publication requires manual steps** | Document process in CONTRIBUTING.md; automate where possible in CI |
| **FastMCP is a third-party dependency** | FastMCP is well-maintained and widely used; fallback to raw SDK if needed |

## Open Questions

1. **Should list_inboxes be exposed as a resource or tool?** Currently not in the documented interface, but useful for agents to discover available inboxes. Recommendation: Add as resource `email://inboxes`.

2. **Rate limiting for wait_for_reply polling?** Could overwhelm API if many agents wait simultaneously. Consider adding jitter and exponential backoff.
