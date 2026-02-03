## ADDED Requirements

### Requirement: MCP server supports multiple transports

The MCP server SHALL support stdio, SSE, and HTTP transports for communication with different MCP clients and deployment scenarios.

#### Scenario: Server starts with stdio transport (default)
- **WHEN** a client runs `nornweave mcp` command without transport flag
- **THEN** the server starts and listens on stdin for MCP protocol messages
- **AND** responds on stdout with MCP protocol responses

#### Scenario: Server starts with SSE transport
- **WHEN** a client runs `nornweave mcp --transport sse`
- **THEN** the server starts an HTTP server with SSE endpoints
- **AND** listens on the configured host and port (default: 0.0.0.0:3000)

#### Scenario: Server starts with HTTP transport
- **WHEN** a client runs `nornweave mcp --transport http`
- **THEN** the server starts a streamable HTTP server
- **AND** listens on the configured host and port (default: 0.0.0.0:3000)

#### Scenario: Server uses configured API URL
- **WHEN** environment variable `NORNWEAVE_API_URL` is set to `http://localhost:8000`
- **THEN** all API calls from the MCP server target that base URL

#### Scenario: Server uses configured API key
- **WHEN** environment variable `NORNWEAVE_API_KEY` is set
- **THEN** all API calls include `X-API-Key` header with that value

#### Scenario: Server works without API key
- **WHEN** environment variable `NORNWEAVE_API_KEY` is not set
- **THEN** API calls are made without authentication headers

### Requirement: SSE transport enables web-based MCP clients

The MCP server SHALL provide SSE transport for browser-based and web MCP clients.

#### Scenario: SSE endpoint accepts connections
- **WHEN** a web client connects to the SSE endpoint
- **THEN** the server establishes an SSE connection
- **AND** sends MCP protocol messages as server-sent events

#### Scenario: SSE supports custom host and port
- **WHEN** user runs `nornweave mcp --transport sse --host 127.0.0.1 --port 8080`
- **THEN** the SSE server binds to 127.0.0.1:8080

### Requirement: HTTP transport enables cloud deployments

The MCP server SHALL provide streamable HTTP transport for remote and cloud deployments.

#### Scenario: HTTP endpoint handles MCP requests
- **WHEN** an HTTP client sends an MCP request to the server
- **THEN** the server processes the request and returns an MCP response

#### Scenario: HTTP supports custom host and port
- **WHEN** user runs `nornweave mcp --transport http --host 0.0.0.0 --port 9000`
- **THEN** the HTTP server binds to 0.0.0.0:9000

#### Scenario: HTTP transport works with load balancers
- **WHEN** the MCP server runs behind a load balancer
- **THEN** requests are handled statelessly without session affinity requirements

### Requirement: Resource email://inbox/{inbox_id}/recent returns recent threads

The MCP server SHALL expose a resource at `email://inbox/{inbox_id}/recent` that returns the most recent thread summaries for an inbox.

#### Scenario: Fetch recent threads for valid inbox
- **WHEN** client requests resource `email://inbox/ibx_123/recent`
- **THEN** server returns JSON array of up to 10 thread summaries
- **AND** each summary contains `id`, `subject`, `last_message_at`, `message_count`, `participants`

#### Scenario: Fetch recent threads for non-existent inbox
- **WHEN** client requests resource `email://inbox/invalid_id/recent`
- **THEN** server returns an error indicating inbox not found

### Requirement: Resource email://thread/{thread_id} returns thread content

The MCP server SHALL expose a resource at `email://thread/{thread_id}` that returns the full thread content in Markdown format optimized for LLM context.

#### Scenario: Fetch thread content for valid thread
- **WHEN** client requests resource `email://thread/th_456`
- **THEN** server returns Markdown-formatted thread content
- **AND** content includes thread subject as heading
- **AND** each message shows sender, date, and body separated by horizontal rules

#### Scenario: Fetch thread content for non-existent thread
- **WHEN** client requests resource `email://thread/invalid_id`
- **THEN** server returns an error indicating thread not found

### Requirement: Tool create_inbox provisions new email address

The MCP server SHALL expose a tool `create_inbox` that creates a new inbox with a specified name and username.

#### Scenario: Create inbox with valid inputs
- **WHEN** client calls `create_inbox` with `name="Support Bot"` and `username="support"`
- **THEN** server creates inbox via POST /v1/inboxes
- **AND** returns created inbox with `id`, `email_address`, `name`

#### Scenario: Create inbox with duplicate username
- **WHEN** client calls `create_inbox` with a username that already exists
- **THEN** server returns an error indicating the email address is already in use

#### Scenario: Create inbox with invalid username
- **WHEN** client calls `create_inbox` with an empty or invalid username
- **THEN** server returns a validation error

### Requirement: Tool send_email sends message with Markdown body

The MCP server SHALL expose a tool `send_email` that sends an email, automatically converting Markdown to HTML.

#### Scenario: Send new email (creates new thread)
- **WHEN** client calls `send_email` with `inbox_id`, `recipient`, `subject`, and `body`
- **THEN** server sends email via POST /v1/messages
- **AND** returns `message_id`, `thread_id`, and `status`

#### Scenario: Send reply to existing thread
- **WHEN** client calls `send_email` with `inbox_id`, `recipient`, `subject`, `body`, and `thread_id`
- **THEN** server includes `reply_to_thread_id` in the API request
- **AND** message is added to the existing thread

#### Scenario: Send email to invalid inbox
- **WHEN** client calls `send_email` with a non-existent `inbox_id`
- **THEN** server returns an error indicating inbox not found

