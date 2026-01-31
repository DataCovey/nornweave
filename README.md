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
  <a href="https://github.com/nornweave/nornweave/actions"><img src="https://github.com/nornweave/nornweave/workflows/CI/badge.svg" alt="CI Status"></a>
  <a href="https://pypi.org/project/nornweave/"><img src="https://img.shields.io/pypi/v/nornweave.svg" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/nornweave/"><img src="https://img.shields.io/pypi/pyversions/nornweave.svg" alt="Python Versions"></a>
  <a href="https://github.com/nornweave/nornweave/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
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
- **Persistent Storage**: PostgreSQL with abstracted storage adapters
- **Email Sending**: Send replies through your configured provider
- **API Key Authentication**: Secure your endpoints

### Intelligence (The Agent Layer)
- **Content Parsing**: HTML to clean Markdown, cruft removal
- **Threading**: Automatic conversation grouping via email headers
- **MCP Server**: Connect directly to Claude, Cursor, and other MCP clients
- **Attachment Processing**: Extract text from PDFs and documents

### Enterprise (The Platform Layer)
- **Semantic Search**: Vector embeddings with pgvector
- **Real-time Webhooks**: Get notified of new messages
- **Rate Limiting**: Protect against runaway agents
- **Multi-Tenancy**: Organizations and projects

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/nornweave/nornweave.git
cd nornweave

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys

# Start the stack
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head
```

### Using uv (Development)

```bash
# Clone the repository
git clone https://github.com/nornweave/nornweave.git
cd nornweave

# Install dependencies
make install-dev

# Copy environment configuration
cp .env.example .env

# Start PostgreSQL (or use your own)
docker compose up -d postgres

# Run migrations
make migrate

# Start the development server
make dev
```

### Configure Your Email Provider

1. Set `EMAIL_PROVIDER` in `.env` (e.g., `mailgun`)
2. Add your provider's API key
3. Configure the webhook URL in your provider's dashboard:
   ```
   https://your-server.com/webhooks/mailgun
   ```

## API Overview

### Create an Inbox

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Support Agent", "email_username": "support"}'
```

### Read a Thread

```bash
curl http://localhost:8000/v1/threads/th_123 \
  -H "Authorization: Bearer YOUR_API_KEY"
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
  -H "Authorization: Bearer YOUR_API_KEY" \
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

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave-mcp",
      "args": ["--api-url", "http://localhost:8000"]
    }
  }
}
```

## Architecture

NornWeave uses a thematic architecture inspired by Norse mythology:

| Component | Name | Purpose |
|-----------|------|---------|
| Storage Layer | **Urdr** (The Well) | Database adapters (PostgreSQL, SQLite) |
| Ingestion Engine | **Verdandi** (The Loom) | Webhook processing, HTML to Markdown |
| API & Outbound | **Skuld** (The Prophecy) | REST API, email sending, rate limiting |
| Gateway | **Yggdrasil** | API router connecting all providers |
| MCP Tools | **Huginn & Muninn** | Read/write tools for AI agents |

## Supported Providers

| Provider | Sending | Receiving | Auto-Route Setup |
|----------|---------|-----------|------------------|
| Mailgun | yes | yes | yes |
| AWS SES | yes | yes | manual |
| SendGrid | yes | yes | yes |
| Resend | yes | yes | yes |

## Documentation

- [Getting Started Guide](https://nornweave.github.io/nornweave/getting-started/)
- [API Reference](https://nornweave.github.io/nornweave/api/)
- [Architecture Overview](https://nornweave.github.io/nornweave/architecture/)
- [Provider Setup Guides](https://nornweave.github.io/nornweave/guides/)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

NornWeave is open-source software licensed under the [Apache 2.0 License](LICENSE).

---

<p align="center">
  <sub>Image: "Nornorna spinner odet tradar vid Yggdrasil" by L. B. Hansen</sub><br>
  <sub><a href="https://commons.wikimedia.org/w/index.php?curid=164065">Public Domain</a></sub>
</p>
