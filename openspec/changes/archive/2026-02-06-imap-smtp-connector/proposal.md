## Why

NornWeave currently requires a transactional email provider (Mailgun, SES, SendGrid, Resend) for both sending and receiving emails. This creates a vendor dependency that conflicts with the project's self-hosted philosophy. Many teams already have a mail server (Gmail, Office 365, Fastmail, self-hosted Postfix/Dovecot) but don't have a transactional email account. Adding IMAP/SMTP as a native email provider eliminates this barrier, making NornWeave usable with any standard mail server — zero vendor lock-in, zero additional accounts needed.

## What Changes

- New `SmtpImapAdapter` implementing `EmailProvider` for sending via SMTP and receiving via IMAP
- SMTP sending via `aiosmtplib` with TLS/STARTTLS support, mapping cleanly to the existing `send_email()` interface
- IMAP polling infrastructure: a background worker that periodically checks IMAP mailboxes for new messages using UID-based state tracking to avoid re-processing
- Raw RFC 822 email parsing using Python's `email` standard library, converting to the existing `InboundMessage` format and feeding into the Verdandi ingestion pipeline
- New configuration settings for SMTP/IMAP server credentials and polling intervals
- `EMAIL_PROVIDER=imap-smtp` as the new provider option alongside existing providers

## Capabilities

### New Capabilities
- `imap-smtp-adapter`: SMTP sending and IMAP polling adapter implementing the `EmailProvider` interface, including raw email parsing, UID-based state tracking, and background polling infrastructure

### Modified Capabilities
- `rest-api`: New endpoint `POST /v1/inboxes/{id}/sync` for on-demand IMAP sync (manual trigger)

## Non-goals

- **OAuth2 for Gmail/O365**: Username/password and app-password authentication only in this change. OAuth2 token flows are a separate future enhancement.
- **IMAP IDLE**: Real-time push via IMAP IDLE is an optimization for later. Initial implementation uses interval-based polling.
- **Per-inbox provider configuration**: All inboxes share the same IMAP/SMTP server credentials. Multi-server or mixed-provider setups are out of scope.
- **NornWeave as an IMAP server**: Exposing inboxes via IMAP for admin debugging was considered and rejected — the cost/benefit ratio doesn't justify it.

## Impact

- **New dependency**: `aiosmtplib` for async SMTP sending
- **Standard library**: `email`, `imaplib` (or `aioimaplib` for async) for IMAP/message parsing
- **Code changes**: New adapter in `adapters/`, new polling worker, config additions to `Settings`, dependency injection update in `yggdrasil/dependencies.py`
- **API**: One new endpoint (`POST /v1/inboxes/{id}/sync`); existing send/receive APIs unchanged
- **Database**: May need a small table or column to track IMAP polling state (last seen UID per inbox)
- **No breaking changes**: Existing webhook-based providers continue to work unchanged
