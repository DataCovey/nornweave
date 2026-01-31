# Configuration

NornWeave is configured via environment variables. Copy `.env.example` to `.env` and set values.

## Storage (Urdr)

- `DB_DRIVER`: `postgres` or `sqlite`
- `DATABASE_URL`: Connection string (e.g. `postgresql+asyncpg://user:pass@localhost:5432/nornweave` or `sqlite+aiosqlite:///./nornweave.db`)

## Email provider

- `EMAIL_PROVIDER`: `mailgun`, `ses`, `sendgrid`, or `resend`
- `EMAIL_DOMAIN`: Default sending domain
- Provider-specific keys: `MAILGUN_API_KEY`, `SENDGRID_API_KEY`, `RESEND_API_KEY`, or AWS credentials for SES

## API security

- `API_KEY`: Secret used for `Authorization: Bearer <API_KEY>`
- `CORS_ORIGINS`: Comma-separated origins (default `*`)

## Server

- `HOST`, `PORT`: Bind address (default `0.0.0.0:8000`)
- `ENVIRONMENT`: `development`, `staging`, `production`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## Phase 3

- `REDIS_URL`: For rate limiting
- `OPENAI_API_KEY`: For semantic search embeddings
- `WEBHOOK_SECRET`: For signing outbound webhooks
