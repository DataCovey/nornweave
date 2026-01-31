# NornWeave

**Open-source, self-hosted Inbox-as-a-Service API for AI Agents.**

Standard email APIs are stateless and built for transactional sending. NornWeave adds a **stateful layer** (Inboxes, Threads, History) and an **intelligent layer** (Markdown parsing, Semantic Search) to make email consumable by LLMs via REST or MCP.

## Features

- **Phase 1**: Virtual inboxes, webhook ingestion, storage (PostgreSQL/SQLite), sending (Mailgun, SES, SendGrid, Resend), API key auth
- **Phase 2**: HTML to Markdown, threading, MCP server (Huginn & Muninn), attachment extraction
- **Phase 3**: Semantic search (pgvector), rate limiting, outbound webhooks, multi-tenancy

## Quick Links

- [Installation](getting-started/installation.md)
- [Quickstart](getting-started/quickstart.md)
- [REST API](api/rest.md)
- [MCP](api/mcp.md)
- [Architecture](architecture/overview.md)
