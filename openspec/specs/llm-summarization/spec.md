## ADDED Requirements

### Requirement: SummaryProvider protocol defines the LLM integration contract

The system SHALL define a `SummaryProvider` protocol with a single async method `summarize(text: str) -> SummaryResult` that all LLM provider implementations MUST satisfy.

`SummaryResult` SHALL contain:
- `summary` (str): The generated summary text
- `input_tokens` (int): Number of input tokens consumed
- `output_tokens` (int): Number of output tokens consumed
- `total_tokens` (int): Total tokens consumed (input + output)
- `model` (str): The model identifier used

#### Scenario: Protocol is satisfied by all providers
- **WHEN** `OpenAISummaryProvider`, `AnthropicSummaryProvider`, and `GeminiSummaryProvider` are instantiated
- **THEN** each satisfies the `SummaryProvider` protocol
- **AND** each implements `async summarize(text: str) -> SummaryResult`

#### Scenario: SummaryResult contains token usage
- **WHEN** a provider completes a summarization call
- **THEN** the returned `SummaryResult` contains accurate `input_tokens`, `output_tokens`, and `total_tokens` from the provider response

### Requirement: OpenAI provider calls the Chat Completions API

The `OpenAISummaryProvider` SHALL call the OpenAI Chat Completions API using the `openai` Python SDK with the configured model and prompt.

The default model SHALL be `gpt-4o-mini` when `LLM_MODEL` is not set.

#### Scenario: Successful summarization with OpenAI
- **WHEN** `LLM_PROVIDER` is `openai` and `LLM_API_KEY` is a valid OpenAI key
- **AND** `summarize(text)` is called with thread text
- **THEN** the provider calls OpenAI Chat Completions with the system prompt and user text
- **AND** returns a `SummaryResult` with the generated summary

#### Scenario: OpenAI uses configured model
- **WHEN** `LLM_MODEL` is set to `gpt-4o`
- **THEN** the provider uses `gpt-4o` instead of the default `gpt-4o-mini`

#### Scenario: OpenAI API error is raised
- **WHEN** the OpenAI API returns an error (rate limit, auth failure, etc.)
- **THEN** the provider raises an exception with a descriptive error message

### Requirement: Anthropic provider calls the Messages API

The `AnthropicSummaryProvider` SHALL call the Anthropic Messages API using the `anthropic` Python SDK with the configured model and prompt.

The default model SHALL be `claude-haiku` when `LLM_MODEL` is not set.

#### Scenario: Successful summarization with Anthropic
- **WHEN** `LLM_PROVIDER` is `anthropic` and `LLM_API_KEY` is a valid Anthropic key
- **AND** `summarize(text)` is called with thread text
- **THEN** the provider calls Anthropic Messages API with the system prompt and user text
- **AND** returns a `SummaryResult` with the generated summary

#### Scenario: Anthropic uses configured model
- **WHEN** `LLM_MODEL` is set to `claude-sonnet-4-20250514`
- **THEN** the provider uses `claude-sonnet-4-20250514` instead of the default

#### Scenario: Anthropic API error is raised
- **WHEN** the Anthropic API returns an error
- **THEN** the provider raises an exception with a descriptive error message

### Requirement: Gemini provider calls the Google GenAI API

The `GeminiSummaryProvider` SHALL call the Google Generative AI API using the `google-genai` Python SDK with the configured model and prompt.

The default model SHALL be `gemini-2.0-flash` when `LLM_MODEL` is not set.

#### Scenario: Successful summarization with Gemini
- **WHEN** `LLM_PROVIDER` is `gemini` and `LLM_API_KEY` is a valid Google API key
- **AND** `summarize(text)` is called with thread text
- **THEN** the provider calls Google GenAI API with the system prompt and user text
- **AND** returns a `SummaryResult` with the generated summary

#### Scenario: Gemini uses configured model
- **WHEN** `LLM_MODEL` is set to `gemini-2.0-pro`
- **THEN** the provider uses `gemini-2.0-pro` instead of the default

#### Scenario: Gemini API error is raised
- **WHEN** the Google GenAI API returns an error
- **THEN** the provider raises an exception with a descriptive error message

### Requirement: Factory function creates the correct provider from config

The system SHALL provide a `get_summary_provider()` factory function that returns the appropriate `SummaryProvider` based on `LLM_PROVIDER` configuration, or `None` if the feature is disabled.

#### Scenario: No provider configured (feature disabled)
- **WHEN** `LLM_PROVIDER` is not set or is empty
- **THEN** `get_summary_provider()` returns `None`

#### Scenario: OpenAI provider selected
- **WHEN** `LLM_PROVIDER` is `openai` and `LLM_API_KEY` is set
- **THEN** `get_summary_provider()` returns an `OpenAISummaryProvider` instance

#### Scenario: Provider configured but SDK not installed
- **WHEN** `LLM_PROVIDER` is `openai` but the `openai` package is not installed
- **THEN** `get_summary_provider()` raises an error with install instructions (e.g., "Install with: uv add openai")

#### Scenario: Provider configured but API key missing
- **WHEN** `LLM_PROVIDER` is `anthropic` but `LLM_API_KEY` is empty
- **THEN** the system SHALL raise a startup configuration error

### Requirement: LLM configuration uses environment variables

The system SHALL add the following settings to the `Settings` class in `core/config.py`:

| Env Var | Type | Default |
|---------|------|---------|
| `LLM_PROVIDER` | `Literal["openai", "anthropic", "gemini"] \| None` | `None` |
| `LLM_API_KEY` | `str` | `""` |
| `LLM_MODEL` | `str` | `""` |
| `LLM_SUMMARY_PROMPT` | `str` | *(default prompt)* |
| `LLM_DAILY_TOKEN_LIMIT` | `int` | `1_000_000` |

#### Scenario: Default configuration disables the feature
- **WHEN** no `LLM_*` env vars are set
- **THEN** `LLM_PROVIDER` is `None` and summarization is disabled

#### Scenario: Custom prompt overrides default
- **WHEN** `LLM_SUMMARY_PROMPT` is set to a custom string
- **THEN** the custom prompt is used as the system message for all summarization calls

#### Scenario: Default prompt is used when not overridden
- **WHEN** `LLM_SUMMARY_PROMPT` is not set
- **THEN** the built-in default prompt is used

### Requirement: Provider SDKs are optional dependencies

The LLM provider SDKs (`openai`, `anthropic`, `google-genai`) SHALL be declared as optional extras in `pyproject.toml`, not as hard dependencies.

#### Scenario: Base install has no LLM dependencies
- **WHEN** a user installs NornWeave without extras
- **THEN** none of the LLM provider packages are installed

#### Scenario: Install with specific provider extra
- **WHEN** a user runs `uv add nornweave[openai]`
- **THEN** the `openai` package is installed as a dependency

#### Scenario: Install all LLM providers
- **WHEN** a user runs `uv add nornweave[llm]`
- **THEN** all three provider packages (`openai`, `anthropic`, `google-genai`) are installed
