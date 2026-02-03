## ADDED Requirements

### Requirement: Package follows n8n community node conventions

The package SHALL be named `n8n-nodes-nornweave` and follow n8n community node standards for discoverability and installation.

#### Scenario: Package is installable via n8n community nodes
- **WHEN** a user searches for "nornweave" in n8n's community nodes panel
- **THEN** the package appears in search results with name, description, and install option

#### Scenario: Package metadata is correct
- **WHEN** the package.json is inspected
- **THEN** it contains `n8n-community-node-package` in keywords
- **AND** the `n8n` attribute lists all nodes and credentials

### Requirement: Credential type for NornWeave API

The package SHALL provide a `NornWeaveApi` credential type that authenticates requests to a self-hosted NornWeave instance.

#### Scenario: User configures credentials with base URL only
- **WHEN** user creates NornWeaveApi credentials with only `baseUrl` set
- **THEN** requests are sent to that base URL without authentication headers
- **AND** the credential is valid (API key is optional)

#### Scenario: User configures credentials with API key
- **WHEN** user creates NornWeaveApi credentials with `baseUrl` and `apiKey`
- **THEN** all requests include `X-API-Key` header with the configured value

#### Scenario: Base URL validation
- **WHEN** user enters an invalid URL format for `baseUrl`
- **THEN** credential validation fails with a descriptive error message

### Requirement: Action node with resource/operation structure

The NornWeave action node SHALL organize operations using the resource/operation pattern with four resources: Inbox, Message, Thread, and Search.

#### Scenario: User selects a resource
- **WHEN** user adds NornWeave node to workflow
- **THEN** a "Resource" dropdown appears with options: Inbox, Message, Thread, Search

#### Scenario: Operations change based on resource
- **WHEN** user selects "Inbox" resource
- **THEN** "Operation" dropdown shows: Create, Delete, Get, Get Many
- **WHEN** user selects "Message" resource
- **THEN** "Operation" dropdown shows: Get, Get Many, Send
- **WHEN** user selects "Thread" resource
- **THEN** "Operation" dropdown shows: Get, Get Many
- **WHEN** user selects "Search" resource
- **THEN** "Operation" dropdown shows: Query

### Requirement: Inbox Create operation

The node SHALL allow creating a new inbox via POST /v1/inboxes.

#### Scenario: Create inbox with name and username
- **WHEN** user executes Inbox > Create with name "Support" and email_username "support"
- **THEN** node sends POST to /v1/inboxes with body `{"name": "Support", "email_username": "support"}`
- **AND** returns the created inbox object with id, email_address, name

#### Scenario: Create inbox fails with duplicate username
- **WHEN** user executes Inbox > Create with an existing email_username
- **THEN** node returns an error with HTTP 409 status and descriptive message

### Requirement: Inbox Delete operation

The node SHALL allow deleting an inbox via DELETE /v1/inboxes/{inbox_id}.

#### Scenario: Delete existing inbox
- **WHEN** user executes Inbox > Delete with a valid inbox_id
- **THEN** node sends DELETE to /v1/inboxes/{inbox_id}
- **AND** returns success (empty response or confirmation)

#### Scenario: Delete non-existent inbox
- **WHEN** user executes Inbox > Delete with an invalid inbox_id
- **THEN** node returns an error with HTTP 404 status

### Requirement: Inbox Get operation

The node SHALL allow retrieving a single inbox via GET /v1/inboxes/{inbox_id}.

#### Scenario: Get existing inbox
- **WHEN** user executes Inbox > Get with a valid inbox_id
- **THEN** node returns the inbox object with id, email_address, name, provider_config

#### Scenario: Get non-existent inbox
- **WHEN** user executes Inbox > Get with an invalid inbox_id
- **THEN** node returns an error with HTTP 404 status

### Requirement: Inbox Get Many operation with pagination

The node SHALL allow listing inboxes via GET /v1/inboxes with pagination support.

#### Scenario: Get all inboxes
- **WHEN** user executes Inbox > Get Many with "Return All" enabled
- **THEN** node fetches all pages and returns complete list of inboxes

#### Scenario: Get limited inboxes
- **WHEN** user executes Inbox > Get Many with "Return All" disabled and limit=10
- **THEN** node returns at most 10 inboxes

### Requirement: Message Get operation

The node SHALL allow retrieving a single message via GET /v1/messages/{message_id}.

#### Scenario: Get existing message
- **WHEN** user executes Message > Get with a valid message_id
- **THEN** node returns the message object with id, thread_id, inbox_id, direction, content_raw, content_clean, metadata, created_at

### Requirement: Message Get Many operation with pagination

The node SHALL allow listing messages for an inbox via GET /v1/messages with pagination support.

#### Scenario: Get messages for inbox
- **WHEN** user executes Message > Get Many with inbox_id parameter
- **THEN** node sends GET to /v1/messages?inbox_id={inbox_id}
- **AND** returns list of messages for that inbox

