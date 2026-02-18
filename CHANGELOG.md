# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.8] - 2026-02-18

### Added

- **Demo mode** — local sandbox provider for trying NornWeave without email credentials or a real domain:
  - `nornweave api --demo` CLI flag for zero-configuration quickstart (no `.env` file needed)
  - `DemoAdapter` email provider (`EMAIL_PROVIDER=demo`) with synthetic message IDs, no real delivery
  - `POST /v1/demo/inbound` endpoint to simulate inbound emails for testing and `wait_for_reply` flows
  - Auto-creates `demo@demo.nornweave.local` inbox on startup
  - Loopback delivery: emails sent to demo inboxes are automatically delivered back as inbound messages
  - Domain defaults to `demo.nornweave.local` when in demo mode

---

## [0.1.7] - 2026-02-09

### Added

- Sample Email MCP Agent (`mcp_ai_agents/email_mcp_agent/`) demonstrating a customer-support use case with NornWeave's MCP tools
- FAQ entries comparing NornWeave to closed-source alternatives

### Changed

- Default database driver to SQLite with auto-table-creation for zero-config quickstart
- SQL-agnostic table creation in ORM for broader database compatibility

### Fixed

- Validate `EMAIL_DOMAIN` at inbox creation, returning HTTP 422 when missing instead of creating inboxes with empty domains
- Validate provider credentials in `get_email_provider()` dependency, returning a clear HTTP 422 before constructing adapters with missing API keys or hostnames
- Surface email send errors with `status="failed"` and error details instead of silently suppressing exceptions
- Startup warnings when `EMAIL_DOMAIN` is unset or selected provider is missing required credentials
- Comprehensive documentation fixes: quickstart flow, `.env.example` accuracy, removed misleading `Authorization: Bearer` headers from curl examples, added `EMAIL_DOMAIN` callouts to provider guides

---

## [0.1.6] - 2026-02-07

### Added

- Global send rate limiting for outbound email. Two new env vars (`GLOBAL_SEND_RATE_LIMIT_PER_MINUTE`, `GLOBAL_SEND_RATE_LIMIT_PER_HOUR`) cap sends per rolling minute/hour. Exceeding returns HTTP 429 with `Retry-After` header. In-memory sliding-window counters — no Redis required.
- Domain-level allow/blocklist filtering for inbound and outbound email. Four new env vars (`INBOUND_DOMAIN_ALLOWLIST`, `INBOUND_DOMAIN_BLOCKLIST`, `OUTBOUND_DOMAIN_ALLOWLIST`, `OUTBOUND_DOMAIN_BLOCKLIST`) accept comma-separated regex patterns. Blocklist takes precedence. Inbound rejections return `domain_blocked`; outbound rejections return HTTP 403.

---

## [0.1.5] - 2026-02-06

### Added

- IMAP/SMTP email provider (`EMAIL_PROVIDER=imap-smtp`): send via SMTP and receive via IMAP polling, connecting to any standard mail server (Gmail, Office 365, Fastmail, self-hosted, etc.) without a transactional email account
- Shared `ingest_message()` function in `verdandi/ingest.py` unifying inbound email processing across all providers
- RFC 822 email parser (`verdandi/email_parser.py`) for parsing raw IMAP messages into `InboundMessage` objects
- `imap_poll_state` database table for persistent IMAP UID tracking across restarts
- `POST /v1/inboxes/{inbox_id}/sync` endpoint for on-demand IMAP sync
- Configurable IMAP post-fetch behavior: `IMAP_MARK_AS_READ` and `IMAP_DELETE_AFTER_FETCH` settings
- Background IMAP poller with exponential backoff reconnect, managed by FastAPI lifespan

---

## [0.1.4] - 2026-02-05

### Added

- **LLM Thread Summaries** - Automatic thread summarization using your LLM provider:
  - Support for OpenAI, Anthropic, and Google Gemini as summarization backends
  - Opt-in via `LLM_PROVIDER` env var (disabled by default)
  - Summaries update on each new message using Talon-cleaned text (no quoted-reply duplication)
  - Customizable summarization prompt via `LLM_SUMMARY_PROMPT`
  - Daily token budget with `LLM_DAILY_TOKEN_LIMIT` to control costs
  - `summary` field on Thread and ThreadItem in REST API responses
  - MCP resources include summaries for agent triage workflows
  - New optional dependency extras: `pip install nornweave[openai]`, `[anthropic]`, `[gemini]`, or `[llm]` for all
