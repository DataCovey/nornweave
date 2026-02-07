## Why

NornWeave sends outbound email with no throughput controls — every `POST /messages` call fires immediately to the upstream provider. This is risky for self-hosted operators: a misbehaving agent or integration can exhaust provider quotas, trigger provider-side throttling, or spike costs in minutes. Operators need a simple, instance-level safety net that caps how many emails NornWeave will send per minute and per hour, rejecting or signalling excess requests before they reach the provider.

## What Changes

- **Two new env-var settings**:
  - `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` — maximum emails sent globally per rolling minute. `0` or unset = unlimited.
  - `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` — maximum emails sent globally per rolling hour. `0` or unset = unlimited.
- **In-memory sliding-window rate limiter** in `skuld/rate_limiter.py` — replaces the current placeholder. Uses a sliding-window counter (no external dependencies; works with SQLite or PostgreSQL).
- **Pre-send check** in the `send_message` route — before calling the provider, the rate limiter is consulted. If either window is exhausted, return `HTTP 429 Too Many Requests` with a `Retry-After` header indicating when capacity will be available.
- **Logging** — every rate-limited rejection logged at `WARNING` level with the current count and limit for observability.
- **Health / status endpoint enrichment** (optional) — expose current usage counts via the existing status or a new `/v1/rate-limit` read-only endpoint so operators can monitor headroom.

## Non-goals

- Per-inbox, per-thread, or per-recipient-domain rate limits — this is a global (instance-level) policy only.
- Queueing or deferred delivery — excess requests are rejected, not queued. A send queue belongs to a later phase.
- Distributed / multi-instance rate limiting (e.g., Redis-backed) — single-process in-memory is sufficient for the self-hosted single-instance deployment target. Redis support can be layered later.
- Provider-side rate-limit detection and back-pressure (429 from upstream) — that is a separate concern.

## Capabilities

### New Capabilities

- `global-send-rate-limiting`: Instance-level per-minute and per-hour sliding-window rate limits for outbound email, configured via environment variables and enforced before provider calls.

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **Config** (`core/config.py`): Two new optional `int` settings with sensible defaults (unlimited).
- **Skuld** (`skuld/rate_limiter.py`): Replace placeholder with a sliding-window counter implementation.
- **Outbound path** (`yggdrasil/routes/v1/messages.py`): New pre-send check that calls the rate limiter and returns 429 on rejection.
- **Tests**: Unit tests for the sliding-window logic (boundary, reset, concurrent calls); integration test for 429 response.
- **Docs**: New "Rate Limiting" section in configuration guide.
- **No database changes, no migration, no breaking API changes.**
