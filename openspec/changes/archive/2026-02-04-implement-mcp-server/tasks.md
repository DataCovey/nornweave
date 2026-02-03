## 1. Setup and Dependencies

- [x] 1.1 Add `fastmcp` to MCP optional dependencies in pyproject.toml
- [x] 1.2 Create `huginn/client.py` with async HTTP client class for NornWeave API
- [x] 1.3 Add configuration loading for `NORNWEAVE_API_URL` and `NORNWEAVE_API_KEY`

## 2. MCP Resources (Huginn)

- [x] 2.1 Implement `email://inbox/{inbox_id}/recent` resource in `huginn/resources.py`
- [x] 2.2 Implement `email://thread/{thread_id}` resource in `huginn/resources.py`
- [x] 2.3 Add Markdown formatting for thread content (subject heading, message separators)

## 3. MCP Tools (Muninn)

- [x] 3.1 Implement `create_inbox` tool in `muninn/tools.py`
- [x] 3.2 Implement `send_email` tool with thread_id support in `muninn/tools.py`
- [x] 3.3 Implement `search_email` tool with limit parameter in `muninn/tools.py`
- [x] 3.4 Implement `wait_for_reply` tool with polling and timeout in `muninn/tools.py`

## 4. MCP Server Entry Point

- [x] 4.1 Implement FastMCP server setup in `huginn/server.py`
- [x] 4.2 Register resources and tools with FastMCP app
- [x] 4.3 Configure stdio transport for MCP communication (default)
- [x] 4.4 Add SSE transport support for web-based MCP clients
- [x] 4.5 Add HTTP (streamable) transport support for cloud deployments

## 5. CLI Command

- [x] 5.1 Add `nornweave mcp` CLI command to start MCP server
- [x] 5.2 Add `--transport [stdio|sse|http]` option (default: stdio)
- [x] 5.3 Add `--host` and `--port` options for SSE/HTTP transports
- [x] 5.4 Add `--api-url` option for custom API endpoint
- [x] 5.5 Update CLI help text with all MCP configuration options

## 6. Registry Metadata

- [x] 6.1 Create `smithery.yaml` with server metadata and tool descriptions
- [x] 6.2 Create `mcp-get.json` with package metadata for mcp-get.com
- [x] 6.3 Create `glama.json` with capabilities for glama.ai/mcp

## 7. Testing

- [x] 7.1 Create mock NornWeave API server for MCP tests in `tests/integration/test_mcp/`
- [x] 7.2 Add integration tests for resource fetching
- [x] 7.3 Add integration tests for tool execution
- [x] 7.4 Add integration tests for SSE and HTTP transports
- [x] 7.5 Add unit tests for HTTP client in `tests/unit/test_huginn/`

## 8. Documentation

- [x] 8.1 Update `web/content/docs/api/mcp.md` with actual usage examples and registry links
- [x] 8.2 Update `web/content/docs/getting-started/installation.md` with MCP server installation steps (pip install, running `nornweave mcp`, transport options)
- [x] 8.3 Update `web/content/docs/getting-started/configuration.md` with MCP server environment variables (transport, host, port, API URL)
- [x] 8.4 Update `web/content/docs/concepts/architecture.md` diagrams to show MCP transport options (stdio, SSE, HTTP)
- [x] 8.5 Add registry submission instructions to CONTRIBUTING.md
- [x] 8.6 Update CHANGELOG.md with MCP server implementation
