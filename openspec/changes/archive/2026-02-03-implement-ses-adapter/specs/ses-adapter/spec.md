## ADDED Requirements

### Requirement: Send email via AWS SES v2 API

The SES adapter SHALL send emails using the AWS SES v2 API (`POST https://email.{region}.amazonaws.com/v2/email/outbound-emails`) with AWS Signature Version 4 authentication and `Content.Simple` payload structure.

#### Scenario: Send simple email

- **WHEN** `send_email` is called with recipients, subject, and body
- **THEN** the adapter sends a POST request to `/v2/email/outbound-emails` with SigV4 authentication
- **AND** returns the SES message ID from the response `MessageId` field

#### Scenario: Send email with HTML body

- **WHEN** `send_email` is called with both plain text body and html_body
- **THEN** the request payload includes both `Body.Text` and `Body.Html` content

#### Scenario: Send email with Markdown conversion

- **WHEN** `send_email` is called with plain text body and no html_body
- **THEN** the adapter converts the body to HTML using markdown library
- **AND** includes both plain and HTML versions in the request

#### Scenario: API error handling

- **WHEN** SES API returns a non-2xx status code
- **THEN** the adapter raises an HTTPStatusError with the error details

#### Scenario: Handle account suspended error

- **WHEN** SES API returns AccountSuspendedException
- **THEN** the adapter raises an appropriate error indicating sending is disabled

### Requirement: Support email threading headers

The SES adapter SHALL include RFC 5322 threading headers (Message-ID, In-Reply-To, References) using the `Content.Simple.Headers` array.

#### Scenario: Send reply with threading headers

- **WHEN** `send_email` is called with `in_reply_to` and `references` parameters
- **THEN** the request includes `In-Reply-To` and `References` in the `Headers` array

#### Scenario: Send with custom Message-ID

- **WHEN** `send_email` is called with a `message_id` parameter
- **THEN** the request includes the custom `Message-ID` in the `Headers` array

### Requirement: Support CC and BCC recipients

The SES adapter SHALL support carbon copy and blind carbon copy recipients using the `Destination` object.

#### Scenario: Send email with CC recipients

- **WHEN** `send_email` is called with `cc` parameter containing email addresses
- **THEN** the request includes CC recipients in `Destination.CcAddresses`

#### Scenario: Send email with BCC recipients

- **WHEN** `send_email` is called with `bcc` parameter containing email addresses
- **THEN** the request includes BCC recipients in `Destination.BccAddresses`

### Requirement: Support email attachments for sending

The SES adapter SHALL support sending emails with file attachments using the `Content.Simple.Attachments` array.

#### Scenario: Send email with attachment

- **WHEN** `send_email` is called with attachments list
- **THEN** the request includes attachments with `RawContent` (base64-encoded), `FileName`, and `ContentType`

#### Scenario: Send email with inline attachment

- **WHEN** `send_email` is called with an attachment having inline disposition
- **THEN** the request includes the attachment with `ContentDisposition: "inline"` and `ContentId`

### Requirement: Parse SES inbound webhooks via SNS

The SES adapter SHALL parse SNS notification payloads containing SES email data into standardized `InboundMessage` objects.

#### Scenario: Parse simple inbound email

- **WHEN** `parse_inbound_webhook` is called with an SNS notification containing SES email data
- **THEN** it returns an `InboundMessage` with from_address, to_address, subject, body_plain, and body_html populated

#### Scenario: Parse sender from mail.source field

- **WHEN** the SNS notification `mail.source` contains "alice@example.com"
- **THEN** the `from_address` is set to "alice@example.com"

#### Scenario: Parse sender from commonHeaders with display name

- **WHEN** the `mail.commonHeaders.from` contains "Alice Smith <alice@example.com>"
- **THEN** the `from_address` is extracted as "alice@example.com"

#### Scenario: Parse email headers from mail.headers array

- **WHEN** the notification includes `mail.headers` array with name/value pairs
- **THEN** the adapter parses it into a dictionary accessible via `InboundMessage.headers`

#### Scenario: Extract threading headers from mail.commonHeaders

- **WHEN** the notification `mail.commonHeaders` contains messageId, inReplyTo, or references
- **THEN** these are populated in the corresponding `InboundMessage` fields

#### Scenario: Parse raw MIME content for body and attachments

- **WHEN** the notification includes a `content` field with raw MIME email
- **THEN** the adapter parses the MIME content to extract body_plain, body_html, and attachments

### Requirement: Parse inbound email attachments from MIME content

The SES adapter SHALL parse attachment data from the raw MIME content and map to `InboundAttachment` objects.

