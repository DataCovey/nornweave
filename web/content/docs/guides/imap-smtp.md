---
title: IMAP/SMTP Setup Guide
description: "Connect NornWeave to any mail server using standard IMAP and SMTP protocols. Zero vendor lock-in — works with Gmail, Office 365, Fastmail, Postfix, and more."
weight: 5
keywords:
  - IMAP setup
  - SMTP setup
  - self-hosted email
  - IMAP polling
  - SMTP sending
  - bring your own mail server
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

This guide walks through using IMAP/SMTP as your email provider for NornWeave. Unlike the webhook-based providers (Mailgun, SendGrid, SES, Resend), this option connects directly to any standard mail server — no transactional email account needed.

## Prerequisites

- A mail server that supports IMAP and SMTP (Gmail, Office 365, Fastmail, self-hosted Postfix/Dovecot, etc.)
- An email account with IMAP access enabled
- SMTP credentials for sending (often the same as IMAP)

## How It Works

| Aspect | IMAP/SMTP | Webhook Providers |
|--------|-----------|-------------------|
| **Sending** | Direct SMTP connection | Provider API |
| **Receiving** | IMAP polling (pull) | Webhooks (push) |
| **Latency** | Configurable interval (default 60s) | Near-instant |
| **Dependencies** | `nornweave[smtpimap]` | Included by default |
| **Setup** | Mail server credentials | Provider account + DNS |

NornWeave polls the IMAP mailbox periodically for new messages, parses them, and feeds them into the same ingestion pipeline used by webhook providers. Outbound emails are sent via SMTP.

## Step 1: Install Dependencies

The IMAP/SMTP adapter requires additional packages:

```bash
pip install nornweave[smtpimap]
# or with uv
uv add nornweave[smtpimap]
```

## Step 2: Configure NornWeave

Update your `.env` file:

```bash
# Provider selection
EMAIL_PROVIDER=imap-smtp

# SMTP (sending)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=nornweave@example.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# IMAP (receiving)
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USERNAME=nornweave@example.com
IMAP_PASSWORD=your-app-password
IMAP_USE_SSL=true
IMAP_POLL_INTERVAL=60
IMAP_MAILBOX=INBOX

# Post-fetch behavior
IMAP_MARK_AS_READ=true
IMAP_DELETE_AFTER_FETCH=false
```

### Configuration Reference

#### SMTP Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | *(required)* | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port (587 for STARTTLS, 465 for implicit TLS) |
| `SMTP_USERNAME` | | SMTP authentication username |
| `SMTP_PASSWORD` | | SMTP authentication password |
| `SMTP_USE_TLS` | `true` | Enable TLS (STARTTLS on 587, implicit on 465) |

#### IMAP Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAP_HOST` | *(required)* | IMAP server hostname |
| `IMAP_PORT` | `993` | IMAP port (993 for SSL, 143 for plain) |
| `IMAP_USERNAME` | | IMAP authentication username |
| `IMAP_PASSWORD` | | IMAP authentication password |
| `IMAP_USE_SSL` | `true` | Use SSL/TLS for IMAP connection |
| `IMAP_POLL_INTERVAL` | `60` | Seconds between IMAP polls |
| `IMAP_MAILBOX` | `INBOX` | IMAP folder to poll |

#### Post-Fetch Behavior

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAP_MARK_AS_READ` | `true` | Set `\Seen` flag after processing |
| `IMAP_DELETE_AFTER_FETCH` | `false` | Delete messages after processing |

{{< callout type="warning" >}}
`IMAP_DELETE_AFTER_FETCH=true` requires `IMAP_MARK_AS_READ=true`. NornWeave will refuse to start if delete is enabled without mark-as-read.
{{< /callout >}}

## Step 3: Provider-Specific Examples

### Gmail

Use an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password):

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
```

{{< callout type="info" >}}
Gmail requires "Allow less secure apps" or an App Password. OAuth2 is not yet supported.
{{< /callout >}}

### Office 365 / Outlook

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
IMAP_HOST=outlook.office365.com
IMAP_PORT=993
```

### Self-hosted (Postfix + Dovecot)

```bash
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587
IMAP_HOST=mail.yourdomain.com
IMAP_PORT=993
```

## Step 4: Verify Setup

{{% steps %}}

### Restart NornWeave

```bash
docker compose restart api
```

You should see in the logs:

```
IMAP poller starting: imap.example.com:993/INBOX (interval=60s)
```

### Create a Test Inbox

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email_username": "test"}'
```

### Send a Test Email

Send an email to your configured address and wait up to `IMAP_POLL_INTERVAL` seconds.

### Manual Sync (optional)

Trigger an immediate sync instead of waiting:

```bash
curl -X POST http://localhost:8000/v1/inboxes/{inbox_id}/sync \
  -H "Authorization: Bearer YOUR_API_KEY"
```

{{% /steps %}}

## IMAP Polling Behavior

- **UID tracking**: NornWeave tracks the last-seen message UID per inbox to avoid re-processing. State persists across restarts.
- **UIDVALIDITY**: If the IMAP server's UIDVALIDITY changes (rare, happens on mailbox rebuild), NornWeave resets and re-syncs all messages.
- **Connection resilience**: If the IMAP connection fails, the poller retries with exponential backoff (up to 5 minutes) without crashing the application.
- **Single mailbox**: All inboxes share the same IMAP account. Routing is based on the `To:` address matching an inbox, same as webhook providers.

## Troubleshooting

### IMAP Connection Refused

- Verify IMAP is enabled on your mail server
- Check `IMAP_HOST`, `IMAP_PORT`, and `IMAP_USE_SSL` settings
- Ensure your firewall allows outbound connections to the IMAP port

### Emails Not Being Picked Up

- Check that the poll interval isn't too long (`IMAP_POLL_INTERVAL`)
- Verify emails are in the correct folder (`IMAP_MAILBOX`)
- Use the manual sync endpoint to trigger an immediate check
- Ensure the `To:` address matches a configured inbox

### SMTP Authentication Failed

- Verify `SMTP_USERNAME` and `SMTP_PASSWORD`
- For Gmail, use an App Password instead of your account password
- Check that the port and TLS settings match your server's requirements
