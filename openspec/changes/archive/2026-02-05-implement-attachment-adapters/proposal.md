## Why

NornWeave has partial attachment storage infrastructure (storage backends, models, database CRUD) but lacks the integration layer that makes attachments usable. Users cannot retrieve attachments via API, list attachments by thread/inbox, send messages with attachments, or use attachments through MCP tools. The storage backends also lack proper package extras for their cloud dependencies.

## What Changes

- **API Routes**: Add `/v1/attachments` endpoints to list and retrieve attachment metadata and binary content
- **Query by Context**: Enable listing attachments by message_id, thread_id, or inbox_id
- **Send with Attachments**: Integrate attachment handling into message sending (API and MCP)
- **MCP Tools**: Add attachment tools to muninn/ for AI agent access
- **Package Extras**: Add `s3`, `gcs` pypi extras with boto3 and google-cloud-storage dependencies
- **Complete Database Backend**: Finish DatabaseBlobStorage implementation (retrieve, delete, exists)
- **Content Encoding**: Store attachments as raw bytes (decode from base64 on input). On retrieval, user chooses format: raw binary (default) or base64-encoded

## Capabilities

### New Capabilities

- `attachment-api`: REST endpoints for listing and retrieving attachments by message/thread/inbox, downloading attachment content with signed URLs
- `attachment-mcp`: MCP tools for AI agents to list attachments and retrieve attachment content
- `attachment-send`: Integration of attachment handling into outbound message sending via API and MCP

### Modified Capabilities

- `python-packaging`: Add `s3` and `gcs` package extras with cloud storage dependencies (boto3, google-cloud-storage)

## Impact

- **Code**: New routes in `yggdrasil/routes/v1/attachments.py`, new MCP tools in `muninn/`, updates to `messages.py` routes and MCP tools
- **Database**: New query methods in `urdr/adapters/base.py` for listing by thread_id and inbox_id
- **Dependencies**: New optional dependencies in pyproject.toml (boto3 for `s3` extra, google-cloud-storage for `gcs` extra)
- **Storage**: Complete DatabaseBlobStorage implementation, ensure all backends are production-ready
- **APIs**: New `/v1/attachments` endpoints, updated message creation endpoints to accept attachments
