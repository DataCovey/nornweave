---
title: NornWeave API Reference
description: "Complete API documentation for NornWeave. REST endpoints and MCP integration for inboxes, threads, messages, and search operations."
weight: 3
keywords:
  - NornWeave API
  - REST API reference
  - MCP API
  - email API endpoints
sitemap_priority: 0.85
sitemap_changefreq: weekly
---

NornWeave provides two ways to interact with your email data:

{{< cards >}}
  {{< card link="rest" title="REST API" icon="code" subtitle="Traditional HTTP endpoints for all operations" >}}
  {{< card link="mcp" title="MCP Integration" icon="chip" subtitle="Model Context Protocol for AI clients" >}}
{{< /cards >}}

## Authentication

{{< callout type="info" >}}
API key authentication is **not yet enforced**. All endpoints are currently accessible without credentials. The `API_KEY` environment variable is reserved for a future release.
{{< /callout >}}

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
