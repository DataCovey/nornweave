---
title: REST API Reference
description: "Complete REST API documentation for NornWeave. Endpoints for inboxes, threads, messages, and search with authentication, request/response examples."
weight: 1
keywords:
  - NornWeave REST API
  - email API endpoints
  - inbox API
  - thread API
  - message API
  - email search API
  - email attachments API
  - attachment storage
sitemap_priority: 0.85
sitemap_changefreq: weekly
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
  "summary": "Customer asked about pricing. Support replied with $20/month starting price.",
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
| `summary` | LLM-generated thread summary (null when summarization is disabled or not yet generated) |

{{< callout type="info" >}}
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

### List Messages

List and search messages with flexible filters.

```http
GET /v1/messages
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inbox_id` | string | One of these | Filter by inbox |
| `thread_id` | string | One of these | Filter by thread |
| `q` | string | No | Text search (subject, body, sender, attachment filenames) |
| `limit` | number | No | Max results (default: 50) |
| `offset` | number | No | Offset for pagination |

{{< callout type="warning" >}}
At least one of `inbox_id` or `thread_id` must be provided.
{{< /callout >}}

**Response:**

```json
{
  "items": [
    {
      "id": "msg_001",
      "thread_id": "th_123",
      "inbox_id": "ibx_abc123",
      "direction": "inbound",
      "provider_message_id": "<abc123@mail.gmail.com>",
      "subject": "Pricing Question",
      "from_address": "bob@gmail.com",
      "to_addresses": ["support@mail.yourdomain.com"],
      "cc_addresses": null,
      "bcc_addresses": null,
      "reply_to_addresses": null,
      "text": "Hi, how much does your service cost?",
      "html": "<p>Hi, how much does your service cost?</p>",
      "content_clean": "Hi, how much does your service cost?",
      "timestamp": "2025-01-31T10:00:00Z",
      "labels": [],
      "preview": "Hi, how much does your service cost?",
      "size": 1234,
      "in_reply_to": null,
      "references": null,
      "metadata": {},
      "created_at": "2025-01-31T10:00:00Z"
    }
  ],
  "count": 1,
  "total": 1
}
```

**Example:**

```bash
# List all messages in an inbox
curl "http://localhost:8000/v1/messages?inbox_id=ibx_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search for messages containing "invoice"
curl "http://localhost:8000/v1/messages?inbox_id=ibx_abc123&q=invoice" \
  -H "Authorization: Bearer YOUR_API_KEY"

# List messages in a specific thread
curl "http://localhost:8000/v1/messages?thread_id=th_123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

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
  "direction": "inbound",
  "provider_message_id": "<abc123@mail.gmail.com>",
  "subject": "Pricing Question",
  "from_address": "bob@gmail.com",
  "to_addresses": ["support@mail.yourdomain.com"],
  "cc_addresses": null,
  "bcc_addresses": null,
  "reply_to_addresses": null,
  "text": "Hi, how much does your service cost?",
  "html": "<p>Hi, how much does your service cost?</p>",
  "content_clean": "Hi, how much does your service cost?",
  "timestamp": "2025-01-31T10:00:00Z",
  "labels": [],
  "preview": "Hi, how much does your service cost?",
  "size": 1234,
  "in_reply_to": null,
  "references": null,
  "metadata": {},
  "created_at": "2025-01-31T10:00:00Z"
}
```

### Send a Message with Attachments

Send an email with file attachments.

```http
POST /v1/messages
```

**Request Body:**

```json
{
  "inbox_id": "ibx_abc123",
  "to": ["client@gmail.com"],
  "subject": "Contract for Review",
  "body": "Please review the attached contract.",
  "attachments": [
    {
      "filename": "contract.pdf",
      "content_type": "application/pdf",
      "content": "JVBERi0xLjQKJeLjz9M... (base64-encoded content)"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inbox_id` | string | Yes | Inbox to send from |
| `to` | array | Yes | Recipient email addresses |
| `subject` | string | Yes | Email subject |
| `body` | string | Yes | Markdown content |
| `attachments` | array | No | List of attachments |
| `attachments[].filename` | string | Yes | Original filename |
| `attachments[].content_type` | string | Yes | MIME type (e.g., `application/pdf`) |
| `attachments[].content` | string | Yes | Base64-encoded file content |

