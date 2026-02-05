## ADDED Requirements

### Requirement: Thread model includes a summary field

The `Thread`, `ThreadItem`, and `ThreadORM` models SHALL include a `summary: str | None` field that stores the LLM-generated thread summary.

The field SHALL be nullable and default to `None` (no summary available).

#### Scenario: New thread has no summary
- **WHEN** a new thread is created during message ingestion
- **THEN** the `summary` field is `None`

#### Scenario: Summary is populated after LLM processing
- **WHEN** an LLM provider generates a summary for a thread
- **AND** the thread is updated in storage
- **THEN** the `summary` field contains the generated summary text

#### Scenario: ThreadItem includes summary in list views
- **WHEN** threads are listed via `GET /v1/inboxes/{id}/threads`
- **THEN** each `ThreadItem` in the response includes the `summary` field

#### Scenario: Thread includes summary in detail views
- **WHEN** a thread is fetched via `GET /v1/threads/{id}`
- **THEN** the `Thread` response includes the `summary` field

### Requirement: Database migration adds summary column to threads table

The system SHALL provide an Alembic migration that adds a `summary TEXT` nullable column to the `threads` table.

#### Scenario: Upgrade adds summary column
- **WHEN** the migration is applied (upgrade)
- **THEN** the `threads` table has a new `summary` column of type `TEXT`, nullable, default `NULL`

#### Scenario: Downgrade removes summary column
- **WHEN** the migration is reverted (downgrade)
- **THEN** the `summary` column is removed from the `threads` table

#### Scenario: Existing threads are unaffected
- **WHEN** the migration runs on a database with existing threads
- **THEN** all existing threads have `summary = NULL`
- **AND** no data is lost

### Requirement: Summarization is triggered after message ingestion

The system SHALL trigger thread summarization after a new message is successfully created and the thread is updated, as a fire-and-forget async operation.

Summarization SHALL NOT block or delay the message ingestion response.

#### Scenario: Inbound message triggers summary generation
- **WHEN** a new inbound message is ingested into a thread
- **AND** `LLM_PROVIDER` is configured
- **THEN** the system generates/updates the thread summary asynchronously after the message is persisted

#### Scenario: Outbound message triggers summary generation
- **WHEN** a new outbound message is sent and recorded in a thread
- **AND** `LLM_PROVIDER` is configured
- **THEN** the system generates/updates the thread summary asynchronously

#### Scenario: Feature disabled skips summarization
- **WHEN** a new message is ingested
- **AND** `LLM_PROVIDER` is not configured
- **THEN** no summarization call is made and the `summary` field remains unchanged

#### Scenario: Summarization failure does not block ingestion
- **WHEN** a new message is ingested
- **AND** the LLM provider call fails (network error, API error, etc.)
- **THEN** the message is still persisted successfully
- **AND** the thread's previous summary is preserved (or remains `None`)
- **AND** a warning is logged

### Requirement: Thread text is prepared from Talon-cleaned extracted_text

The system SHALL prepare thread text for summarization by concatenating the `extracted_text` field of all messages in the thread, ordered chronologically, with sender and timestamp headers.

Each message SHALL be formatted as:
```
[YYYY-MM-DD HH:MM] sender@example.com:
<extracted_text content>
```

Messages are separated by blank lines.

#### Scenario: Thread with multiple messages
- **WHEN** a thread has 3 messages from different senders
- **THEN** the prepared text contains all 3 messages in chronological order
- **AND** each message has a `[date time] sender:` header
- **AND** the text uses `extracted_text` (not raw `text`)

#### Scenario: Message with no extracted_text falls back to text
- **WHEN** a message has `extracted_text = None` but `text` is populated
- **THEN** the system uses the `text` field for that message

#### Scenario: Message with no text content is skipped
- **WHEN** a message has both `extracted_text = None` and `text = None`
- **THEN** that message is omitted from the prepared text

### Requirement: Large threads are truncated to fit context window

The system SHALL truncate thread text from the oldest messages when the total text exceeds the model's context window capacity.

The system SHALL keep the most recent messages that fit within 80% of the model's context window, reserving space for the prompt and response.

#### Scenario: Thread fits within context window
- **WHEN** the total prepared text is within the context window limit
- **THEN** all messages are included in the summarization input

#### Scenario: Thread exceeds context window
- **WHEN** the total prepared text exceeds 80% of the model's context window
- **THEN** the oldest messages are removed until the text fits
- **AND** a note is prepended: "[Earlier messages truncated — summary covers the most recent messages]"

### Requirement: ThreadORM.to_pydantic maps summary field

The `ThreadORM.to_pydantic()` method SHALL include the `summary` field when converting to both `Thread` and `ThreadItem` Pydantic models.

#### Scenario: ORM to Thread conversion includes summary
- **WHEN** a `ThreadORM` with a non-null `summary` is converted to a `Thread` Pydantic model
- **THEN** the `Thread.summary` field contains the summary text

#### Scenario: ORM to ThreadItem conversion includes summary
- **WHEN** a `ThreadORM` with a non-null `summary` is converted to a `ThreadItem` Pydantic model
- **THEN** the `ThreadItem.summary` field contains the summary text

#### Scenario: Null summary is preserved
- **WHEN** a `ThreadORM` with `summary = None` is converted
- **THEN** both `Thread.summary` and `ThreadItem.summary` are `None`
