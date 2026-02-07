## ADDED Requirements

### Requirement: Configuration via environment variables

The system SHALL accept two optional environment variables to configure global outbound rate limits. A value of `0` or unset means "unlimited" (no rate limiting applied).

| Variable | Type | Default | Semantics |
|---|---|---|---|
| `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` | integer | `0` | Maximum outbound emails per rolling minute |
| `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` | integer | `0` | Maximum outbound emails per rolling hour |

Both windows SHALL be enforced independently — a request MUST pass both checks to proceed.

#### Scenario: No rate limiting configured (defaults)

- **WHEN** both `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` and `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` are `0` or unset
- **THEN** the system SHALL allow all outbound sends with no rate limiting applied

#### Scenario: Only per-minute limit configured

- **WHEN** `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` is `10` and `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` is `0`
- **THEN** the system SHALL enforce only the per-minute limit (max 10 sends per rolling minute) and impose no hourly cap

#### Scenario: Only per-hour limit configured

- **WHEN** `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` is `100` and `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` is `0`
- **THEN** the system SHALL enforce only the per-hour limit (max 100 sends per rolling hour) and impose no per-minute cap

#### Scenario: Both limits configured

- **WHEN** `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` is `5` and `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` is `50`
- **THEN** the system SHALL enforce both limits independently — a send is allowed only if both the per-minute count is below 5 and the per-hour count is below 50

#### Scenario: Negative value rejected at startup

- **WHEN** either env var is set to a negative integer (e.g., `-1`)
- **THEN** the system SHALL raise a startup validation error naming the offending variable

### Requirement: Sliding-window rate limiting

The system SHALL use a sliding-window counter to track outbound send counts within each configured window. The counter SHALL only be incremented after a send is successfully dispatched to the email provider — failed or filtered sends SHALL NOT count against the limit.

#### Scenario: Counter increments on successful send

- **WHEN** an outbound email is successfully sent via the provider
- **THEN** the rate-limit counter SHALL be incremented by 1 for both the per-minute and per-hour windows

#### Scenario: Counter does not increment on domain-filtered send

- **WHEN** an outbound send is rejected by the domain filter (HTTP 403)
- **THEN** the rate-limit counter SHALL NOT be incremented

#### Scenario: Counter does not increment on rate-limited send

- **WHEN** an outbound send is rejected by the rate limiter itself (HTTP 429)
- **THEN** the rate-limit counter SHALL NOT be incremented

#### Scenario: Window rolls forward over time

- **WHEN** 5 emails are sent within a 1-minute window with a per-minute limit of 5, and then 61 seconds pass with no sends
- **THEN** the per-minute counter SHALL have capacity for 5 new sends (old sends have expired from the window)

### Requirement: HTTP 429 response on rate limit exceeded

When a send request would exceed either configured rate limit, the system SHALL reject the request with HTTP 429 Too Many Requests. The response SHALL include a `Retry-After` header indicating the number of seconds until capacity is expected to be available.

The rate-limit check SHALL occur after domain filtering and before the email is dispatched to the provider.

#### Scenario: Per-minute limit exceeded

- **WHEN** the per-minute limit is `3` and 3 emails have been sent in the current minute, and a new send request arrives
- **THEN** the API SHALL return HTTP 429 with a JSON body containing a `detail` field explaining the rate limit, and a `Retry-After` header with the seconds until the oldest send in the window expires

#### Scenario: Per-hour limit exceeded

- **WHEN** the per-hour limit is `10` and 10 emails have been sent in the current hour, and a new send request arrives
- **THEN** the API SHALL return HTTP 429 with a `Retry-After` header and a `detail` message referencing the hourly limit

#### Scenario: Both limits exceeded simultaneously

- **WHEN** both the per-minute and per-hour windows are exhausted
- **THEN** the API SHALL return HTTP 429 with the `Retry-After` value set to the longer of the two wait times

#### Scenario: Domain-filtered request is not rate-checked

- **WHEN** a send request targets a domain blocked by the outbound domain filter
- **THEN** the system SHALL return HTTP 403 (domain filter) and SHALL NOT consult the rate limiter

### Requirement: Audit logging for rate-limit decisions

The system SHALL log every rate-limited rejection at `WARNING` level, including:
- Which limit was exceeded (per-minute, per-hour, or both)
- The current count and the configured limit
- The computed retry-after value in seconds

Allowed sends SHALL be logged at `DEBUG` level with the current counts.

#### Scenario: Rate-limited rejection is logged

- **WHEN** a send request is rejected due to the per-minute limit (limit=5, current=5)
- **THEN** the system SHALL emit a WARNING log entry containing "per-minute", "5/5", and the retry-after seconds

#### Scenario: Allowed send is logged at DEBUG

- **WHEN** a send request passes rate limiting (per-minute: 2/5, per-hour: 10/50)
- **THEN** the system SHALL emit a DEBUG log entry with the current counts for both windows
