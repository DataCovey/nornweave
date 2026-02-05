## MODIFIED Requirements

### Requirement: Resource email://inbox/{inbox_id}/recent returns recent threads

The MCP server SHALL expose a resource at `email://inbox/{inbox_id}/recent` that returns the most recent thread summaries for an inbox.

#### Scenario: Fetch recent threads for valid inbox
- **WHEN** client requests resource `email://inbox/ibx_123/recent`
- **THEN** server returns JSON array of up to 10 thread summaries
- **AND** each summary contains `id`, `subject`, `last_message_at`, `message_count`, `participants`, `summary`

#### Scenario: Fetch recent threads for non-existent inbox
- **WHEN** client requests resource `email://inbox/invalid_id/recent`
- **THEN** server returns an error indicating inbox not found

#### Scenario: Summary field in recent threads
- **WHEN** client requests resource `email://inbox/ibx_123/recent`
- **AND** some threads have LLM-generated summaries
- **THEN** threads with summaries include `summary` with the summary text
- **AND** threads without summaries include `summary` as null

### Requirement: Resource email://thread/{thread_id} returns thread content

The MCP server SHALL expose a resource at `email://thread/{thread_id}` that returns the full thread content in Markdown format optimized for LLM context.

When a thread summary is available, the resource SHALL include it prominently before the message list to reduce the amount of content the agent needs to process.

#### Scenario: Fetch thread content for valid thread
- **WHEN** client requests resource `email://thread/th_456`
- **THEN** server returns Markdown-formatted thread content
- **AND** content includes thread subject as heading
- **AND** each message shows sender, date, and body separated by horizontal rules

#### Scenario: Thread content includes summary when available
- **WHEN** client requests resource `email://thread/th_456`
- **AND** the thread has a generated summary
- **THEN** the Markdown output includes a "## Summary" section before the message list
- **AND** the summary text is displayed under that section

#### Scenario: Thread content omits summary section when not available
- **WHEN** client requests resource `email://thread/th_456`
- **AND** the thread has no summary (`summary` is null)
- **THEN** the Markdown output does not include a "## Summary" section

#### Scenario: Fetch thread content for non-existent thread
- **WHEN** client requests resource `email://thread/invalid_id`
- **THEN** server returns an error indicating thread not found
