## ADDED Requirements

### Requirement: Manual IMAP sync endpoint

The REST API SHALL provide a `POST /v1/inboxes/{inbox_id}/sync` endpoint that triggers an immediate IMAP sync for a specific inbox when the SMTP/IMAP provider is active.

#### Scenario: Successful manual sync

- **WHEN** a POST request is made to `/v1/inboxes/{inbox_id}/sync`
- **AND** `EMAIL_PROVIDER` is `imap-smtp`
- **AND** the inbox exists
- **THEN** the endpoint triggers an immediate IMAP fetch for that inbox
- **AND** returns HTTP 200 with `{ "status": "synced", "new_messages": <count> }`

#### Scenario: Sync when provider is not SMTP

- **WHEN** a POST request is made to `/v1/inboxes/{inbox_id}/sync`
- **AND** `EMAIL_PROVIDER` is NOT `imap-smtp`
- **THEN** the endpoint returns HTTP 404 with detail indicating IMAP sync is only available with the imap-smtp provider

#### Scenario: Sync for non-existent inbox

- **WHEN** a POST request is made to `/v1/inboxes/{inbox_id}/sync`
- **AND** no inbox exists with that ID
- **THEN** the endpoint returns HTTP 404 with detail indicating inbox not found

#### Scenario: Sync with IMAP connection failure

- **WHEN** a POST request is made to `/v1/inboxes/{inbox_id}/sync`
- **AND** the IMAP server is unreachable
- **THEN** the endpoint returns HTTP 502 with detail indicating IMAP connection failure

#### Scenario: Sync requires authentication

- **WHEN** a POST request is made to `/v1/inboxes/{inbox_id}/sync` without a valid API key
- **THEN** the endpoint returns HTTP 401 consistent with other authenticated endpoints
