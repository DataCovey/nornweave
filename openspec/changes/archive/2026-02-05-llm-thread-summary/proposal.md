## Why

NornWeave is designed so LLM agents can interact with email — but long threads (10, 30, 50+ messages) force agents to read every message to understand context, wasting tokens and latency. By storing an LLM-generated **Thread Summary** that updates incrementally on each new message, an agent can understand any thread by reading just the summary + the last 2 messages. This is the single highest-leverage feature for making NornWeave truly AI-native.

## What Changes

- **Add `summary` field to threads** — a new nullable text column on the threads table, exposed in the Thread model, REST API responses, and MCP resources.
- **LLM summarization on ingestion** — when a new message arrives and the feature is enabled, concatenate the thread's Talon-cleaned `extracted_text` for all messages (removing quoted-reply duplication) and call the configured LLM provider to generate/update the summary.
- **Multi-provider LLM support** — support OpenAI, Anthropic, and Google Gemini as summarization backends, selected via `LLM_PROVIDER` env var. Disabled by default (no provider = no summarization). Each provider requires its own API key env var.
- **Customizable summarization prompt** — ship a sensible default prompt; allow override via `LLM_SUMMARY_PROMPT` env var.
- **Daily token budget with counter** — track token usage per day in the database. When `LLM_DAILY_TOKEN_LIMIT` is reached, summarization is silently disabled until the next UTC day. Counter resets automatically.

## Capabilities

### New Capabilities

- `llm-summarization`: Core LLM integration layer — provider abstraction (OpenAI, Anthropic, Gemini), configuration, prompt management, and the summarization call itself.
- `thread-summary`: Thread-level summary storage, the ingestion hook that triggers summarization, feeding Talon-cleaned text to the LLM, and exposing the summary in the Thread model / API / MCP.
- `llm-token-budget`: Daily token usage counter stored in the database, configurable daily limit, automatic reset, and the gate that disables summarization when the budget is exhausted.

### Modified Capabilities

- `rest-api`: Thread responses (`GET /v1/threads/{id}`, `GET /v1/inboxes/{id}/threads`) gain a `summary` field.
- `mcp-server`: MCP thread resources include the summary when available, reducing context window usage for agents.

## Impact

- **Models**: `Thread`, `ThreadItem`, `ThreadORM` gain a `summary: str | None` field.
- **Database**: New migration adding `summary TEXT` column to `threads` table; new `llm_token_usage` table (date, tokens_used).
- **Config**: New env vars — `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_SUMMARY_PROMPT`, `LLM_DAILY_TOKEN_LIMIT`.
- **Dependencies**: New optional deps — `openai`, `anthropic`, `google-genai` (only the chosen provider is needed at runtime).
- **Ingestion pipeline** (`verdandi`): Post-threading hook calls summarization asynchronously.
- **API responses**: Thread endpoints include `summary` field (null when disabled).
- **MCP resources** (`huginn`): Thread content resource includes summary for agent consumption.
- **Outbound** (`skuld`): No changes.
