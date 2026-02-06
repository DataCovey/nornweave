## 1. Package & Configuration

- [x] 1.1 Add `smtpimap` optional dependency group to `pyproject.toml` (`aiosmtplib`, `aioimaplib`) and include it in the `all` extra
- [x] 1.2 Add SMTP settings to `Settings` in `core/config.py`: `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` (true)
- [x] 1.3 Add IMAP settings to `Settings`: `IMAP_HOST`, `IMAP_PORT` (993), `IMAP_USERNAME`, `IMAP_PASSWORD`, `IMAP_USE_SSL` (true), `IMAP_POLL_INTERVAL` (60), `IMAP_MAILBOX` ("INBOX")
- [x] 1.4 Add post-fetch behavior settings to `Settings`: `IMAP_MARK_AS_READ` (true), `IMAP_DELETE_AFTER_FETCH` (false)
- [x] 1.5 Update `email_provider` Literal type to include `"imap-smtp"` alongside existing providers
- [x] 1.6 Add model validator to enforce safety invariant: `IMAP_DELETE_AFTER_FETCH=true` requires `IMAP_MARK_AS_READ=true`
- [x] 1.7 Add `aioimaplib` and `aiosmtplib` to mypy overrides for `ignore_missing_imports`

## 2. Database: IMAP Poll State

- [x] 2.1 Create SQLAlchemy model for `imap_poll_state` table with columns: `inbox_id` (PK, FK), `last_uid` (int), `uid_validity` (int), `mailbox` (str, default "INBOX"), `updated_at` (datetime)
- [x] 2.2 Create Alembic migration to add the `imap_poll_state` table
- [x] 2.3 Add poll state CRUD methods to `StorageInterface`: `get_imap_poll_state(inbox_id)`, `upsert_imap_poll_state(inbox_id, last_uid, uid_validity, mailbox)`
- [x] 2.4 Implement poll state methods in PostgreSQL adapter
- [x] 2.5 Implement poll state methods in SQLite adapter

## 3. Shared Ingestion Function

- [x] 3.1 Create `verdandi/ingest.py` with `ingest_message(inbound, storage, settings) -> IngestResult` extracting common logic from webhook handlers (inbox lookup, dedup, thread resolution, message creation, attachment storage, thread update, summarization)
- [x] 3.2 Define `IngestResult` dataclass with fields: `status` (received/duplicate/no_inbox), `message_id`, `thread_id`, optional `warning`
- [x] 3.3 Refactor Resend webhook handler to use `ingest_message()` and verify behavior is preserved
- [x] 3.4 Refactor Mailgun webhook handler to use `ingest_message()`
- [x] 3.5 Refactor SES webhook handler to use `ingest_message()` (placeholder — no ingestion logic to refactor yet)
- [x] 3.6 Refactor SendGrid webhook handler to use `ingest_message()` (placeholder — no ingestion logic to refactor yet)

## 4. RFC 822 Email Parser

- [x] 4.1 Create `verdandi/email_parser.py` with `parse_raw_email(raw_bytes: bytes) -> InboundMessage` using `email.message.EmailMessage` with `email.policy.default`
- [x] 4.2 Implement MIME body extraction: walk parts for `text/plain` and `text/html`, handle `multipart/alternative` and `multipart/mixed`
- [x] 4.3 Implement header parsing: `From`, `To`, `Cc`, `Subject`, `Date`, `Message-ID`, `In-Reply-To`, `References` (space-separated → list)
- [x] 4.4 Implement attachment extraction: map MIME parts to `InboundAttachment` with filename, content_type, content bytes, disposition, and content_id
- [x] 4.5 Implement `Authentication-Results` header parsing for SPF/DKIM/DMARC results
- [x] 4.6 Handle edge cases: RFC 2047 encoded headers, missing headers with sensible defaults, malformed emails

## 5. SMTP Sender

- [x] 5.1 Create `adapters/smtp_imap.py` with `SmtpSender` class
- [x] 5.2 Implement `send_email()`: build `email.message.EmailMessage`, set headers (From, To, Cc, Subject, Message-ID, In-Reply-To, References), add text/html body parts
- [x] 5.3 Implement attachment support: add `SendAttachment` objects as MIME parts with correct disposition and content_id
- [x] 5.4 Implement SMTP connection: STARTTLS (port 587) vs implicit TLS (port 465) based on `SMTP_USE_TLS` and `SMTP_PORT`
- [x] 5.5 Implement SMTP authentication with `SMTP_USERNAME`/`SMTP_PASSWORD`
- [x] 5.6 Implement Markdown → HTML conversion when `html_body` is not provided

