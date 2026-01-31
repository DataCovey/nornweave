# Architecture Overview

NornWeave uses a thematic architecture inspired by Norse mythology.

| Component        | Name              | Purpose                                      |
|-----------------|-------------------|----------------------------------------------|
| Storage layer   | **Urdr** (The Well) | Database adapters (PostgreSQL, SQLite)     |
| Ingestion       | **Verdandi** (The Loom) | Webhook processing, HTML to Markdown   |
| API & outbound  | **Skuld** (The Prophecy) | REST API, sending, rate limiting    |
| Gateway         | **Yggdrasil**     | API router connecting all providers          |
| MCP             | **Huginn & Muninn** | Read/write tools for AI agents            |

## Data flow

1. **Inbound**: Provider webhook → Yggdrasil (webhook route) → Verdandi (parse/sanitize) → Urdr (store).
2. **Outbound**: Client → Yggdrasil (REST) → Skuld (send) → Provider.
3. **Agents**: MCP client → Huginn/Muninn (resources/tools) → Yggdrasil/Urdr/Skuld.

## Abstraction layers

- **Storage**: `StorageInterface` (Urdr). Implementations: Postgres, SQLite.
- **Email**: `EmailProvider` (BYOP). Implementations: Mailgun, SES, SendGrid, Resend.

Configuration (e.g. `DB_DRIVER`, `EMAIL_PROVIDER`) selects the implementation at runtime.
