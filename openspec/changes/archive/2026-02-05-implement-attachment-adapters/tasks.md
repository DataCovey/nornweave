## 1. Package Extras

- [x] 1.1 Add `s3` extra to pyproject.toml with `boto3>=1.35.0` dependency
- [x] 1.2 Add `gcs` extra to pyproject.toml with `google-cloud-storage>=2.18.0` dependency
- [x] 1.3 Update `all` extra to include `s3` and `gcs`
- [x] 1.4 Verify lazy imports in S3Storage and GCSStorage provide clear error messages

## 2. Database Layer

- [x] 2.1 Add `list_attachments_for_thread` method to database adapter in `urdr/adapters/base.py`
- [x] 2.2 Add `list_attachments_for_inbox` method to database adapter in `urdr/adapters/base.py`
- [x] 2.3 Ensure AttachmentORM has `storage_path`, `storage_backend`, `content_hash`, `content` fields

## 3. Attachment API Routes

- [x] 3.1 Create `yggdrasil/routes/v1/attachments.py` router module
- [x] 3.2 Implement `GET /v1/attachments` endpoint with message_id/thread_id/inbox_id filters
- [x] 3.3 Implement `GET /v1/attachments/{attachment_id}` endpoint for metadata
- [x] 3.4 Implement `GET /v1/attachments/{attachment_id}/content` endpoint with format param
- [x] 3.5 Add signed URL verification for local and database backends
- [x] 3.6 Register attachments router in `yggdrasil/routes/v1/__init__.py`

## 4. Message Sending with Attachments

- [x] 4.1 Create `SendAttachmentInput` Pydantic model in messages route
- [x] 4.2 Extend `SendMessageRequest` with optional `attachments` field
- [x] 4.3 Implement base64 decoding and validation for attachment content
- [x] 4.4 Integrate attachment storage in `send_message` endpoint
- [x] 4.5 Create attachment database records linked to message
- [x] 4.6 Pass attachments to email provider's `send_email` method
- [x] 4.7 Ensure atomic transaction for message and attachment creation

## 5. MCP Tools

- [x] 5.1 Add `list_attachments` tool to `muninn/tools.py`
- [x] 5.2 Add `get_attachment_content` tool to `muninn/tools.py` (always base64)
- [x] 5.3 Add `send_email_with_attachments` tool to `muninn/tools.py`
- [x] 5.4 Register new tools in MCP server tool definitions
- [x] 5.5 Update `huginn/client.py` with attachment API methods if needed

## 6. Testing

- [x] 6.1 Add unit tests for attachment API routes
- [x] 6.2 Add unit tests for database adapter attachment methods
- [x] 6.3 Add unit tests for attachment storage integration
- [x] 6.4 Add unit tests for MCP attachment tools
- [x] 6.5 Add integration tests for send message with attachments flow
- [x] 6.6 Add integration tests with PostgreSQL + database blob storage
- [x] 6.7 Add integration tests with PostgreSQL + filesystem storage
- [x] 6.8 Update docker-compose.yml to include all attachment dependencies

## 8. Resend Adapter Fix (Added)

- [x] 8.1 Fix Resend fetch_attachment_content to use correct API endpoint
- [x] 8.2 Parse download_url from Resend API response and fetch actual content
- [x] 8.3 Update webhook handler to store attachment content in configured storage backend

## 7. Documentation

- [x] 7.1 Update API reference docs with attachment endpoints (`web/content/docs/api/`)
- [x] 7.2 Update MCP reference docs with new attachment tools (`web/content/docs/api/mcp.md`)
- [x] 7.3 Update component diagrams to include attachment storage options
- [x] 7.4 Document storage backend configuration (env vars, setup for S3/GCS)
- [x] 7.5 Update CHANGELOG.md with attachment adapter changes
