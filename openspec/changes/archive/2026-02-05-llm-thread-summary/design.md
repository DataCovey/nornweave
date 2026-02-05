## Context

NornWeave stores email threads with message-level Talon extraction (`extracted_text` strips quoted replies and signatures). Today, an LLM agent must read every message in a thread to understand it. For a 50-message thread, that's enormous context window waste — most of the content is redundant across messages.

The thread model (`ThreadORM`), full response model (`Thread`), and list-view model (`ThreadItem`) have no summary field. The ingestion path (webhook → thread resolution → message create → thread update) has no post-processing hooks. There is no LLM integration layer in the codebase today, though an `openai_api_key` placeholder exists in `Settings`. The rate limiter in `skuld` is also a placeholder.

`ThreadItem` is used by list endpoints (`GET /v1/inboxes/{id}/threads`) and the MCP `email://inbox/{id}/recent` resource. Both `Thread` and `ThreadItem` need the summary field so agents can see summaries when scanning thread lists *and* when viewing a single thread.

Messages already carry `extracted_text` (Talon-cleaned, no quoted replies) — this is the ideal input for summarization since it contains only the *new* content from each message.

## Goals / Non-Goals

**Goals:**

- Allow an LLM agent to understand any thread by reading `summary` + last 2 messages instead of the full thread
- Support OpenAI, Anthropic, and Google Gemini as summarization providers
- Keep the feature fully opt-in and disabled by default
- Protect against runaway LLM costs with a daily token budget
- Make summarization non-blocking — a failed summary never blocks message ingestion

**Non-Goals:**

- Streaming or real-time summary updates (summary is generated after ingestion, not streamed to clients)
- Per-inbox or per-thread summarization settings (global config only in this iteration)
- Summary quality evaluation or A/B testing
- Embedding generation or semantic search over summaries
- Supporting local/self-hosted LLM providers (e.g. Ollama) — can be added later
- Multi-language prompt management — single prompt, user can override for their language

## Decisions

### D1: Provider abstraction — lightweight protocol, not a framework

**Decision**: Define a `SummaryProvider` protocol with a single `async summarize(text: str) -> SummaryResult` method. Implement one class per provider (`OpenAISummaryProvider`, `AnthropicSummaryProvider`, `GeminiSummaryProvider`). Factory function picks the right one from config.

**Alternatives considered**:
- *LiteLLM*: Unified API wrapper. Adds a heavy dependency, hides provider-specific tuning, and brings transitive deps. Rejected — our surface area is a single `chat.completions` call per provider.
- *Abstract base class hierarchy*: Over-engineered for 3 simple implementations. Protocol is lighter.

**Rationale**: Each provider SDK is already minimal (`openai`, `anthropic`, `google-genai`). A protocol keeps the interface testable and mockable without framework lock-in. Adding a new provider is one file.

### D2: Where to trigger summarization — post-ingestion hook in verdandi

**Decision**: After a message is created and the thread is updated, call `generate_thread_summary()` as a fire-and-forget async task. If it fails, log a warning and leave the summary unchanged.

The hook goes in the ingestion flow (`ingest_inbound_message` / webhook handlers). The summarization function:
1. Checks if LLM is enabled (provider configured)
2. Checks the daily token budget
3. Loads all messages for the thread, collects their `extracted_text`
4. Concatenates them chronologically
5. Calls the LLM provider
6. Updates the thread's `summary` field
7. Records token usage

**Alternatives considered**:
- *Background job queue (Celery/arq)*: Adds infrastructure complexity. NornWeave doesn't have a job queue yet. Deferred to a later iteration if latency becomes an issue.
- *Database trigger*: Not portable across PostgreSQL and SQLite.

**Rationale**: Inline async call keeps the architecture simple. Summarization is fast (< 2s with GPT-4o-mini). The fire-and-forget pattern ensures ingestion latency is unaffected — the thread update (with summary) happens after the HTTP response to the webhook provider.

### D3: What text to feed the LLM — concatenated `extracted_text`, not raw body

**Decision**: For each message in the thread (ordered by timestamp), use `extracted_text` (Talon-cleaned). Format as a conversation:

```
[2026-01-15 10:30] alice@example.com:
Hey, can we discuss the contract terms?

[2026-01-15 14:22] bob@example.com:
Sure, I've reviewed section 3...
```

This removes quoted replies and signatures that would otherwise duplicate content across messages.

**Alternatives considered**:
- *Raw `text` field*: Contains quoted replies → massively inflates token count in long threads.
- *Only the latest message + previous summary (incremental)*: Risks drift — summary gradually loses details from early messages. Full-thread re-summarization is more accurate and tokens are cheap for short text.

**Rationale**: Using `extracted_text` gives the LLM the minimal unique content per message. For a 50-message thread where each reply quotes the full chain, this could be 10-20x fewer tokens than using raw text.

### D4: Summary model — single `LLM_SUMMARY_PROMPT` env var with a good default

**Decision**: Ship a default prompt that produces structured summaries. Allow full override via `LLM_SUMMARY_PROMPT` env var.

Default prompt:
```
You are an email thread summarizer. Given a chronological email conversation,
produce a concise summary that captures:
- Key topics discussed
- Decisions made or actions agreed upon
- Open questions or pending items
- Current status of the conversation

Keep the summary under 300 words. Use bullet points for clarity.
Do not include greetings, sign-offs, or meta-commentary.
```

