"""Anthropic summarization provider."""

import logging

from nornweave.verdandi.llm.base import SummaryResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku"


class AnthropicSummaryProvider:
    """Summarization provider using Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "", prompt: str = "") -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            msg = (
                "Anthropic package is required for LLM_PROVIDER='anthropic'. "
                "Install with: uv add anthropic"
            )
            raise ImportError(msg)

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model or DEFAULT_MODEL
        self.prompt = prompt

    async def summarize(self, text: str) -> SummaryResult:
        """Generate a summary using Anthropic Messages API."""
        try:
            from anthropic import APIError
        except ImportError:
            APIError = Exception  # type: ignore[assignment,misc]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.prompt,
                messages=[
                    {"role": "user", "content": text},
                ],
            )
        except APIError as e:
            logger.error("Anthropic API error: %s %s", e.status_code, e.message)
            raise

        summary = ""
        for block in response.content:
            if block.type == "text":
                summary += block.text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return SummaryResult(
            summary=summary.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=response.model or self.model,
        )
