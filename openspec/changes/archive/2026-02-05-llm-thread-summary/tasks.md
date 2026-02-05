## 1. Configuration & Dependencies

- [x] 1.1 Add `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_SUMMARY_PROMPT`, `LLM_DAILY_TOKEN_LIMIT` settings to `Settings` class in `src/nornweave/core/config.py` with env var aliases and defaults (provider=None, key="", model="", default prompt, limit=1_000_000)
- [x] 1.2 Add startup validation: if `LLM_PROVIDER` is set but `LLM_API_KEY` is empty, raise a configuration error with a clear message
- [x] 1.3 Add optional dependency extras to `pyproject.toml`: `openai`, `anthropic`, `gemini` (individual), and `llm` (all three combined)

## 2. Data Model & Migration

- [x] 2.1 Add `summary: str | None` field to `ThreadItem` Pydantic model in `src/nornweave/models/thread.py`
- [x] 2.2 Add `summary: str | None` field to `Thread` Pydantic model in `src/nornweave/models/thread.py`
- [x] 2.3 Add `summary: Mapped[str | None]` column (Text, nullable) to `ThreadORM` in `src/nornweave/urdr/orm.py`
- [x] 2.4 Update `ThreadORM.to_pydantic()` to include `summary` in the returned `Thread` model
- [x] 2.5 Update `ThreadORM.from_pydantic()` to map `summary` from `Thread` to ORM
- [x] 2.6 Add `LlmTokenUsageORM` model to `src/nornweave/urdr/orm.py` with columns: `date` (Date, PK), `tokens_used` (Integer, default 0), `updated_at` (DateTime, auto-updated)
- [x] 2.7 Create Alembic migration that adds `summary TEXT` column to `threads` table and creates `llm_token_usage` table (with upgrade and downgrade)

## 3. LLM Provider Abstraction

- [x] 3.1 Create `src/nornweave/verdandi/llm/` package with `__init__.py`
- [x] 3.2 Create `src/nornweave/verdandi/llm/base.py` with `SummaryResult` dataclass and `SummaryProvider` protocol (single `async summarize(text: str) -> SummaryResult` method)
- [x] 3.3 Implement `OpenAISummaryProvider` in `src/nornweave/verdandi/llm/openai.py` — calls Chat Completions API, default model `gpt-4o-mini`, returns `SummaryResult` with token usage
- [x] 3.4 Implement `AnthropicSummaryProvider` in `src/nornweave/verdandi/llm/anthropic.py` — calls Messages API, default model `claude-haiku`, returns `SummaryResult` with token usage
- [x] 3.5 Implement `GeminiSummaryProvider` in `src/nornweave/verdandi/llm/gemini.py` — calls Google GenAI API, default model `gemini-2.0-flash`, returns `SummaryResult` with token usage
- [x] 3.6 Implement `get_summary_provider()` factory in `src/nornweave/verdandi/llm/__init__.py` — returns correct provider from config, `None` if disabled, raises clear error if SDK not installed or API key missing

## 4. Token Budget

- [x] 4.1 Add `get_token_usage(date) -> int` and `record_token_usage(date, tokens) -> None` methods to `StorageInterface` in `src/nornweave/core/interfaces.py`
- [x] 4.2 Implement token usage methods in `BaseSQLAlchemyAdapter` (`src/nornweave/urdr/adapters/base.py`) — upsert row for date, increment `tokens_used`
- [x] 4.3 Create `check_token_budget(storage) -> bool` helper in `src/nornweave/verdandi/summarize.py` — returns True if under `LLM_DAILY_TOKEN_LIMIT` (or limit is 0 = unlimited), False otherwise

## 5. Summarization Orchestration