#### Scenario: Inbox ID is required
- **WHEN** user executes Message > Get Many without inbox_id
- **THEN** node shows validation error indicating inbox_id is required

### Requirement: Message Send operation

The node SHALL allow sending an outbound email via POST /v1/messages.

#### Scenario: Send new message (new thread)
- **WHEN** user executes Message > Send with inbox_id, to, subject, and body
- **THEN** node sends POST to /v1/messages with the provided fields
- **AND** returns response with id, thread_id, provider_message_id, status

#### Scenario: Send reply to existing thread
- **WHEN** user executes Message > Send with inbox_id, to, subject, body, and reply_to_thread_id
- **THEN** node includes reply_to_thread_id in request body
- **AND** the message is added to the existing thread

#### Scenario: Body accepts Markdown
- **WHEN** user sends a message with Markdown formatting in body
- **THEN** the Markdown is preserved and sent to NornWeave API

### Requirement: Thread Get operation

The node SHALL allow retrieving a thread with messages via GET /v1/threads/{thread_id}.

#### Scenario: Get thread with messages
- **WHEN** user executes Thread > Get with a valid thread_id
- **THEN** node returns thread object with id, subject, and messages array
- **AND** messages are in LLM-ready format with role, author, content, timestamp

### Requirement: Thread Get Many operation with pagination

The node SHALL allow listing threads for an inbox via GET /v1/threads with pagination support.

#### Scenario: Get threads for inbox
- **WHEN** user executes Thread > Get Many with inbox_id parameter
- **THEN** node returns list of thread summaries ordered by most recent activity

### Requirement: Search Query operation

The node SHALL allow searching messages via POST /v1/search.

#### Scenario: Search messages by query
- **WHEN** user executes Search > Query with query text and inbox_id
- **THEN** node sends POST to /v1/search with body `{"query": "...", "inbox_id": "..."}`
- **AND** returns matching messages with count

#### Scenario: Search with limit
- **WHEN** user executes Search > Query with limit parameter
- **THEN** node includes limit in request body
- **AND** returns at most that many results

### Requirement: Trigger node for webhook events

The NornWeave Trigger node SHALL receive webhook events when emails arrive or delivery events occur.

#### Scenario: Trigger on new inbound email
- **WHEN** NornWeave receives an inbound email and posts to the trigger webhook URL
- **THEN** the workflow is triggered with email data (message_id, thread_id, content, metadata)

#### Scenario: Trigger on delivery events
- **WHEN** NornWeave posts a delivery event (sent, delivered, bounced, opened, clicked)
- **THEN** the workflow is triggered with event data including event_type

#### Scenario: Event type filtering
- **WHEN** user configures trigger with specific event types (e.g., only "email.received")
- **THEN** the workflow only triggers for matching event types
- **AND** other events are acknowledged but do not trigger execution

### Requirement: Trigger provides test and production URLs

The trigger node SHALL provide both test and production webhook URLs following n8n conventions.

#### Scenario: Test webhook URL
- **WHEN** user clicks "Listen for Test Event" in n8n editor
- **THEN** a test webhook URL is displayed for manual testing

#### Scenario: Production webhook URL
- **WHEN** workflow is activated
- **THEN** a production webhook URL is active and ready to receive events

### Requirement: All operations return consistent output format

All node operations SHALL return data as `INodeExecutionData[]` for compatibility with downstream nodes.

#### Scenario: Single item response wrapped in array
- **WHEN** an operation returns a single object (e.g., Get Inbox)
- **THEN** the output is an array containing that single object

#### Scenario: List response returns array
- **WHEN** an operation returns multiple items (e.g., Get Many)
- **THEN** the output is an array of objects, one per item

### Requirement: Error responses include actionable information

The node SHALL transform API errors into user-friendly n8n error messages.

#### Scenario: HTTP 404 error
- **WHEN** an API call returns 404 Not Found
- **THEN** the node error message indicates the resource was not found
- **AND** includes the resource type and ID that was requested

#### Scenario: HTTP 422 validation error
- **WHEN** an API call returns 422 with validation details
- **THEN** the node error message includes the specific validation failures

#### Scenario: Network error
- **WHEN** the NornWeave instance is unreachable
- **THEN** the node error message indicates connection failure
- **AND** suggests checking the base URL configuration

### Requirement: Documentation in package README

The npm package SHALL include comprehensive README documentation.

#### Scenario: README covers installation
- **WHEN** user views the package README
- **THEN** it includes step-by-step installation instructions for n8n

#### Scenario: README covers credential setup
- **WHEN** user views the package README
- **THEN** it explains how to configure NornWeave credentials with base URL and optional API key

#### Scenario: README covers webhook setup
- **WHEN** user views the package README
- **THEN** it explains how to configure their email provider to send webhooks to the n8n trigger URL
