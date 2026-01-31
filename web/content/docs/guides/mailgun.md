---
title: Mailgun Setup Guide
description: "Complete guide to integrating Mailgun with NornWeave. Domain verification, DNS setup, webhook configuration, and API credentials for AI agent email."
weight: 1
keywords:
  - Mailgun setup
  - Mailgun webhook
  - Mailgun API integration
  - email domain setup
  - Mailgun DNS records
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

This guide walks through setting up Mailgun as your email provider for NornWeave.

## Prerequisites

- A Mailgun account ([sign up](https://www.mailgun.com/))
- A domain you control for sending/receiving email
- Access to your domain's DNS settings

## Step 1: Create a Mailgun Domain

{{% steps %}}

### Log in to Mailgun

Go to the [Mailgun Dashboard](https://app.mailgun.com/) and navigate to **Sending** > **Domains**.

### Add Your Domain

Click **Add New Domain** and enter your domain (e.g., `mail.yourdomain.com`).

{{< callout type="info" >}}
We recommend using a subdomain like `mail.` or `mg.` rather than your root domain.
{{< /callout >}}

### Configure DNS Records

Mailgun will provide DNS records to add. You'll need:

- **TXT record** for SPF
- **TXT record** for DKIM
- **MX records** for receiving

Example DNS records:

| Type | Name | Value |
|------|------|-------|
| TXT | mail | `v=spf1 include:mailgun.org ~all` |
| TXT | smtp._domainkey.mail | `k=rsa; p=...` |
| MX | mail | `mxa.mailgun.org` (priority 10) |
| MX | mail | `mxb.mailgun.org` (priority 10) |

### Verify Domain

After adding DNS records, click **Verify DNS Settings** in Mailgun.

{{% /steps %}}

## Step 2: Get API Credentials

{{% steps %}}

### Navigate to API Keys

Go to **Settings** > **API Security** in the Mailgun dashboard.

### Copy Your API Key

Copy your **Private API key**. It looks like: `key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

{{< callout type="warning" >}}
Keep your API key secret. Never commit it to version control.
{{< /callout >}}

{{% /steps %}}

## Step 3: Configure Inbound Routes

{{% steps %}}

### Navigate to Receiving

Go to **Receiving** > **Routes** in the Mailgun dashboard.

### Create a Route

Click **Create Route** with these settings:

- **Expression Type**: Match Recipient
- **Recipient**: `.*@mail.yourdomain.com` (catch-all)
- **Actions**:
  - Forward: `https://your-server.com/webhooks/mailgun`
  - Store and Notify: Enabled (optional, for debugging)

### Test the Route

Send a test email to `test@mail.yourdomain.com` and check NornWeave logs.

{{% /steps %}}

## Step 4: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MAILGUN_DOMAIN=mail.yourdomain.com
MAILGUN_REGION=us  # or: eu
```

| Variable | Description |
|----------|-------------|
| `MAILGUN_API_KEY` | Your private API key |
| `MAILGUN_DOMAIN` | Your verified domain |
| `MAILGUN_REGION` | `us` for US region, `eu` for EU region |

## Step 5: Verify Setup

{{% steps %}}

### Restart NornWeave

```bash
docker compose restart api
```

### Create a Test Inbox

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email_username": "test"}'
```

### Send a Test Email

Send an email to `test@mail.yourdomain.com` from your personal email.

### Check Logs

```bash
docker compose logs -f api
```

You should see the incoming webhook being processed.

{{% /steps %}}

## Auto-Route Setup

NornWeave can automatically create Mailgun routes when you create an inbox. This requires:

1. Your API key has permission to manage routes
2. `MAILGUN_AUTO_ROUTE=true` in your environment

When enabled, creating an inbox will automatically create a matching Mailgun route.

## Troubleshooting

### Webhook Not Receiving

- Verify your server is publicly accessible
- Check Mailgun logs for delivery attempts
- Ensure the route expression matches your inbox addresses

### DNS Verification Failed

- DNS changes can take up to 48 hours to propagate
- Use `dig` or `nslookup` to verify records
- Ensure no typos in the DNS values

### Emails Going to Spam

- Verify SPF and DKIM are properly configured
- Check your domain reputation in Mailgun
- Start with small volumes to warm up the domain
