---
title: NornWeave Documentation
description: "Complete documentation for NornWeave - learn how to set up virtual inboxes, configure email providers, and integrate AI agents with the REST API and MCP."
cascade:
  type: docs
keywords:
  - NornWeave documentation
  - email API documentation
  - MCP integration guide
  - REST API reference
  - AI agent email setup
sitemap_priority: 0.9
sitemap_changefreq: weekly
---

Welcome to the NornWeave documentation. Learn how to set up and use the Inbox-as-a-Service API for your AI agents.

<p style="text-align: center;">
  <img src="/images/logo-big-blue.png" alt="NornWeave" style="width: 50%; max-width: 50%; height: auto;">
</p>

## Getting Started

{{< cards >}}
  {{< card link="getting-started" title="Getting Started" icon="play" subtitle="Installation, configuration, and your first inbox" >}}
  {{< card link="concepts" title="Concepts" icon="academic-cap" subtitle="Understand NornWeave's architecture and design" >}}
  {{< card link="api" title="API Reference" icon="code" subtitle="REST API and MCP integration documentation" >}}
  {{< card link="guides" title="Provider Guides" icon="book-open" subtitle="Setup guides for Mailgun, SendGrid, SES, and more" >}}
{{< /cards >}}

## Architecture Overview

| Component | Name | Purpose |
|-----------|------|---------|
| Storage Layer | **Urdr** (The Well) | Database adapters (PostgreSQL, SQLite) |
| Ingestion Engine | **Verdandi** (The Loom) | Webhook processing, HTML to Markdown |
| API & Outbound | **Skuld** (The Prophecy) | REST API, email sending, rate limiting |
| Gateway | **Yggdrasil** | API router connecting all providers |
| MCP Tools | **Huginn & Muninn** | Read/write tools for AI agents |

For detailed data flows and sequence diagrams, see [Concepts → Architecture]({{< relref "concepts/architecture" >}}).

## Supported Mail Providers

| Provider | Sending | Receiving | Auto-Route Setup |
|----------|---------|-----------|------------------|
| Mailgun | Yes | Yes | Yes |
| AWS SES | Yes | Yes | Manual |
| SendGrid | Yes | Yes | Yes |
| Resend | Yes | Yes | Yes |