## 6. IMAP Receiver & Poller

- [x] 6.1 Create `ImapReceiver` class in `adapters/smtp_imap.py` with IMAP connection management (connect, authenticate, select mailbox)
- [x] 6.2 Implement `fetch_new_messages(last_uid)`: `UID SEARCH UID {last_uid+1}:*`, `UID FETCH` raw messages
- [x] 6.3 Implement UIDVALIDITY tracking: check on each poll, reset `last_uid` to 0 if changed
- [x] 6.4 Implement post-fetch behavior: set `\Seen` flag when `IMAP_MARK_AS_READ=true`, flag `\Deleted` + expunge when `IMAP_DELETE_AFTER_FETCH=true`
- [x] 6.5 Implement connection error handling with exponential backoff reconnect
- [x] 6.6 Create `verdandi/imap_poller.py` with `ImapPoller` class: polling loop with `asyncio.sleep(IMAP_POLL_INTERVAL)`, per-inbox state management, call `parse_raw_email()` then `ingest_message()` for each new message

## 7. SmtpImapAdapter Facade

- [x] 7.1 Create `SmtpImapAdapter(EmailProvider)` in `adapters/smtp_imap.py` composing `SmtpSender` and `ImapReceiver`
- [x] 7.2 Implement `send_email()` delegating to `SmtpSender`
- [x] 7.3 Implement `parse_inbound_webhook()` raising `NotImplementedError`
- [x] 7.4 Update `get_email_provider()` in `yggdrasil/dependencies.py` to handle `EMAIL_PROVIDER=imap-smtp` with lazy import of `SmtpImapAdapter`

## 8. Background Poller Integration

- [x] 8.1 Update `lifespan()` in `yggdrasil/app.py`: create and start `ImapPoller` as `asyncio.Task` when `EMAIL_PROVIDER=imap-smtp`
- [x] 8.2 Implement clean shutdown: cancel poller task on app shutdown, await with `CancelledError` suppression

## 9. Manual Sync Endpoint

- [x] 9.1 Create `POST /v1/inboxes/{inbox_id}/sync` route in `yggdrasil/routes/v1/inboxes.py`
- [x] 9.2 Implement provider check: return 404 if `EMAIL_PROVIDER` is not `imap-smtp`
- [x] 9.3 Implement inbox validation: return 404 if inbox not found
- [x] 9.4 Implement on-demand IMAP fetch for the specific inbox, return `{ "status": "synced", "new_messages": <count> }`
- [x] 9.5 Handle IMAP connection failures: return 502 with error detail

## 10. Tests

- [x] 10.1 Unit tests for `parse_raw_email()`: plain text, multipart, threading headers, attachments, inline attachments, encoded headers, malformed emails
- [x] 10.2 Unit tests for `SmtpSender.send_email()`: basic send, TLS modes, threading headers, CC/BCC, attachments, HTML body, Markdown conversion
- [x] 10.3 Unit tests for `ImapReceiver`: UID search, fetch, UIDVALIDITY change, mark-as-read, delete-after-fetch, connection failure/reconnect
- [x] 10.4 Unit tests for `ingest_message()`: successful ingestion, duplicate detection, no matching inbox
- [x] 10.5 Unit tests for configuration validation: safety invariant (delete without mark-as-read), provider literal acceptance
- [x] 10.6 Integration test for manual sync endpoint: successful sync, wrong provider, missing inbox, IMAP failure
- [x] 10.7 Add sample `.eml` test fixtures to `tests/fixtures/` for the email parser tests

## 11. Documentation

- [x] 11.1 Create IMAP/SMTP setup guide at `web/content/docs/guides/imap-smtp.md` following the pattern of existing provider guides (Mailgun, SES, SendGrid, Resend): installation (`nornweave[smtpimap]`), configuration (SMTP/IMAP env vars), IMAP polling behavior, post-fetch options, manual sync endpoint
- [x] 11.2 Update `web/content/docs/guides/_index.md` to add IMAP/SMTP card alongside existing provider cards
- [x] 11.3 Update provider comparison tables in `web/content/docs/_index.md` and `web/content/docs/concepts/_index.md` to include IMAP/SMTP row (sending: SMTP, receiving: IMAP polling, no auto-route setup)
- [x] 11.4 Update FAQ at `web/content/docs/faq.md` to mention IMAP/SMTP as a provider-agnostic option alongside Mailgun/SendGrid/SES/Resend
- [x] 11.5 Update CHANGELOG.md with the new IMAP/SMTP provider feature
