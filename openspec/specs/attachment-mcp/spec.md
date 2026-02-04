## ADDED Requirements

### Requirement: List attachments MCP tool

The system SHALL provide an MCP tool `list_attachments` for AI agents to list attachment metadata.

#### Scenario: List attachments by message via MCP
- **WHEN** AI agent calls `list_attachments` with `message_id` parameter
- **THEN** tool returns list of attachment metadata objects
- **AND** each object includes `id`, `filename`, `content_type`, `size`

#### Scenario: List attachments by thread via MCP
- **WHEN** AI agent calls `list_attachments` with `thread_id` parameter
- **THEN** tool returns list of attachment metadata from all messages in thread

#### Scenario: List attachments by inbox via MCP
- **WHEN** AI agent calls `list_attachments` with `inbox_id` parameter
- **AND** optionally provides `limit` parameter
- **THEN** tool returns paginated list of attachment metadata

#### Scenario: List attachments with no filter
- **WHEN** AI agent calls `list_attachments` without any filter parameter
- **THEN** tool raises an exception with clear error message

### Requirement: Get attachment content MCP tool

The system SHALL provide an MCP tool `get_attachment_content` for AI agents to retrieve attachment binary data.

#### Scenario: Get attachment content successfully
- **WHEN** AI agent calls `get_attachment_content` with valid `attachment_id`
- **THEN** tool returns JSON object with `content`, `content_type`, `filename`
- **AND** `content` field contains base64-encoded attachment data

#### Scenario: Get non-existent attachment content
- **WHEN** AI agent calls `get_attachment_content` with invalid `attachment_id`
- **THEN** tool raises an exception indicating attachment not found

### Requirement: MCP tool always returns base64 content

The system SHALL always return base64-encoded content from MCP attachment tools since MCP uses JSON transport.

#### Scenario: Content encoding for MCP
- **WHEN** AI agent calls `get_attachment_content`
- **THEN** `content` field is always base64-encoded regardless of original format

### Requirement: Send email with attachments MCP tool

The system SHALL provide an MCP tool `send_email_with_attachments` for AI agents to send emails with attachments.

#### Scenario: Send email with single attachment
- **WHEN** AI agent calls `send_email_with_attachments` with:
  - `inbox_id`, `recipient`, `subject`, `body`
  - `attachments` list with one item containing `filename`, `content_type`, `content` (base64)
- **THEN** email is sent with the attachment
- **AND** tool returns `message_id`, `thread_id`, `status`

#### Scenario: Send email with multiple attachments
- **WHEN** AI agent calls `send_email_with_attachments` with multiple attachments
- **THEN** email is sent with all attachments
- **AND** each attachment is stored in configured storage backend

#### Scenario: Send email with invalid base64 content
- **WHEN** AI agent calls `send_email_with_attachments` with invalid base64 in attachment content
- **THEN** tool raises an exception with clear error message

#### Scenario: Send email with attachments as reply
- **WHEN** AI agent calls `send_email_with_attachments` with `thread_id` parameter
- **THEN** email with attachments is added to existing thread

### Requirement: Original send_email tool unchanged

The existing `send_email` MCP tool SHALL remain unchanged and not accept attachments.

#### Scenario: Existing send_email tool works
- **WHEN** AI agent calls `send_email` with `inbox_id`, `recipient`, `subject`, `body`
- **THEN** email is sent without attachments
- **AND** behavior is identical to before this change
