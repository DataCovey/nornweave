"""OpenAI summarization provider."""

import logging

from nornweave.verdandi.llm.base import SummaryResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAISummaryProvider:
    """Summarization provider using OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "", prompt: str = "") -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            msg = (
                "OpenAI package is required for LLM_PROVIDER='openai'. Install with: uv add openai"
            )
            raise ImportError(msg)

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or DEFAULT_MODEL
        self.prompt = prompt

    async def summarize(self, text: str) -> SummaryResult:
        """Generate a summary using OpenAI Chat Completions API."""
        try:
            from openai import APIError
        except ImportError:
            APIError = Exception  # type: ignore[assignment,misc]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": text},
                ],
            )
        except APIError as e:
            logger.error("OpenAI API error: %s %s", e.status_code, e.message)
            raise

        choice = response.choices[0]
        summary = choice.message.content or ""
        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return SummaryResult(
            summary=summary.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=response.model or self.model,
        )
