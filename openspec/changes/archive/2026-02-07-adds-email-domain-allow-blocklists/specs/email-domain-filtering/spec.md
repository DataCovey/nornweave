## ADDED Requirements

### Requirement: Configuration via environment variables

The system SHALL accept four optional environment variables to configure domain filtering. Each variable is a comma-separated list of regex patterns. An empty or unset variable means "no restriction" for that list.

| Variable | Direction | Semantics |
|---|---|---|
| `INBOUND_DOMAIN_ALLOWLIST` | Inbound | Sender domain MUST match ≥1 pattern to be accepted |
| `INBOUND_DOMAIN_BLOCKLIST` | Inbound | Sender domain MUST NOT match any pattern |
| `OUTBOUND_DOMAIN_ALLOWLIST` | Outbound | Recipient domain MUST match ≥1 pattern to be sent |
| `OUTBOUND_DOMAIN_BLOCKLIST` | Outbound | Recipient domain MUST NOT match any pattern |

Patterns SHALL be applied using full-match semantics against the domain portion only (the part after `@`).

#### Scenario: No filtering configured (defaults)

- **WHEN** all four env vars are empty or unset
- **THEN** the system SHALL accept all inbound sender domains and allow sending to all outbound recipient domains (no filtering applied)

#### Scenario: Single pattern in allowlist

- **WHEN** `INBOUND_DOMAIN_ALLOWLIST` is set to `example\.com`
- **THEN** the system SHALL accept inbound email from `user@example.com` and reject inbound email from `user@other.com`

#### Scenario: Multiple comma-separated patterns

- **WHEN** `OUTBOUND_DOMAIN_BLOCKLIST` is set to `spam\.com,junk\.org`
- **THEN** the system SHALL reject outbound sends to `user@spam.com` and `user@junk.org`, and allow sends to `user@clean.com`

#### Scenario: Invalid regex pattern at startup

- **WHEN** any of the four env vars contains an invalid regex pattern (e.g., `[invalid`)
- **THEN** the system SHALL raise a startup error naming the offending pattern and the env var it came from

### Requirement: Blocklist-first evaluation order

The system SHALL evaluate domain filters in the following order:

1. If the **blocklist** is non-empty and the domain matches any blocklist pattern → **reject**.
2. If the **allowlist** is non-empty and the domain does NOT match any allowlist pattern → **reject**.
3. Otherwise → **allow**.

The blocklist SHALL always take precedence over the allowlist.

#### Scenario: Domain matches both blocklist and allowlist

- **WHEN** `INBOUND_DOMAIN_ALLOWLIST` is `.*\.example\.com` and `INBOUND_DOMAIN_BLOCKLIST` is `noreply\.example\.com`
- **THEN** the system SHALL reject inbound email from `sender@noreply.example.com` (blocklist wins)

#### Scenario: Domain matches allowlist only

- **WHEN** `OUTBOUND_DOMAIN_ALLOWLIST` is `partner\.com` and `OUTBOUND_DOMAIN_BLOCKLIST` is empty
- **THEN** the system SHALL allow outbound email to `user@partner.com` and reject outbound email to `user@other.com`

#### Scenario: Domain matches blocklist only

- **WHEN** `INBOUND_DOMAIN_BLOCKLIST` is `blocked\.org` and `INBOUND_DOMAIN_ALLOWLIST` is empty
- **THEN** the system SHALL reject inbound email from `user@blocked.org` and allow inbound email from `user@anything-else.com`

### Requirement: Full-match regex semantics

Each pattern SHALL be matched using full-match semantics (`re.fullmatch`), meaning the pattern must match the entire domain string, not a substring.

#### Scenario: Pattern does not partially match

- **WHEN** `INBOUND_DOMAIN_BLOCKLIST` is `evil\.com`
- **THEN** the system SHALL reject `user@evil.com` but SHALL allow `user@notevil.com`

#### Scenario: Wildcard subdomain pattern

- **WHEN** `OUTBOUND_DOMAIN_ALLOWLIST` is `(.*\.)?acme\.com`
- **THEN** the system SHALL allow `user@acme.com` and `user@sub.acme.com` but reject `user@other.com`

### Requirement: Inbound domain filtering

The system SHALL check the sender's domain against the inbound allowlist/blocklist during message ingestion. The check MUST happen before any storage, threading, or attachment processing.

When a sender domain is rejected, the ingestion pipeline SHALL return a result with status `domain_blocked` and SHALL NOT create any message, thread, or attachment records.

#### Scenario: Inbound email from blocked sender domain

- **WHEN** an inbound email arrives from `spammer@blocked.org` and `INBOUND_DOMAIN_BLOCKLIST` contains `blocked\.org`
- **THEN** the ingestion pipeline SHALL return status `domain_blocked` and no message or thread SHALL be created

#### Scenario: Inbound email from allowed sender domain

- **WHEN** an inbound email arrives from `partner@allowed.com` and `INBOUND_DOMAIN_ALLOWLIST` contains `allowed\.com`
- **THEN** the ingestion pipeline SHALL proceed normally and create the message and thread

#### Scenario: Inbound email from unlisted domain when allowlist is active

- **WHEN** an inbound email arrives from `stranger@unknown.com` and `INBOUND_DOMAIN_ALLOWLIST` is `allowed\.com`
- **THEN** the ingestion pipeline SHALL return status `domain_blocked`

#### Scenario: Filtering applies to all inbound paths

- **WHEN** domain filtering is configured
- **THEN** the filter SHALL apply identically to emails arriving via webhooks (Mailgun, SES, SendGrid, Resend) and via IMAP polling

### Requirement: Outbound domain filtering

The system SHALL check all recipient domains in the `to` field against the outbound allowlist/blocklist before sending. If any recipient domain is rejected, the entire send operation SHALL be refused.

The API SHALL return HTTP 403 (Forbidden) with a response body that lists the specific blocked domains.

#### Scenario: Outbound send to blocked recipient domain

- **WHEN** a send request targets `user@blocked.org` and `OUTBOUND_DOMAIN_BLOCKLIST` contains `blocked\.org`
- **THEN** the API SHALL return HTTP 403 with a body naming `blocked.org` as the blocked domain, and no email SHALL be sent

#### Scenario: Outbound send with mixed allowed and blocked recipients

- **WHEN** a send request targets `["user@ok.com", "user@blocked.org"]` and `OUTBOUND_DOMAIN_BLOCKLIST` contains `blocked\.org`
- **THEN** the API SHALL return HTTP 403 listing `blocked.org`, and no email SHALL be sent to any recipient

#### Scenario: Outbound send to allowed recipient domain

- **WHEN** a send request targets `user@partner.com` and `OUTBOUND_DOMAIN_ALLOWLIST` contains `partner\.com`
- **THEN** the system SHALL proceed to send the email normally

### Requirement: Audit logging for filter decisions

The system SHALL log every domain rejection at `INFO` level, including:
- The direction (inbound or outbound)
- The email address or domain that was rejected
- The pattern that matched (for blocklist rejections) or the fact that no allowlist pattern matched

Allow-through decisions SHALL be logged at `DEBUG` level.

#### Scenario: Blocked inbound email is logged

- **WHEN** an inbound email from `user@blocked.org` is rejected by the blocklist pattern `blocked\.org`
- **THEN** the system SHALL emit an INFO log entry containing the direction ("inbound"), the domain ("blocked.org"), and the matching pattern ("blocked\.org")

#### Scenario: Allowed email is logged at DEBUG

- **WHEN** an inbound email from `user@ok.com` passes domain filtering
- **THEN** the system SHALL emit a DEBUG log entry indicating the domain was allowed
