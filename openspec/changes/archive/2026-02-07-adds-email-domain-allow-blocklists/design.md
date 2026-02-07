## Context

NornWeave has two main email paths:

- **Inbound**: webhook handlers and IMAP poller both converge on `verdandi.ingest.ingest_message()`, which receives an `InboundMessage` and writes it to storage.
- **Outbound**: the `send_message` route in `yggdrasil/routes/v1/messages.py` sends mail via `email_provider.send_email()`.

Neither path performs any domain-level policy enforcement today. Operators who need to restrict traffic must do so externally (MTA rules, firewall, etc.).

The configuration layer uses `pydantic-settings` (`core/config.py`) with env-var aliases. Lists like `CORS_ORIGINS` are stored as plain strings; there is no existing pattern for list-of-regex fields.

## Goals / Non-Goals

**Goals:**

- Allow operators to define domain-level allow/blocklists for both inbound (sender) and outbound (recipient) traffic, using environment variables.
- Enforce these policies consistently across all email entry/exit points.
- Keep the filtering logic provider-agnostic and centralized.
- Provide clear, auditable logging of every policy decision.

**Non-Goals:**

- Per-inbox / per-thread overrides (global policy only).
- Full email-address matching (domain-only).
- Admin UI or runtime reloading (env-var config, requires restart).
- Subdomain inheritance (e.g., `example\.com` does **not** auto-match `sub.example.com`; operators write `(.*\.)?example\.com` if they want that).

## Decisions

### D1 — New module `core/domain_filter.py`

**Decision**: Create a standalone module that owns all filtering logic.

**Rationale**: Both inbound and outbound paths need the same check. Duplicating the logic in `verdandi` and `yggdrasil` would be fragile. A single module is easy to unit-test in isolation.

**Alternatives considered**:
- *Middleware in FastAPI*: Would only cover webhook-based inbound + outbound route, would miss IMAP poller, and conflates HTTP concerns with email policy.
- *Validation inside adapter layer*: Would require changes to every adapter implementation.

### D2 — Four independent env-var lists (comma-separated regex patterns)

**Decision**: Four settings, each a comma-separated string of regex patterns:

| Env Var | Direction | Semantics |
|---|---|---|
| `INBOUND_DOMAIN_ALLOWLIST` | Receiving | Sender domain must match ≥1 pattern (empty = allow all) |
| `INBOUND_DOMAIN_BLOCKLIST` | Receiving | Sender domain rejected if matches any pattern (empty = block none) |
| `OUTBOUND_DOMAIN_ALLOWLIST` | Sending | Recipient domain must match ≥1 pattern (empty = allow all) |
| `OUTBOUND_DOMAIN_BLOCKLIST` | Sending | Recipient domain rejected if matches any pattern (empty = block none) |

Stored in `Settings` as `str` (default `""`). The `DomainFilter` class parses and compiles patterns once at construction.

**Rationale**: Follows the existing config convention (env var → string field). Keeping raw strings in `Settings` avoids pydantic parsing regex objects. Compilation happens in `DomainFilter.__init__` so the cost is paid once.

**Alternatives considered**:
- *`list[str]` with custom pydantic validator*: Adds parsing complexity to the Settings class; comma-separated strings are simpler and consistent with `CORS_ORIGINS`.
- *Separate allow/block mode enum*: Over-constrains; operators may want both an allowlist and a blocklist simultaneously (e.g., allow `company\.com` but block `noreply\.company\.com`).

### D3 — Evaluation order: blocklist-first

**Decision**: For each domain checked:
1. If the **blocklist** is non-empty and the domain matches any blocklist pattern → **reject**.
2. If the **allowlist** is non-empty and the domain does **not** match any allowlist pattern → **reject**.
3. Otherwise → **allow**.

This means the blocklist always wins (a domain explicitly blocked cannot be saved by the allowlist).

**Rationale**: Blocklist-first is a widely understood security convention (deny > allow). It lets operators allowlist a broad domain while carving out exceptions.

### D4 — Compile-once, full-match semantics

**Decision**: Each pattern is compiled via `re.compile(pattern)` at startup and applied using `re.fullmatch()` against the domain portion (after `@`).

**Rationale**: `fullmatch` prevents accidental partial matches (e.g., pattern `evil.com` must not match `notevil.com`). Compile-once avoids per-message regex overhead. Invalid patterns raise `re.error` at startup, failing fast.

### D5 — Inbound insertion point

**Decision**: Add the check in `ingest_message()` immediately after inbox lookup (step 1, line 60) and before duplicate detection (step 2, line 70). Return a new `IngestResult(status="domain_blocked")`.

**Rationale**: This is the earliest point where we know both the sender domain (`inbound.from_address`) and that the inbox is valid. Checking before dedup avoids wasting a storage query on a blocked sender. All inbound paths (webhooks + IMAP poller) converge here, so a single insertion handles every provider.

### D6 — Outbound insertion point

**Decision**: Add the check in the `send_message` route, after inbox lookup but before `email_provider.send_email()`. Check **all** domains in `payload.to`. Raise `HTTPException(403)` with a descriptive error listing the blocked domains.

**Rationale**: Checking before the provider call prevents any network traffic for blocked sends. Using 403 (Forbidden) distinguishes policy rejection from auth errors (401) and validation errors (422). Checking every recipient — not just the first — gives the caller a complete error message.

### D7 — Logging

**Decision**: Log at `INFO` level for every block decision, including the direction, the domain, and which pattern matched. Log at `DEBUG` level for allow-through decisions.

**Rationale**: `INFO`-level block logging gives operators auditability without overwhelming logs in the normal (allowed) case.

## Risks / Trade-offs

**[Invalid regex crashes startup]** → Mitigation: Catch `re.error` during `DomainFilter.__init__` and raise a clear `ValueError` naming the offending pattern and env var. This fails fast at boot rather than silently at runtime.

**[Regex complexity / ReDoS]** → Mitigation: Document that patterns are applied per-message and should be kept simple. For v1 we do not add a timeout or complexity limit; this is acceptable because the operator controls the patterns. Can revisit if user-supplied patterns are ever supported.

**[No hot-reload]** → Trade-off accepted. Changing lists requires a restart. This is consistent with all other NornWeave config. A future enhancement could watch a config file or add an admin endpoint.

**[Outbound checks only cover `to`, not `cc`/`bcc`]** → The current `SendMessageRequest` schema only has a `to` field (no `cc`/`bcc`). When those are added in the future, the filter call must be updated to include them. Add a code comment as a reminder.

## Open Questions

_(none — all decisions resolved)_
