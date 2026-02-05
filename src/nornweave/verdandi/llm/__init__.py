"""LLM provider abstraction for thread summarization.

Factory function to create the appropriate SummaryProvider based on configuration.
"""

import logging

from nornweave.core.config import get_settings
from nornweave.verdandi.llm.base import SummaryProvider, SummaryResult

__all__ = ["SummaryProvider", "SummaryResult", "get_summary_provider"]

logger = logging.getLogger(__name__)


def get_summary_provider() -> SummaryProvider | None:
    """
    Create and return the appropriate SummaryProvider based on LLM configuration.

    Returns:
        A SummaryProvider instance if LLM_PROVIDER is configured, None if disabled.

    Raises:
        ImportError: If the required provider SDK is not installed.
        ValueError: If LLM_PROVIDER is set but LLM_API_KEY is missing.
    """
    settings = get_settings()

    if settings.llm_provider is None:
        return None

    api_key = settings.llm_api_key
    model = settings.llm_model
    prompt = settings.llm_summary_prompt

    if settings.llm_provider == "openai":
        from nornweave.verdandi.llm.openai import OpenAISummaryProvider

        return OpenAISummaryProvider(api_key=api_key, model=model, prompt=prompt)

    if settings.llm_provider == "anthropic":
        from nornweave.verdandi.llm.anthropic import AnthropicSummaryProvider

        return AnthropicSummaryProvider(api_key=api_key, model=model, prompt=prompt)

    if settings.llm_provider == "gemini":
        from nornweave.verdandi.llm.gemini import GeminiSummaryProvider

        return GeminiSummaryProvider(api_key=api_key, model=model, prompt=prompt)

    msg = f"Unknown LLM provider: {settings.llm_provider}"
    raise ValueError(msg)
