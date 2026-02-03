---
title: Resend Setup Guide
description: "Step-by-step Resend integration with NornWeave. API key creation, domain verification, webhook setup for receiving emails for AI agent email."
weight: 4
keywords:
  - Resend setup
  - Resend webhook
  - Resend API integration
  - Resend inbound email
  - email webhook setup
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

This guide walks through setting up Resend as your email provider for NornWeave.

## Prerequisites

- A Resend account ([sign up](https://resend.com/))
- A domain you control for sending/receiving email
- Access to your domain's DNS settings

## Step 1: Create API Key

{{% steps %}}

### Log in to Resend

Go to the [Resend Dashboard](https://resend.com/).

### Create API Key

Navigate to **API Keys** > **Create API Key**.

- Name: `NornWeave`
- Permissions: **Full Access** (required for both sending and receiving)

### Copy the Key

Copy the API key immediately - it won't be shown again. It looks like: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

{{< callout type="warning" >}}
Keep your API key secret. Never commit it to version control.
{{< /callout >}}

{{% /steps %}}

## Step 2: Verify Your Domain

{{% steps %}}

### Navigate to Domains

Go to the [Domains page](https://resend.com/domains) > **Add Domain**.

{{< callout type="info" >}}
We recommend using a subdomain like `mail.` or `updates.` rather than your root domain to isolate sending reputation.
{{< /callout >}}

### Add DNS Records

Resend will provide DNS records to verify ownership. You'll need to add:

| Type | Name | Value |
|------|------|-------|
| TXT | `send.mail` | `v=spf1 include:amazonses.com ~all` |
| CNAME | `resend._domainkey.mail` | `resend._domainkey.resend.dev` |
| MX | `mail` | `feedback-smtp.us-east-1.amazonses.com` (priority 10) |

The exact values will be shown in your Resend dashboard for your specific domain.

### Verify Domain

Click **Verify DNS Records** in Resend. Verification typically completes within minutes, but can take up to 72 hours.

{{% /steps %}}

## Step 3: Enable Receiving

Resend supports receiving emails (inbound) via webhooks. You have two options:

### Option A: Use Resend-Managed Domain

Resend provides a `.resend.app` domain for testing. Any emails sent to `<anything>@<id>.resend.app` will be received.

To find your Resend domain:
1. Go to the [Emails page](https://resend.com/emails)
2. Select the **Receiving** tab
3. The predefined address should be shown.

### Option B: Use Custom Domain

For production, use your own domain:

{{% steps %}}

### Enable Receiving

Go to your domain details and enable the **Receiving** toggle.

### Add MX Record

Add the MX record shown in the Resend dashboard to your DNS:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | mail | `inbound-smtp.resend.com` | 10 |

{{< callout type="warning" >}}
If you already have MX records for your root domain, use a subdomain (e.g., `mail.yourdomain.com`) to avoid conflicts.
{{< /callout >}}

### Verify MX Record

Click **I've added the record** and wait for verification.

{{% /steps %}}

## Step 4: Configure Webhooks

{{% steps %}}

### Navigate to Webhooks

Go to the [Webhooks page](https://resend.com/webhooks).

### Add Webhook

Click **Add Webhook** with these settings:

- **URL**: `https://your-server.com/webhooks/resend`
- **Events**: Select `email.received` (and optionally `email.delivered`, `email.bounced` for tracking)

### Copy Webhook Secret

Copy the webhook signing secret for verifying webhook authenticity.

{{% /steps %}}

## Step 5: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Your API key from Step 1 |
| `RESEND_WEBHOOK_SECRET` | Webhook signing secret for verification |

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

You should see the incoming webhook being processed.

{{% /steps %}}

## Webhook Payload

Resend sends a JSON webhook payload for received emails:

```json
{
  "type": "email.received",
  "created_at": "2024-02-22T23:41:12.126Z",
  "data": {
    "email_id": "56761188-7520-42d8-8898-ff6fc54ce618",
    "created_at": "2024-02-22T23:41:11.894719+00:00",
    "from": "Sender <sender@example.com>",
    "to": ["test@mail.yourdomain.com"],
    "cc": [],
    "bcc": [],
    "message_id": "<example+123>",
    "subject": "Test Email",
    "attachments": [
      {
        "id": "2a0c9ce0-3112-4728-976e-47ddcd16a318",
        "filename": "document.pdf",
        "content_type": "application/pdf"
      }
    ]
  }
}
```

{{< callout type="info" >}}
Webhooks include metadata only, not the email body or attachment content. Use the [Received Emails API](https://resend.com/docs/api-reference/emails/retrieve-received-email) to fetch the full content.
{{< /callout >}}

## Troubleshooting

### Webhook Not Receiving

- Verify your server is publicly accessible
- Check the webhook events log in Resend dashboard
- Ensure you selected the `email.received` event type
- Verify webhook signature validation is working

### Domain Verification Failed

- DNS changes can take up to 72 hours to propagate
- Use `dig` or `nslookup` to verify records
- Ensure no typos in the DNS values
- Check the domain status in Resend dashboard

### Emails Not Arriving

- Verify MX records are correct with `dig MX mail.yourdomain.com`
- Ensure MX record has the lowest priority if you have multiple
- Check the Receiving tab in Resend for incoming emails

### Webhook Verification Failing

Resend webhooks include `svix-id`, `svix-timestamp`, and `svix-signature` headers for verification. Ensure you're using the correct webhook secret.

```python
# Example verification
import hashlib
import hmac

def verify_webhook(payload, headers, secret):
    msg_id = headers.get('svix-id')
    timestamp = headers.get('svix-timestamp')
    signature = headers.get('svix-signature')
    
    signed_content = f"{msg_id}.{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(),
        signed_content.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"v1,{expected}", signature)
```