The `LLM_MODEL` env var controls which model to use (defaults to a cost-effective option per provider: `gpt-4o-mini` for OpenAI, `claude-haiku` for Anthropic, `gemini-2.0-flash` for Gemini).

### D5: Token budget — database counter with daily reset

**Decision**: New `llm_token_usage` table with columns: `date DATE PRIMARY KEY`, `tokens_used INTEGER`, `updated_at TIMESTAMP`. Before each summarization call, check if `tokens_used` for today's date (UTC) is below `LLM_DAILY_TOKEN_LIMIT`. After the call, increment with the actual tokens consumed (from provider response). If the row for today doesn't exist, create it.

**Alternatives considered**:
- *Redis counter*: Faster, but NornWeave doesn't require Redis for core features. Adding a Redis dependency for a counter is overkill.
- *In-memory counter*: Resets on restart, doesn't work with multiple workers.
- *Per-inbox budget*: More granular, but adds complexity. Global budget is simpler for v1.

**Rationale**: Database counter is persistent, works across restarts and workers, and uses the same database infrastructure already in place. A single-row-per-day table is trivially small.

### D6: Configuration — env vars following existing patterns

**Decision**: Add to `Settings` in `core/config.py`:

| Env Var | Type | Default | Description |
|---------|------|---------|-------------|
| `LLM_PROVIDER` | `Literal["openai", "anthropic", "gemini"] \| None` | `None` | Provider selection. `None` = feature disabled |
| `LLM_API_KEY` | `str` | `""` | API key for the selected provider |
| `LLM_MODEL` | `str` | `""` | Model override (auto-selected if empty) |
| `LLM_SUMMARY_PROMPT` | `str` | *(default prompt)* | Custom summarization prompt |
| `LLM_DAILY_TOKEN_LIMIT` | `int` | `1_000_000` | Max tokens/day (0 = unlimited) |

Validation: if `LLM_PROVIDER` is set but `LLM_API_KEY` is empty, raise a startup error.

### D7: Data model — summary on both `Thread` and `ThreadItem`

**Decision**: Add `summary: str | None` to all three thread representations:

- **`ThreadORM`** — new nullable `TEXT` column on the `threads` table (Alembic migration).
- **`Thread`** (Pydantic) — full thread response model, used by `GET /v1/threads/{id}`.
- **`ThreadItem`** (Pydantic) — list-view model, used by `GET /v1/inboxes/{id}/threads` and MCP `email://inbox/{id}/recent`.

Including `summary` in `ThreadItem` is intentional: an LLM agent listing threads can triage them by summary without fetching each thread individually. This is the primary agent workflow — scan inbox, pick thread, act.

The `to_pydantic()` method on `ThreadORM` populates `summary` for both models. The `ListThreadsResponse` inherits the field through `ThreadItem`.

**Alternatives considered**:
- *Summary only on `Thread` (full model)*: Forces agents to fetch each thread to see summaries, defeating the purpose for list/triage workflows.
- *Separate `ThreadSummary` model*: Adds a third representation. Unnecessary — the summary is a single nullable string, not a complex object.

### D8: New module location — `src/nornweave/verdandi/summarize.py`

**Decision**: Place the summarization logic in `verdandi` (the ingestion engine), since it's triggered during message ingestion. The provider abstraction lives in a new `src/nornweave/verdandi/llm/` subpackage:

```
verdandi/
├── llm/
│   ├── __init__.py        # Factory: get_summary_provider()
│   ├── base.py            # SummaryProvider protocol + SummaryResult
│   ├── openai.py          # OpenAI implementation
│   ├── anthropic.py       # Anthropic implementation
│   └── gemini.py          # Gemini implementation
├── summarize.py           # generate_thread_summary() orchestration
├── content.py             # (existing) Talon extraction
├── threading.py           # (existing) JWZ threading
└── ...
```

**Rationale**: Verdandi is "The Loom" — it processes incoming content. Summarization is a content processing step. Keeping it here avoids a new top-level module and maintains the existing architectural theme.

## Risks / Trade-offs

**[LLM latency adds to ingestion time]** → Summarization runs as fire-and-forget after the message is persisted. The API response to the webhook provider is not delayed. If the summary takes too long or fails, the thread is still fully functional — just without an updated summary.

**[Provider API failures]** → All LLM calls are wrapped in try/except. Failures are logged and the thread retains its previous summary (or `None`). No retry logic in v1 — the next message arrival will re-summarize.

**[Token budget race condition with concurrent workers]** → Two workers could both check the budget, both see it under the limit, and both proceed — briefly exceeding the budget. Acceptable for v1 since the overshoot is bounded (at most one extra summary per concurrent worker). Can be addressed later with `SELECT ... FOR UPDATE` if needed.

**[Large threads may exceed LLM context window]** → For threads with hundreds of messages, the concatenated text may exceed the model's context window. Mitigation: truncate from the oldest messages, keeping the most recent N messages that fit within a configurable max input token count (default: 80% of model's context window). The prompt instructs the LLM to note that earlier messages were truncated.

**[Cost visibility]** → Users need to monitor their token usage. The `llm_token_usage` table is queryable. A future REST endpoint (`GET /v1/admin/llm-usage`) could expose this, but is out of scope for this change.

**[Optional dependencies]** → Provider SDKs (`openai`, `anthropic`, `google-genai`) are optional extras in `pyproject.toml`. If a user configures `LLM_PROVIDER=openai` but hasn't installed the `openai` package, the startup validation should produce a clear error message with install instructions.
