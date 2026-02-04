---
title: "n8n Integration"
description: "Connect NornWeave to n8n for workflow automation"
weight: 10
---

[n8n](https://n8n.io/) is a popular open-source workflow automation platform. The `n8n-nodes-nornweave` community node lets you integrate NornWeave into your n8n workflows for email automation.

## Installation

### From n8n Community Nodes

1. Go to **Settings** > **Community Nodes**
2. Click **Install**
3. Search for `n8n-nodes-nornweave`
4. Accept the risks and click **Install**

### Manual Installation (Self-hosted n8n)

```bash
npm install n8n-nodes-nornweave
```

Then restart your n8n instance.

## Setting Up Credentials

1. In n8n, go to **Credentials** > **Add credential**
2. Search for "NornWeave API"
3. Enter your configuration:

| Field | Description | Example |
|-------|-------------|---------|
| Base URL | Your NornWeave instance URL | `http://localhost:8000` |
| API Key | Optional authentication key | `nw_key_...` |

4. Click **Save** - n8n will test the connection

## Available Nodes

### NornWeave (Action Node)

Perform operations on your NornWeave instance:

#### Inbox Operations
- **Create**: Create a new inbox with a custom email username
- **Delete**: Remove an inbox and all its data
- **Get**: Retrieve inbox details
- **Get Many**: List all inboxes with pagination

#### Message Operations
- **Get**: Retrieve a specific message
- **Get Many**: List messages in an inbox
- **Send**: Send an outbound email (Markdown supported)

#### Thread Operations
- **Get**: Retrieve a conversation thread with all messages
- **Get Many**: List threads in an inbox

#### Search Operations
- **Query**: Search messages by content

### NornWeave Trigger

Trigger workflows when email events occur:

| Event | Description |
|-------|-------------|
| `email.received` | New inbound email arrived |
| `email.sent` | Outbound email accepted |
| `email.delivered` | Email delivered successfully |
| `email.bounced` | Email bounced (hard fail) |
| `email.opened` | Recipient opened email |
| `email.clicked` | Recipient clicked a link |

## Webhook Configuration

The NornWeave Trigger node receives events via webhooks. You need to configure your email provider to forward events to the n8n webhook URL.

### Step 1: Get the Webhook URL

1. Add a **NornWeave Trigger** node to your workflow
2. Select the events you want to listen for
3. Click **Listen for Test Event** to see the test URL
4. For production, use the **Production URL** (visible when workflow is saved)

### Step 2: Configure Your Email Provider

#### Mailgun

1. Go to your Mailgun dashboard → **Sending** → **Webhooks**
2. Add a new webhook pointing to your n8n webhook URL
3. Select the events to forward

#### SendGrid

1. Go to SendGrid → **Settings** → **Mail Settings** → **Event Webhook**
2. Enable the webhook and enter your n8n URL
3. Select the events to track

#### AWS SES

1. Create an SNS topic for SES notifications
2. Subscribe your n8n webhook URL to the SNS topic
3. Configure SES to publish events to the SNS topic

#### Resend

1. Go to Resend dashboard → **Webhooks**
2. Add a new endpoint with your n8n URL
3. Select the events to receive

## Example Workflows

### AI-Powered Auto-Reply

Automatically respond to support emails using AI:

```
[NornWeave Trigger]
  ↓ (email.received)
[IF] Subject contains "support"
  ↓ (true)
[NornWeave] Get Thread
  ↓
[OpenAI] Generate reply based on thread context
  ↓
[NornWeave] Send Message (reply_to_thread_id)
```

### Lead Capture to CRM

Capture inbound emails and create CRM records:

```
[NornWeave Trigger]
  ↓ (email.received)
[NornWeave] Get Message
  ↓
[OpenAI] Extract contact info from email
  ↓
[HubSpot/Salesforce] Create Contact
```

### Bounce Notification

Alert your team when emails bounce:

```
[NornWeave Trigger]
  ↓ (email.bounced)
[Slack] Post message to #email-alerts
  ↓
[NornWeave] Get Thread
  ↓
[Notion] Add to bounced emails database
```

### Scheduled Inbox Digest

Send a daily summary of inbox activity:

```
[Schedule Trigger] (daily at 9am)
  ↓
[NornWeave] Get Many Threads (limit: 50)
  ↓
[OpenAI] Summarize thread subjects and status
  ↓
[Email] Send digest to team
```

## Tips

### Use Thread Context for AI

When building AI-powered workflows, use **Thread > Get** to retrieve the full conversation history. This gives AI models the context they need to generate appropriate responses.

### Filter Events

Configure the trigger to only listen for events you need. This reduces noise and improves workflow efficiency.

### Handle Errors

Add error handling nodes to manage cases where:
- The NornWeave instance is unreachable
- A resource (inbox, message) is not found
- Rate limits are hit

## Troubleshooting

### Connection Failed

- Verify your Base URL is correct and accessible from n8n
- Check that NornWeave is running (`/health` endpoint should return OK)
- If using Docker, ensure network connectivity between containers

### Webhook Not Triggering

- Confirm the webhook URL is correctly configured in your email provider
- Check that the workflow is activated (not just saved)
- Verify the event type is selected in the trigger node
- Test with the "Listen for Test Event" feature

### Authentication Errors

- Double-check your API key if authentication is enabled
- Ensure the key hasn't expired or been revoked

## Resources

- [n8n Community Nodes Documentation](https://docs.n8n.io/integrations/community-nodes/)
- [NornWeave API Reference](/docs/api)
- [npm package](https://www.npmjs.com/package/n8n-nodes-nornweave)
