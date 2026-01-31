---
title: API Reference
weight: 3
---

NornWeave provides two ways to interact with your email data:

{{< cards >}}
  {{< card link="rest" title="REST API" icon="code" subtitle="Traditional HTTP endpoints for all operations" >}}
  {{< card link="mcp" title="MCP Integration" icon="chip" subtitle="Model Context Protocol for AI clients" >}}
{{< /cards >}}

## Authentication

All API requests require authentication using an API key in the `Authorization` header:

```bash
Authorization: Bearer YOUR_API_KEY
```

## Base URL

The REST API is served at:

```
http://localhost:8000/v1
```

## Quick Reference

### Inboxes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/inboxes` | Create an inbox |
| `GET` | `/v1/inboxes/{id}` | Get an inbox |
| `DELETE` | `/v1/inboxes/{id}` | Delete an inbox |

### Threads

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/threads/{id}` | Get a thread (LLM-formatted) |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/messages` | Send a message |
| `GET` | `/v1/messages/{id}` | Get a message |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/search` | Search messages |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks/mailgun` | Mailgun inbound |
| `POST` | `/webhooks/sendgrid` | SendGrid inbound |
| `POST` | `/webhooks/ses` | AWS SES inbound |
