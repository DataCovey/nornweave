## Why

n8n is a popular open-source workflow automation platform with a large community of users building integrations. Currently, n8n users cannot integrate NornWeave into their automations without manually crafting HTTP requests. A native community node would enable users to easily build email-powered workflows using NornWeave's stateful inbox capabilities—automating support ticket handling, lead nurturing sequences, AI agent email loops, and more.

## What Changes

- **New npm package**: `n8n-nodes-nornweave` published to npm as a community node
- **Credential type**: NornWeave API credentials (base URL + optional API key)
- **Regular node operations**: Inbox management (CRUD), message operations (send, list, get), thread operations (list, get), and search
- **Trigger node**: Webhook-based trigger for new inbound emails and delivery events (sent, delivered, bounced, opened, clicked)
- **Documentation**: Integration guide in NornWeave docs site

## Capabilities

### New Capabilities
- `n8n-node`: Community node package providing NornWeave operations and triggers for n8n workflow automation

### Modified Capabilities
<!-- No existing capabilities are being modified -->

## Impact

- **New repository/package**: Standalone npm package following n8n community node conventions (can live in this repo under `packages/n8n-nodes-nornweave/` or separate repo)
- **Dependencies**: n8n-workflow, n8n-core (peer dependencies)
- **Build tooling**: TypeScript compilation, npm publishing workflow
- **Documentation**: New guide at `web/content/docs/integrations/n8n.md`
- **Testing**: Unit tests for node operations, integration tests against local NornWeave instance
