# REST API Capability - Message Response Expansion

Defines the expanded MessageResponse model for the REST API.

## ADDED Requirements

### Requirement: MessageResponse includes email metadata fields

The `MessageResponse` model SHALL include all essential email metadata fields to provide complete message information.

**Required fields:**
- `id` (str): Message ID
- `thread_id` (str): Thread ID
- `inbox_id` (str): Inbox ID
- `direction` (str): "inbound" or "outbound"
- `provider_message_id` (str | null): Provider's message ID
- `subject` (str | null): Email subject
- `from_address` (str | null): Sender email address
- `to_addresses` (list[str]): Recipient email addresses
- `cc_addresses` (list[str] | null): CC recipient addresses
- `bcc_addresses` (list[str] | null): BCC recipient addresses
- `reply_to_addresses` (list[str] | null): Reply-to addresses
- `text` (str | null): Plain text body
- `html` (str | null): HTML body
- `content_clean` (str): Extracted text without quoted replies
- `timestamp` (datetime | null): Message timestamp
- `labels` (list[str]): Message labels
- `preview` (str | null): Short text preview
- `size` (int): Message size in bytes
- `in_reply_to` (str | null): Message-ID being replied to
- `references` (list[str] | null): Thread reference Message-IDs
- `metadata` (dict): Additional headers/metadata
- `created_at` (datetime | null): Record creation timestamp

#### Scenario: Get single message with all fields
- **WHEN** a request is made to `GET /v1/messages/{message_id}`
- **THEN** the response includes all MessageResponse fields populated from the stored message

#### Scenario: List messages with all fields
- **WHEN** a request is made to `GET /v1/messages?inbox_id={inbox_id}`
- **THEN** each message in the response includes all MessageResponse fields

#### Scenario: Null handling for optional fields
- **WHEN** a message has no CC recipients
- **THEN** the `cc_addresses` field is `null` in the response

### Requirement: MessageResponse field names are consistent

The API SHALL use consistent field naming conventions for message responses.

#### Scenario: Address field naming
- **WHEN** returning sender information
- **THEN** the field is named `from_address` (not `from` or `sender`)

#### Scenario: List field naming
- **WHEN** returning recipient lists
- **THEN** fields are named `to_addresses`, `cc_addresses`, `bcc_addresses` (plural with _addresses suffix)

### Requirement: Message conversion preserves all data

The internal `_message_to_response()` function SHALL map all fields from the `Message` model to `MessageResponse`.

#### Scenario: Full field mapping
- **WHEN** converting a Message with all fields populated
- **THEN** all fields appear in the MessageResponse with correct values

#### Scenario: Empty list defaults
- **WHEN** converting a Message with empty `to` list
- **THEN** the `to_addresses` field is an empty list, not null

### Requirement: MessageListResponse includes total count

The `MessageListResponse` model SHALL include a `total` field for pagination support.

**Response fields:**
- `items` (list[MessageResponse]): List of messages for current page
- `count` (int): Number of items in current page
- `total` (int): Total number of matching messages across all pages

#### Scenario: Paginated response with total
- **WHEN** a list request matches 150 messages with limit=50
- **THEN** the response has `count=50`, `total=150`, and 50 items

#### Scenario: Single page response
- **WHEN** a list request matches 30 messages with default limit
- **THEN** the response has `count=30`, `total=30`, and 30 items

### Requirement: MCP tools return expanded message data

MCP tools that return message data SHALL include all fields defined in MessageResponse.

#### Scenario: MCP get_message returns all fields
- **WHEN** an agent calls `get_message(message_id="msg-123")`
- **THEN** the returned message includes subject, from_address, to_addresses, text, html, timestamp, and all other fields

#### Scenario: MCP list_messages returns all fields
- **WHEN** an agent calls `list_messages(inbox_id="inbox-1")`
- **THEN** each message in the response includes all expanded fields
