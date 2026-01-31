---
title: REST API
weight: 1
---

The NornWeave REST API provides full control over inboxes, threads, and messages.

## Authentication

All requests require an API key in the `Authorization` header:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Base URL

```
http://localhost:8000/v1
```

---

## Inboxes

### Create an Inbox

Create a new virtual inbox for your AI agent.

```http
POST /v1/inboxes
```

**Request Body:**

```json
{
  "name": "Support Agent",
  "email_username": "support"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Display name for the inbox |
| `email_username` | string | Yes | Local part of the email address |

**Response:**

```json
{
  "id": "ibx_abc123",
  "name": "Support Agent",
  "email_address": "support@mail.yourdomain.com",
  "created_at": "2025-01-31T12:00:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Support Agent", "email_username": "support"}'
```

{{< callout type="info" >}}
If using Mailgun or SendGrid with auto-route setup enabled, NornWeave will automatically create the routing rule in your provider.
{{< /callout >}}

### Get an Inbox

```http
GET /v1/inboxes/{inbox_id}
```

**Response:**

```json
{
  "id": "ibx_abc123",
  "name": "Support Agent",
  "email_address": "support@mail.yourdomain.com",
  "created_at": "2025-01-31T12:00:00Z"
}
```

### Delete an Inbox

```http
DELETE /v1/inboxes/{inbox_id}
```

**Response:** `204 No Content`

---

## Threads

Threads are the core unit for LLM context. They group related messages into a conversation format.

### Get a Thread

```http
GET /v1/threads/{thread_id}
```

**Response:**

```json
{
  "id": "th_123",
  "inbox_id": "ibx_abc123",
  "subject": "Re: Pricing Question",
  "last_message_at": "2025-01-31T10:05:00Z",
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "author": "bob@gmail.com",
      "content": "Hi, how much does your service cost?",
      "timestamp": "2025-01-31T10:00:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "author": "support@mail.yourdomain.com",
      "content": "Thanks for reaching out! Our pricing starts at $20/month.",
      "timestamp": "2025-01-31T10:05:00Z"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `role` | `user` for inbound messages, `assistant` for outbound |
| `content` | Clean Markdown content (HTML converted, cruft removed) |

{{< callout type="tip" >}}
The `role` field maps directly to LLM chat formats, making it easy to use thread content as conversation history.
{{< /callout >}}

---

## Messages

### Send a Message

Send a new email or reply to an existing thread.

```http
POST /v1/messages
```

**Request Body:**

```json
{
  "inbox_id": "ibx_abc123",
  "to": ["client@gmail.com"],
  "subject": "Hello from NornWeave",
  "body": "This is **Markdown** content that will be converted to HTML.",
  "reply_to_thread_id": "th_123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inbox_id` | string | Yes | Inbox to send from |
| `to` | array | Yes | Recipient email addresses |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Markdown content |
| `reply_to_thread_id` | string | No | Thread ID for replies |

**Response:**

```json
{
  "id": "msg_003",
  "thread_id": "th_123",
  "inbox_id": "ibx_abc123",
  "direction": "OUTBOUND",
  "to": ["client@gmail.com"],
  "subject": "Hello from NornWeave",
  "content_clean": "This is **Markdown** content that will be converted to HTML.",
  "created_at": "2025-01-31T12:00:00Z"
}
```

{{< callout type="info" >}}
When `reply_to_thread_id` is provided, NornWeave automatically:
- Sets proper `In-Reply-To` and `References` headers
- Adds the message to the existing thread
- Maintains conversation threading in email clients
{{< /callout >}}

### Get a Message

```http
GET /v1/messages/{message_id}
```

**Response:**

```json
{
  "id": "msg_001",
  "thread_id": "th_123",
  "inbox_id": "ibx_abc123",
  "direction": "INBOUND",
  "from": "bob@gmail.com",
  "to": ["support@mail.yourdomain.com"],
  "subject": "Pricing Question",
  "content_raw": "<html>...",
  "content_clean": "Hi, how much does your service cost?",
  "metadata": {
    "message_id": "<abc123@mail.gmail.com>",
    "headers": {}
  },
  "created_at": "2025-01-31T10:00:00Z"
}
```

---

## Search

Search for messages across your inboxes.

```http
POST /v1/search
```

**Request Body:**

```json
{
  "query": "pricing",
  "inbox_id": "ibx_abc123",
  "limit": 10
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `inbox_id` | string | No | Limit to specific inbox |
| `limit` | number | No | Max results (default: 10) |

**Response:**

```json
{
  "results": [
    {
      "message_id": "msg_001",
      "thread_id": "th_123",
      "subject": "Pricing Question",
      "snippet": "Hi, how much does your service cost?",
      "score": 0.95
    }
  ],
  "total": 1
}
```

{{< callout type="info" >}}
**Phase 1**: Search uses SQL `ILIKE` for simple text matching.  
**Phase 3**: Search will use vector embeddings for semantic search.
{{< /callout >}}

---

## Webhooks

These endpoints receive inbound email from your provider. Configure them in your provider's dashboard.

### Mailgun

```http
POST /webhooks/mailgun
```

### SendGrid

```http
POST /webhooks/sendgrid
```

### AWS SES

```http
POST /webhooks/ses
```

See [Provider Guides](../../guides) for setup instructions.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "not_found",
    "message": "Thread not found",
    "details": {}
  }
}
```

| Status Code | Description |
|-------------|-------------|
| `400` | Bad request (invalid parameters) |
| `401` | Unauthorized (missing/invalid API key) |
| `404` | Resource not found |
| `429` | Rate limited |
| `500` | Internal server error |
