# Webhooks

NornWeave receives inbound emails via webhooks from email providers. Configure your email provider to forward incoming emails to NornWeave's webhook endpoints.

## Supported Providers

| Provider | Webhook Endpoint |
|----------|------------------|
| Mailgun | `POST /webhooks/mailgun` |
| Amazon SES | `POST /webhooks/ses` |
| SendGrid | `POST /webhooks/sendgrid` |
| Resend | `POST /webhooks/resend` |

## Provider Configuration

### Mailgun

1. Log into your Mailgun dashboard
2. Navigate to **Receiving** → **Create Route**
3. Set up a catch-all or specific route:
   - **Expression Type**: Match Recipient
   - **Recipient**: `.*@yourdomain.com` (or specific addresses)
   - **Forward**: `https://your-nornweave-server.com/webhooks/mailgun`
   - **Actions**: Check "Forward" and "Store and Notify"

```bash
# Test with curl (simulating Mailgun webhook)
curl -X POST https://your-server.com/webhooks/mailgun \
  -F "recipient=support@yourdomain.com" \
  -F "sender=customer@example.com" \
  -F "subject=Test Email" \
  -F "body-plain=Hello, this is a test message."
```

### Amazon SES

1. Set up SES to receive emails (requires verified domain)
2. Create an SNS topic for email notifications
3. Configure SNS to POST to NornWeave:
   - **Protocol**: HTTPS
   - **Endpoint**: `https://your-nornweave-server.com/webhooks/ses`

```python
# SES webhook payload structure
{
    "Type": "Notification",
    "Message": {
        "notificationType": "Received",
        "mail": {
            "messageId": "...",
            "source": "sender@example.com",
            "destination": ["inbox@yourdomain.com"],
            "headers": [...],
            "commonHeaders": {
                "subject": "Email Subject",
                "from": ["Sender <sender@example.com>"],
                "to": ["inbox@yourdomain.com"]
            }
        },
        "content": "Raw email content..."
    }
}
```

### SendGrid

1. Go to **Settings** → **Inbound Parse** in SendGrid
2. Add a host and URL:
   - **Host**: Your receiving domain (e.g., `yourdomain.com`)
   - **URL**: `https://your-nornweave-server.com/webhooks/sendgrid`
3. Enable **POST the raw, full MIME message** for attachments

```bash
# SendGrid sends multipart/form-data
curl -X POST https://your-server.com/webhooks/sendgrid \
  -F "to=support@yourdomain.com" \
  -F "from=customer@example.com" \
  -F "subject=Test Email" \
  -F "text=Plain text body" \
  -F "html=<p>HTML body</p>"
```

### Resend

1. Configure Resend's inbound email feature
2. Set webhook URL: `https://your-nornweave-server.com/webhooks/resend`

```json
// Resend webhook payload
{
  "type": "email.received",
  "data": {
    "from": "sender@example.com",
    "to": ["inbox@yourdomain.com"],
    "subject": "Email Subject",
    "text": "Plain text content",
    "html": "<p>HTML content</p>"
  }
}
```

## Webhook Processing

When NornWeave receives a webhook, it:

1. **Parses the payload** using the provider-specific adapter
2. **Finds the inbox** by matching the recipient email address
3. **Resolves threading** using `In-Reply-To` and `References` headers
4. **Converts HTML to Markdown** for LLM-ready content
5. **Stores the message** linked to the appropriate thread

### Response Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Email processed successfully |
| `200 OK` with `{"status": "no_inbox"}` | No inbox found for recipient (logged, not retried) |
| `400 Bad Request` | Failed to parse webhook payload |

## Security

### Webhook Verification

For production deployments, verify webhook signatures to ensure requests come from your email provider.

**Mailgun Example:**

```python
import hashlib
import hmac

def verify_mailgun_signature(
    api_key: str,
    timestamp: str,
    token: str,
    signature: str
) -> bool:
    """Verify Mailgun webhook signature."""
    data = f"{timestamp}{token}"
    expected = hmac.new(
        api_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### HTTPS

Always use HTTPS for webhook endpoints in production to encrypt email content in transit.

### IP Allowlisting

Optionally restrict webhook endpoints to provider IP ranges:

- **Mailgun**: [Mailgun IP ranges](https://documentation.mailgun.com/en/latest/user_manual.html#webhooks)
- **SendGrid**: [SendGrid IP addresses](https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook)
- **SES**: AWS IP ranges for your region

## Local Development

For local development, use a tunneling service to expose your local server:

```bash
# Using ngrok
ngrok http 8000

# Configure webhook URL as: https://abc123.ngrok.io/webhooks/mailgun
```

## Troubleshooting

### No Inbox Found

If webhooks return `{"status": "no_inbox"}`:
- Verify the inbox exists with the correct email address
- Check the `EMAIL_DOMAIN` environment variable matches your provider domain
- Ensure the recipient address in the webhook matches exactly

### Threading Not Working

If messages aren't being grouped into threads:
- Check that your email provider includes `In-Reply-To` and `References` headers
- Verify outbound messages include proper `Message-ID` headers
- Check the `provider_message_id` is being stored correctly

### Missing Content

If `content_clean` is empty:
- Verify HTML→Markdown conversion is working
- Check both `body-plain` and `body-html` fields in the webhook payload
- Review the verdandi parser logs for errors
