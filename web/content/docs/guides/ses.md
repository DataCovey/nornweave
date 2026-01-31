---
title: AWS SES Setup
weight: 3
---

This guide walks through setting up Amazon Simple Email Service (SES) as your email provider for NornWeave.

## Prerequisites

- An AWS account
- A domain you control for sending/receiving email
- Access to your domain's DNS settings
- AWS CLI configured (optional but helpful)

## Step 1: Verify Your Domain

{{< steps >}}

### Navigate to SES Console

Go to the [Amazon SES Console](https://console.aws.amazon.com/ses/).

### Verify Domain

Click **Verified identities** > **Create identity** > **Domain**.

Enter your domain (e.g., `mail.yourdomain.com`).

### Add DNS Records

SES will provide DNS records to verify ownership:

| Type | Name | Value |
|------|------|-------|
| CNAME | `_amazonses.mail` | `xxxxxxxx.dkim.amazonses.com` |
| CNAME | `xxxxx._domainkey.mail` | `xxxxx.dkim.amazonses.com` |
| TXT | `_amazonses.mail` | `xxxxxxxxxxxxxxxxxxxxxxxx` |

### Wait for Verification

Verification can take up to 72 hours, but usually completes within minutes.

{{< /steps >}}

## Step 2: Request Production Access

{{< callout type="warning" >}}
New SES accounts are in "sandbox mode" and can only send to verified addresses. Request production access to remove this limitation.
{{< /callout >}}

{{< steps >}}

### Navigate to Account Dashboard

In SES Console, go to **Account dashboard**.

### Request Production Access

Click **Request production access** and fill out the form:

- **Mail type**: Transactional
- **Website URL**: Your application URL
- **Use case description**: Explain NornWeave's purpose

### Wait for Approval

AWS typically approves within 24 hours.

{{< /steps >}}

## Step 3: Create IAM Credentials

{{< steps >}}

### Create IAM User

Go to [IAM Console](https://console.aws.amazon.com/iam/) > **Users** > **Add user**.

- Name: `nornweave-ses`
- Access type: **Programmatic access**

### Attach Policy

Create a custom policy or attach `AmazonSESFullAccess`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### Save Credentials

Copy the **Access Key ID** and **Secret Access Key**.

{{< /steps >}}

## Step 4: Configure Inbound Email

SES receiving is more complex than other providers. You'll need:

{{< steps >}}

### Create S3 Bucket

Create an S3 bucket to store incoming emails temporarily.

### Create Receipt Rule Set

In SES, go to **Email receiving** > **Rule sets** > **Create rule set**.

### Create Receipt Rule

Add a rule with:

- **Recipients**: `mail.yourdomain.com` (or specific addresses)
- **Actions**:
  1. S3: Store in your bucket
  2. Lambda: Trigger a function to call NornWeave webhook

### Configure MX Record

Add MX record pointing to SES:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | mail | `inbound-smtp.us-east-1.amazonaws.com` | 10 |

(Use the correct region for your SES setup)

{{< /steps >}}

## Step 5: Create Lambda Function (Optional)

To forward emails to NornWeave, create a Lambda function:

```python
import json
import urllib.request

def lambda_handler(event, context):
    # Parse SES event
    ses_message = event['Records'][0]['ses']
    
    # Forward to NornWeave
    webhook_url = 'https://your-server.com/webhooks/ses'
    
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(ses_message).encode(),
        headers={'Content-Type': 'application/json'}
    )
    
    urllib.request.urlopen(req)
    
    return {'statusCode': 200}
```

## Step 6: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
```

## Step 7: Verify Setup

{{< steps >}}

### Restart NornWeave

```bash
docker compose restart api
```

### Test Sending

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_test",
    "to": ["verified@email.com"],
    "subject": "Test",
    "body": "Hello from NornWeave!"
  }'
```

{{< /steps >}}

## Troubleshooting

### Emails Not Being Received

- Verify MX records are correct
- Check SES receipt rule is active
- Verify Lambda function permissions

### Sending Fails

- Ensure you're out of sandbox mode (or sending to verified addresses)
- Check IAM permissions
- Verify the region matches your SES configuration

### Rate Limits

SES has sending limits. Monitor your quota in the SES dashboard and request increases as needed.
