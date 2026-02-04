## ADDED Requirements

### Requirement: Send email via SendGrid v3 API

The SendGrid adapter SHALL send emails using the SendGrid v3 Mail Send API (`POST https://api.sendgrid.com/v3/mail/send`) with proper authentication and payload structure.

#### Scenario: Send simple email

- **WHEN** `send_email` is called with recipients, subject, and body
- **THEN** the adapter sends a POST request to `/v3/mail/send` with Bearer token authentication
- **AND** returns the SendGrid message ID from the `X-Message-Id` response header

#### Scenario: Send email with HTML body

- **WHEN** `send_email` is called with both plain text body and html_body
- **THEN** the request payload includes both `text/plain` and `text/html` content types

#### Scenario: Send email with Markdown conversion

- **WHEN** `send_email` is called with plain text body and no html_body
- **THEN** the adapter converts the body to HTML using markdown library
- **AND** includes both plain and HTML versions in the request

#### Scenario: API error handling

- **WHEN** SendGrid API returns a non-2xx status code
- **THEN** the adapter raises an HTTPStatusError with the error details

### Requirement: Support email threading headers

The SendGrid adapter SHALL include RFC 5322 threading headers (Message-ID, In-Reply-To, References) when provided.

#### Scenario: Send reply with threading headers

- **WHEN** `send_email` is called with `in_reply_to` and `references` parameters
- **THEN** the request includes `In-Reply-To` and `References` in the `headers` object

#### Scenario: Send with custom Message-ID

- **WHEN** `send_email` is called with a `message_id` parameter
- **THEN** the request includes the custom `Message-ID` in the `headers` object

### Requirement: Support CC and BCC recipients

The SendGrid adapter SHALL support carbon copy and blind carbon copy recipients.

#### Scenario: Send email with CC recipients

- **WHEN** `send_email` is called with `cc` parameter containing email addresses
- **THEN** the request includes CC recipients in the personalizations object

#### Scenario: Send email with BCC recipients

- **WHEN** `send_email` is called with `bcc` parameter containing email addresses
- **THEN** the request includes BCC recipients in the personalizations object

### Requirement: Support email attachments for sending

The SendGrid adapter SHALL support sending emails with file attachments.

#### Scenario: Send email with attachment

- **WHEN** `send_email` is called with attachments list
- **THEN** the request includes base64-encoded attachment content with filename and content type

#### Scenario: Send email with inline attachment

- **WHEN** `send_email` is called with an attachment having inline disposition
- **THEN** the request includes the attachment with `disposition: "inline"` and `content_id`

### Requirement: Parse SendGrid Inbound Parse webhooks

The SendGrid adapter SHALL parse Inbound Parse webhook payloads (multipart/form-data) into standardized `InboundMessage` objects.

#### Scenario: Parse simple inbound email

- **WHEN** `parse_inbound_webhook` is called with a SendGrid Inbound Parse payload
- **THEN** it returns an `InboundMessage` with from_address, to_address, subject, body_plain, and body_html populated

#### Scenario: Parse sender from "Name <email>" format

- **WHEN** the webhook `from` field contains "Alice Smith <alice@example.com>"
- **THEN** the `from_address` is extracted as "alice@example.com"

#### Scenario: Parse email headers

- **WHEN** the webhook includes a `headers` field (newline-separated string)
- **THEN** the adapter parses it into a dictionary accessible via `InboundMessage.headers`

#### Scenario: Extract threading headers from parsed headers

- **WHEN** the webhook headers contain Message-ID, In-Reply-To, or References
- **THEN** these are populated in the corresponding `InboundMessage` fields

### Requirement: Parse inbound email attachments

The SendGrid adapter SHALL parse attachment metadata from `attachment-info` JSON and map to `InboundAttachment` objects.

#### Scenario: Parse regular attachments

- **WHEN** the webhook includes `attachment-info` with attachment metadata
- **THEN** the adapter creates `InboundAttachment` objects with filename, content_type, and disposition

#### Scenario: Parse inline attachments with content-id

- **WHEN** the webhook includes `content-ids` mapping Content-ID to attachment field
- **THEN** the adapter sets `content_id` on the corresponding `InboundAttachment`
- **AND** sets disposition to `INLINE`

#### Scenario: Build content_id_map for inline image resolution

- **WHEN** the webhook contains inline attachments with content-ids
- **THEN** the `InboundMessage.content_id_map` maps Content-ID to attachment identifier

### Requirement: Parse email verification results

The SendGrid adapter SHALL extract SPF, DKIM, and spam score from Inbound Parse webhooks.

#### Scenario: Parse SPF result

- **WHEN** the webhook includes `SPF` field with value "pass"
- **THEN** the `InboundMessage.spf_result` is set to "pass"

#### Scenario: Parse DKIM result

- **WHEN** the webhook includes `dkim` field with verification results
- **THEN** the `InboundMessage.dkim_result` is populated with the verification string

### Requirement: Verify webhook signatures using ECDSA

The SendGrid adapter SHALL support ECDSA signature verification for Inbound Parse webhooks when a security policy is configured.

#### Scenario: Verify valid webhook signature

- **WHEN** `verify_webhook_signature` is called with raw payload, headers containing `X-Twilio-Email-Event-Webhook-Signature` and `X-Twilio-Email-Event-Webhook-Timestamp`, and a valid public key
- **THEN** the method returns the verified payload without raising an exception

#### Scenario: Reject invalid webhook signature

- **WHEN** `verify_webhook_signature` is called with an invalid signature
- **THEN** the method raises `SendGridWebhookError`

#### Scenario: Reject expired webhook timestamp

- **WHEN** `verify_webhook_signature` is called with a timestamp older than the allowed tolerance
- **THEN** the method raises `SendGridWebhookError` indicating timestamp validation failed

#### Scenario: Handle missing signature headers

- **WHEN** `verify_webhook_signature` is called without required signature headers
- **THEN** the method raises `SendGridWebhookError` indicating missing headers

### Requirement: Provide webhook helper methods

The SendGrid adapter SHALL provide helper methods for webhook event handling consistent with other adapters.

#### Scenario: Identify inbound email event

- **WHEN** `is_inbound_event` is called with an Inbound Parse payload
- **THEN** it returns `True`

#### Scenario: Get event type

- **WHEN** `get_event_type` is called with an Inbound Parse payload
- **THEN** it returns `"inbound"` (SendGrid Inbound Parse doesn't have event types like Event Webhooks)
