---
title: NornWeave Configuration
description: "Complete configuration reference for NornWeave. Environment variables for database, email providers, API keys, and logging settings."
weight: 2
keywords:
  - NornWeave configuration
  - environment variables
  - API key setup
  - database configuration
  - email provider config
  - attachment storage
  - S3 attachments
  - GCS attachments
sitemap_priority: 0.85
sitemap_changefreq: weekly
---

NornWeave is configured through environment variables. This page documents all available options.

## Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_DRIVER` | Database driver (`postgres` or `sqlite`) | `postgres` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `nornweave` |
| `POSTGRES_USER` | Database user | `nornweave` |
| `POSTGRES_PASSWORD` | Database password | Required |

### Example

```bash
DB_DRIVER=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=nornweave
POSTGRES_USER=nornweave
POSTGRES_PASSWORD=your-secure-password
```

## Email Provider Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_PROVIDER` | Provider to use (`mailgun`, `sendgrid`, `ses`, `resend`) | Required |

### Mailgun

```bash
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=mail.yourdomain.com
MAILGUN_REGION=us  # or: eu
```

### SendGrid

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key
```

### AWS SES

```bash
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

### Resend

| Variable | Description | Default |
|----------|-------------|---------|
| `RESEND_API_KEY` | Resend API key for sending emails | Required |
| `RESEND_WEBHOOK_SECRET` | Svix signing secret for webhook verification | Optional |

```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx  # Optional: for webhook signature verification
```

The `RESEND_WEBHOOK_SECRET` is the Svix signing secret from your Resend webhook configuration. When set, NornWeave verifies the signature on incoming webhooks to ensure they originated from Resend.

## API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API key for authentication | Required |
| `API_HOST` | Host to bind to | `0.0.0.0` |
| `API_PORT` | Port to listen on | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Example

```bash
API_KEY=your-secure-api-key
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Attachment Storage Configuration

NornWeave supports multiple storage backends for email attachments. Choose the one that best fits your deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND` | Storage backend (`local`, `database`, `s3`, `gcs`) | `local` |
| `NORNWEAVE_ATTACHMENT_STORAGE_PATH` | Local filesystem path for attachments | `/var/nornweave/attachments` |
| `NORNWEAVE_ATTACHMENT_URL_EXPIRY` | Signed URL expiry time (seconds) | `3600` |
| `NORNWEAVE_ATTACHMENT_URL_SECRET` | Secret key for URL signing | Auto-generated |

### Local Filesystem Storage (Default)

Store attachments on the local filesystem. Good for development and single-server deployments.

```bash
NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=local
NORNWEAVE_ATTACHMENT_STORAGE_PATH=/var/nornweave/attachments
```

### Database Storage

Store attachments as BLOBs in the database. Simple deployments without separate storage infrastructure.

```bash
NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=database
```

{{< callout type="warning" >}}
Database storage is suitable for small attachments. For large files or high-volume use, consider S3 or GCS.
{{< /callout >}}

### AWS S3 Storage

Store attachments in Amazon S3 or any S3-compatible storage (MinIO, DigitalOcean Spaces, etc.).

Requires the `s3` extra:

```bash
pip install nornweave[s3]
```

Configuration:

```bash
NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=nornweave-attachments
AWS_S3_REGION=us-east-1

# Optional: for S3-compatible storage (MinIO, etc.)
AWS_S3_ENDPOINT_URL=http://localhost:9000
```

### Google Cloud Storage

Store attachments in Google Cloud Storage.

Requires the `gcs` extra:

```bash
pip install nornweave[gcs]
```

Configuration:

```bash
NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=gcs
GCS_BUCKET=nornweave-attachments
GCS_PROJECT=your-project-id

# Optional: explicit credentials path
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Storage Backend Comparison

| Backend | Best For | Requires Extra | Notes |
|---------|----------|----------------|-------|
| `local` | Development, single server | No | Fast, no external deps |
| `database` | Simple deployments | No | Small files only |
| `s3` | Production, scalable | `[s3]` | Presigned URLs |
| `gcs` | Google Cloud deployments | `[gcs]` | Presigned URLs |

## LLM Thread Summarization

NornWeave can automatically generate thread summaries using your LLM provider. This allows AI agents to understand long threads by reading just the summary instead of every message.

The feature is **disabled by default**. To enable it, set `LLM_PROVIDER` to one of the supported providers and provide the API key.

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (`openai`, `anthropic`, or `gemini`) | (disabled) |
| `LLM_API_KEY` | API key for the selected provider | Required when provider is set |
| `LLM_MODEL` | Model override (auto-selected per provider if empty) | (auto) |
| `LLM_SUMMARY_PROMPT` | Custom system prompt for summarization | Built-in default |
| `LLM_DAILY_TOKEN_LIMIT` | Max tokens per day (0 = unlimited) | `1000000` |

Requires the provider's optional dependency:

```bash
pip install nornweave[openai]    # For OpenAI (default model: gpt-4o-mini)
pip install nornweave[anthropic]  # For Anthropic (default model: claude-haiku)
pip install nornweave[gemini]     # For Gemini (default model: gemini-2.0-flash)
pip install nornweave[llm]        # All providers
```

### Example

```bash
# Enable with OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_DAILY_TOKEN_LIMIT=500000

