---
title: Adapters
weight: 2
---

NornWeave uses adapter patterns for both storage and email providers, allowing you to choose the implementation that fits your needs.

## Storage Adapters (Urdr)

The storage layer uses a `StorageInterface` that can be implemented by different database backends.

### PostgresAdapter

The production-ready adapter using PostgreSQL with asyncpg.

```bash
DB_DRIVER=postgres
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nornweave
```

Features:
- Full async support via asyncpg
- Alembic migrations for schema management
- Production-ready with connection pooling
- Supports pgvector for semantic search (Phase 3)

### SQLiteAdapter

A lightweight adapter for local development and testing.

```bash
DB_DRIVER=sqlite
DATABASE_URL=sqlite+aiosqlite:///./nornweave.db
```

Features:
- Single file database, no server required
- Async support via aiosqlite
- Great for development and testing
- Not recommended for production

## Email Provider Adapters (BYOP)

The "Bring Your Own Provider" model allows you to use your preferred email service.

### MailgunAdapter

```bash
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=key-xxxxxxxx
MAILGUN_DOMAIN=mail.yourdomain.com
```

### SESAdapter

```bash
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

### SendGridAdapter

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxx
```

### ResendAdapter

```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxxxxx
```

## Provider Interface

Each provider implements the `EmailProvider` interface:

```python
class EmailProvider(Protocol):
    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        from_address: str,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Send an email. Returns provider message ID."""
        ...

    def parse_inbound_webhook(
        self,
        payload: dict[str, Any],
    ) -> InboundMessage:
        """Parse provider webhook payload into standardized format."""
        ...

    async def setup_inbound_route(
        self,
        inbox_address: str,
        webhook_url: str,
    ) -> None:
        """Optional: Configure provider to route inbound mail."""
        ...
```

## Adding Custom Adapters

To add a new storage or provider adapter:

1. Implement the appropriate interface (`StorageInterface` or `EmailProvider`)
2. Register the adapter in the factory
3. Add configuration options to the settings

See the existing adapters in `src/nornweave/urdr/adapters/` and `src/nornweave/adapters/` for examples.
