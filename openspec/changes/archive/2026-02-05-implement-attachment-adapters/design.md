## Context

NornWeave has partial attachment infrastructure that was scaffolded but never integrated:

**Existing Infrastructure:**
- `AttachmentStorageBackend` interface in `core/storage.py` with store/retrieve/delete/get_download_url/exists methods
- Four storage backends: `LocalFilesystemStorage`, `S3Storage`, `GCSStorage`, `DatabaseBlobStorage`
- Attachment models: `Attachment`, `AttachmentMeta`, `SendAttachment`, `AttachmentResponse`
- Database CRUD in `urdr/adapters/base.py`: `create_attachment`, `get_attachment`, `list_attachments_for_message`, `delete_attachment`
- Factory function `create_attachment_storage()` for backend selection via settings

**Missing Pieces:**
- No API routes to list/retrieve attachments
- No MCP tools for attachment access
- `SendMessageRequest` doesn't accept attachments
- `DatabaseBlobStorage` has `NotImplementedError` placeholders
- No package extras for S3/GCS cloud dependencies
- Only `list_attachments_for_message` exists—no query by thread or inbox

## Goals / Non-Goals

**Goals:**
- Expose attachment listing and retrieval via REST API and MCP tools
- Enable sending messages with attachments via API and MCP
- Complete `DatabaseBlobStorage` implementation
- Add `s3` and `gcs` package extras for cloud storage dependencies
- Support querying attachments by message_id, thread_id, or inbox_id
- Allow users to choose binary (default) or base64 encoding on retrieval

**Non-Goals:**
- Attachment processing/extraction (PDF text, image OCR)—covered by existing `attachments` extra
- Virus scanning or content moderation
- Streaming large file uploads (simple base64 in request body is sufficient for typical email attachments)
- Direct upload to cloud storage (server-side upload only)

## Decisions

### 1. API Route Structure

**Decision:** Create `/v1/attachments` router with RESTful endpoints.

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/attachments` | List attachments (filterable by message_id, thread_id, inbox_id) |
| GET | `/v1/attachments/{attachment_id}` | Get attachment metadata |
| GET | `/v1/attachments/{attachment_id}/content` | Download attachment content |

**Alternatives Considered:**
- Nest under messages (`/v1/messages/{id}/attachments`): Rejected because attachments need independent access by ID, and querying by thread/inbox would be awkward.
- Separate download endpoint vs. Accept header content negotiation: Chose separate `/content` endpoint for clarity and cacheability.

### 2. Content Retrieval Format

**Decision:** Use query parameter `?format=binary|base64` on `/content` endpoint, defaulting to `binary`.

- `format=binary` (default): Returns raw bytes with `Content-Type` from attachment metadata
- `format=base64`: Returns JSON `{"content": "<base64-encoded>", "content_type": "...", "filename": "..."}`

**Rationale:** Query param is explicit and works well with signed URLs. Binary default matches typical download behavior.

### 3. Listing by Context

**Decision:** Add `list_attachments_for_thread` and `list_attachments_for_inbox` to database adapter.

The API uses a single endpoint with mutually exclusive filter params:
```
GET /v1/attachments?message_id=...
GET /v1/attachments?thread_id=...
GET /v1/attachments?inbox_id=...
```

Exactly one filter is required. Returns `AttachmentMeta` items (lightweight: id, filename, content_type, size).

### 4. Sending with Attachments

**Decision:** Extend `SendMessageRequest` with optional `attachments` field.

```python
class SendAttachmentInput(BaseModel):
    filename: str
    content_type: str
    content: str  # base64-encoded

class SendMessageRequest(BaseModel):
    # ... existing fields ...
    attachments: list[SendAttachmentInput] | None = None
```

Flow:
1. Decode base64 → raw bytes
2. Store via `AttachmentStorageBackend.store()`
3. Create `AttachmentORM` record with storage_key
4. Pass attachments to email provider's `send_email()` (already supports `attachments` param)

### 5. MCP Tools

**Decision:** Add three attachment tools to `muninn/tools.py`:

| Tool | Description |
|------|-------------|
| `list_attachments` | List attachment metadata for a message/thread/inbox |
| `get_attachment_content` | Retrieve attachment content (base64 encoded for MCP transport) |
| `send_email_with_attachments` | Extended send_email with attachment support |

MCP tools always return base64 for content (JSON transport requirement). The existing `send_email` tool remains unchanged; `send_email_with_attachments` is a new tool.

### 6. Package Extras

**Decision:** Add new extras to `pyproject.toml`:

```toml
s3 = ["boto3>=1.35.0"]
gcs = ["google-cloud-storage>=2.18.0"]
```

Update `all` extra to include these. The lazy imports in `S3Storage` and `GCSStorage` already handle missing dependencies gracefully.

### 7. DatabaseBlobStorage Completion

**Decision:** Complete the placeholder methods by accepting a database session parameter.

The `DatabaseBlobStorage` backend is special—it doesn't store content externally but uses the `content` column on `AttachmentORM`. The storage layer (not the backend) handles the actual DB operations.

**Implementation approach:**
- `store()`: Return `StorageResult` with `storage_key=attachment_id` (caller sets `content` on ORM)
- `retrieve()`: Raise `NotImplementedError` with guidance to use storage layer
- `delete()`: Raise `NotImplementedError` with guidance to use storage layer
- `exists()`: Raise `NotImplementedError` with guidance to use storage layer

The actual retrieval happens in the API route, which has DB access:
```python
# In attachments route
if attachment.storage_backend == "database":
    content = attachment.content  # From ORM
else:
    content = await storage_backend.retrieve(attachment.storage_key)
```

**Rationale:** Keeps storage backends stateless and decoupled from SQLAlchemy sessions.

### 8. Signed URL Security

**Decision:** Reuse existing signed URL pattern from `LocalFilesystemStorage` and `DatabaseBlobStorage`.

- HMAC-SHA256 signature with configurable secret
- Expiry timestamp in URL
- Verification in download endpoint

Cloud backends (S3, GCS) use native presigned URLs which handle their own security.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large attachments may timeout or OOM | Document size limits in API (recommend <25MB per attachment). Streaming is a future enhancement. |
| Base64 encoding increases payload size by ~33% | Default to binary for API. Base64 only for MCP (required) or explicit request. |
| DatabaseBlobStorage not suitable for large files | Document as development/small deployment option. Recommend S3/GCS for production. |
| Missing cloud credentials fail at runtime | Lazy import pattern provides clear error message. Document required env vars. |
| Attachment orphaning if message send fails | Use database transaction: create attachment record and message atomically. |

### 9. Resend Adapter Attachment Retrieval (Added)

**Decision:** Fix Resend adapter to correctly fetch attachment content via two-step API call.

**Problem:** The initial implementation used the wrong API endpoint and didn't follow Resend's attachment retrieval pattern.

**Correct Implementation:**
1. Call `GET /emails/{email_id}/attachments/{attachment_id}` to get attachment metadata including `download_url`
2. Fetch actual content from the CDN `download_url` returned in the response

See: https://resend.com/docs/api-reference/emails/retrieve-email-attachment

**Webhook Handler Fix:** Also fixed the Resend webhook handler to:
1. Store attachment content in the configured storage backend (not just metadata)
2. Create proper attachment records with storage path, backend name, and content hash
3. For database backend, also store the content blob

## Open Questions

1. **Attachment size limit?** — Suggest 25MB default, configurable via settings.
2. **Retention policy?** — Out of scope for this change, but consider adding `expires_at` field for future cleanup.
