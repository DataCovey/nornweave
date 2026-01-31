---
title: Architecture
weight: 1
---

NornWeave's architecture uses thematic naming inspired by Norse mythology, with each component having a clear technical purpose.

## Component Overview

| Layer | Name | Roles |
|-----------|---------------|-------------------|
| Storage Layer | **Urdr** (The Well) | Database adapters for persistence |
| Ingestion Engine | **Verdandi** (The Loom) | Webhook processing, HTML to Markdown parsing |
| API & Outbound | **Skuld** (The Prophecy) | REST API, email sending, rate limiting |
| API Gateway | **Yggdrasil** | Central router connecting all providers |
| MCP Tools | **Huginn & Muninn** | Read/write tools for AI agents |

### Component connections and actions

The diagram below shows how the main components connect and what actions they perform on each other.

```mermaid
flowchart LR
    subgraph external [External]
        Provider[Email Providers\nMailgun, SES, SendGrid, Resend]
        Agent[AI Agent\nREST or MCP client]
    end

    subgraph yggdrasil [Yggdrasil - Gateway]
        G[API Router]
    end

    subgraph verdandi [Verdandi - Ingestion]
        V[Parse webhook\nHTML→Markdown\nThreading]
    end

    subgraph urdr [Urdr - Storage]
        U[(PostgreSQL\nSQLite)]
    end

    subgraph skuld [Skuld - Outbound]
        S[Send email\nRate limit]
    end

    subgraph mcp [Huginn & Muninn]
        M[MCP read/write]
    end

    Provider -->|"POST /webhooks/{provider}"| G
    G -->|"route webhook"| V
    V -->|"store message & thread"| U
    Agent -->|"GET /v1/threads, POST /v1/messages"| G
    M -->|"calls API"| G
    G -->|"fetch thread/messages"| U
    G -->|"send message"| S
    S -->|"deliver via API"| Provider
    S -->|"persist sent message"| U
```

- **Inbound:** Provider sends webhook → Yggdrasil routes → Verdandi parses and threads → Urdr stores.
- **Read:** Agent (or MCP) calls API → Yggdrasil → Urdr returns thread/messages.
- **Reply:** Agent (or MCP) posts message → Yggdrasil → Skuld sends via provider and Urdr stores the sent message.

## System Architecture Diagram

```mermaid
flowchart TB
    subgraph providers [Email Providers]
        MG[Mailgun]
        SES[AWS SES]
        SG[SendGrid]
        RS[Resend]
    end
    
    subgraph yggdrasil [Yggdrasil - API Gateway]
        WH[Webhook Routes]
        API[REST API v1]
    end
    
    subgraph verdandi [Verdandi - Ingestion Engine]
        Parser[HTML Parser]
        Sanitizer[Cruft Remover]
        Threader[Threading Logic]
    end
    
    subgraph urdr [Urdr - Storage Layer]
        PG[(PostgreSQL)]
        SQLite[(SQLite)]
    end
    
    subgraph skuld [Skuld - Outbound Sender]
        Sender[Email Sender]
        RateLimiter[Rate Limiter]
    end
    
    subgraph mcp [Huginn & Muninn - MCP Tools]
        Resources[Resources]
        Tools[Tools]
    end
    
    providers --> WH
    WH --> verdandi
    verdandi --> urdr
    API --> urdr
    API --> skuld
    skuld --> providers
    mcp --> API
```

## Data Flow

### Inbound Email Flow

1. External user sends an email to your inbox address
2. Email provider (Mailgun, etc.) calls the webhook endpoint
3. **Yggdrasil** receives the webhook and routes to the appropriate handler
4. **Verdandi** parses the raw email:
   - Converts HTML to Markdown
   - Removes reply cruft ("On Jan 1, John wrote:")
   - Extracts attachments
5. **Verdandi** determines threading using `In-Reply-To` and `References` headers
6. **Urdr** stores the message and updates the thread

### Agent Reading Flow

1. AI Agent calls `GET /v1/threads/{id}` (or uses MCP)
2. **Yggdrasil** routes the request
3. **Urdr** fetches the thread and messages
4. Response formatted as LLM-ready conversation

### Agent Reply Flow

1. AI Agent calls `POST /v1/messages` (or uses MCP `send_email`)
2. **Yggdrasil** routes the request
3. **Skuld** processes the outbound message:
   - Converts Markdown to HTML
   - Adds threading headers
   - Applies rate limiting
4. **Skuld** sends via the configured provider
5. **Urdr** stores the sent message

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User as External User
    participant Provider as Email Provider
    participant Yggdrasil as Yggdrasil - API Gateway
    participant Verdandi as Verdandi - Ingestion Engine
    participant Urdr as Urdr - Storage
    participant Skuld as Skuld - Outbound Sender
    participant Agent as AI Agent

    Note over User,Agent: Inbound Email Flow
    User->>Provider: Sends email
    Provider->>Yggdrasil: POST /webhooks/{provider}
    Yggdrasil->>Verdandi: Parse raw email
    Verdandi->>Verdandi: HTML to Markdown
    Verdandi->>Urdr: Store message and thread
    
    Note over User,Agent: Agent Reading Flow
    Agent->>Yggdrasil: GET /v1/threads/{id}
    Yggdrasil->>Urdr: Fetch thread
    Urdr-->>Agent: Markdown conversation
    
    Note over User,Agent: Agent Reply Flow
    Agent->>Yggdrasil: POST /v1/messages
    Yggdrasil->>Skuld: Send email
    Skuld->>Provider: Deliver via API
    Provider->>User: Email delivered
```

## Database Schema

The storage layer enforces this schema through the `StorageAdapter`:

### Inboxes Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `email_address` | String | Unique email address |
| `name` | String | Display name |
| `provider_config` | JSON | Provider-specific metadata |
| `created_at` | Timestamp | Creation time |

### Threads Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `inbox_id` | UUID | Foreign key to Inbox |
| `subject` | Text | Thread subject |
| `last_message_at` | Timestamp | Last activity |
| `participant_hash` | String | Hash of participants for grouping |

### Messages Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `thread_id` | UUID | Foreign key to Thread |
| `inbox_id` | UUID | Foreign key to Inbox |
| `provider_message_id` | String | Message-ID header |
| `direction` | Enum | `INBOUND` or `OUTBOUND` |
| `content_raw` | Text | Original HTML/Text |
| `content_clean` | Text | LLM-ready Markdown |
| `metadata` | JSON | Headers, attachments, etc. |
| `created_at` | Timestamp | Message time |

## Directory Structure

The codebase follows the thematic naming:

```
src/nornweave/
├── core/           # Shared interfaces and config
├── urdr/           # Storage layer
│   └── adapters/   # PostgreSQL, SQLite implementations
├── verdandi/       # Ingestion engine
│   ├── parser.py   # HTML to Markdown
│   ├── sanitizer.py # Cruft removal
│   └── threading.py # Thread grouping
├── skuld/          # Outbound layer
│   ├── sender.py   # Email sending
│   └── rate_limiter.py
├── yggdrasil/      # API gateway
│   ├── app.py      # FastAPI application
│   └── routes/     # API endpoints
├── huginn/         # MCP resources
└── muninn/         # MCP tools
```
