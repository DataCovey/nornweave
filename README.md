<p align="center">
  <img src="web/static/images/Nornorna_spinner.jpg" alt="The Norns weaving fate at Yggdrasil" width="400">
</p>

<h1 align="center">NornWeave</h1>

<p align="center">
  <em>"Laws they made there, and life allotted / To the sons of men, and set their fates."</em><br>
  - Voluspa (The Prophecy of the Seeress), Poetic Edda, Stanza 20
</p>

<p align="center">
  <strong>Open-source, self-hosted Inbox-as-a-Service API for AI Agents</strong>
</p>

<p align="center">
  <a href="https://github.com/DataCovey/nornweave/actions"><img src="https://github.com/DataCovey/nornweave/workflows/CI/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/DataCovey/nornweave/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
</p>

---

## What is NornWeave?

Standard email APIs are stateless and built for transactional sending. **NornWeave** adds a **stateful layer** (Inboxes, Threads, History) and an **intelligent layer** (Markdown parsing, Semantic Search) to make email consumable by LLMs via REST or MCP.

In Norse mythology, the Norns (Urdr, Verdandi, and Skuld) dwell at the base of Yggdrasil, the World Tree. They weave the tapestry of fate for all beings. Similarly, NornWeave:

- Takes raw "water" (incoming email data streams)
- Weaves disconnected messages into coherent **Threads** (the Tapestry)
- Nourishes AI Agents with clean, structured context

## Features

### Foundation (The Mail Proxy)
- **Virtual Inboxes**: Create email addresses for your AI agents
- **Webhook Ingestion**: Receive emails from Mailgun, SES, SendGrid, Resend
- **IMAP/SMTP**: Poll existing mailboxes (IMAP) and send via SMTP for any provider or self-hosted server
- **Persistent Storage**: SQLite (default) or PostgreSQL with abstracted storage adapters
- **Email Sending**: Send replies through your configured provider

### Intelligence (The Agent Layer)
- **Content Parsing**: HTML to clean Markdown, cruft removal
- **Threading**: Automatic conversation grouping via email headers
- **Thread Summarization**: LLM-generated thread summaries (OpenAI, Anthropic, Gemini) for list views and token savings
- **MCP Server**: Connect directly to Claude, Cursor, and other MCP clients
- **Attachment Processing**: Extract text from PDFs and documents

### Enterprise (The Platform Layer)
- **Semantic Search**: Vector embeddings with pgvector
- **Real-time Webhooks**: Get notified of new messages
- **Rate Limiting**: Protect against runaway agents
- **Multi-Tenancy**: Organizations and projects

## Quick Start

### Install from PyPI

```bash
# Base installation (SQLite, Mailgun/SES/SendGrid/Resend)
pip install nornweave

# With IMAP/SMTP support (any mailbox)
pip install nornweave[smtpimap]

# With PostgreSQL support
pip install nornweave[postgres]

# With MCP server for AI agents
pip install nornweave[mcp]

# Full installation
pip install nornweave[all]
```

### Configure Your Email Domain

Create a `.env` file in the directory where you'll run the server:

```bash
# .env — minimum configuration for inbox creation
EMAIL_DOMAIN=mail.yourdomain.com   # your email provider's domain
```

> **Tip:** The domain depends on your provider (e.g. `mail.yourdomain.com` for Mailgun,
> `yourdomain.resend.app` for Resend). Without `EMAIL_DOMAIN`, inbox creation will fail.

