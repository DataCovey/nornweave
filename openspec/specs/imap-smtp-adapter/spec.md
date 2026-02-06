# IMAP/SMTP Adapter Capability

Defines the IMAP/SMTP email provider adapter that enables sending via SMTP and receiving via IMAP polling, as an alternative to transactional providers (Mailgun, SES, SendGrid, Resend).

## Requirements

### Requirement: Send email via SMTP with aiosmtplib

The SMTP/IMAP adapter SHALL send emails using `aiosmtplib` through the `send_email()` method of the `EmailProvider` interface, supporting TLS/STARTTLS, threading headers, CC/BCC, and attachments.

#### Scenario: Send simple email via SMTP

- **WHEN** `send_email` is called with recipients, subject, and plain text body
- **THEN** the adapter connects to the configured SMTP server and sends the email
- **AND** returns a generated Message-ID as the provider message ID

#### Scenario: Send email with STARTTLS on port 587

- **WHEN** `SMTP_USE_TLS` is `true` and `SMTP_PORT` is `587`
- **THEN** the adapter connects to the SMTP server and upgrades to TLS via STARTTLS

#### Scenario: Send email with implicit TLS on port 465

- **WHEN** `SMTP_USE_TLS` is `true` and `SMTP_PORT` is `465`
- **THEN** the adapter connects using implicit TLS (SSL wrapper)

#### Scenario: Send email with threading headers

- **WHEN** `send_email` is called with `message_id`, `in_reply_to`, and `references` parameters
- **THEN** the outgoing email includes `Message-ID`, `In-Reply-To`, and `References` headers per RFC 5322

#### Scenario: Send email with CC and BCC recipients

- **WHEN** `send_email` is called with `cc` and `bcc` lists
- **THEN** CC addresses appear in the `Cc:` header and all recipients (to, cc, bcc) receive the message
- **AND** BCC addresses do NOT appear in any header

#### Scenario: Send email with attachments

- **WHEN** `send_email` is called with a list of `SendAttachment` objects
- **THEN** the email is sent as a MIME multipart message with each attachment as a part
- **AND** inline attachments include `Content-ID` and `Content-Disposition: inline`

#### Scenario: Send email with HTML body

- **WHEN** `send_email` is called with `html_body` parameter
- **THEN** the email is sent as `multipart/alternative` with both plain text and HTML parts

#### Scenario: Send email with Markdown conversion

- **WHEN** `send_email` is called with plain text body and no `html_body`
- **THEN** the adapter converts the body to HTML using the `markdown` library
- **AND** includes both plain text and HTML parts

#### Scenario: SMTP authentication

- **WHEN** `SMTP_USERNAME` and `SMTP_PASSWORD` are configured
- **THEN** the adapter authenticates with the SMTP server before sending

#### Scenario: SMTP connection failure

- **WHEN** the SMTP server is unreachable or rejects the connection
- **THEN** the adapter raises an appropriate error with connection details for debugging

### Requirement: Parse raw RFC 822 emails into InboundMessage

The adapter SHALL parse raw email messages fetched via IMAP into the standardized `InboundMessage` dataclass using Python's `email.message.EmailMessage` API.

#### Scenario: Parse simple plain text email

- **WHEN** a raw RFC 822 message with `Content-Type: text/plain` is parsed
- **THEN** the resulting `InboundMessage` has `body_plain` populated and `body_html` set to `None`

#### Scenario: Parse multipart email with HTML and plain text

- **WHEN** a raw `multipart/alternative` message is parsed
- **THEN** the resulting `InboundMessage` has both `body_plain` and `body_html` populated

#### Scenario: Parse threading headers

- **WHEN** the raw email contains `Message-ID`, `In-Reply-To`, and `References` headers
- **THEN** these are mapped to the corresponding `InboundMessage` fields
- **AND** `references` is parsed from a space-separated string into a list

#### Scenario: Parse sender and recipient addresses

- **WHEN** the raw email has `From: Alice <alice@example.com>` and `To: inbox@nornweave.example.com`
- **THEN** `from_address` is `alice@example.com` and `to_address` is `inbox@nornweave.example.com`

#### Scenario: Parse CC addresses

- **WHEN** the raw email has a `Cc:` header with multiple addresses
- **THEN** `cc_addresses` contains all parsed CC email addresses

#### Scenario: Parse email with attachments

- **WHEN** the raw email is `multipart/mixed` with attachment MIME parts
- **THEN** each attachment is mapped to an `InboundAttachment` with `filename`, `content_type`, `content`, `size_bytes`, and `disposition`

#### Scenario: Parse inline attachments with Content-ID

