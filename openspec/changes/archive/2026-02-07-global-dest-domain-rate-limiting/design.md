## Context

NornWeave's outbound email path is direct and synchronous: `POST /v1/messages` → domain filter check → `email_provider.send_email()` → store record. There is no throttling between the API and the provider. The `skuld` module has placeholders for rate limiting (`skuld/rate_limiter.py`) and scheduling (`skuld/scheduler.py`), but neither is implemented.

Configuration uses `pydantic-settings` (`core/config.py`). Integer settings with sane defaults are standard (e.g., `IMAP_POLL_INTERVAL`, `LLM_DAILY_TOKEN_LIMIT`). The LLM token-budget feature provides a useful pattern: a per-day counter stored in the database (`LlmTokenUsageORM`). However, the rate limiter targets sub-minute granularity, making database-backed counters too costly per request.

The deployment model is single-process / single-instance. Distributed coordination is a non-goal.

## Goals / Non-Goals

**Goals:**

- Cap outbound email throughput at the instance level with two independent windows (per-minute and per-hour).
- Reject excess requests with HTTP 429 and a `Retry-After` header so callers can back off.
- Zero external dependencies — pure in-memory, no Redis.
- Replace the `skuld/rate_limiter.py` placeholder with a production-ready module that can be extended later (per-inbox, per-domain, etc.).

**Non-Goals:**

- Per-inbox, per-thread, or per-recipient-domain limits.
- Queuing / deferred delivery of rate-limited messages.
- Distributed (multi-instance) rate limiting.
- Handling upstream 429 responses from providers.
- Persisting rate-limit state across process restarts.

## Decisions

### D1 — Sliding-window counter algorithm

**Decision**: Use a fixed-window counter with sub-window granularity (sliding-window log variant) per limit. Each window is divided into equal-sized buckets (e.g., 1-second buckets for the per-minute window, 1-minute buckets for the per-hour window). On each `record()` call the current bucket is incremented; on each `allow()` check the sum of buckets within the window is compared against the limit.

**Rationale**: A simple fixed-window counter has edge-case bursts at window boundaries (up to 2× the limit). Sub-bucket granularity provides a smooth approximation of a true sliding window with O(1) memory per window. No external dependencies and thread-safe with a simple `threading.Lock`.

**Alternatives considered**:
- *Token bucket*: More complex to tune (refill rate + burst size) for two independent windows. Sliding-window counters map directly to the "N per minute / N per hour" mental model.
- *Database-backed counter (like LLM token budget)*: Too slow for per-request checking and unnecessarily durable — rate-limit state is ephemeral by design.
- *Redis-backed (e.g., `redis-py` INCR + EXPIRE)*: Adds an infrastructure dependency; overkill for single-instance.

### D2 — Two env-var settings with zero-means-unlimited semantics

**Decision**: Two new integer settings:

| Env Var | Type | Default | Semantics |
|---|---|---|---|
| `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` | `int` | `0` | Max sends per rolling minute. `0` = unlimited. |
| `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` | `int` | `0` | Max sends per rolling hour. `0` = unlimited. |

Added to the `Settings` class in `core/config.py`.

**Rationale**: Follows the existing `LLM_DAILY_TOKEN_LIMIT` pattern where `0` means unlimited. Two independent windows let operators set a burst cap (per-minute) and a sustained cap (per-hour) separately.

**Alternatives considered**:
- *Single "per-second" limit*: Too fine-grained for email. Operators think in "emails per minute/hour".
- *Floating-point rate (e.g., 1.5 emails/sec)*: Unintuitive and harder to validate.
- *YAML/JSON config for multiple rate-limit tiers*: Over-engineers the global-only use case.

### D3 — `GlobalRateLimiter` class in `skuld/rate_limiter.py`

**Decision**: Implement a `GlobalRateLimiter` class that:
- Accepts per-minute and per-hour limits at construction.
- Exposes `check() -> RateLimitResult` (read-only, returns allowed/denied + retry-after).
- Exposes `record() -> None` (increments the counter after a successful send).
- Is instantiated once at startup and injected via FastAPI `Depends()`.

Separating `check()` from `record()` ensures the counter is only incremented when the email is actually dispatched, not on rejected or failed sends.

**Rationale**: Stateful singleton avoids re-creating state per request. Dependency injection keeps the route testable (swap in a mock limiter). Separating check/record avoids false-positive counting when sends fail.

**Alternatives considered**:
- *Middleware*: Would apply to all routes, not just sends. Harder to distinguish email sends from reads.
- *Decorator on `send_message`*: Less testable, harder to share across routes if future send endpoints are added.

### D4 — Insertion point: after domain filter, before provider call

**Decision**: In `send_message()`, call `rate_limiter.check()` after the outbound domain filter check and before `email_provider.send_email()`. On denial, raise `HTTPException(429)` with a JSON body containing `detail` and a `Retry-After` header (seconds). After a successful `send_email()`, call `rate_limiter.record()`.

**Rationale**: Domain filtering is a policy decision that should short-circuit before rate-limit accounting. Placing the check just before the provider call means the counter reflects actual send attempts, not filtered rejects.

### D5 — `Retry-After` header calculation

**Decision**: When a window is exhausted, compute the number of seconds until the oldest bucket in that window expires (i.e., when capacity will free up). Return the larger of the two windows' retry-after values if both are exhausted.

**Rationale**: `Retry-After` in seconds is standard for HTTP 429 (RFC 7231 §7.1.3). Giving the caller an accurate wait time enables well-behaved back-off.

### D6 — Logging

**Decision**: Log at `WARNING` level on every rate-limited rejection, including the limit name (per-minute or per-hour), current count, and limit value. Log at `DEBUG` level when a send is allowed and the counter is incremented.

**Rationale**: `WARNING` makes rate-limit events visible in default log levels without flooding. Matches the pattern used in domain filtering (INFO for blocks, DEBUG for allows), elevated to WARNING here because rate limiting indicates load pressure.

## Risks / Trade-offs

**[State lost on restart]** → Accepted trade-off. Rate-limit counters reset when the process restarts. For single-instance deployments this is acceptable — a restart is rare and the window is short (1 min / 1 hour). Persisting would add complexity for minimal benefit.

**[No multi-instance coordination]** → Accepted. NornWeave targets single-instance self-hosted deployments. If multi-instance is needed later, the `GlobalRateLimiter` interface can be swapped for a Redis-backed implementation behind the same `check()`/`record()` API.

**[Time-of-check vs time-of-use]** → Between `check()` and `record()`, another concurrent request could also pass the check. Under asyncio's cooperative model this is low-risk (no true parallelism in a single event loop), but if thread-based workers are used, the `threading.Lock` in the counter prevents races. Worst case: one extra email over the limit in a burst — acceptable for a safety-net feature.

**[No queue / no retry for the caller]** → Rate-limited requests get a flat 429. Callers must implement their own retry using the `Retry-After` hint. This is intentional — queueing is a separate concern for a later phase.

## Open Questions

_(none — all decisions resolved)_
