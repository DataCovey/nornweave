# Message Search Capability

Defines search and filtering capabilities for messages across the API and MCP interfaces.

## Requirements

### Requirement: Filter messages by thread_id

The system SHALL allow filtering messages by `thread_id` parameter to retrieve all messages within a specific thread.

#### Scenario: Filter by thread_id only
- **WHEN** a request is made to `GET /v1/messages?thread_id={thread_id}`
- **THEN** the system returns all messages belonging to that thread

#### Scenario: Filter by thread_id with inbox_id
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}&thread_id={thread_id}`
- **THEN** the system returns messages from the thread, filtered to the specified inbox

### Requirement: Require at least one filter

The system SHALL require at least one filter parameter (`inbox_id` or `thread_id`) to prevent unbounded queries.

#### Scenario: No filters provided
- **WHEN** a request is made to `GET /v1/messages` without any filter parameters
- **THEN** the system returns HTTP 422 with error message indicating at least one filter is required

#### Scenario: Only text search without filter
- **WHEN** a request is made to `GET /v1/messages?q=search_term` without inbox_id or thread_id
- **THEN** the system returns HTTP 422 with error message indicating at least one filter is required

### Requirement: Text search across message fields

The system SHALL search across `subject`, `text`, `from_address`, and attachment filenames when the `q` parameter is provided.

#### Scenario: Text search within inbox
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}&q=search_term`
- **THEN** the system returns messages where subject, text body, from_address, or any attachment filename contains the search term (case-insensitive)

#### Scenario: Text search within thread
- **WHEN** a request is made to `GET /v1/messages?thread_id={thread_id}&q=search_term`
- **THEN** the system returns messages in the thread where subject, text body, from_address, or any attachment filename contains the search term

#### Scenario: Search by attachment filename
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}&q=invoice.pdf`
- **THEN** the system returns messages that have an attachment with filename containing "invoice.pdf"

#### Scenario: No matches found
- **WHEN** a request is made with a search term that matches no messages
- **THEN** the system returns an empty list with count 0

### Requirement: Search results are paginated

The system SHALL support pagination for search results using `limit` and `offset` parameters, and return total count for client-side pagination.

#### Scenario: Default pagination
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}&q=search_term` without pagination parameters
- **THEN** the system returns up to 50 messages (default limit) starting from offset 0

#### Scenario: Custom pagination
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}&q=search_term&limit=10&offset=20`
- **THEN** the system returns up to 10 messages starting from the 21st match

#### Scenario: Response includes total count
- **WHEN** a search request returns paginated results
- **THEN** the response includes `total` field with the total number of matching messages (not just the current page)

#### Scenario: Empty page beyond results
- **WHEN** offset exceeds the total number of matching messages
- **THEN** the system returns an empty list with `total` reflecting the actual count

### Requirement: MCP list_messages tool supports thread filtering

The MCP `list_messages` tool SHALL accept `inbox_id` and `thread_id` as optional parameters with the same filter logic as the REST API.

#### Scenario: MCP filter by thread_id
- **WHEN** an agent calls `list_messages(thread_id="thread-123")`
- **THEN** the tool returns all messages in that thread

#### Scenario: MCP combined filters
- **WHEN** an agent calls `list_messages(inbox_id="inbox-1", thread_id="thread-1", q="invoice")`
- **THEN** the tool returns messages in the thread matching the search term

### Requirement: MCP search_messages tool for text search

The MCP server SHALL provide a `search_messages` tool dedicated to text search with filter options, including pagination.

#### Scenario: Search messages via MCP
- **WHEN** an agent calls `search_messages(inbox_id="inbox-1", q="urgent")`
- **THEN** the tool returns messages containing "urgent" in subject, body, sender, or attachment filename

#### Scenario: Search with thread filter via MCP
- **WHEN** an agent calls `search_messages(thread_id="thread-1", q="attachment")`
- **THEN** the tool returns messages in the thread containing "attachment"

#### Scenario: Paginated search via MCP
- **WHEN** an agent calls `search_messages(inbox_id="inbox-1", q="report", limit=10, offset=0)`
- **THEN** the tool returns the first 10 matching messages and the total count
