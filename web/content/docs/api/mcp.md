---
title: MCP Integration
weight: 2
---

NornWeave exposes an MCP (Model Context Protocol) server that allows Claude, Cursor, and other MCP-compatible clients to interact with email directly.

## Configuration

Add NornWeave to your MCP client configuration:

### Cursor / Claude Desktop

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

{{< callout type="info" >}}
Make sure NornWeave is installed and the API server is running before using MCP.
{{< /callout >}}

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

**From:** bob@gmail.com  
**Date:** 2025-01-31 10:00

Hi, how much does your service cost?

---

**From:** support@mail.yourdomain.com  
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
| `recipient` | string | Yes | Email address to send to |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Markdown content |
| `thread_id` | string | No | Thread ID for replies |

**Example:**

```
Send an email to bob@gmail.com with subject "Thanks for your interest" 
saying "We'd love to schedule a demo. Are you available next week?"
```

{{< callout type="tip" >}}
When `thread_id` is provided, NornWeave handles all threading headers automatically.
{{< /callout >}}

### search_email

Find relevant messages in your inboxes.

**Arguments:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `limit` | number | No | Max results (default: 10) |

**Example:**

```
Search for emails about "invoice" from last week
```

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
This tool is experimental and uses long-polling. It may not be suitable for all use cases.
{{< /callout >}}

## Usage Examples

### Natural Language with Claude

Once configured, you can interact with NornWeave using natural language:

> "Check my support inbox for any new messages"

> "Reply to the pricing question thread saying we offer a 14-day free trial"

> "Create a new inbox for handling sales inquiries"

> "Search for any emails mentioning 'refund' in the last month"

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
            "recipient": thread.participants[0],
            "subject": f"Re: {thread.subject}",
            "body": response,
            "thread_id": thread.id
        })
```

## Troubleshooting

### MCP Server Not Found

Ensure NornWeave is installed and in your PATH:

```bash
pip install nornweave
which nornweave
```

### Connection Refused

Make sure the NornWeave API server is running:

```bash
curl http://localhost:8000/health
```

### Authentication Errors

Verify your API key is set correctly in the environment or configuration.
