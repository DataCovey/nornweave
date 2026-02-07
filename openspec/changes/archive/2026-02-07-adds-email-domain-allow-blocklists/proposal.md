## Why

NornWeave currently accepts inbound email from any sender and allows outbound email to any recipient with no domain-level filtering. Self-hosted operators need a way to restrict traffic — e.g., only accepting mail from their own organisation's domains, or blocking known spam domains from outbound sends. Without this, operators must rely on external mail-gateway rules, breaking the "self-contained Inbox-as-a-Service" promise.

## What Changes

- **Four new env-var lists** (comma-separated regexps):
  - `INBOUND_DOMAIN_ALLOWLIST` — only accept inbound mail from sender domains matching at least one pattern. Empty = allow all.
  - `INBOUND_DOMAIN_BLOCKLIST` — reject inbound mail from sender domains matching any pattern. Empty = block none.
  - `OUTBOUND_DOMAIN_ALLOWLIST` — only send outbound mail to recipient domains matching at least one pattern. Empty = allow all.
  - `OUTBOUND_DOMAIN_BLOCKLIST` — reject outbound sends to recipient domains matching any pattern. Empty = block none.
- **Evaluation order**: blocklist is checked first; if a domain matches the blocklist it is rejected regardless of the allowlist. If an allowlist is non-empty, only matching domains pass.
- **Inbound filtering** in `verdandi.ingest.ingest_message()` — reject before any storage or threading work. Returns a new `IngestResult(status="domain_blocked")`.
- **Outbound filtering** in the `send_message` route — return `HTTP 403` with a clear error when a recipient domain is blocked.
- **Logging** — every allow/block decision logged at `INFO` level for auditability.

## Non-goals

- Per-inbox or per-thread overrides — this is a global (instance-level) policy only.
- Full email-address filtering (user-part matching) — only the domain portion is evaluated.
- Admin UI for managing lists — configuration is env-var only for now.
- Wildcard/glob syntax — regex provides a superset; no need for a second pattern language.

## Capabilities

### New Capabilities

- `email-domain-filtering`: Domain-level allow/blocklist filtering for inbound and outbound email, configured via environment variables as lists of regexps.

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **Config** (`core/config.py`): Four new optional `list[str]` settings with comma-separated parsing.
- **Inbound path** (`verdandi/ingest.py`): New early-exit check in `ingest_message()`.
- **Outbound path** (`yggdrasil/routes/v1/messages.py`): New validation before `send_email()` call.
- **New module** (`core/domain_filter.py` or similar): Shared filtering logic (compile regexps once, match domain).
- **Tests**: Unit tests for the filter logic; integration tests for inbound rejection and outbound 403.
- **Docs**: New "Domain Filtering" section in configuration guide.
- **No database changes, no migration, no breaking API changes.**
