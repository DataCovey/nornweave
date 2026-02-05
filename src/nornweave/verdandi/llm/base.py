"""Base protocol and data types for LLM summarization providers."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class SummaryResult:
    """Result of an LLM summarization call."""

    summary: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str


@runtime_checkable
class SummaryProvider(Protocol):
    """Protocol for LLM summarization providers."""

    async def summarize(self, text: str) -> SummaryResult:
        """
        Generate a summary of the given text.

        Args:
            text: The thread text to summarize (formatted conversation).

        Returns:
            SummaryResult with the generated summary and token usage.

        Raises:
            Exception: If the provider API call fails.
        """
        ...