#### Scenario: Parse regular attachments from MIME

- **WHEN** the raw MIME content includes attachment parts
- **THEN** the adapter creates `InboundAttachment` objects with filename, content_type, content, size_bytes, and disposition

#### Scenario: Parse inline attachments with content-id

- **WHEN** the MIME content includes inline parts with Content-ID headers
- **THEN** the adapter sets `content_id` on the corresponding `InboundAttachment`
- **AND** sets disposition to `INLINE`

#### Scenario: Build content_id_map for inline image resolution

- **WHEN** the MIME content contains inline attachments with Content-ID
- **THEN** the `InboundMessage.content_id_map` maps Content-ID to attachment identifier

### Requirement: Parse email verification results from SES receipt

The SES adapter SHALL extract SPF, DKIM, DMARC, spam, and virus verdicts from the SNS notification `receipt` object.

#### Scenario: Parse SPF verdict

- **WHEN** the notification includes `receipt.spfVerdict.status` with value "PASS"
- **THEN** the `InboundMessage.spf_result` is set to "PASS"

#### Scenario: Parse DKIM verdict

- **WHEN** the notification includes `receipt.dkimVerdict.status` with value "PASS"
- **THEN** the `InboundMessage.dkim_result` is set to "PASS"

#### Scenario: Parse DMARC verdict

- **WHEN** the notification includes `receipt.dmarcVerdict.status` with value "PASS"
- **THEN** the `InboundMessage.dmarc_result` is set to "PASS"

### Requirement: Verify SNS webhook signatures using X.509 certificates

The SES adapter SHALL verify SNS message signatures using the X.509 certificate from `SigningCertURL`.

#### Scenario: Verify valid SNS signature

- **WHEN** `verify_webhook_signature` is called with a valid SNS notification containing `Signature`, `SigningCertURL`, and required fields
- **THEN** the method returns without raising an exception

#### Scenario: Reject invalid SNS signature

- **WHEN** `verify_webhook_signature` is called with an invalid signature
- **THEN** the method raises `SESWebhookError`

#### Scenario: Reject SigningCertURL from non-AWS domain

- **WHEN** `verify_webhook_signature` is called with `SigningCertURL` not from `sns.{region}.amazonaws.com`
- **THEN** the method raises `SESWebhookError` indicating invalid certificate URL

#### Scenario: Cache signing certificates

- **WHEN** multiple webhooks arrive with the same `SigningCertURL`
- **THEN** the adapter reuses the cached certificate instead of fetching repeatedly

### Requirement: Handle SNS subscription confirmation

The SES adapter SHALL automatically confirm SNS topic subscriptions when receiving `SubscriptionConfirmation` messages.

#### Scenario: Confirm subscription request

- **WHEN** an SNS message with `Type: "SubscriptionConfirmation"` is received
- **THEN** the adapter fetches the `SubscribeURL` to confirm the subscription
- **AND** returns a success response

#### Scenario: Ignore unsubscribe confirmation

- **WHEN** an SNS message with `Type: "UnsubscribeConfirmation"` is received
- **THEN** the adapter logs the event and returns a success response without action

### Requirement: Provide webhook helper methods

The SES adapter SHALL provide helper methods for webhook event handling consistent with other adapters.

#### Scenario: Identify SNS message type

- **WHEN** `get_sns_message_type` is called with an SNS payload
- **THEN** it returns the value of the `Type` field ("Notification", "SubscriptionConfirmation", or "UnsubscribeConfirmation")

#### Scenario: Identify inbound email event

- **WHEN** `is_inbound_event` is called with an SNS Notification containing SES email data
- **THEN** it returns `True` if `notificationType` is "Received"

#### Scenario: Get event type

- **WHEN** `get_event_type` is called with an SES notification
- **THEN** it returns `"inbound"` for received email notifications

### Requirement: Implement AWS Signature Version 4 authentication

The SES adapter SHALL sign all SES API requests using AWS Signature Version 4 with the configured credentials.

#### Scenario: Sign request with SigV4

- **WHEN** the adapter makes a request to the SES API
- **THEN** the request includes `Authorization` header with AWS4-HMAC-SHA256 signature
- **AND** includes `X-Amz-Date` header with the request timestamp

#### Scenario: Use configured AWS credentials

- **WHEN** the adapter is initialized with `access_key_id`, `secret_access_key`, and `region`
- **THEN** these credentials are used for signing all API requests

#### Scenario: Support optional configuration set

- **WHEN** `send_email` is called and `AWS_SES_CONFIGURATION_SET` is configured
- **THEN** the request includes `ConfigurationSetName` in the payload
