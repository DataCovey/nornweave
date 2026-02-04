---
title: SendGrid Setup Guide
description: "Step-by-step SendGrid integration with NornWeave. API key creation, domain authentication, Inbound Parse webhook setup for AI agent email."
weight: 2
keywords:
  - SendGrid setup
  - SendGrid webhook
  - SendGrid Inbound Parse
  - SendGrid API integration
  - email webhook setup
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

This guide walks through setting up SendGrid as your email provider for NornWeave.

## Prerequisites

- A SendGrid account ([sign up](https://sendgrid.com/))
- A domain you control for sending/receiving email
- Access to your domain's DNS settings

## Step 1: Create API Key

{{% steps %}}

### Log in to SendGrid

Go to the [SendGrid Dashboard](https://app.sendgrid.com/).

### Create API Key

Navigate to **Settings** > **API Keys** > **Create API Key**.

- Name: `NornWeave`
- Permissions: **Full Access** (or restrict to Mail Send and Inbound Parse)

### Copy the Key

Copy the API key immediately - it won't be shown again.

{{% /steps %}}

## Step 2: Authenticate Your Domain

{{% steps %}}

### Navigate to Sender Authentication

Go to **Settings** > **Sender Authentication**.

### Authenticate Domain

Click **Authenticate Your Domain** and follow the wizard.

You'll need to add DNS records:

| Type | Name | Value |
|------|------|-------|
| CNAME | em1234.yourdomain.com | `u1234.wl.sendgrid.net` |
| CNAME | s1._domainkey.yourdomain.com | `s1.domainkey.u1234.wl.sendgrid.net` |
| CNAME | s2._domainkey.yourdomain.com | `s2.domainkey.u1234.wl.sendgrid.net` |

### Verify

Click **Verify** after adding the DNS records.

{{% /steps %}}

## Step 3: Configure Inbound Parse

{{% steps %}}

### Navigate to Inbound Parse

Go to **Settings** > **Inbound Parse**.

### Add Host & URL

Click **Add Host & URL**:

- **Subdomain**: `mail` (or leave blank for root)
- **Domain**: Select your authenticated domain
- **Destination URL**: `https://your-server.com/webhooks/sendgrid`
- Check **POST the raw, full MIME message**

### Configure MX Records

Add MX record for your receiving subdomain:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | mail | `mx.sendgrid.net` | 10 |

{{% /steps %}}

## Step 4: Secure Inbound Parse (Recommended)

SendGrid supports cryptographic signature verification for Inbound Parse webhooks using ECDSA. This is highly recommended for production deployments.

{{% steps %}}

### Create Security Policy

Use the SendGrid API to create a webhook security policy:

```bash
curl -X POST https://api.sendgrid.com/v3/user/webhooks/security/policies \
  -H "Authorization: Bearer YOUR_SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NornWeave Inbound Parse",
    "signature": { "enabled": true }
  }'
```

The response includes a `public_key` - save this securely:

```json
{
  "policy": {
    "id": "dd677638-a16d-4e19-95ea-20231c35511b",
    "signature": {
      "public_key": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE..."
    }
  }
}
```

### Attach Policy to Parse Webhook

Link the security policy to your Inbound Parse settings:

```bash
curl -X PATCH "https://api.sendgrid.com/v3/user/webhooks/parse/settings/mail.yourdomain.com" \
  -H "Authorization: Bearer YOUR_SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhooks/sendgrid",
    "security_policy": "dd677638-a16d-4e19-95ea-20231c35511b"
  }'
```

### Configure Public Key in NornWeave

Add the public key to your environment configuration (see Step 5).

{{% /steps %}}

{{< callout type="info" >}}
When signature verification is enabled, SendGrid adds `X-Twilio-Email-Event-Webhook-Signature` and `X-Twilio-Email-Event-Webhook-Timestamp` headers to webhook requests. NornWeave validates these automatically when `SENDGRID_WEBHOOK_PUBLIC_KEY` is configured.
{{< /callout >}}

## Step 5: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Webhook signature verification (highly recommended for production)
SENDGRID_WEBHOOK_PUBLIC_KEY=MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
```

## Step 6: Verify Setup

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

{{% /steps %}}

## Troubleshooting

### Inbound Parse Not Working

- Verify MX records are correct with `dig MX mail.yourdomain.com`
- Check SendGrid's Activity Feed for incoming emails
- Ensure your webhook URL is publicly accessible

### Authentication Issues

- Regenerate API key if issues persist
- Verify the key has Mail Send permissions
