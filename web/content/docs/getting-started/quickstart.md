---
title: NornWeave Quickstart Tutorial
description: "Create your first AI agent inbox, receive emails via webhook, and send replies in minutes. Step-by-step quickstart guide with code examples."
weight: 3
keywords:
  - NornWeave quickstart
  - AI inbox tutorial
  - email API getting started
  - create inbox API
  - send email REST API
sitemap_priority: 0.9
sitemap_changefreq: weekly
---

This guide walks you through creating your first inbox, receiving an email, and sending a reply.

## Prerequisites

- NornWeave is [installed and running](../installation)
- You have your API key from the [configuration](../configuration)
- [ngrok](https://ngrok.com/) installed (for exposing your local server to webhooks)

## Expose Your Local Server

Email providers need a public URL to send webhooks. Use ngrok to expose your local NornWeave server:

```bash
ngrok http 8000
```

You'll see output like:

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

{{< callout type="info" >}}
Copy your ngrok URL (e.g., `https://abc123.ngrok-free.app`). You'll use this to configure webhooks in your email provider.
{{< /callout >}}

Keep ngrok running in a separate terminal while you work through this guide.

## Create an Inbox

Create a virtual inbox for your AI agent:

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Agent",
    "email_username": "support"
  }'
```

Response:

```json
{
  "id": "ibx_abc123",
  "name": "Support Agent",
  "email_address": "support@mail.yourdomain.com",
  "created_at": "2025-01-31T12:00:00Z"
}
```

{{< callout type="info" >}}
The email address format depends on your provider configuration. The `email_username` becomes the local part before the `@`.
{{< /callout >}}

## Configure Webhook

Point your email provider's inbound webhook to your ngrok URL:

| Provider | Webhook URL |
|----------|-------------|
| Mailgun | `https://abc123.ngrok-free.app/webhooks/mailgun` |
| SendGrid | `https://abc123.ngrok-free.app/webhooks/sendgrid` |
| AWS SES | `https://abc123.ngrok-free.app/webhooks/ses` |

{{< callout type="warning" >}}
Replace `abc123.ngrok-free.app` with your actual ngrok URL. The URL changes each time you restart ngrok (unless you have a paid plan with reserved domains).
{{< /callout >}}

See [Provider Guides](../../guides) for detailed provider-specific setup instructions.

## Receive an Email

When someone sends an email to your inbox address, NornWeave:

1. Receives the webhook from your provider
2. Parses the HTML into clean Markdown
3. Groups the message into a thread
4. Stores it in the database

## List Messages

View all messages in your inbox:

```bash
curl "http://localhost:8000/v1/messages?inbox_id=ibx_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:

```json
{
  "items": [
    {
      "id": "msg_001",
      "thread_id": "th_123",
      "inbox_id": "ibx_abc123",
      "direction": "inbound",
      "content_clean": "Hi, I have a question about your pricing.",
      "metadata": {
        "From": "Alice <alice@example.com>",
        "Subject": "Pricing Question"
      },
      "created_at": "2025-01-31T10:00:00Z"
    }
  ],
  "count": 1
}
```

{{< callout type="info" >}}
Messages include `direction` to distinguish between `inbound` (received) and `outbound` (sent) emails. The `content_clean` field contains the message body converted to Markdown.
{{< /callout >}}

## Search Messages

Search for messages containing specific text:

```bash
curl -X POST "http://localhost:8000/v1/search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_abc123",
    "query": "pricing"
  }'
```

Response:

```json
{
  "items": [
    {
      "id": "msg_001",
      "thread_id": "th_123",
      "inbox_id": "ibx_abc123",
      "direction": "inbound",
      "content_clean": "Hi, I have a question about your pricing.",
      "created_at": "2025-01-31T10:00:00Z"
    }
  ],
  "count": 1,
  "query": "pricing"
}
```

{{< callout type="info" >}}
Search finds messages by matching text in the message content. Use the `thread_id` from the results to reply to a specific conversation.
{{< /callout >}}

## Send an Email

Send a new email (creates a new thread):

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_abc123",
    "to": ["alice@example.com"],
    "subject": "Welcome to our service!",
    "body": "Hi Alice!\n\nThanks for signing up. Let us know if you have any questions."
  }'
```

Response:

```json
{
  "id": "msg_002",
  "thread_id": "th_456",
  "provider_message_id": "<abc123@mail.yourdomain.com>",
  "status": "sent"
}
```

## Read a Thread

Retrieve a conversation thread (optimized for LLM context):

```bash
curl http://localhost:8000/v1/threads/th_123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:

```json
{
  "id": "th_123",
  "subject": "Re: Pricing Question",
  "messages": [
    {
      "role": "user",
      "author": "bob@gmail.com",
      "content": "Hi, how much does your service cost?",
      "timestamp": "2025-01-31T10:00:00Z"
    },
    {
      "role": "assistant",
      "author": "support@mail.yourdomain.com",
      "content": "Thanks for reaching out! Our pricing starts at $20/month.",
      "timestamp": "2025-01-31T10:05:00Z"
    }
  ]
}
```

{{< callout type="info" >}}
The thread format uses `role: "user"` for incoming emails and `role: "assistant"` for outgoing emails, making it easy to use with LLM chat APIs.
{{< /callout >}}

## Reply to a Thread

To reply to an existing conversation, include the `reply_to_thread_id`:

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_abc123",
    "reply_to_thread_id": "th_123",
    "to": ["alice@example.com"],
    "subject": "Re: Pricing Question",
    "body": "Hi there!\n\nThanks for your interest! Our pricing starts at **$20/month** for the basic plan."
  }'
```

Response:

```json
{
  "id": "msg_003",
  "thread_id": "th_123",
  "provider_message_id": "<def456@mail.yourdomain.com>",
  "status": "sent"
}
```

{{< callout type="info" >}}
NornWeave automatically converts Markdown to HTML for the email body and handles threading headers (`In-Reply-To`, `References`) so replies appear correctly in the recipient's email client.
{{< /callout >}}

## Using MCP

If you're using Claude, Cursor, or another MCP-compatible client, you can interact with NornWeave directly.

First, install MCP support:

```bash
pip install nornweave[mcp]
```

Add to your MCP configuration:

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

Then use natural language:

> "Check my support inbox for new messages"
> "Reply to the pricing question thread saying we offer a 14-day free trial"

See [MCP Integration](../../api/mcp) for more details.

## Next Steps

{{< cards >}}
  {{< card link="../../api/rest" title="REST API Reference" icon="code" subtitle="Complete API documentation" >}}
  {{< card link="../../api/mcp" title="MCP Integration" icon="chip" subtitle="Connect with Claude and Cursor" >}}
  {{< card link="../../concepts" title="Concepts" icon="academic-cap" subtitle="Learn about NornWeave's architecture" >}}
{{< /cards >}}
