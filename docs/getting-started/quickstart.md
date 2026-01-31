# Quickstart

## 1. Configure environment

```bash
cp .env.example .env
# Edit .env: set DATABASE_URL, EMAIL_PROVIDER, provider API keys, API_KEY
```

## 2. Start dependencies (Docker)

```bash
docker compose up -d postgres redis
```

## 3. Run migrations

```bash
make migrate
# or: uv run alembic upgrade head
```

## 4. Start the API

```bash
make dev
# or: uv run uvicorn nornweave.yggdrasil.app:app --reload --port 8000
```

## 5. Verify

- Health: `curl http://localhost:8000/health`
- Docs: open http://localhost:8000/docs

## 6. Configure your email provider

Set your webhook URL in the provider dashboard to:

`https://your-server.com/webhooks/<provider>` (e.g. `/webhooks/mailgun`).

See [Configuration](configuration.md) and provider guides under [Guides](../guides/mailgun.md).