### Requirement: Tool search_email finds relevant messages

The MCP server SHALL expose a tool `search_email` that searches messages by query text.

#### Scenario: Search with valid query
- **WHEN** client calls `search_email` with `query="invoice"` and `inbox_id`
- **THEN** server searches via POST /v1/search
- **AND** returns array of matching messages with `id`, `thread_id`, `content`, `created_at`

#### Scenario: Search with limit parameter
- **WHEN** client calls `search_email` with `query`, `inbox_id`, and `limit=5`
- **THEN** server returns at most 5 results

#### Scenario: Search in non-existent inbox
- **WHEN** client calls `search_email` with a non-existent `inbox_id`
- **THEN** server returns an error indicating inbox not found

### Requirement: Tool wait_for_reply blocks until reply arrives (experimental)

The MCP server SHALL expose an experimental tool `wait_for_reply` that polls for new messages in a thread until a reply arrives or timeout is reached.

#### Scenario: Reply arrives before timeout
- **WHEN** client calls `wait_for_reply` with `thread_id` and `timeout_seconds=60`
- **AND** a new inbound message arrives in that thread within 60 seconds
- **THEN** server returns the new message content

#### Scenario: Timeout without reply
- **WHEN** client calls `wait_for_reply` with `thread_id` and `timeout_seconds=10`
- **AND** no new message arrives within 10 seconds
- **THEN** server returns a timeout indicator (not an error)

#### Scenario: Wait on non-existent thread
- **WHEN** client calls `wait_for_reply` with a non-existent `thread_id`
- **THEN** server returns an error indicating thread not found

#### Scenario: Default timeout
- **WHEN** client calls `wait_for_reply` without `timeout_seconds`
- **THEN** server uses default timeout of 300 seconds (5 minutes)

### Requirement: CLI command nornweave mcp starts MCP server

The CLI SHALL provide a `nornweave mcp` command that starts the MCP server for standalone operation with transport selection.

#### Scenario: Start MCP server with defaults
- **WHEN** user runs `nornweave mcp`
- **THEN** MCP server starts with stdio transport
- **AND** uses `NORNWEAVE_API_URL` from environment (default: `http://localhost:8000`)

#### Scenario: Start MCP server with custom API URL
- **WHEN** user runs `nornweave mcp --api-url http://remote:8000`
- **THEN** MCP server starts and targets the specified API URL

#### Scenario: Start MCP server with SSE transport
- **WHEN** user runs `nornweave mcp --transport sse`
- **THEN** MCP server starts with SSE transport on default host/port (0.0.0.0:3000)

#### Scenario: Start MCP server with HTTP transport
- **WHEN** user runs `nornweave mcp --transport http`
- **THEN** MCP server starts with HTTP transport on default host/port (0.0.0.0:3000)

#### Scenario: Configure host and port for network transports
- **WHEN** user runs `nornweave mcp --transport sse --host 127.0.0.1 --port 8080`
- **THEN** MCP server binds to the specified host and port

#### Scenario: Help text describes all options
- **WHEN** user runs `nornweave mcp --help`
- **THEN** help text explains `--transport`, `--api-url`, `--host`, `--port` options
- **AND** describes environment variable configuration

### Requirement: Registry metadata for Smithery.ai publication

The repository SHALL include `smithery.yaml` with metadata for Smithery.ai registry.

#### Scenario: smithery.yaml contains required fields
- **WHEN** Smithery.ai crawler reads `smithery.yaml` from repository root
- **THEN** file contains `name`, `description`, `version`, `author`, `repository`, `install`, and `tools` fields

#### Scenario: Tools are documented in smithery.yaml
- **WHEN** Smithery.ai displays the NornWeave server page
- **THEN** all 4 tools (`create_inbox`, `send_email`, `search_email`, `wait_for_reply`) are listed with descriptions

### Requirement: Registry metadata for mcp-get.com publication

The repository SHALL include `mcp-get.json` with metadata for mcp-get.com registry.

#### Scenario: mcp-get.json contains required fields
- **WHEN** mcp-get.com indexes the repository
- **THEN** file contains `name`, `description`, `version`, `homepage`, `repository`, and `command` fields

### Requirement: Registry metadata for glama.ai publication

The repository SHALL include `glama.json` with metadata for glama.ai/mcp registry.

#### Scenario: glama.json contains required fields
- **WHEN** glama.ai indexes the repository
- **THEN** file contains `name`, `description`, `version`, `repository`, `install`, and `capabilities` fields

### Requirement: MCP server entry point registered in pyproject.toml

The package SHALL register the MCP server as an entry point for MCP client discovery.

#### Scenario: Entry point is discoverable
- **WHEN** an MCP client queries installed packages for `mcp.servers` entry points
- **THEN** `nornweave` entry point points to `nornweave.huginn.server:serve`

#### Scenario: Entry point is already configured
- **WHEN** inspecting pyproject.toml
- **THEN** `[project.entry-points."mcp.servers"]` section contains `nornweave = "nornweave.huginn.server:serve"`

### Requirement: Integration tests verify MCP server functionality

The test suite SHALL include integration tests for MCP server operations.

#### Scenario: Test resource fetch
- **WHEN** integration test calls `email://inbox/{id}/recent` resource
- **THEN** test verifies response structure and content

#### Scenario: Test tool execution
- **WHEN** integration test calls `create_inbox` tool
- **THEN** test verifies inbox is created via underlying API

#### Scenario: Tests use mock API server
- **WHEN** MCP integration tests run
- **THEN** they target a mock HTTP server (not real NornWeave instance)
