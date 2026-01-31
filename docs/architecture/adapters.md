# Adapters

## Storage adapters (Urdr)

- **PostgresAdapter**: Production; uses asyncpg and Alembic migrations.
- **SQLiteAdapter**: Local development; single file, no separate server.

Set `DB_DRIVER=postgres` or `sqlite` and `DATABASE_URL` accordingly.

## Email provider adapters (BYOP)

- **MailgunAdapter**: Mailgun API and webhook format.
- **SESAdapter**: AWS SES (sending and receiving if configured).
- **SendGridAdapter**: SendGrid API and webhook format.
- **ResendAdapter**: Resend API and webhook format.

Set `EMAIL_PROVIDER` and the corresponding API keys (e.g. `MAILGUN_API_KEY`).

Each provider implements:

- `send_email(...)` — Send a message; returns provider message id.
- `parse_inbound_webhook(payload)` — Turn provider webhook payload into a standardized `InboundMessage`.
- `setup_inbound_route(inbox_address)` — Optional; configure provider to route inbound mail to our webhook URL.
