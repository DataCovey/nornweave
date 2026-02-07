## 1. Configuration

- [x] 1.1 Add `global_send_rate_limit_per_minute` and `global_send_rate_limit_per_hour` fields (type `int`, default `0`) to `Settings` in `src/nornweave/core/config.py` with corresponding env-var aliases `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` and `GLOBAL_SEND_RATE_LIMIT_PER_HOUR`
- [x] 1.2 Add a `@model_validator` that rejects negative values for either setting, raising a clear `ValueError` naming the offending variable

## 2. Rate Limiter Module

- [x] 2.1 Implement a `SlidingWindowCounter` class in `src/nornweave/skuld/rate_limiter.py` that tracks event counts over a rolling window using time-bucketed counters (e.g., 1-second buckets for minute window, 1-minute buckets for hour window)
- [x] 2.2 Implement `SlidingWindowCounter.count() -> int` that returns the total events in the current window (summing non-expired buckets)
- [x] 2.3 Implement `SlidingWindowCounter.record() -> None` that increments the current bucket
- [x] 2.4 Implement `SlidingWindowCounter.seconds_until_capacity() -> float` that returns how long until the oldest bucket expires and frees capacity (for the `Retry-After` header)
- [x] 2.5 Implement a `GlobalRateLimiter` class that wraps two optional `SlidingWindowCounter` instances (per-minute and per-hour) and exposes `check() -> RateLimitResult` and `record() -> None`
- [x] 2.6 Define `RateLimitResult` as a small dataclass/NamedTuple with fields: `allowed: bool`, `retry_after_seconds: float`, `detail: str`
- [x] 2.7 Add thread safety via `threading.Lock` in `SlidingWindowCounter` to guard bucket mutations

## 3. FastAPI Integration

- [x] 3.1 Create a FastAPI dependency (`get_rate_limiter`) that returns a singleton `GlobalRateLimiter` configured from `Settings`
- [x] 3.2 Insert `rate_limiter.check()` in `send_message()` in `src/nornweave/yggdrasil/routes/v1/messages.py` — after the domain filter check and before `email_provider.send_email()`
- [x] 3.3 On `check()` denial, raise `HTTPException(429)` with a JSON `detail` and a `Retry-After` response header (integer seconds, rounded up)
- [x] 3.4 After a successful `send_email()` call, invoke `rate_limiter.record()` to increment the counters

## 4. Logging

- [x] 4.1 Log at `WARNING` level on every rate-limited rejection, including the limit name (per-minute / per-hour), current count, limit, and retry-after seconds
- [x] 4.2 Log at `DEBUG` level on every allowed send with current counts for both windows

## 5. Unit Tests

- [x] 5.1 Create `tests/unit/skuld/test_rate_limiter.py` with tests for `SlidingWindowCounter`: basic counting, window expiry, `seconds_until_capacity` accuracy
- [x] 5.2 Add tests for `GlobalRateLimiter`: both limits disabled (always allow), per-minute only, per-hour only, both active, counter not incremented on check-only
- [x] 5.3 Add tests for `RateLimitResult` construction and the `Retry-After` calculation
- [x] 5.4 Add test for negative config values rejected by `Settings` validator

## 6. Integration Tests

- [x] 6.1 Add integration test: send when under rate limit → HTTP 201, message sent
- [x] 6.2 Add integration test: send when per-minute limit is exhausted → HTTP 429 with `Retry-After` header
- [x] 6.3 Add integration test: send when per-hour limit is exhausted → HTTP 429 with `Retry-After` header
- [x] 6.4 Add integration test: rate-limited request does not increment the counter (subsequent request after wait succeeds)
- [x] 6.5 Add integration test: domain-filtered request returns 403 and does not affect rate-limit counters

## 7. Documentation

- [x] 7.1 Add "Rate Limiting" section to the configuration guide in `web/content/docs/getting-started/configuration.md`
- [x] 7.2 Document the changes in `/CHANGELOG.md`
