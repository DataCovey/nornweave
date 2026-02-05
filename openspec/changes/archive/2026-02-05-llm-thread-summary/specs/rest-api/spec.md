## ADDED Requirements

### Requirement: Thread responses include summary field

All REST API endpoints that return thread data SHALL include a `summary: str | null` field in the response.

Affected endpoints:
- `GET /v1/threads/{thread_id}` — returns `Thread` with `summary`
- `GET /v1/inboxes/{inbox_id}/threads` — returns `ListThreadsResponse` where each `ThreadItem` includes `summary`

#### Scenario: Thread with summary
- **WHEN** a request is made to `GET /v1/threads/{thread_id}`
- **AND** the thread has a generated summary
- **THEN** the response includes `"summary": "<summary text>"`

#### Scenario: Thread without summary
- **WHEN** a request is made to `GET /v1/threads/{thread_id}`
- **AND** the thread has no summary (feature disabled or not yet generated)
- **THEN** the response includes `"summary": null`

#### Scenario: Thread list includes summaries
- **WHEN** a request is made to `GET /v1/inboxes/{inbox_id}/threads`
- **THEN** each thread item in the `threads` array includes the `summary` field
