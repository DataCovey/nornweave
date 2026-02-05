"""Thread summarization orchestration.

Generates LLM-powered thread summaries from Talon-cleaned message content.
Runs as a fire-and-forget post-ingestion hook.
"""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from nornweave.core.config import get_settings
from nornweave.verdandi.llm import get_summary_provider

if TYPE_CHECKING:
    from nornweave.core.interfaces import StorageInterface
    from nornweave.models.message import Message

logger = logging.getLogger(__name__)

# Approximate context window sizes per model family (in tokens).
# Used for truncation. Conservative estimates at 80% capacity.
_CONTEXT_WINDOWS: dict[str, int] = {
    # OpenAI
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-3.5-turbo": 16_385,
    # Anthropic
    "claude-haiku": 200_000,
    "claude-sonnet": 200_000,
    "claude-opus": 200_000,
    # Gemini
    "gemini-2.0-flash": 1_000_000,
    "gemini-2.0-pro": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
    "gemini-1.5-pro": 2_000_000,
}
_DEFAULT_CONTEXT_WINDOW = 128_000
# Approximate chars per token for truncation estimation
_CHARS_PER_TOKEN = 4


def prepare_thread_text(messages: list[Message]) -> str:
    """
    Prepare thread text for summarization from Talon-cleaned extracted_text.

    Concatenates extracted_text for all messages in chronological order,
    with [datetime] sender: headers. Falls back to raw text if extracted_text
    is unavailable. Skips messages with no text content.

    Args:
        messages: List of messages ordered by timestamp ascending.

    Returns:
        Formatted conversation text ready for LLM summarization.
    """
    sorted_messages = sorted(messages, key=lambda m: m.timestamp or datetime.min)
    parts: list[str] = []

    for msg in sorted_messages:
        text = msg.extracted_text or msg.text
        if not text or not text.strip():
            continue

        timestamp_str = (
            msg.timestamp.strftime("%Y-%m-%d %H:%M") if msg.timestamp else "unknown date"
        )
        sender = msg.from_address or "unknown"
        parts.append(f"[{timestamp_str}] {sender}:\n{text.strip()}")

    return "\n\n".join(parts)


def truncate_to_context_window(text: str, model: str) -> str:
    """
    Truncate thread text to fit within the model's context window.

    Keeps the most recent messages (from the end) that fit within 80% of
    the model's context window, reserving space for the prompt and response.

    Args:
        text: The full conversation text.
        model: The model identifier (used to look up context window size).

    Returns:
        The text, possibly truncated with a note about earlier messages.
    """
    # Find context window for this model (match by prefix for versioned models)
    context_window = _DEFAULT_CONTEXT_WINDOW
    for model_prefix, window in _CONTEXT_WINDOWS.items():
        if model.startswith(model_prefix):
            context_window = window
            break

    max_chars = int(context_window * 0.8 * _CHARS_PER_TOKEN)

    if len(text) <= max_chars:
        return text

    # Split into message blocks and keep from the end
    blocks = text.split("\n\n")
    kept: list[str] = []
    total_chars = 0
    truncation_note = "[Earlier messages truncated — summary covers the most recent messages]\n\n"
    available_chars = max_chars - len(truncation_note)

    for block in reversed(blocks):
        block_len = len(block) + 2  # +2 for the \n\n separator
        if total_chars + block_len > available_chars:
            break
        kept.insert(0, block)
        total_chars += block_len

    if len(kept) < len(blocks):
        return truncation_note + "\n\n".join(kept)

    return text


async def check_token_budget(storage: StorageInterface) -> bool:
    """
    Check if the daily token budget allows another summarization call.

    Args:
        storage: Storage interface for reading token usage.

    Returns:
        True if summarization can proceed, False if budget is exhausted.
    """
    settings = get_settings()
    limit = settings.llm_daily_token_limit

    # 0 means unlimited
    if limit == 0:
        return True

    today = datetime.now(UTC).date()
    current_usage = await storage.get_token_usage(today)

    if current_usage >= limit:
        logger.debug(
            "Daily token limit reached (%d/%d), skipping summarization", current_usage, limit
        )
        return False

    return True


async def generate_thread_summary(storage: StorageInterface, thread_id: str) -> None:
    """
    Generate or update the LLM summary for a thread.

    Orchestrates: check budget → load messages → prepare text → truncate →
    call provider → update thread summary → record tokens.

    This function is designed to be called fire-and-forget after message
    ingestion. Failures are logged and never propagated.

    Args:
        storage: Storage interface for reading/writing data.
        thread_id: ID of the thread to summarize.
    """
    try:
        # Step 1: Check if LLM is enabled
        provider = get_summary_provider()
        if provider is None:
            return

        # Step 2: Check daily token budget
        if not await check_token_budget(storage):
            return

        # Step 3: Load all messages for the thread
        messages = await storage.list_messages_for_thread(thread_id, limit=1000)
        if not messages:
            return

        # Step 4: Prepare thread text
        text = prepare_thread_text(messages)
        if not text.strip():
            return

        # Step 5: Truncate if needed
        settings = get_settings()
        model = settings.llm_model or ""
        text = truncate_to_context_window(text, model)

        # Step 6: Call the LLM provider
        result = await provider.summarize(text)

        # If provider didn't report tokens, estimate from character count
        if result.total_tokens == 0 and (text or result.summary):
            estimated_input = len(text) // 4
            estimated_output = len(result.summary) // 4
            result = type(result)(
                summary=result.summary,
                input_tokens=estimated_input,
                output_tokens=estimated_output,
                total_tokens=estimated_input + estimated_output,
                model=result.model,
            )
            logger.warning(
                "Provider did not report token usage for thread %s, estimated %d tokens",
                thread_id,
                result.total_tokens,
            )

        # Step 7: Update thread summary
        thread = await storage.get_thread(thread_id)
        if thread is None:
            logger.warning("Thread %s not found when updating summary", thread_id)
            return

        thread.summary = result.summary
        await storage.update_thread(thread)

        # Step 8: Record token usage
        today = datetime.now(UTC).date()
        await storage.record_token_usage(today, result.total_tokens)

        logger.info(
            "Updated summary for thread %s (model=%s, tokens=%d)",
            thread_id,
            result.model,
            result.total_tokens,
        )

    except Exception as exc:
        # Provider errors are already logged at ERROR level by the provider itself.
        # Log a concise warning here without the full traceback to keep logs clean.
        logger.warning("Failed to generate summary for thread %s: %s", thread_id, exc)
