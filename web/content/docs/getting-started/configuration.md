---
title: Configuration
weight: 2
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

```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=your-api-key
```

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

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ENABLED` | Enable MCP server | `true` |
| `MCP_API_URL` | URL for the REST API | `http://localhost:8000` |

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

# MCP
MCP_ENABLED=true
MCP_API_URL=http://localhost:8000
```

## Next Steps

{{< cards >}}
  {{< card link="../quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox" >}}
  {{< card link="../../guides" title="Provider Guides" icon="book-open" subtitle="Detailed setup for each provider" >}}
{{< /cards >}}
