# SendGrid setup

1. Create a SendGrid account and verify a sender/domain.
2. In NornWeave `.env`:
   - `EMAIL_PROVIDER=sendgrid`
   - `SENDGRID_API_KEY=<your API key>`
   - `EMAIL_DOMAIN=<verified domain>`
3. In SendGrid: **Settings** → **Mail Settings** → **Inbound Parse**:
   - Add host and URL: `https://your-server.com/webhooks/sendgrid`
   - Set destination (e.g. catch-all or subdomain).
4. Optionally configure domain authentication (DKIM/SPF) in SendGrid.