- **WHEN** the raw email contains inline parts with `Content-ID` headers
- **THEN** the corresponding `InboundAttachment` has `disposition` set to `INLINE` and `content_id` populated
- **AND** `content_id_map` is built for CID URL resolution

#### Scenario: Parse Authentication-Results header

- **WHEN** the raw email contains an `Authentication-Results` header with SPF, DKIM, and DMARC results
- **THEN** `spf_result`, `dkim_result`, and `dmarc_result` are populated on the `InboundMessage`

#### Scenario: Handle RFC 2047 encoded headers

- **WHEN** the raw email has MIME-encoded headers (e.g., `=?UTF-8?B?...?=` subject)
- **THEN** headers are decoded properly using `email.policy.default`

#### Scenario: Handle malformed email gracefully

- **WHEN** a raw email has missing or malformed headers
- **THEN** the parser populates available fields and uses sensible defaults for missing ones (empty string for subject, current timestamp for missing Date)

### Requirement: Poll IMAP mailbox for new messages on an interval

The adapter SHALL run a background polling loop that periodically checks the configured IMAP mailbox for new messages and feeds them into the ingestion pipeline.

#### Scenario: Poll on configured interval

- **WHEN** the application starts with `EMAIL_PROVIDER=imap-smtp`
- **THEN** the IMAP poller starts as a background task polling every `IMAP_POLL_INTERVAL` seconds (default 60)

#### Scenario: Fetch only new messages using UID

- **WHEN** a poll cycle runs and `last_uid` is 42 for an inbox
- **THEN** the poller issues `UID SEARCH UID 43:*` to find messages newer than UID 42
- **AND** fetches only those messages

#### Scenario: First poll with no prior state

- **WHEN** a poll cycle runs and no `imap_poll_state` record exists for an inbox
- **THEN** the poller fetches all messages currently in the mailbox
- **AND** creates the state record with the highest processed UID

#### Scenario: Feed fetched messages into ingestion pipeline

- **WHEN** new messages are fetched from IMAP
- **THEN** each message is parsed into an `InboundMessage` and passed to the shared `ingest_message()` function
- **AND** the ingestion pipeline handles inbox lookup, deduplication, threading, attachment storage, and summarization

#### Scenario: Update UID state after successful ingestion

- **WHEN** a message with UID 55 is successfully ingested
- **THEN** `imap_poll_state.last_uid` is updated to 55 for the corresponding inbox
- **AND** `updated_at` is set to the current timestamp

#### Scenario: Graceful shutdown

- **WHEN** the FastAPI application shuts down
- **THEN** the poller task is cancelled cleanly without losing in-progress messages

#### Scenario: Connection failure with reconnect

- **WHEN** the IMAP connection fails during a poll cycle
- **THEN** the poller logs the error and retries with exponential backoff
- **AND** does NOT crash the FastAPI application

#### Scenario: UIDVALIDITY change detection

- **WHEN** the IMAP server reports a different `UIDVALIDITY` than what is stored in `imap_poll_state`
- **THEN** the poller resets `last_uid` to 0 and re-syncs all messages in the mailbox
- **AND** logs a warning about the UIDVALIDITY change

### Requirement: Track IMAP polling state per inbox

The adapter SHALL persist IMAP polling state in an `imap_poll_state` database table to track the last processed UID per inbox and avoid re-processing.

#### Scenario: State table schema

- **WHEN** the Alembic migration runs
- **THEN** the `imap_poll_state` table is created with columns: `inbox_id` (PK, FK to inboxes), `last_uid` (integer), `uid_validity` (integer), `mailbox` (string, default "INBOX"), `updated_at` (datetime)

#### Scenario: State persists across restarts

- **WHEN** the application restarts and the poller begins
- **THEN** it reads `last_uid` and `uid_validity` from `imap_poll_state` and resumes from where it left off

#### Scenario: State record creation for new inbox

- **WHEN** a poll cycle encounters an inbox with no `imap_poll_state` record
- **THEN** a new record is created with `last_uid=0` and the current `UIDVALIDITY` from the server

### Requirement: Configurable post-fetch behavior

The adapter SHALL support configurable behavior for marking messages as read and deleting them after ingestion.

#### Scenario: Mark messages as read (default)

- **WHEN** `IMAP_MARK_AS_READ` is `true` (the default)
- **THEN** the poller sets the `\Seen` flag on each message after successful ingestion

#### Scenario: Do not mark messages as read

- **WHEN** `IMAP_MARK_AS_READ` is `false`
- **THEN** the poller leaves message flags unchanged after ingestion

#### Scenario: Delete messages after fetch