See [Configuration](https://nornweave.datacovey.com/docs/getting-started/configuration/) for all available settings.

### Start the API Server

```bash
# SQLite is the default — no database setup required
nornweave api
```

The API will be available at `http://localhost:8000`. Data is stored in `./nornweave.db`.

### Using Docker (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/DataCovey/nornweave.git
cd nornweave

# Copy environment configuration and set EMAIL_DOMAIN + provider keys (see above)
cp .env.example .env

# Start the stack
docker compose up -d

# Run migrations (PostgreSQL only — SQLite tables are created automatically)
docker compose exec api alembic upgrade head
```

### Using uv (Development)

```bash
# Clone the repository
git clone https://github.com/DataCovey/nornweave.git
cd nornweave

# Install dependencies
make install-dev

# Copy environment configuration and set EMAIL_DOMAIN + provider keys (see above)
cp .env.example .env

# Run migrations (PostgreSQL only — SQLite tables are created automatically)
# make migrate

# Start the development server
make dev
```

## API Overview

### Create an Inbox

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Content-Type: application/json" \
  -d '{"name": "Support Agent", "email_username": "support"}'
```

### Read a Thread

```bash
curl http://localhost:8000/v1/threads/th_123
```

Response (LLM-optimized):
```json
{
  "id": "th_123",
  "subject": "Re: Pricing Question",
  "messages": [
    { "role": "user", "author": "bob@gmail.com", "content": "How much is it?", "timestamp": "..." },
    { "role": "assistant", "author": "agent@myco.com", "content": "$20/mo", "timestamp": "..." }
  ]
}
```

### Send a Reply

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_555",
    "reply_to_thread_id": "th_123",
    "to": ["client@gmail.com"],
    "subject": "Re: Pricing Question",
    "body": "Thanks for your interest! Our pricing starts at $20/mo."
  }'
```

## MCP Integration

NornWeave exposes an MCP server for direct integration with Claude, Cursor, and other MCP-compatible clients.

### Available Tools

| Tool | Description |
|------|-------------|
| `create_inbox` | Provision a new email address |
| `send_email` | Send an email (auto-converts Markdown to HTML) |
| `search_email` | Find relevant messages in your inbox |
| `wait_for_reply` | Block until a reply arrives (experimental) |

### Configure in Cursor/Claude

```bash
pip install nornweave[mcp]
```

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave",
      "args": ["mcp"],
      "env": {
        "NORNWEAVE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Architecture

NornWeave uses a thematic architecture inspired by Norse mythology:

| Component | Name | Purpose |
|-----------|------|---------|
| Storage Layer | **Urdr** (The Well) | Database adapters (PostgreSQL, SQLite), migrations |
| Ingestion Engine | **Verdandi** (The Loom) | Webhook + IMAP ingestion, HTML→Markdown, threading, LLM thread summarization |
| Outbound | **Skuld** (The Prophecy) | Email sending, rate limiting, webhooks |
| Gateway | **Yggdrasil** | FastAPI routes, middleware, API endpoints |
| MCP | **Huginn & Muninn** | Read resources and write tools for AI agents |

## Supported Providers

| Provider | Sending | Receiving | Auto-Route Setup |
|----------|---------|-----------|------------------|
| Mailgun | yes | yes | yes |
| AWS SES | yes | yes | manual |
| SendGrid | yes | yes | yes |
| Resend | yes | yes | yes |
| IMAP/SMTP | yes (SMTP) | yes (IMAP polling) | config |

## Documentation

- [Getting Started Guide](https://nornweave.datacovey.com/docs/getting-started/)
- [API Reference](https://nornweave.datacovey.com/docs/api/)
- [Architecture Overview](https://nornweave.datacovey.com/docs/concepts/architecture/)
- [Provider Setup Guides](https://nornweave.datacovey.com/docs/guides/)

## Repository Structure

This is a monorepo:

| Directory | Purpose |
|-----------|---------|
| **`src/nornweave/`** | Main Python package: adapters (Mailgun, SES, SendGrid, Resend, SMTP/IMAP), core config, models, **huginn** (MCP resources), **muninn** (MCP tools), **skuld** (outbound/sending), **urdr** (storage, migrations), **verdandi** (ingestion, parsing, threading), **yggdrasil** (FastAPI gateway), search, storage backends |
| **`clients/python/`** | Python client SDK (`nornweave-client`) |
| **`packages/n8n-nodes-nornweave/`** | n8n community node for NornWeave |
| **`tests/`** | Test suite: `fixtures/`, `integration/`, `unit/`, `e2e/` |
| **`web/`** | Hugo documentation site (`content/docs/`) |
| **`scripts/`** | DB init, migrations, dev setup |
| **`skills/`** | Distributable AI assistant skills (e.g. `nornweave-api`) |
| **`openspec/`** | Specs (`specs/`) and change artifacts (`changes/`, `changes/archive/`) |

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

NornWeave is open-source software licensed under the [Apache 2.0 License](LICENSE).

---

<p align="center">
  <sub>Image: "Nornorna spinner odet tradar vid Yggdrasil" by L. B. Hansen</sub><br>
  <sub><a href="https://commons.wikimedia.org/w/index.php?curid=164065">Public Domain</a></sub>
</p>