- **Expanded MessageResponse** - API message responses now include all email metadata fields:
  - `subject`, `from_address`, `to_addresses`, `cc_addresses`, `bcc_addresses`, `reply_to_addresses`
  - `text`, `html`, `content_clean`, `timestamp`, `labels`, `preview`, `size`
  - `in_reply_to`, `references`, `metadata`
- **Flexible message search** - Enhanced `GET /v1/messages` endpoint:
  - Make `inbox_id` optional, add `thread_id` filter
  - Text search (`q` parameter) across subject, body, sender, and attachment filenames
  - Pagination support with `total` count in response
- **MCP `list_messages` tool** - New tool for listing messages with filters
- **Enhanced `search_email` MCP tool** - Now supports `thread_id` filter and returns expanded message data
- **Attachment storage adapters** - Pluggable storage backends for email attachments:
  - `LocalFilesystemStorage` - Store attachments on local filesystem (default)
  - `DatabaseBlobStorage` - Store as BLOBs in PostgreSQL/SQLite database
  - `S3Storage` - Store in AWS S3 or S3-compatible storage (MinIO, DigitalOcean Spaces)
  - `GCSStorage` - Store in Google Cloud Storage
- **Attachment API endpoints** - New REST API for attachment management:
  - `GET /v1/attachments` - List attachments by message, thread, or inbox
  - `GET /v1/attachments/{id}` - Get attachment metadata with download URL
  - `GET /v1/attachments/{id}/content` - Download attachment content (binary or base64)
- **Attachment MCP tools** - New MCP tools for AI agents:
  - `send_email_with_attachments` - Send emails with file attachments
  - `list_attachments` - List attachments for a message, thread, or inbox
  - `get_attachment_content` - Retrieve attachment content as base64
- **Send messages with attachments** - API and MCP support for sending emails with attachments (base64 encoded)
- **Signed URLs** - Secure, time-limited URLs for attachment downloads (local/database storage)
- **Presigned URLs** - Native cloud provider URLs for S3/GCS storage backends
- **MinIO support** - S3-compatible storage for development/testing in docker-compose
- **PyPI package extras** - New installation options:
  - `pip install nornweave[s3]` for S3 storage support
  - `pip install nornweave[gcs]` for GCS storage support

### Changed

- Updated `docker-compose.yml` with MinIO service for S3-compatible attachment storage testing
- Extended database schema with `attachments` table for metadata storage
- Updated component architecture diagrams to include attachment storage

---

## [0.1.3] - 2026-02-05

### Fixed

- **Email provider dependency loading** - Lazy-import only the adapter for the configured provider in `get_email_provider`, so optional dependencies (e.g. `cryptography` for SendGrid) are not required when using other providers (Mailgun, Resend, SES). Fixes 500 when sending email with Resend when SendGrid’s dependencies were not installed.

---

## [0.1.2] - 2026-02-04

### Added

- **PyPI packaging** - NornWeave is now available on PyPI:
  - Install with `pip install nornweave` (base package with SQLite)
  - Install with `pip install nornweave[postgres]` for PostgreSQL support
  - Install with `pip install nornweave[mcp]` for MCP server support
  - Install with `pip install nornweave[all]` for all features
- GitHub Actions workflow for PyPI publishing with trusted publishing (OIDC)
- Installation validation script (`scripts/validate_install.py`)

### Changed

- **Breaking**: PostgreSQL dependencies (`asyncpg`, `psycopg2-binary`) moved from base to `[postgres]` extra
  - Existing users running PostgreSQL should install with `pip install nornweave[postgres]`
  - Base package now works with SQLite out of the box without PostgreSQL dependencies
- Updated Dockerfile to explicitly install `[postgres,mcp]` extras
- Updated Makefile with new install targets (`install-postgres`, `install-mcp`, `install-prod`)
- Aligned MCP configuration examples across all documentation

---

## [0.1.1] - 2026-02-04

### Changed

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

[Unreleased]: https://github.com/DataCovey/nornweave/compare/v0.1.8...HEAD
[0.1.8]: https://github.com/DataCovey/nornweave/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/DataCovey/nornweave/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/DataCovey/nornweave/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/DataCovey/nornweave/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/DataCovey/nornweave/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/DataCovey/nornweave/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/DataCovey/nornweave/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/DataCovey/nornweave/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/DataCovey/nornweave/releases/tag/v0.1.0
