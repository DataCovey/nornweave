## ADDED Requirements

### Requirement: List attachments by message

The system SHALL provide an endpoint to list all attachments for a specific message.

#### Scenario: List attachments for message with attachments
- **WHEN** user sends `GET /v1/attachments?message_id={message_id}`
- **AND** the message has 2 attachments
- **THEN** response status is 200
- **AND** response contains `items` array with 2 attachment metadata objects
- **AND** each item includes `id`, `filename`, `content_type`, `size`

#### Scenario: List attachments for message without attachments
- **WHEN** user sends `GET /v1/attachments?message_id={message_id}`
- **AND** the message has no attachments
- **THEN** response status is 200
- **AND** response contains empty `items` array

#### Scenario: List attachments for non-existent message
- **WHEN** user sends `GET /v1/attachments?message_id={non_existent_id}`
- **THEN** response status is 404
- **AND** response contains error detail

### Requirement: List attachments by thread

The system SHALL provide an endpoint to list all attachments across all messages in a thread.

#### Scenario: List attachments for thread with messages containing attachments
- **WHEN** user sends `GET /v1/attachments?thread_id={thread_id}`
- **AND** the thread has 3 messages with 5 total attachments
- **THEN** response status is 200
- **AND** response contains `items` array with 5 attachment metadata objects

#### Scenario: List attachments for non-existent thread
- **WHEN** user sends `GET /v1/attachments?thread_id={non_existent_id}`
- **THEN** response status is 404

### Requirement: List attachments by inbox

The system SHALL provide an endpoint to list all attachments across all messages in an inbox.

#### Scenario: List attachments for inbox
- **WHEN** user sends `GET /v1/attachments?inbox_id={inbox_id}`
- **THEN** response status is 200
- **AND** response contains `items` array with attachment metadata objects
- **AND** results are paginated with `limit` and `offset` parameters

#### Scenario: List attachments for non-existent inbox
- **WHEN** user sends `GET /v1/attachments?inbox_id={non_existent_id}`
- **THEN** response status is 404

### Requirement: Filter parameter is required

The system SHALL require exactly one filter parameter when listing attachments.

#### Scenario: Missing filter parameter
- **WHEN** user sends `GET /v1/attachments` without any filter
- **THEN** response status is 400
- **AND** response contains error detail explaining required filter

#### Scenario: Multiple filter parameters
- **WHEN** user sends `GET /v1/attachments?message_id=x&thread_id=y`
- **THEN** response status is 400
- **AND** response contains error detail explaining only one filter is allowed

### Requirement: Get attachment metadata

The system SHALL provide an endpoint to retrieve metadata for a single attachment.

#### Scenario: Get existing attachment metadata
- **WHEN** user sends `GET /v1/attachments/{attachment_id}`
- **THEN** response status is 200
- **AND** response contains `id`, `filename`, `content_type`, `size`, `message_id`, `created_at`

#### Scenario: Get non-existent attachment
- **WHEN** user sends `GET /v1/attachments/{non_existent_id}`
- **THEN** response status is 404

### Requirement: Download attachment content as binary

The system SHALL provide an endpoint to download attachment content as raw binary data by default.

#### Scenario: Download attachment as binary (default)
- **WHEN** user sends `GET /v1/attachments/{attachment_id}/content`
- **THEN** response status is 200
- **AND** `Content-Type` header matches the attachment's content_type
- **AND** `Content-Disposition` header includes the filename
- **AND** response body contains raw binary content

#### Scenario: Download attachment as binary (explicit)
- **WHEN** user sends `GET /v1/attachments/{attachment_id}/content?format=binary`
- **THEN** response status is 200
- **AND** response body contains raw binary content

### Requirement: Download attachment content as base64

The system SHALL allow downloading attachment content as base64-encoded JSON.

#### Scenario: Download attachment as base64
- **WHEN** user sends `GET /v1/attachments/{attachment_id}/content?format=base64`
- **THEN** response status is 200
- **AND** `Content-Type` header is `application/json`
- **AND** response body is JSON with `content`, `content_type`, `filename` fields
- **AND** `content` field contains base64-encoded data

### Requirement: Signed URLs for local and database storage

The system SHALL use signed URLs with expiry for local filesystem and database storage backends.

#### Scenario: Signed URL verification succeeds
- **WHEN** user accesses `/v1/attachments/{id}/content` with valid `token` and `expires` params
- **AND** current time is before expiry
- **THEN** content is returned successfully

#### Scenario: Signed URL expired
- **WHEN** user accesses `/v1/attachments/{id}/content` with expired `expires` param
- **THEN** response status is 401 or 403
- **AND** response indicates URL has expired

#### Scenario: Signed URL invalid signature
- **WHEN** user accesses `/v1/attachments/{id}/content` with invalid `token`
- **THEN** response status is 401 or 403

### Requirement: Cloud storage presigned URLs

The system SHALL use native presigned URLs for S3 and GCS storage backends.

#### Scenario: Get download URL for S3 attachment
- **WHEN** attachment metadata is requested for S3-stored attachment
- **THEN** `download_url` field contains AWS presigned URL
- **AND** URL is valid for 1 hour by default

#### Scenario: Get download URL for GCS attachment
- **WHEN** attachment metadata is requested for GCS-stored attachment
- **THEN** `download_url` field contains GCS signed URL
- **AND** URL is valid for 1 hour by default