# Optional: custom model and prompt
LLM_MODEL=gpt-4o
LLM_SUMMARY_PROMPT="Summarize this email thread in 3 bullet points."
```

{{< callout type="info" >}}
Summaries are generated after each new message. If the daily token limit is reached, summarization is paused until the next day (UTC). Token usage is tracked in the database and can be queried from the `llm_token_usage` table.
{{< /callout >}}

## Domain Filtering (Allow/Blocklists)

NornWeave supports domain-level allow/blocklists for both inbound (receiving) and outbound (sending) email. Use these to restrict which external domains your instance interacts with.

Each variable accepts a **comma-separated list of regex patterns** (Python `re` syntax). Patterns are matched against the full domain using `re.fullmatch` (no partial matches).

| Variable | Direction | Semantics | Default |
|----------|-----------|-----------|---------|
| `INBOUND_DOMAIN_ALLOWLIST` | Inbound | Sender domain must match at least one pattern | (empty — allow all) |
| `INBOUND_DOMAIN_BLOCKLIST` | Inbound | Sender domain rejected if it matches any pattern | (empty — block none) |
| `OUTBOUND_DOMAIN_ALLOWLIST` | Outbound | Recipient domain must match at least one pattern | (empty — allow all) |
| `OUTBOUND_DOMAIN_BLOCKLIST` | Outbound | Recipient domain rejected if it matches any pattern | (empty — block none) |

**Evaluation order:** Blocklist is checked first. If a domain matches the blocklist it is rejected, regardless of the allowlist. If the allowlist is non-empty, only matching domains pass.

### Examples

```bash
# Only accept inbound email from your own domain
INBOUND_DOMAIN_ALLOWLIST=(.*\.)?yourcompany\.com

# Block known spam domains from inbound
INBOUND_DOMAIN_BLOCKLIST=spam\.com,junk\.org

# Allow sending only to specific partners
OUTBOUND_DOMAIN_ALLOWLIST=partner\.com,client\.org

# Block a subdomain while allowing the parent
INBOUND_DOMAIN_ALLOWLIST=(.*\.)?example\.com
INBOUND_DOMAIN_BLOCKLIST=noreply\.example\.com
```

{{< callout type="info" >}}
Patterns use Python regex syntax. Escape dots with `\.` for literal matching. Use `(.*\.)?example\.com` to match a domain and all its subdomains. Invalid patterns cause a startup error.
{{< /callout >}}

## MCP Server Configuration

The MCP server connects AI agents to NornWeave. Configure it using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `NORNWEAVE_API_URL` | NornWeave REST API base URL | `http://localhost:8000` |
| `NORNWEAVE_API_KEY` | API key for authentication | (none) |
| `NORNWEAVE_MCP_HOST` | Host to bind MCP server (SSE/HTTP) | `0.0.0.0` |
| `NORNWEAVE_MCP_PORT` | Port for MCP server (SSE/HTTP) | `3000` |

### Example

```bash
# MCP server configuration
NORNWEAVE_API_URL=http://localhost:8000
NORNWEAVE_API_KEY=your-api-key
NORNWEAVE_MCP_HOST=0.0.0.0
NORNWEAVE_MCP_PORT=3000
```

### CLI Options

The MCP server also accepts command-line options:

```bash
nornweave mcp --help

Options:
  --transport [stdio|sse|http]  MCP transport type [default: stdio]
  --host TEXT                   Host to bind (SSE/HTTP) [default: 0.0.0.0]
  --port INTEGER                Port to listen (SSE/HTTP) [default: 3000]
  --api-url TEXT                NornWeave API URL [default: http://localhost:8000]
```

## Complete Example

Here's a complete `.env` file:

```bash
# Database
DB_DRIVER=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=nornweave
POSTGRES_USER=nornweave
POSTGRES_PASSWORD=super-secret-password

# Email Provider (Mailgun)
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mail.example.com
MAILGUN_REGION=us

# API
API_KEY=nw-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Attachment Storage (S3 example)
NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET=nornweave-attachments
AWS_S3_REGION=us-east-1

# MCP Server
NORNWEAVE_API_URL=http://localhost:8000
NORNWEAVE_API_KEY=nw-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# LLM Thread Summarization (optional)
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_DAILY_TOKEN_LIMIT=1000000
```

## Next Steps

{{< cards >}}
  {{< card link="../quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox" >}}
  {{< card link="../../guides" title="Provider Guides" icon="book-open" subtitle="Detailed setup for each provider" >}}
{{< /cards >}}