**Response:**

```json
{
  "id": "msg_003",
  "thread_id": "th_123",
  "inbox_id": "ibx_abc123",
  "direction": "OUTBOUND",
  "to": ["client@gmail.com"],
  "subject": "Contract for Review",
  "content_clean": "Please review the attached contract.",
  "attachments": [
    {
      "id": "att_789",
      "filename": "contract.pdf",
      "content_type": "application/pdf",
      "size": 102400
    }
  ],
  "created_at": "2025-01-31T12:00:00Z"
}
```

---

## Attachments

### List Attachments

List attachments, filtered by message, thread, or inbox.

```http
GET /v1/attachments
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | One of these | Filter by message |
| `thread_id` | string | One of these | Filter by thread |
| `inbox_id` | string | One of these | Filter by inbox |
| `limit` | number | No | Max results (default: 100) |
| `offset` | number | No | Offset for pagination |

{{< callout type="warning" >}}
Exactly one of `message_id`, `thread_id`, or `inbox_id` must be provided.
{{< /callout >}}

**Response:**

```json
{
  "items": [
    {
      "id": "att_789",
      "message_id": "msg_001",
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "created_at": "2025-01-31T10:00:00Z"
    }
  ],
  "count": 1
}
```

### Get Attachment Metadata

```http
GET /v1/attachments/{attachment_id}
```

**Response:**

```json
{
  "id": "att_789",
  "message_id": "msg_001",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 102400,
  "disposition": "attachment",
  "storage_backend": "local",
  "content_hash": "sha256:abc123...",
  "download_url": "/v1/attachments/att_789/content?token=...&expires=...",
  "created_at": "2025-01-31T10:00:00Z"
}
```

{{< callout type="info" >}}
For S3 and GCS storage backends, `download_url` will be a presigned URL directly to the cloud storage. For local and database storage, it's a signed URL to the NornWeave API.
{{< /callout >}}

### Download Attachment Content

```http
GET /v1/attachments/{attachment_id}/content
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | `binary` (default) or `base64` |
| `token` | string | Conditional | Signed URL token (for local/db storage) |
| `expires` | number | Conditional | Token expiry timestamp |

**Response (format=binary):**

Returns raw binary content with appropriate `Content-Type` and `Content-Disposition` headers.

**Response (format=base64):**

```json
{
  "content": "JVBERi0xLjQKJeLjz9M...",
  "content_type": "application/pdf",
  "filename": "document.pdf"
}
```

**Example:**

```bash
# Download as binary
curl -o document.pdf \
  "http://localhost:8000/v1/attachments/att_789/content?token=abc&expires=1234567890" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Download as base64 JSON
curl "http://localhost:8000/v1/attachments/att_789/content?format=base64&token=abc&expires=1234567890" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Search

Search for messages using the flexible message list endpoint.

```http
GET /v1/messages?inbox_id={inbox_id}&q={query}
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inbox_id` | string | One of these | Filter by inbox |
| `thread_id` | string | One of these | Filter by thread |
| `q` | string | Yes | Search query |
| `limit` | number | No | Max results (default: 50) |
| `offset` | number | No | Offset for pagination |

The search looks across:
- Email subject
- Email body (text)
- Sender address (`from_address`)
- Attachment filenames

**Response:**

```json
{
  "items": [
    {
      "id": "msg_001",
      "thread_id": "th_123",
      "inbox_id": "ibx_abc123",
      "subject": "Pricing Question",
      "from_address": "bob@gmail.com",
      "text": "Hi, how much does your service cost?",
      "content_clean": "Hi, how much does your service cost?",
      "created_at": "2025-01-31T10:00:00Z"
    }
  ],
  "count": 1,
  "total": 1
}
```

**Example:**

```bash
# Search in an inbox
curl "http://localhost:8000/v1/messages?inbox_id=ibx_abc123&q=pricing" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search within a thread
curl "http://localhost:8000/v1/messages?thread_id=th_123&q=contract" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search with pagination
curl "http://localhost:8000/v1/messages?inbox_id=ibx_abc123&q=invoice&limit=10&offset=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

{{< callout type="info" >}}
Search uses SQL `ILIKE` for case-insensitive text matching. Results include the `total` count for pagination support.
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
