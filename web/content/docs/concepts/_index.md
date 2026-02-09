---
title: NornWeave Concepts & Architecture
description: "Understand NornWeave's Norse mythology-inspired architecture. Learn about Inboxes, Threads, Messages, storage adapters, and the BYOP email provider model."
weight: 2
keywords:
  - NornWeave architecture
  - email threading
  - inbox abstraction
  - storage adapter
  - email provider abstraction
sitemap_priority: 0.7
sitemap_changefreq: monthly
---

NornWeave uses a thematic architecture inspired by Norse mythology. This section explains the core concepts and how they map to the system's components.

## The Norse Connection

In Norse mythology, the **Norns** (Urdr, Verdandi, and Skuld) dwell at the base of **Yggdrasil**, the World Tree. They draw water from the Well of Urdr to nourish the tree and prevent it from rotting, while simultaneously weaving the tapestry of fate for all beings.

Email is often a chaotic, rotting mess of raw HTML and disconnected messages. **NornWeave** acts as the Norns for AI Agents:

- It takes the raw "water" (incoming data streams)
- It "weaves" disconnected messages into coherent **Threads** (the Tapestry)
- It nourishes the Agent (Yggdrasil) with clean, structured context so it can survive and function at the center of the user's workflow

And this translates to the main components of the software architecture:

- **Urdr (The Well)** represents "The Past." The database holds the immutable history of what has already happened (logs, stored messages).

- **Verdandi (The Loom)** represents "The Present" or "Becoming." This engine processes incoming webhooks in real-time, parsing raw HTML into clean Markdown threads.

- **Skuld (The Prophecy)** represents "The Future" or "Debt." This layer handles what *shall be* done: sending emails, scheduling replies, and managing API credits/rate limits.

- **Yggdrasil** is the central axis that connects all disparate worlds (Email Providers like Mailgun, SES) into one unified structure.

- **Huginn & Muninn** are Odin's ravens (Thought and Memory). These are the specific MCP tools that fly out to retrieve knowledge for the Agent.

## Core Entities

### Inbox

An **Inbox** represents a virtual email address that your AI agent can use. Each inbox:

- Has a unique email address (e.g., `support@mail.yourdomain.com`)
- Can receive and send emails
- Contains multiple threads

### Thread

A **Thread** groups related messages into a conversation. NornWeave automatically:

- Groups messages using `In-Reply-To` and `References` headers
- Maintains conversation context
- Formats threads for LLM consumption (with `user` and `assistant` roles)

### Message

A **Message** is a single email within a thread. Each message has:

- **Raw content**: Original HTML/text from the email
- **Clean content**: LLM-ready Markdown (HTML converted, reply cruft removed)
- **Direction**: `INBOUND` (received) or `OUTBOUND` (sent)
- **Metadata**: Headers, timestamps, and attachments

## Abstraction Layers

NornWeave uses two critical abstraction layers for flexibility:

### Storage Adapter Layer (Urdr)

The system uses a `StorageInterface` to persist data, not hardcoded to any specific database.

| Implementation | Description | Use Case |
|----------------|-------------|----------|
| `SQLiteAdapter` | SQLite — zero-config default | Development, small deployments |
| `PostgresAdapter` | PostgreSQL with full features | Production |

### Provider Adapter Layer (BYOP Model)

The "Bring Your Own Provider" model abstracts the email sending/receiving mechanism.

| Provider | Sending | Receiving | Auto-Route Setup |
|----------|---------|-----------|------------------|
| Mailgun | Yes | Yes (webhooks) | Yes |
| AWS SES | Yes | Yes (webhooks) | Manual |
| SendGrid | Yes | Yes (webhooks) | Yes |
| Resend | Yes | Yes (webhooks) | Yes |
| IMAP/SMTP | Yes (SMTP) | Yes (IMAP polling) | N/A |

## Learn More

{{< cards >}}
  {{< card link="architecture" title="Architecture" icon="template" subtitle="Detailed system architecture with diagrams" >}}
  {{< card link="../api" title="API Reference" icon="code" subtitle="REST and MCP documentation" >}}
{{< /cards >}}
