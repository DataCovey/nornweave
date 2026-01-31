---
title: Roadmap
---

NornWeave is being developed in phases. This page outlines the current status and upcoming features.

## Current Status

### Phase 1: Foundation (The Mail Proxy) - Available

The foundation layer is complete and provides core email functionality:

- **Virtual Inboxes**: Create email addresses for your AI agents
- **Webhook Ingestion**: Receive emails from Mailgun, SES, SendGrid, Resend
- **Persistent Storage**: PostgreSQL with abstracted storage adapters
- **Email Sending**: Send replies through your configured provider
- **API Key Authentication**: Secure your endpoints

### Phase 2: Intelligence (The Agent Layer) - Available

The intelligence layer adds LLM-friendly features:

- **Content Parsing**: HTML to clean Markdown conversion
- **Cruft Removal**: Automatic removal of reply quotes and signatures
- **Smart Threading**: Automatic conversation grouping via email headers
- **MCP Server**: Direct integration with Claude, Cursor, and other MCP clients
- **Attachment Processing**: Extract text from PDFs and documents

---

## Phase 3: Enterprise Platform - Coming Soon

Phase 3 will bring enterprise-grade features for production deployments.

### Semantic Search

Vector embeddings for intelligent message search.

```bash
# Instead of exact text matching...
POST /v1/search
{
  "query": "Find the invoice from last week"
}
```

- Uses vector embeddings (pgvector) for semantic understanding
- Natural language queries like "emails about refunds"
- Ranked results by relevance
- Filter by date, sender, inbox

### Real-time Webhooks

Register URLs to receive notifications when new messages arrive.

```bash
POST /v1/webhooks
{
  "url": "https://my-agent.com/webhook",
  "events": ["message.received"],
  "inbox_id": "ibx_123"
}
```

- Instant notifications for new messages
- Configurable event types
- Retry logic with exponential backoff
- Webhook signature verification

### Multi-Tenancy

Organizations and projects to isolate data for teams.

```
Organization
├── Project: Production
│   ├── Inbox: support@...
│   └── Inbox: sales@...
└── Project: Staging
    └── Inbox: test@...
```

- **Organizations**: Top-level isolation for companies
- **Projects**: Environments within an organization
- **API Keys**: Scoped to projects
- **Usage Tracking**: Per-project metrics

### Custom Domains

Manage DKIM/SPF verification status for your domains.

```bash
POST /v1/domains
{
  "domain": "mail.example.com"
}

# Response includes DNS records to configure
{
  "domain": "mail.example.com",
  "status": "pending",
  "dns_records": [
    {"type": "TXT", "name": "_dmarc", "value": "..."},
    {"type": "CNAME", "name": "selector._domainkey", "value": "..."}
  ]
}
```

- Domain verification workflow
- Automatic DNS record generation
- Status monitoring
- Multiple domains per project

### Rate Limiting and Credits

Protect against runaway agents and manage API usage.

```yaml
# Rate limit configuration
rate_limits:
  messages_per_minute: 60
  messages_per_day: 1000
  
credits:
  enabled: true
  monthly_limit: 10000
```

- Per-inbox rate limits
- Organization-wide quotas
- Usage alerts
- Credit-based billing support

### Analytics Dashboard

Visibility into email operations.

- Message volume over time
- Response time metrics
- Error rates and debugging
- Per-inbox statistics

---

## Future Considerations

These features are being evaluated for future phases:

### Calendar Integration

Parse and respond to calendar invites within email threads.

### Contact Management

Build and maintain contact profiles from email interactions.

### Template Engine

Pre-defined response templates for common scenarios.

### Approval Workflows

Human-in-the-loop approval before sending sensitive emails.

---

## Contributing

We welcome contributions! If you'd like to help build these features:

1. Check the [GitHub Issues](https://github.com/nornweave/nornweave/issues) for current priorities
2. Read the [Contributing Guide](https://github.com/nornweave/nornweave/blob/main/CONTRIBUTING.md)
3. Join the discussion in Issues or Discussions

{{< cards >}}
  {{< card link="https://github.com/nornweave/nornweave" title="GitHub Repository" icon="github" subtitle="Star, fork, or contribute" >}}
  {{< card link="https://github.com/nornweave/nornweave/issues" title="Issues" icon="exclamation-circle" subtitle="Report bugs or request features" >}}
{{< /cards >}}
