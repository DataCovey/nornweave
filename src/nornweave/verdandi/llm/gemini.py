"""Google Gemini summarization provider using REST API directly.

Uses httpx instead of the google-genai SDK to avoid credential resolution
conflicts with other Google Cloud libraries (google-auth, google-cloud-storage).
"""

import logging
from typing import Any

import httpx

from nornweave.verdandi.llm.base import SummaryResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiSummaryProvider:
    """Summarization provider using Google Generative Language REST API."""

    def __init__(self, api_key: str, model: str = "", prompt: str = "") -> None:
        self.api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.prompt = prompt

    async def summarize(self, text: str) -> SummaryResult:
        """Generate a summary using the Gemini REST API."""
        url = f"{_BASE_URL}/models/{self.model}:generateContent"

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": text}]}],
        }
        if self.prompt:
            payload["systemInstruction"] = {"parts": [{"text": self.prompt}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": self.api_key,
                },
            )

        if response.status_code != 200:
            body = (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            error_msg = body.get("error", {}).get("message", response.text[:200])
            logger.error("Gemini API error %d: %s", response.status_code, error_msg)
            msg = f"Gemini API returned {response.status_code}: {error_msg}"
            raise RuntimeError(msg)

        data = response.json()
        candidates = data.get("candidates", [])
        summary = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            summary = "".join(p.get("text", "") for p in parts)

        # Extract token usage from usageMetadata
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        total_tokens = usage.get("totalTokenCount", input_tokens + output_tokens)

        return SummaryResult(
            summary=summary.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model=self.model,
        )
