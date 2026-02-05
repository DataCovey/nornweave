## Context

The current `MessageResponse` model in `yggdrasil/routes/v1/messages.py` only exposes 9 fields:
- `id`, `thread_id`, `inbox_id`, `direction`, `provider_message_id`
- `content_raw`, `content_clean`, `metadata`, `created_at`

However, the underlying `Message` Pydantic model has 20+ fields including essential email metadata:
- `subject`, `from_address`, `to`, `cc`, `bcc`, `reply_to`
- `text`, `html`, `extracted_text`, `extracted_html`
- `timestamp`, `labels`, `preview`, `size`
- `in_reply_to`, `references`, `headers`

The current search endpoint (`GET /v1/messages`) requires `inbox_id` and optionally accepts `q` for text search, but users cannot filter by `thread_id` or search for specific messages by ID.

## Goals / Non-Goals

**Goals:**
- Expand `MessageResponse` to include all useful email fields from the `Message` model
- Add `thread_id` as optional filter to the messages list endpoint
- Allow combining filters (e.g., search within a thread, or search across an inbox)
- Add `total` count to `MessageListResponse` for proper pagination support
- Update MCP tools to expose the same capabilities
- Maintain backward compatibility (additive changes only)

**Non-Goals:**
- Full-text search indexing (use existing SQL ILIKE for now)
- Advanced search operators (AND, OR, exact match, etc.)
- Search result highlighting/snippets
- Cursor-based pagination (continue using offset-based)

## Decisions

### 1. MessageResponse Field Expansion

**Decision**: Add all email metadata fields to `MessageResponse`, mirroring the `Message` model structure.

**New fields to add:**
```python
subject: str | None
from_address: str | None
to_addresses: list[str]
cc_addresses: list[str] | None
bcc_addresses: list[str] | None
reply_to_addresses: list[str] | None
text: str | None
html: str | None
timestamp: datetime | None
labels: list[str]
preview: str | None
size: int
in_reply_to: str | None
references: list[str] | None
```

**Rationale**: The data already exists in the database and Message model. Not exposing it via API forces users to use workarounds. The response size increase is acceptable since messages are typically fetched individually or in small batches.

**Alternative considered**: Create a separate "detailed" endpoint (`/v1/messages/{id}/full`). Rejected because it adds complexity and most use cases need the full data anyway.

### 2. Search Filter Parameters

**Decision**: Make `inbox_id` optional and add `thread_id` as an optional query parameter. Require at least one filter to prevent unbounded queries. Single message retrieval uses the existing `GET /v1/messages/{message_id}` endpoint.

**Filter combinations:**
| inbox_id | thread_id | Behavior |
|----------|-----------|----------|
| ✓ | - | All messages in inbox (current behavior) |
| - | ✓ | All messages in thread |
| ✓ | ✓ | Messages in thread, filtered to inbox |
| - | - | **Error**: At least one filter required |

**Text search (`q`)**: Applies ILIKE search on `subject`, `text`, `from_address`, and attachment filenames when provided with any filter combination.

**Rationale**: Flexible filtering covers common use cases: browse inbox, view thread, search within thread. Single message retrieval already has a dedicated endpoint.

**Alternative considered**: Add `message_id` as a filter parameter. Rejected because `GET /v1/messages/{message_id}` already exists and is the standard REST pattern for retrieving a single resource.

### 3. MCP Tool Updates

**Decision**: Update existing `list_messages` tool and add `search_messages` tool.

- `list_messages`: Add `thread_id`, `message_id` parameters; return expanded fields
- `search_messages`: Dedicated tool for text search with all filter options

**Rationale**: Agents need the same filtering capabilities as the REST API. Separating list and search follows the existing MCP tool pattern.

### 4. Database Query Approach

**Decision**: Use existing SQLAlchemy queries with optional filter chaining. No new indexes required initially.

**Query structure:**
```python
query = select(MessageORM)
if inbox_id:
    query = query.where(MessageORM.inbox_id == inbox_id)
if thread_id:
    query = query.where(MessageORM.thread_id == thread_id)
if q:
    search_term = f"%{q}%"
    # Join with attachments table to search filenames
    attachment_subquery = (
        select(AttachmentORM.message_id)
        .where(AttachmentORM.filename.ilike(search_term))
        .distinct()
    )
    query = query.where(
        or_(
            MessageORM.subject.ilike(search_term),
            MessageORM.text.ilike(search_term),
            MessageORM.from_address.ilike(search_term),
            MessageORM.id.in_(attachment_subquery),
        )
    )
```

**Rationale**: Simple implementation that works for typical mailbox sizes. Subquery for attachment filenames avoids duplicating messages with multiple attachments. Performance can be optimized later with indexes if needed.

## Risks / Trade-offs

**[Risk] Larger response payloads** → Acceptable trade-off for usability. Consider adding `fields` parameter later for sparse responses.

**[Risk] ILIKE search performance on large mailboxes** → Monitor query performance. Add GIN/trigram index if needed. Current scope is <100k messages per inbox.

**[Risk] Breaking change if fields are renamed** → Use consistent field names from `Message` model. Document API response schema.

## Migration Plan

1. Update `MessageResponse` model with new fields
2. Update `_message_to_response()` conversion function
3. Update `list_messages` endpoint to accept new filter parameters
4. Add database adapter methods for filtered queries if needed
5. Update MCP tools in `muninn/tools.py`
6. Update MCP client in `huginn/client.py`
7. Update documentation
8. No database migration required (fields already exist in ORM)

**Rollback**: Revert code changes. No data migration involved.
