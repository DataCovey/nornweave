## ADDED Requirements

### Requirement: Token usage is tracked per day in the database

The system SHALL store daily LLM token usage in an `llm_token_usage` table with the following schema:

| Column | Type | Constraints |
|--------|------|-------------|
| `date` | `DATE` | Primary key |
| `tokens_used` | `INTEGER` | NOT NULL, default 0 |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL, auto-updated |

#### Scenario: First summarization of the day creates a new row
- **WHEN** a summarization call completes on a day with no existing usage row
- **THEN** a new row is inserted with `date` = today (UTC) and `tokens_used` = tokens consumed by the call

#### Scenario: Subsequent calls increment the counter
- **WHEN** a summarization call completes on a day with an existing usage row
- **THEN** the `tokens_used` column is incremented by the tokens consumed
- **AND** `updated_at` is refreshed

#### Scenario: Usage is tracked by UTC date
- **WHEN** a summarization call occurs at 2026-02-05 23:59 UTC
- **THEN** the tokens are counted under date `2026-02-05`

### Requirement: Database migration creates llm_token_usage table

The system SHALL provide an Alembic migration that creates the `llm_token_usage` table.

#### Scenario: Upgrade creates the table
- **WHEN** the migration is applied (upgrade)
- **THEN** the `llm_token_usage` table exists with `date`, `tokens_used`, and `updated_at` columns

#### Scenario: Downgrade drops the table
- **WHEN** the migration is reverted (downgrade)
- **THEN** the `llm_token_usage` table is removed

### Requirement: Daily token limit gates summarization

The system SHALL check the daily token budget before each summarization call. If `tokens_used` for today (UTC) meets or exceeds `LLM_DAILY_TOKEN_LIMIT`, the summarization call SHALL be skipped.

#### Scenario: Under budget — summarization proceeds
- **WHEN** today's `tokens_used` is 500,000 and `LLM_DAILY_TOKEN_LIMIT` is 1,000,000
- **THEN** the summarization call proceeds normally

#### Scenario: At budget — summarization is skipped
- **WHEN** today's `tokens_used` is 1,000,000 and `LLM_DAILY_TOKEN_LIMIT` is 1,000,000
- **THEN** the summarization call is skipped
- **AND** a debug log message is emitted: "Daily token limit reached, skipping summarization"

#### Scenario: Over budget — summarization is skipped
- **WHEN** today's `tokens_used` is 1,200,000 and `LLM_DAILY_TOKEN_LIMIT` is 1,000,000
- **THEN** the summarization call is skipped

#### Scenario: No row for today — budget is available
- **WHEN** there is no `llm_token_usage` row for today's date
- **THEN** the budget check treats usage as 0 and summarization proceeds

#### Scenario: Unlimited budget
- **WHEN** `LLM_DAILY_TOKEN_LIMIT` is set to `0`
- **THEN** the budget check is bypassed and summarization always proceeds

### Requirement: Budget resets automatically each day

The token budget SHALL reset automatically by using the UTC date as the primary key. No cleanup job or manual reset is required.

#### Scenario: New day starts with zero usage
- **WHEN** the date changes from 2026-02-05 to 2026-02-06 (UTC)
- **AND** a summarization call is made on 2026-02-06
- **THEN** a new row is created with `tokens_used` starting from the tokens consumed by that call
- **AND** the previous day's row remains for historical reference

#### Scenario: Historical data is preserved
- **WHEN** multiple days of usage have accumulated
- **THEN** all rows remain in the `llm_token_usage` table
- **AND** each row represents a single day's total usage

### Requirement: Token recording uses actual provider-reported tokens

The system SHALL record the actual token count reported by the LLM provider in the `SummaryResult`, not an estimate.

#### Scenario: Tokens match provider response
- **WHEN** the OpenAI API reports `usage.total_tokens = 1,523`
- **THEN** the `llm_token_usage` row for today is incremented by exactly 1,523

#### Scenario: Provider does not report tokens
- **WHEN** a provider's response does not include token usage information
- **THEN** the system SHALL estimate tokens based on input/output character count (1 token ≈ 4 characters)
- **AND** log a warning about the estimation
