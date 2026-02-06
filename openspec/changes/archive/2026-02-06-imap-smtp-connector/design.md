## Context

NornWeave's email provider layer is built around the `EmailProvider` ABC with two methods: `send_email()` for outbound and `parse_inbound_webhook()` for inbound. All four existing adapters (Mailgun, SES, SendGrid, Resend) follow a push model — providers push email data to NornWeave via webhooks. The webhook handlers in `yggdrasil/routes/webhooks/` receive these payloads, call the adapter's `parse_inbound_webhook()`, then run the ingestion pipeline (find inbox → dedup → resolve thread → parse content → store message → store attachments → trigger summarization).

Adding IMAP/SMTP introduces a fundamentally different model: SMTP sending maps naturally to `send_email()`, but IMAP receiving is pull-based (NornWeave polls the mail server) rather than push-based (provider calls NornWeave). This is the core design challenge.

The FastAPI app uses a `lifespan` context manager for startup/shutdown (currently database init/close only). The project uses `uv` for package management with optional dependency groups (`postgres`, `mcp`, `attachments`, etc.) in `pyproject.toml`.

## Goals / Non-Goals

**Goals:**
- Send emails via SMTP with full feature parity (threading headers, CC/BCC, attachments, TLS)
- Receive emails via IMAP polling with UID-based state tracking
- Reuse the existing Verdandi ingestion pipeline (threading, parsing, attachments, summarization)
- Package as an optional dependency flavor (`smtpimap`) following existing patterns
- Background polling integrated into the FastAPI lifespan (no separate process required)
- Manual sync endpoint for on-demand IMAP fetching

**Non-Goals:**
- OAuth2 authentication flows (Gmail, Office 365)
- IMAP IDLE for real-time push
- Per-inbox IMAP/SMTP credentials (single server config)
- Changes to the `EmailProvider` ABC contract

## Decisions

### 1. Adapter split: `SmtpSender` + `ImapReceiver` composed into `SmtpImapAdapter`

The `EmailProvider` ABC bundles sending and inbound parsing into one class. For IMAP/SMTP, these are completely independent concerns (different servers, protocols, credentials). The adapter will internally compose two focused classes:

- `SmtpSender` — handles `send_email()` via `aiosmtplib`
- `ImapReceiver` — handles IMAP polling, UID tracking, and raw email parsing into `InboundMessage`
- `SmtpImapAdapter(EmailProvider)` — facade that delegates to both and satisfies the ABC

**Why not modify the ABC?** Changing `EmailProvider` would affect all four existing adapters for no benefit. The `parse_inbound_webhook()` method on `SmtpImapAdapter` will raise `NotImplementedError` since IMAP doesn't use webhooks — the receiver feeds messages directly into the ingestion pipeline, bypassing the webhook route.

**Alternatives considered:**
- Separate `InboundProvider` / `OutboundProvider` ABCs: Cleaner in theory, but over-engineers the interface for a single adapter variant. Can refactor later if more pull-based providers emerge.

### 2. IMAP library: `aioimaplib` for native async

Use `aioimaplib` for async IMAP operations rather than running stdlib `imaplib` in a thread executor.

**Why `aioimaplib`?**
- Native async avoids thread pool overhead and plays well with the existing async-first architecture
- Supports IMAP4rev1 including `UID FETCH`, `UID SEARCH`, and `IDLE` (future use)
- Actively maintained, pure Python

**Why not `imaplib` + `asyncio.to_thread`?**
- Works but adds thread pool complexity and makes cancellation harder
- Every IMAP operation would block a thread pool slot during network I/O

### 3. Background worker: `asyncio.Task` in FastAPI lifespan

The IMAP poller runs as an `asyncio.Task` created during the app lifespan, alongside database initialization:

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    await init_database(settings)
    poller_task = None
    if settings.email_provider == "imap-smtp":
        from nornweave.verdandi.imap_poller import ImapPoller
        poller = ImapPoller(settings)
        poller_task = asyncio.create_task(poller.run())
    yield
    if poller_task:
        poller_task.cancel()
        with suppress(asyncio.CancelledError):
            await poller_task
    await close_database()
