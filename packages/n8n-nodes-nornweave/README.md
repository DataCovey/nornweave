# @nornweave/n8n-nodes-nornweave

This is an n8n community node for [NornWeave](https://nornweave.datacovey.com/) - an open-source, self-hosted Inbox-as-a-Service API for AI Agents.

NornWeave provides a stateful email layer (Inboxes, Threads, History) and an intelligent layer (Markdown parsing, Semantic Search) for LLMs.

[n8n](https://n8n.io/) is a [fair-code licensed](https://docs.n8n.io/reference/license/) workflow automation platform.

## Installation

Follow the [installation guide](https://docs.n8n.io/integrations/community-nodes/installation/) in the n8n community nodes documentation.

### Quick Install

1. Go to **Settings** > **Community Nodes**
2. Select **Install**
3. Enter `@nornweave/n8n-nodes-nornweave`
4. Agree to the risks and select **Install**

## Credentials

To connect to your NornWeave instance, you need to create credentials:

1. Go to **Credentials** > **Add credential**
2. Search for "NornWeave API"
3. Configure:
   - **Base URL**: The URL of your NornWeave instance (e.g., `http://localhost:8000` or `https://nornweave.yourdomain.com`)
   - **API Key** (optional): If your instance requires authentication, enter your API key

The credential will be tested by calling the `/health` endpoint on your NornWeave instance.

## Operations

### NornWeave Node

The main node supports the following operations:

#### Inbox
- **Create**: Create a new email inbox
- **Delete**: Delete an inbox
- **Get**: Get inbox details by ID
- **Get Many**: List all inboxes

#### Message
- **Get**: Get a message by ID
- **Get Many**: List messages in an inbox
- **Send**: Send an outbound email (supports Markdown body, reply threading)

#### Thread
- **Get**: Get a thread with all messages (LLM-ready format)
- **Get Many**: List threads in an inbox

#### Search
- **Query**: Search messages by content

### NornWeave Trigger

The trigger node listens for webhook events from NornWeave:

- **Email Received**: New inbound email arrived
- **Email Sent**: Outbound email accepted for delivery
- **Email Delivered**: Email successfully delivered
- **Email Bounced**: Email bounced (permanent failure)
- **Email Opened**: Recipient opened the email
- **Email Clicked**: Recipient clicked a link

## Webhook Setup

The NornWeave Trigger requires webhook configuration in your email provider:

1. Add a **NornWeave Trigger** node to your workflow
2. Copy the **Webhook URL** shown in the node (use the Production URL for live workflows)
3. Configure your email provider (Mailgun, SendGrid, SES, Resend) to forward webhooks to this URL
4. Activate your workflow

See the [NornWeave n8n integration guide](https://nornweave.datacovey.com/docs/integrations/n8n/) for detailed setup instructions for each provider.

## Example Workflows

### Auto-reply to Support Emails

```
NornWeave Trigger (email.received) 
  → IF (subject contains "support")
  → OpenAI (generate reply)
  → NornWeave (Send message, reply_to_thread_id)
```

### Notify on Email Bounce

```
NornWeave Trigger (email.bounced)
  → Slack (post to #alerts channel)
```

### Weekly Inbox Summary

```
Schedule Trigger (weekly)
  → NornWeave (Get Many threads)
  → OpenAI (summarize)
  → Email (send summary)
```

## Resources

- [NornWeave Documentation](https://nornweave.datacovey.com/docs)
- [NornWeave GitHub](https://github.com/DataCovey/nornweave)
- [n8n Community Nodes Documentation](https://docs.n8n.io/integrations/community-nodes/)

## License

MIT
