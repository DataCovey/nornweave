---
title: AWS SES Setup Guide
description: "Configure Amazon SES with NornWeave. Domain verification, SNS notifications for inbound email, and AI agent email integration."
weight: 3
keywords:
  - AWS SES setup
  - Amazon SES integration
  - SES webhook
  - SES SNS notification
  - AWS email service
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

This guide walks through setting up Amazon Simple Email Service (SES) as your email provider for NornWeave.

## Prerequisites

- An AWS account
- A domain you control for sending/receiving email
- Access to your domain's DNS settings
- AWS CLI configured (optional but helpful)

## Regional Availability

{{< callout type="info" >}}
SES email **receiving** is only available in specific regions: us-east-1, us-east-2, us-west-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, and others. Check the [AWS SES endpoints documentation](https://docs.aws.amazon.com/general/latest/gr/ses.html) for the full list.
{{< /callout >}}

## Step 1: Verify Your Domain

{{% steps %}}

### Navigate to SES Console

Go to the [Amazon SES Console](https://console.aws.amazon.com/ses/).

### Verify Domain

Click **Verified identities** > **Create identity** > **Domain**.

Enter your domain (e.g., `mail.yourdomain.com`).

### Add DNS Records

SES will provide DNS records to verify ownership and enable DKIM:

| Type | Name | Value |
|------|------|-------|
| CNAME | `_amazonses.mail` | `xxxxxxxx.dkim.amazonses.com` |
| CNAME | `xxxxx._domainkey.mail` | `xxxxx.dkim.amazonses.com` |
| TXT | `_amazonses.mail` | `xxxxxxxxxxxxxxxxxxxxxxxx` |

### Wait for Verification

Verification can take up to 72 hours, but usually completes within minutes.

{{% /steps %}}

## Step 2: Request Production Access

{{< callout type="warning" >}}
New SES accounts are in "sandbox mode" and can only send to verified addresses. Request production access to remove this limitation.
{{< /callout >}}

{{% steps %}}

### Navigate to Account Dashboard

In SES Console, go to **Account dashboard**.

### Request Production Access

Click **Request production access** and fill out the form:

- **Mail type**: Transactional
- **Website URL**: Your application URL
- **Use case description**: Explain NornWeave's purpose (AI agent email management)

### Wait for Approval

AWS typically approves within 24 hours.

{{% /steps %}}

## Step 3: Create IAM Credentials

{{% steps %}}

### Create IAM User

Go to [IAM Console](https://console.aws.amazon.com/iam/) > **Users** > **Add user**.

- Name: `nornweave-ses`
- Access type: **Programmatic access**

### Attach Policy

Create a custom policy with minimal permissions:

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

{{% /steps %}}

## Step 4: Configure Inbound Email with SNS

NornWeave receives inbound emails via SNS notifications. This is the simplest setup (no S3 or Lambda required).

{{< callout type="info" >}}
SNS notifications have a 150KB size limit. For larger emails, see the [Advanced: S3 Storage](#advanced-s3-storage-for-large-emails) section below.
{{< /callout >}}

{{% steps %}}

### Create SNS Topic

Go to [SNS Console](https://console.aws.amazon.com/sns/) > **Topics** > **Create topic**.

- **Type**: Standard
- **Name**: `nornweave-ses-inbound`

### Create HTTPS Subscription

In your SNS topic, click **Create subscription**:

- **Protocol**: HTTPS
- **Endpoint**: `https://your-server.com/webhooks/ses`

{{< callout type="warning" >}}
SNS will send a subscription confirmation request. NornWeave automatically confirms these when signature verification passes. Make sure your webhook endpoint is publicly accessible.
{{< /callout >}}

### Configure MX Record

Add MX record pointing to SES for your receiving subdomain:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | mail | `inbound-smtp.us-east-1.amazonaws.com` | 10 |

Use the correct region endpoint for your SES setup.

### Create Receipt Rule Set

In SES Console, go to **Email receiving** > **Rule sets** > **Create rule set**.

Name: `nornweave-rules`

### Create Receipt Rule

Add a rule in your rule set:

1. Click **Create rule**
2. **Recipients**: Leave empty to match all, or specify addresses/domains
3. **Actions**: Add **SNS** action
   - **SNS topic**: Select `nornweave-ses-inbound`
   - **Encoding**: UTF-8
4. **Enable spam and virus scanning**: Recommended

### Activate Rule Set

Select your rule set and click **Set as active**.

{{% /steps %}}

## Step 5: Configure NornWeave

Update your `.env` file:

```bash
EMAIL_PROVIDER=ses
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

# Optional: SES configuration set for tracking
AWS_SES_CONFIGURATION_SET=
```

## Step 6: Verify Setup

{{% steps %}}

### Restart NornWeave

```bash
docker compose restart api
```

### Check Logs for Subscription Confirmation

```bash
docker compose logs -f api
```

You should see: "SNS subscription confirmed successfully"

### Create a Test Inbox

```bash
curl -X POST http://localhost:8000/v1/inboxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email_username": "test"}'
```

### Test Receiving

Send an email to `test@mail.yourdomain.com` from your personal email.

### Test Sending

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inbox_id": "ibx_test",
    "to": ["your@email.com"],
    "subject": "Test from NornWeave",
    "body": "Hello from NornWeave via SES!"
  }'
```

{{% /steps %}}

## Advanced: S3 Storage for Large Emails

For emails larger than 150KB (common with attachments), use S3 storage:

{{% steps %}}

### Create S3 Bucket

Create an S3 bucket to store incoming emails:

```bash
aws s3 mb s3://nornweave-ses-emails --region us-east-1
```

### Update S3 Bucket Policy

Add a policy allowing SES to write to the bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ses.amazonaws.com"},
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::nornweave-ses-emails/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceAccount": "YOUR_ACCOUNT_ID"
        }
      }
    }
  ]
}
```

### Update Receipt Rule

Modify your receipt rule to:

1. **First action**: S3 (store the email)
2. **Second action**: SNS (notify NornWeave)

{{< callout type="info" >}}
S3 integration for NornWeave is planned for a future release. For now, use a Lambda function to forward the email content.
{{< /callout >}}

{{% /steps %}}

## Troubleshooting

### Inbound Emails Not Arriving

- Verify MX records with `dig MX mail.yourdomain.com`
- Check receipt rule set is **active** (only one can be active)
- Verify SNS subscription is **confirmed** (check SNS console)
- Check NornWeave logs for errors

### SNS Subscription Not Confirming

- Ensure webhook URL is publicly accessible (not localhost)
- Check firewall/security groups allow HTTPS traffic
- Verify SSL certificate is valid

### Sending Fails

- Ensure you're out of sandbox mode (or sending to verified addresses)
- Check IAM permissions include `ses:SendEmail`
- Verify the region matches your verified identity
- Check SES sending quota in the dashboard

### Signature Verification Fails

- Ensure server time is synchronized (NTP)
- Check that the full SNS message body is passed to NornWeave unchanged

### Rate Limits

SES has sending limits that start low (200/day in sandbox). Monitor your quota in the SES dashboard and request increases as needed.

| Quota | Sandbox | Production (typical) |
|-------|---------|---------------------|
| Daily sending | 200 | 50,000+ |
| Sending rate | 1/sec | 14/sec |
