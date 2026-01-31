---
title: "Getting Started"
date: 2025-01-01
draft: false
---

## Quick start

1. **Clone and config**
   ```bash
   git clone https://github.com/nornweave/nornweave.git
   cd nornweave
   cp .env.example .env
   ```
   Edit `.env` with your database URL and email provider keys.

2. **Select adapters**
   - `DB_DRIVER=postgres` (or `sqlite` for local dev)
   - `EMAIL_PROVIDER=mailgun` (or `ses`, `sendgrid`, `resend`)

3. **Set keys**
   - `DATABASE_URL`, provider API key (e.g. `MAILGUN_API_KEY`), `API_KEY`

4. **Run**
   ```bash
   docker compose up -d
   make migrate
   make dev
   ```

5. **Configure webhook**
   In your provider dashboard, set the inbound webhook URL to:
   `https://your-server.com/webhooks/<provider>` (e.g. `/webhooks/mailgun`).

For full documentation, see the [docs site](https://nornweave.github.io/nornweave/).