```

**Why lifespan task, not a separate process?**
- Zero operational overhead — no extra process to manage, no IPC
- Shares the database session factory and settings already initialized
- Clean shutdown via task cancellation on app stop
- Sufficient for the single-server polling model (non-goal: multi-server)

**Why not Celery/ARQ/background workers?**
- Adds a heavy dependency (Redis, broker) for a simple periodic loop
- The `ratelimit` extra already includes Redis, but requiring it for basic IMAP is too much friction

### 4. UID-based state tracking via `imap_poll_state` table

Track the last-seen IMAP UID per inbox to avoid re-processing:

```
imap_poll_state
├── inbox_id (FK → inboxes.id, PK)
├── last_uid (int) — highest UID successfully processed
├── mailbox (str) — IMAP folder name (default "INBOX")
└── updated_at (datetime)
```

**Why a separate table, not a column on Inbox?**
- Keeps IMAP-specific state decoupled from the core Inbox model
- Only exists when using the SMTP/IMAP provider — no schema noise for webhook users
- Easy to extend later (e.g., per-folder tracking, error counts)

This requires an Alembic migration. The table is created conditionally and is harmless if the SMTP/IMAP provider isn't used.

### 5. Raw email parsing: stdlib `email` module → `InboundMessage`

Parse RFC 822 messages using Python's `email.message.EmailMessage` (modern API) and map to the existing `InboundMessage` dataclass:

- `email.policy.default` for proper header decoding (MIME, RFC 2047)
- Walk MIME parts to extract `text/plain`, `text/html`, and attachments
- Map `Message-ID`, `In-Reply-To`, `References` headers for threading
- Extract SPF/DKIM/DMARC from `Authentication-Results` header (if present)

This is actually simpler than the provider-specific webhook parsing because the raw email format is standardized. The SES adapter already does similar MIME parsing for its `content` field.

### 6. Package flavor: `smtpimap` optional dependency group

Add to `pyproject.toml`:

```toml
smtpimap = [
    "aiosmtplib>=2.0.0",
    "aioimaplib>=2.0.0",
]
```

Update the `all` extra to include it:

```toml
all = [
    "nornweave[postgres,mcp,attachments,search,ratelimit,s3,gcs,llm,smtpimap]",
]
```

**Why a separate flavor?**
- `aiosmtplib` and `aioimaplib` are only needed when using this provider
- Follows the existing pattern (postgres, mcp, attachments, etc.)
- Install with `pip install nornweave[smtpimap]` or `uv add nornweave[smtpimap]`

### 7. Provider config: `EMAIL_PROVIDER=imap-smtp` with dedicated settings

```
EMAIL_PROVIDER=imap-smtp
SMTP_HOST=mail.example.com
SMTP_PORT=587
SMTP_USERNAME=user@example.com
SMTP_PASSWORD=secret
SMTP_USE_TLS=true          # STARTTLS (port 587) vs implicit TLS (port 465)
IMAP_HOST=mail.example.com
IMAP_PORT=993
IMAP_USERNAME=user@example.com
IMAP_PASSWORD=secret
IMAP_USE_SSL=true
IMAP_POLL_INTERVAL=60      # seconds between polls
IMAP_MAILBOX=INBOX          # IMAP folder to poll
```

**Why `imap-smtp` as the provider name?**
- Makes the dual nature explicit — this provider handles both IMAP (receiving) and SMTP (sending)
- Avoids confusion: `smtp` alone would suggest send-only, surprising users when IMAP polling activates
- Mirrors the `smtpimap` package flavor name for consistency

### 8. Ingestion flow: poller → shared ingestion function

Extract the common ingestion logic from webhook handlers into a shared function in Verdandi:

```python
# verdandi/ingest.py
async def ingest_message(
    inbound: InboundMessage,
    storage: StorageInterface,
    settings: Settings,
) -> IngestResult:
    """Shared ingestion: find inbox → dedup → thread → parse → store → summarize."""
```

Both webhook handlers and the IMAP poller call this function. This eliminates the duplicated ingestion logic across the four webhook handlers and provides a clean entry point for the poller.

**Why refactor now?**
- The webhook handlers (Mailgun, Resend, SES, SendGrid) each duplicate ~100 lines of identical ingestion logic (find inbox, dedup, create thread, store message, store attachments, update thread, trigger summary)
- Adding a fifth consumer (IMAP poller) that duplicates this again would make it worse
- A shared function also benefits future providers

### 9. Manual sync endpoint: `POST /v1/inboxes/{inbox_id}/sync`

Triggers an immediate IMAP sync for a specific inbox. Returns the number of new messages fetched. Only available when `EMAIL_PROVIDER=imap-smtp`.

This is useful for:
- Testing/debugging IMAP connectivity
- Immediate sync after inbox creation
- Webhooks from external systems that know new mail arrived

Returns `404` if the provider isn't `imap-smtp`, `200` with sync results otherwise.

## Risks / Trade-offs

**[Polling latency]** → Interval-based polling adds up to `IMAP_POLL_INTERVAL` seconds of delay. Mitigation: default to 60s (acceptable for AI agent use cases), document IMAP IDLE as future optimization. The manual sync endpoint provides an escape hatch.

**[Connection stability]** → Long-lived IMAP connections can drop. Mitigation: reconnect with exponential backoff in the polling loop. Log connection failures clearly. The poller should be resilient to transient network issues.

**[Single mailbox model]** → All inboxes poll from the same IMAP account/folder. Inbound routing relies on the `To:` address matching an inbox, same as webhooks. Mitigation: this works well for catch-all or aliased mailboxes. Per-inbox credentials are a documented non-goal.

**[UID validity]** → IMAP UIDs reset when `UIDVALIDITY` changes (rare, happens on mailbox rebuild). Mitigation: store `UIDVALIDITY` in `imap_poll_state` and re-sync from scratch if it changes.

**[Alembic migration]** → Adding the `imap_poll_state` table requires a migration that runs for all users, even those not using SMTP/IMAP. Mitigation: the table is tiny and empty for non-SMTP users — no performance impact.

**[`aioimaplib` maturity]** → Less battle-tested than `imaplib`. Mitigation: fallback plan is to use `imaplib` with `asyncio.to_thread()` if `aioimaplib` proves unreliable. The `ImapReceiver` abstraction makes this swap internal.

### 10. Post-fetch behavior: configurable mark-as-read and delete

Two settings control what happens to emails after NornWeave processes them:

```
IMAP_MARK_AS_READ=true       # Set \Seen flag after processing (default: true)
IMAP_DELETE_AFTER_FETCH=false # Expunge after processing (default: false)
```

**Mark as read (`IMAP_MARK_AS_READ`):** Defaults to `true`. Setting the `\Seen` flag serves as a secondary guard against re-processing if UID tracking fails, and signals to other clients that the message has been consumed. Users who also read the mailbox directly can set this to `false` to avoid confusion.

**Delete after fetch (`IMAP_DELETE_AFTER_FETCH`):** Defaults to `false`. When `true`, messages are flagged `\Deleted` and expunged after successful ingestion. Useful for dedicated NornWeave mailboxes where the IMAP account is solely a relay. Requires `IMAP_MARK_AS_READ=true` as a safety invariant — the adapter will refuse to start if delete is enabled without mark-as-read.
