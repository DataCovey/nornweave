# MCP (Model Context Protocol)

NornWeave exposes an MCP server so that Cursor, Claude Desktop, and other MCP clients can read and act on email.

## Resources (read-only)

- `email://inbox/{id}/recent` — List of last 10 thread summaries
- `email://thread/{id}` — Full thread content in Markdown

## Tools

- `create_inbox` — Provision a new email address (args: `name`, `username`)
- `send_email` — Send an email (args: `recipient`, `subject`, `body`, optional `thread_id`)
- `search_email` — Search inbox (args: `query`, `limit`)
- `wait_for_reply` — Block until a reply arrives in a thread (experimental; args: `thread_id`, `timeout_seconds`)

## Configuration

In Cursor or Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave",
      "args": ["--api-url", "http://localhost:8000"]
    }
  }
}
```

Or use the entry point `nornweave` (MCP server) with your API URL. See [Getting Started](getting-started/quickstart.md) to run the API first.
