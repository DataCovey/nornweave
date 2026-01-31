---
title: Concepts
weight: 2
---

NornWeave uses a thematic architecture inspired by Norse mythology. This section explains the core concepts and how they map to the system's components.

## The Norse Connection

In Norse mythology, the **Norns** (Urdr, Verdandi, and Skuld) dwell at the base of **Yggdrasil**, the World Tree. They draw water from the Well of Urdr to nourish the tree and prevent it from rotting, while simultaneously weaving the tapestry of fate for all beings.

Email is often a chaotic, rotting mess of raw HTML and disconnected messages. **NornWeave** acts as the Norns for AI Agents:

- It takes the raw "water" (incoming data streams)
- It "weaves" disconnected messages into coherent **Threads** (the Tapestry)
- It nourishes the Agent (Yggdrasil) with clean, structured context so it can survive and function at the center of the user's workflow

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

### Storage Adapter Layer

The system uses a `StorageInterface` to persist data, not hardcoded to any specific database.

| Implementation | Description | Use Case |
|----------------|-------------|----------|
| `PostgresAdapter` | PostgreSQL with full features | Production |
| `SQLiteAdapter` | SQLite for simplicity | Local development |

### Provider Adapter Layer (BYOP Model)

The "Bring Your Own Provider" model abstracts the email sending/receiving mechanism.

| Provider | Sending | Receiving | Auto-Route Setup |
|----------|---------|-----------|------------------|
| Mailgun | Yes | Yes | Yes |
| AWS SES | Yes | Yes | Manual |
| SendGrid | Yes | Yes | Yes |
| Resend | Yes | Yes | Yes |

## Learn More

{{< cards >}}
  {{< card link="architecture" title="Architecture" icon="template" subtitle="Detailed system architecture with diagrams" >}}
  {{< card link="../api" title="API Reference" icon="code" subtitle="REST and MCP documentation" >}}
{{< /cards >}}
