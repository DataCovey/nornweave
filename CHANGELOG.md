# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 0.1.3

### Added

- (None yet)

### Changed

- (None yet)

### Deprecated

- (None yet)

### Removed

- (None yet)

### Fixed

- (None yet)

### Security

- (None yet)
---

## [0.1.1] - 2026-02-04

### Added

- **MCP Server implementation** (Huginn & Muninn) for AI agent integration:
  - FastMCP-based server with 2 resources and 4 tools
  - Resources: `email://inbox/{id}/recent`, `email://thread/{id}`
  - Tools: `create_inbox`, `send_email`, `search_email`, `wait_for_reply`
  - Support for three transports: stdio (default), SSE, HTTP
  - CLI command `nornweave mcp` with transport selection
  - Registry metadata for Smithery.ai, mcp-get.com, glama.ai
  - Full documentation at `web/content/docs/api/mcp.md`
- n8n community node (`n8n-nodes-nornweave`) for workflow automation:
  - NornWeave action node with Inbox, Message, Thread, and Search operations
  - NornWeave Trigger node for webhook-based workflow triggers
  - Support for email events: received, sent, delivered, bounced, opened, clicked
  - Declarative-style implementation following n8n best practices
  - Full documentation at `web/content/docs/integrations/n8n.md`
- Full SendGrid adapter implementation with:
  - Email sending via v3 Mail Send API (threading headers, CC/BCC, attachments)
  - Inbound Parse webhook parsing with attachment support
  - ECDSA webhook signature verification
  - SPF/DKIM result extraction
- Resend webhook and sending implementation
- Full AWS SES adapter implementation with:
  - Email sending via SES v2 API with Content.Simple (threading headers, CC/BCC, attachments)
  - AWS Signature Version 4 authentication
  - Inbound email via SNS notifications with MIME parsing
  - SNS signature verification using X.509 certificates
  - Automatic SNS subscription confirmation
  - SPF/DKIM/DMARC verdict extraction from SES receipt
  - Updated SES setup guide with SNS-based inbound email configuration

---

## [0.1.0] - 2026-02-02

Initial release. See [Unreleased] for current development.

### Added

- Mailgun webhook and sending implementation
- Implemented **Yggdrasil**: receives the webhook and routes to the appropriate handler
- Implemented **Verdandi** for message and thread parsing
- Implemented **Skuld**, basic API
- Implemented **Urdr**, basic Storage (PSQL and SQLite)
- E2E testing

[Unreleased]: https://github.com/DataCovey/nornweave/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DataCovey/nornweave/releases/tag/v0.1.0
