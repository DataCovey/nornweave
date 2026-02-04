---
title: MCP Integration Guide
description: "Connect NornWeave to Claude, Cursor, and other MCP clients. Resources, tools, and natural language examples for AI agent email automation."
weight: 2
keywords:
  - MCP server
  - Claude MCP integration
  - Cursor MCP
  - Model Context Protocol
  - AI agent email
  - MCP tools
  - MCP resources
  - email attachments MCP
  - AI file attachments
sitemap_priority: 0.85
sitemap_changefreq: weekly
---

NornWeave exposes an MCP (Model Context Protocol) server that allows Claude, Cursor, LangChain, and other MCP-compatible clients to interact with email directly.

## Installation

Install NornWeave with MCP support:

```bash
pip install nornweave[mcp]
```

## Configuration

Add NornWeave to your MCP client configuration:

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave",
      "args": ["mcp"],
      "env": {
        "NORNWEAVE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

{{< callout type="info" >}}
Make sure the NornWeave API server is running before using MCP. Start it with `nornweave api`.
{{< /callout >}}

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NORNWEAVE_API_URL` | NornWeave REST API URL | `http://localhost:8000` |
| `NORNWEAVE_API_KEY` | API key for authentication | (none) |

## Transports

NornWeave MCP server supports three transport types:

### stdio (Default)

For Claude Desktop, Cursor, and local CLI usage:

```bash
nornweave mcp
# or explicitly:
nornweave mcp --transport stdio
```

### SSE (Server-Sent Events)

For web-based MCP clients and browser integrations:

```bash
nornweave mcp --transport sse --host 0.0.0.0 --port 3000
```

### HTTP (Streamable)

For cloud deployments, load balancing, and LangChain integration:

```bash
nornweave mcp --transport http --host 0.0.0.0 --port 3000
```

## Resources (Read-Only)

MCP Resources provide read-only access to email data.

### Recent Threads

```
email://inbox/{inbox_id}/recent
```

Returns the last 10 thread summaries for an inbox.

**Example Response:**

```json
[
  {
    "id": "th_123",
    "subject": "Re: Pricing Question",
    "last_message_at": "2025-01-31T10:05:00Z",
    "message_count": 2,
    "participants": ["bob@gmail.com", "support@mail.yourdomain.com"]
  }
]
```

### Thread Content

```
email://thread/{thread_id}
```

Returns the full thread content in Markdown format, optimized for LLM context.

**Example Response:**

```markdown
## Thread: Re: Pricing Question

**From:** bob@gmail.com ←
**Date:** 2025-01-31 10:00

Hi, how much does your service cost?

---

**From:** support@mail.yourdomain.com →
**Date:** 2025-01-31 10:05

Thanks for reaching out! Our pricing starts at $20/month.
```

## Tools (Actions)

MCP Tools allow AI agents to perform actions.

### create_inbox

Provision a new email address for the agent.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Display name for the inbox |
| `username` | string | Yes | Local part of email address |

**Example:**

```
Create a new inbox called "Sales Bot" with username "sales"
```

### send_email

Send an email, automatically converting Markdown to HTML.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `inbox_id` | string | Yes | Inbox ID to send from |
| `recipient` | string | Yes | Email address to send to |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Markdown content |
| `thread_id` | string | No | Thread ID for replies |

**Example:**

```
Send an email to bob@gmail.com with subject "Thanks for your interest" 
saying "We'd love to schedule a demo. Are you available next week?"
```

{{< callout type="info" >}}
When `thread_id` is provided, NornWeave handles all threading headers automatically.
{{< /callout >}}

### search_email

Find relevant messages in your inboxes.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `inbox_id` | string | Yes | Inbox to search in |
| `limit` | number | No | Max results (default: 10) |

**Example:**

```
Search for emails about "invoice" in the support inbox
```

### send_email_with_attachments

Send an email with file attachments.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `inbox_id` | string | Yes | Inbox ID to send from |
| `recipient` | string | Yes | Email address to send to |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Markdown content |
| `attachments` | array | Yes | List of attachments |
| `thread_id` | string | No | Thread ID for replies |

**Attachment Object:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `filename` | string | Yes | Original filename |
| `content_type` | string | Yes | MIME type (e.g., `application/pdf`) |
| `content` | string | Yes | Base64-encoded file content |

**Example:**

```
Send an email to client@example.com with a PDF attachment 
Subject: "Contract for Review"
Body: "Please review the attached contract."
Attach: contract.pdf (application/pdf)
```

### list_attachments

List attachments for a message, thread, or inbox.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `message_id` | string | One of these | Filter by message |
| `thread_id` | string | One of these | Filter by thread |
| `inbox_id` | string | One of these | Filter by inbox |

**Example:**

```
List all attachments for message msg_001
```

**Returns:**

```json
[
  {
    "id": "att_789",
    "message_id": "msg_001",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "size": 102400
  }
]
```

### get_attachment_content

Get the content of an attachment.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `attachment_id` | string | Yes | Attachment ID |
| `format` | string | No | `base64` (default) or `binary` |

**Example:**

```
Get the content of attachment att_789 as base64
```

**Returns (base64):**

```json
{
  "content": "JVBERi0xLjQKJeLjz9M...",
  "content_type": "application/pdf",
  "filename": "document.pdf"
}
```

{{< callout type="info" >}}
For MCP, `base64` format is recommended as it's easier to handle in JSON-based protocols.
{{< /callout >}}

### wait_for_reply (Experimental)

Block execution until a new email arrives in a thread. Useful for synchronous agent scripts.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_id` | string | Yes | Thread to wait on |
| `timeout_seconds` | number | No | Max wait time (default: 300) |

**Example:**

```
Wait for a reply to thread th_123 for up to 5 minutes
```

{{< callout type="warning" >}}
This tool is experimental and uses polling. It may not be suitable for all use cases.
{{< /callout >}}

## Usage Examples

### Natural Language with Claude

Once configured, you can interact with NornWeave using natural language:

> "Check my support inbox for any new messages"

> "Reply to the pricing question thread saying we offer a 14-day free trial"

> "Create a new inbox for handling sales inquiries"

> "Search for any emails mentioning 'refund' in the support inbox"

### Automated Agent Script

```python
# Pseudo-code for an agent workflow

# 1. Check for new messages
recent = mcp.resource("email://inbox/ibx_support/recent")

for thread in recent:
    if is_urgent(thread):
        # 2. Get full context
        content = mcp.resource(f"email://thread/{thread.id}")
        
        # 3. Generate response
        response = llm.generate(
            prompt=f"Respond to this email:\n{content}"
        )
        
        # 4. Send reply
        mcp.tool("send_email", {
            "inbox_id": "ibx_support",
            "recipient": thread.participants[0],
            "subject": f"Re: {thread.subject}",
            "body": response,
            "thread_id": thread.id
        })
```

## MCP Registries

NornWeave is available on popular MCP registries:

- [Smithery.ai](https://smithery.ai/server/nornweave)
- [mcp-get.com](https://mcp-get.com/packages/nornweave)
- [Glama.ai](https://glama.ai/mcp/servers/nornweave)

## Troubleshooting

### MCP Server Not Found

Ensure NornWeave is installed with MCP support:

```bash
pip install nornweave[mcp]
which nornweave
```

### Connection Refused

Make sure the NornWeave API server is running:

```bash
# Start the API server
nornweave api

# Verify it's running
curl http://localhost:8000/health
```

### Authentication Errors

Verify your API key is set correctly:

```bash
export NORNWEAVE_API_KEY=your-api-key
nornweave mcp
```

Or in your MCP client configuration:

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave",
      "args": ["mcp"],
      "env": {
        "NORNWEAVE_API_URL": "http://localhost:8000",
        "NORNWEAVE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### SSE/HTTP Transport Issues

For network transports, ensure the port is available:

```bash
# Check if port 3000 is in use
lsof -i :3000

# Use a different port
nornweave mcp --transport sse --port 3001
```
