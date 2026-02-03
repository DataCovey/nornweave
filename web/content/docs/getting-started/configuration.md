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

# MCP Server
NORNWEAVE_API_URL=http://localhost:8000
NORNWEAVE_API_KEY=nw-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Next Steps

{{< cards >}}
  {{< card link="../quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox" >}}
  {{< card link="../../guides" title="Provider Guides" icon="book-open" subtitle="Detailed setup for each provider" >}}
{{< /cards >}}
