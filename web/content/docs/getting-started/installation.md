---
title: NornWeave Installation Guide
description: "Install NornWeave using Docker or from source with uv. Complete setup instructions including PostgreSQL database configuration."
weight: 1
keywords:
  - NornWeave installation
  - Docker setup
  - PostgreSQL setup
  - Python installation
  - uv package manager
sitemap_priority: 0.9
sitemap_changefreq: weekly
---

## Deployment Architecture

NornWeave exposes two types of endpoints with different security requirements:

- **Internal API** (`/v1/*`): Used by AI agents to read threads, send messages, and search. Should only be accessible from your internal network.
- **Webhook endpoints** (`/webhooks/*`): Receive inbound email events from providers (Mailgun, SES, SendGrid, Resend). Must be publicly accessible.

The recommended architecture uses a reverse proxy to control access:

```mermaid
flowchart TB
    subgraph internet [Internet]
        Provider[Email Providers<br/>Mailgun, SES, SendGrid, Resend]
    end

    subgraph userNetwork [Your Network / VPC]
        subgraph proxy [Reverse Proxy]
            ExtListener[External Listener<br/>webhooks.example.com:443]
            IntListener[Internal Listener<br/>api.internal:8080]
        end

        subgraph app [NornWeave API]
            API[FastAPI<br/>Port 8000]
        end

        subgraph storage [Storage]
            DB[(PostgreSQL)]
        end

        subgraph agents [AI Agents]
            Agent1[Claude / Cursor<br/>MCP Client]
            Agent2[Custom Agent<br/>REST Client]
        end
    end

    Provider -->|POST /webhooks/*| ExtListener
    ExtListener -->|proxy| API
    IntListener -->|proxy| API
    Agent1 -->|GET /v1/threads| IntListener
    Agent2 -->|POST /v1/messages| IntListener
    API --> DB
```

- **External access**: Only `/webhooks/*` and `/health` are exposed through the external listener
- **Internal access**: AI agents connect through the internal listener, which has full API access
- **Storage**: PostgreSQL runs inside your network, accessible only by the NornWeave API

---

NornWeave can be installed using Docker (recommended) or directly from source using uv.

## Using Docker (Recommended)

Docker is the easiest way to get started with NornWeave.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Steps

{{% steps %}}

### Clone the Repository

```bash
git clone https://github.com/DataCovey/nornweave.git
cd nornweave
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=nornweave
POSTGRES_USER=nornweave
POSTGRES_PASSWORD=your-secure-password

# Email Provider
EMAIL_PROVIDER=mailgun  # or: sendgrid, ses, resend
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=mail.yourdomain.com

# API Security
API_KEY=your-api-key
```

### Start the Stack

```bash
docker compose up -d
```

### Run Database Migrations

```bash
docker compose exec api alembic upgrade head
```

### Verify Installation

```bash
curl http://localhost:8000/health
```

You should see: `{"status": "ok"}`

### Configure Reverse Proxy (Production)

For production deployments, use a reverse proxy to separate internal and external access. Here's a minimal nginx configuration:

```nginx
# External server - only webhooks (public)
server {
    listen 443 ssl;
    server_name webhooks.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Health check for load balancers
    location = /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # Only webhook endpoints are public
    location /webhooks/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Block everything else
    location / {
        return 403;
    }
}

# Internal server - full API access (VPC/private network only)
server {
    listen 8080;  # Bind to internal interface only
    server_name api.internal;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

With this configuration:
- Email providers send webhooks to `https://webhooks.example.com/webhooks/{provider}`
- AI agents connect to `http://api.internal:8080/v1/*` from within your network
- The NornWeave API itself (`127.0.0.1:8000`) is not directly exposed

### (Optional) Validate with Python SDK

For a comprehensive validation of all API endpoints, you can use the Python SDK validation script:

```bash
cd clients/python
uv pip install -e .
python scripts/validate_local.py
```

This runs 22 integration tests covering all SDK features including sync/async clients, pagination, error handling, and raw response access.

{{% /steps %}}

## Using uv (Development)

For development or when you need more control over the installation.

### Prerequisites

- Python 3.14+
- PostgreSQL 15+
- [uv](https://github.com/astral-sh/uv) package manager

### Steps

{{% steps %}}

### Clone and Install

```bash
git clone https://github.com/DataCovey/nornweave.git
cd nornweave

# Install dependencies
make install-dev
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your database and provider settings
```

### Start PostgreSQL

You can use Docker for just the database:

```bash
docker compose up -d postgres
```

Or use your own PostgreSQL instance.

### Run Migrations

```bash
make migrate
```

### Start Development Server

```bash
make dev
```

The API will be available at `http://localhost:8000`.


{{% /steps %}}

## Next Steps

{{< cards >}}
  {{< card link="../configuration" title="Configuration" icon="cog" subtitle="Learn about all configuration options" >}}
  {{< card link="../quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox" >}}
{{< /cards >}}
