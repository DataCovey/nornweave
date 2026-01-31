# Mailgun setup

1. Create a Mailgun account and domain (or use the sandbox domain for testing).
2. In NornWeave `.env`:
   - `EMAIL_PROVIDER=mailgun`
   - `MAILGUN_API_KEY=<your API key>`
   - `MAILGUN_DOMAIN=<your domain>`
   - `EMAIL_DOMAIN=<same or sending domain>`
3. In Mailgun dashboard: **Receiving** → **Create Route**:
   - Match: `match_recipient(".*@your-domain.com")` (or your inbox pattern)
   - Action: Forward to `https://your-server.com/webhooks/mailgun`
   - Priority: 0
4. Optionally verify your domain and configure DKIM/SPF for better deliverability.