- **WHEN** `IMAP_DELETE_AFTER_FETCH` is `true`
- **THEN** the poller flags messages as `\Deleted` and expunges them after successful ingestion

#### Scenario: Do not delete messages (default)

- **WHEN** `IMAP_DELETE_AFTER_FETCH` is `false` (the default)
- **THEN** messages remain in the mailbox after ingestion

#### Scenario: Safety invariant for delete without mark-as-read

- **WHEN** `IMAP_DELETE_AFTER_FETCH` is `true` and `IMAP_MARK_AS_READ` is `false`
- **THEN** the adapter SHALL refuse to start and raise a configuration error

### Requirement: SmtpImapAdapter implements EmailProvider interface

The `SmtpImapAdapter` SHALL implement the `EmailProvider` ABC by composing `SmtpSender` and `ImapReceiver` internal classes.

#### Scenario: send_email delegates to SmtpSender

- **WHEN** `send_email()` is called on the adapter
- **THEN** the call is delegated to the internal `SmtpSender` instance

#### Scenario: parse_inbound_webhook raises NotImplementedError

- **WHEN** `parse_inbound_webhook()` is called on the adapter
- **THEN** it raises `NotImplementedError` because IMAP does not use webhooks

#### Scenario: Adapter instantiation via dependency injection

- **WHEN** `EMAIL_PROVIDER` is set to `imap-smtp`
- **THEN** `get_email_provider()` in `yggdrasil/dependencies.py` creates and returns a `SmtpImapAdapter`

### Requirement: Configuration settings for SMTP/IMAP

The `Settings` class SHALL include all SMTP and IMAP configuration fields with appropriate defaults.

#### Scenario: SMTP settings

- **WHEN** `EMAIL_PROVIDER=imap-smtp` is configured
- **THEN** the following environment variables are available: `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` (default true)

#### Scenario: IMAP settings

- **WHEN** `EMAIL_PROVIDER=imap-smtp` is configured
- **THEN** the following environment variables are available: `IMAP_HOST`, `IMAP_PORT` (default 993), `IMAP_USERNAME`, `IMAP_PASSWORD`, `IMAP_USE_SSL` (default true), `IMAP_POLL_INTERVAL` (default 60), `IMAP_MAILBOX` (default "INBOX")

#### Scenario: Post-fetch behavior settings

- **WHEN** `EMAIL_PROVIDER=imap-smtp` is configured
- **THEN** the following environment variables are available: `IMAP_MARK_AS_READ` (default true), `IMAP_DELETE_AFTER_FETCH` (default false)

#### Scenario: Provider literal updated

- **WHEN** the `email_provider` field is validated
- **THEN** it accepts `"imap-smtp"` as a valid value alongside `"mailgun"`, `"ses"`, `"sendgrid"`, `"resend"`

### Requirement: Package as smtpimap optional dependency flavor

The SMTP/IMAP adapter dependencies SHALL be packaged as an optional dependency group named `smtpimap` in `pyproject.toml`.

#### Scenario: Install smtpimap extras

- **WHEN** a user runs `pip install nornweave[smtpimap]`
- **THEN** `aiosmtplib` and `aioimaplib` are installed

#### Scenario: Included in all extras

- **WHEN** a user runs `pip install nornweave[all]`
- **THEN** the `smtpimap` dependencies are included

#### Scenario: Lazy import on provider selection

- **WHEN** `EMAIL_PROVIDER` is NOT `imap-smtp`
- **THEN** `aiosmtplib` and `aioimaplib` are NOT imported
- **AND** the application starts without these packages installed

### Requirement: Shared ingestion function for all providers

The ingestion pipeline SHALL be extracted into a shared `ingest_message()` function in `verdandi/ingest.py` that both webhook handlers and the IMAP poller use.

#### Scenario: Ingest from IMAP poller

- **WHEN** the IMAP poller parses a new email into `InboundMessage`
- **THEN** it calls `ingest_message()` which performs inbox lookup, deduplication, thread resolution, content parsing, message storage, attachment storage, and thread summarization

#### Scenario: Ingest from webhook handler

- **WHEN** a webhook handler (Mailgun, SES, SendGrid, Resend) receives an inbound email
- **THEN** it can call `ingest_message()` instead of duplicating the ingestion logic

#### Scenario: Duplicate message detection

- **WHEN** `ingest_message()` is called with an `InboundMessage` whose `message_id` already exists for the target inbox
- **THEN** it returns a result indicating the message is a duplicate without creating a new record

#### Scenario: No matching inbox

- **WHEN** `ingest_message()` is called with a `to_address` that does not match any inbox
- **THEN** it returns a result indicating no inbox was found