- [x] 5.1 Create `prepare_thread_text(messages: list[Message]) -> str` function in `src/nornweave/verdandi/summarize.py` — concatenates `extracted_text` (or `text` fallback) chronologically with `[datetime] sender:` headers, skips messages with no text
- [x] 5.2 Create `truncate_to_context_window(text: str, model: str) -> str` function — truncates oldest messages if text exceeds 80% of model context window, prepends truncation note
- [x] 5.3 Create `generate_thread_summary(storage, thread_id) -> None` async function — orchestrates: check budget → load messages → prepare text → truncate → call provider → update thread summary → record tokens. Wrap in try/except, log warnings on failure
- [x] 5.4 Integrate summarization hook into `ingest_inbound_message()` in `tests/helpers/ingest.py` — call `generate_thread_summary()` as fire-and-forget after message is persisted and thread is updated
- [x] 5.5 Integrate summarization hook into `create_outbound_message()` in `tests/helpers/ingest.py` — same fire-and-forget pattern after outbound message is recorded

## 6. Storage Layer Updates

- [x] 6.1 Update `update_thread()` in `BaseSQLAlchemyAdapter` to persist the `summary` field when updating a thread

## 7. API & MCP Integration

- [x] 7.1 Verify thread REST endpoints (`GET /v1/threads/{id}`, `GET /v1/inboxes/{id}/threads`) include `summary` field in responses (should work automatically via Pydantic model changes)
- [x] 7.2 Update MCP resource `email://inbox/{inbox_id}/recent` in `src/nornweave/huginn/resources.py` to include `summary` field in each thread summary returned
- [x] 7.3 Update MCP resource `email://thread/{thread_id}` in `src/nornweave/huginn/resources.py` to include a `## Summary` section in the Markdown output when `summary` is not None

## 8. Tests

- [x] 8.1 Unit tests for `SummaryProvider` protocol — mock each provider, verify `SummaryResult` structure
- [x] 8.2 Unit tests for `get_summary_provider()` factory — test each provider selection, disabled state, missing SDK, missing API key
- [x] 8.3 Unit tests for `prepare_thread_text()` — multiple messages, fallback to text, skip empty, chronological order
- [x] 8.4 Unit tests for `truncate_to_context_window()` — under limit, over limit with truncation note
- [x] 8.5 Unit tests for `check_token_budget()` — under budget, at budget, over budget, no row, unlimited (limit=0)
- [x] 8.6 Unit tests for `generate_thread_summary()` — happy path with mocked provider, feature disabled, budget exhausted, provider failure (graceful)
- [x] 8.7 Integration test for ingestion flow — ingest a message with LLM enabled (mocked provider), verify thread summary is populated
- [x] 8.8 Integration test for token usage tracking — run multiple summarizations, verify counter increments, verify budget gate stops summarization

## 9. Documentation

- [x] 9.1 Document changes in `/CHANGELOG.md` — new LLM thread summary feature, configuration env vars, optional dependencies, daily token budget
- [x] 9.2 Update REST API reference (`web/content/docs/api/rest.md`) — document the `summary` field on Thread and ThreadItem response schemas, note it is nullable and populated when LLM summarization is enabled
- [x] 9.3 Update MCP integration guide (`web/content/docs/api/mcp.md`) — document that `email://inbox/{id}/recent` now returns `summary` per thread and `email://thread/{id}` includes a `## Summary` section when available
- [x] 9.4 Update configuration docs (`web/content/docs/getting-started/configuration.md`) — add `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_SUMMARY_PROMPT`, `LLM_DAILY_TOKEN_LIMIT` env vars with descriptions and usage examples
- [x] 9.5 Update landing page (`web/content/_index.md`) — add "LLM Thread Summaries" as a feature card (or update Phase 2 subtitle to mention thread summarization with your own LLM API key)
- [x] 9.6 Update roadmap page (`web/content/roadmap/_index.md`) — move thread summarization from Phase 3 aspirational to Phase 2 as an available feature (e.g., "LLM Thread Summaries: BYO API key for OpenAI, Anthropic, or Gemini to auto-summarize threads")
