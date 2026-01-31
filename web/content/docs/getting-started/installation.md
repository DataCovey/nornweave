---
title: Installation
weight: 1
---

NornWeave can be installed using Docker (recommended) or directly from source using uv.

## Using Docker (Recommended)

Docker is the easiest way to get started with NornWeave.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Steps

{{< steps >}}

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

You should see: `{"status": "healthy"}`

{{< /steps >}}

## Using uv (Development)

For development or when you need more control over the installation.

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- [uv](https://github.com/astral-sh/uv) package manager

### Steps

{{< steps >}}

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

{{< /steps >}}

## Next Steps

{{< cards >}}
  {{< card link="../configuration" title="Configuration" icon="cog" subtitle="Learn about all configuration options" >}}
  {{< card link="../quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox" >}}
{{< /cards >}}
