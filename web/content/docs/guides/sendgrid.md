---
title: SendGrid Setup
weight: 2
---

This guide walks through setting up SendGrid as your email provider for NornWeave.

## Prerequisites

- A SendGrid account ([sign up](https://sendgrid.com/))
- A domain you control for sending/receiving email
- Access to your domain's DNS settings

## Step 1: Create API Key

{{< steps >}}

### Log in to SendGrid

Go to the [SendGrid Dashboard](https://app.sendgrid.com/).

### Create API Key

Navigate to **Settings** > **API Keys** > **Create API Key**.

- Name: `NornWeave`
- Permissions: **Full Access** (or restrict to Mail Send and Inbound Parse)

### Copy the Key

Copy the API key immediately - it won't be shown again.

{{< /steps >}}

## Step 2: Authenticate Your Domain

{{< steps >}}

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

{{< /steps >}}

## Step 3: Configure Inbound Parse

{{< steps >}}

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

{{< /steps >}}

## Step 4: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 5: Verify Setup

{{< steps >}}

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

{{< /steps >}}

## Troubleshooting

### Inbound Parse Not Working

- Verify MX records are correct with `dig MX mail.yourdomain.com`
- Check SendGrid's Activity Feed for incoming emails
- Ensure your webhook URL is publicly accessible

### Authentication Issues

- Regenerate API key if issues persist
- Verify the key has Mail Send permissions
