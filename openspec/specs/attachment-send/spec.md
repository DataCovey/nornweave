## ADDED Requirements

### Requirement: Send message with attachments via API

The system SHALL accept attachments when sending messages via the REST API.

#### Scenario: Send message with single attachment
- **WHEN** user sends `POST /v1/messages` with:
  - `inbox_id`, `to`, `subject`, `body`
  - `attachments` array with one object containing `filename`, `content_type`, `content` (base64)
- **THEN** response status is 201
- **AND** email is sent with the attachment
- **AND** attachment is stored in configured storage backend
- **AND** attachment metadata is saved to database

#### Scenario: Send message with multiple attachments
- **WHEN** user sends `POST /v1/messages` with `attachments` array containing 3 items
- **THEN** all 3 attachments are included in the sent email
- **AND** all 3 attachments are stored and recorded

#### Scenario: Send message without attachments (backward compatible)
- **WHEN** user sends `POST /v1/messages` without `attachments` field
- **THEN** behavior is identical to before this change
- **AND** message is sent without attachments

### Requirement: Attachment content decoding

The system SHALL decode base64-encoded attachment content before storage.

#### Scenario: Store decoded attachment content
- **WHEN** user sends attachment with base64-encoded content
- **THEN** storage backend receives raw binary bytes (not base64)
- **AND** stored file size matches original binary size

#### Scenario: Invalid base64 content rejected
- **WHEN** user sends attachment with invalid base64 content
- **THEN** response status is 400
- **AND** response contains error detail about invalid base64

### Requirement: Attachment metadata validation

The system SHALL validate attachment metadata before processing.

#### Scenario: Missing filename rejected
- **WHEN** user sends attachment without `filename` field
- **THEN** response status is 422
- **AND** response contains validation error

#### Scenario: Missing content_type rejected
- **WHEN** user sends attachment without `content_type` field
- **THEN** response status is 422
- **AND** response contains validation error

#### Scenario: Empty content rejected
- **WHEN** user sends attachment with empty `content` field
- **THEN** response status is 422
- **AND** response contains validation error

### Requirement: Attachment storage backend selection

The system SHALL store attachments using the configured storage backend.

#### Scenario: Store attachment in local filesystem
- **WHEN** `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=local`
- **AND** user sends message with attachment
- **THEN** attachment is stored in local filesystem at configured path

#### Scenario: Store attachment in S3
- **WHEN** `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=s3`
- **AND** S3 credentials are configured
- **AND** user sends message with attachment
- **THEN** attachment is uploaded to configured S3 bucket

#### Scenario: Store attachment in GCS
- **WHEN** `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=gcs`
- **AND** GCS credentials are configured
- **AND** user sends message with attachment
- **THEN** attachment is uploaded to configured GCS bucket

#### Scenario: Store attachment in database
- **WHEN** `NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=database`
- **AND** user sends message with attachment
- **THEN** attachment content is stored in database BLOB column

### Requirement: Attachment record creation

The system SHALL create attachment database records with storage metadata.

#### Scenario: Attachment record contains storage info
- **WHEN** attachment is stored successfully
- **THEN** `AttachmentORM` record is created with:
  - `storage_path`: key/path for retrieval
  - `storage_backend`: backend name (local, s3, gcs, database)
  - `content_hash`: SHA-256 hash of content

### Requirement: Atomic attachment and message creation

The system SHALL create attachment records and message records atomically.

#### Scenario: Attachment storage failure rolls back
- **WHEN** attachment storage fails after partial upload
- **THEN** no message record is created
- **AND** no attachment record is created
- **AND** response indicates failure

#### Scenario: Message creation failure cleans up attachments
- **WHEN** message record creation fails after attachments are stored
- **THEN** stored attachments are cleaned up (best effort)
- **AND** no orphaned attachment records exist

### Requirement: Email provider receives attachments

The system SHALL pass attachments to the email provider for sending.

#### Scenario: Provider send_email receives attachments
- **WHEN** message with attachments is sent
- **THEN** email provider's `send_email` method receives `attachments` parameter
- **AND** each attachment includes `filename`, `content_type`, `content` (raw bytes)

### Requirement: Attachment linking to message

The system SHALL link attachments to the created message.

#### Scenario: Attachments linked to message
- **WHEN** message with attachments is created
- **THEN** each attachment record has `message_id` pointing to the message
- **AND** listing attachments by message_id returns all attachments
