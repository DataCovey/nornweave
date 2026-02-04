"""Base HTTP client with retry logic and configuration."""

from __future__ import annotations

import time
from typing import Any

import httpx

from nornweave_client._exceptions import (
    ConnectionError,
    TimeoutError,
    raise_for_status,
)
from nornweave_client._types import RequestOptions

# Status codes that are retryable
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Default configuration
DEFAULT_TIMEOUT: float = 60.0
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_BASE_DELAY: float = 0.5  # seconds


class BaseSyncClient:
    """Base synchronous HTTP client with retry logic.

    Handles:
    - Configurable timeouts (client-level and per-request)
    - Automatic retries with exponential backoff
    - Custom httpx client support
    - Error handling and status code validation
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the sync client.

        Args:
            base_url: Base URL for the API (e.g., "http://localhost:8000").
            timeout: Default timeout in seconds.
            max_retries: Default maximum retry attempts for transient errors.
            httpx_client: Optional custom httpx.Client instance.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._owns_client = httpx_client is None
        self._client = httpx_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> BaseSyncClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_timeout(self, request_options: RequestOptions | None) -> float:
        """Get the timeout for a request."""
        if request_options and "timeout" in request_options:
            return request_options["timeout"]
        return self.timeout

    def _get_max_retries(self, request_options: RequestOptions | None) -> int:
        """Get the max retries for a request."""
        if request_options and "max_retries" in request_options:
            return request_options["max_retries"]
        return self.max_retries

    def _should_retry(self, status_code: int, attempt: int, max_retries: int) -> bool:
        """Determine if a request should be retried."""
        return status_code in RETRYABLE_STATUS_CODES and attempt < max_retries

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return float(DEFAULT_BASE_DELAY * (2**attempt))

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            path: API path (e.g., "/v1/inboxes").
            json: JSON body for the request.
            params: Query parameters.
            request_options: Per-request options (timeout, max_retries).

        Returns:
            The httpx.Response object.

        Raises:
            ApiError: On non-success status codes after retries exhausted.
            ConnectionError: When unable to connect.
            TimeoutError: When request times out.
        """
        timeout = self._get_timeout(request_options)
        max_retries = self._get_max_retries(request_options)

        # Build full URL if client doesn't have base_url set
        url = path if self._client.base_url else f"{self.base_url}{path}"

        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    timeout=timeout,
                )

                # Check if we should retry based on status code
                if self._should_retry(response.status_code, attempt, max_retries):
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    continue

                # Raise exception for error status codes
                if response.status_code >= 400:
                    try:
                        body = response.json()
                    except Exception:
                        body = response.text
                    raise_for_status(response.status_code, body)

                return response

            except httpx.ConnectError as e:
                last_exception = e
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    continue
                raise ConnectionError(f"Failed to connect to {self.base_url}: {e}") from e

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                    continue
                raise TimeoutError(f"Request timed out after {timeout}s") from e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in request retry loop")


class BaseAsyncClient:
    """Base asynchronous HTTP client with retry logic.

    Handles:
    - Configurable timeouts (client-level and per-request)
    - Automatic retries with exponential backoff
    - Custom httpx client support
    - Error handling and status code validation
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the async client.

        Args:
            base_url: Base URL for the API (e.g., "http://localhost:8000").
            timeout: Default timeout in seconds.
            max_retries: Default maximum retry attempts for transient errors.
            httpx_client: Optional custom httpx.AsyncClient instance.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._owns_client = httpx_client is None
        self._client = httpx_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> BaseAsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _get_timeout(self, request_options: RequestOptions | None) -> float:
        """Get the timeout for a request."""
        if request_options and "timeout" in request_options:
            return request_options["timeout"]
        return self.timeout

    def _get_max_retries(self, request_options: RequestOptions | None) -> int:
        """Get the max retries for a request."""
        if request_options and "max_retries" in request_options:
            return request_options["max_retries"]
        return self.max_retries

    def _should_retry(self, status_code: int, attempt: int, max_retries: int) -> bool:
        """Determine if a request should be retried."""
        return status_code in RETRYABLE_STATUS_CODES and attempt < max_retries

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return float(DEFAULT_BASE_DELAY * (2**attempt))

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            path: API path (e.g., "/v1/inboxes").
            json: JSON body for the request.
            params: Query parameters.
            request_options: Per-request options (timeout, max_retries).

        Returns:
            The httpx.Response object.

        Raises:
            ApiError: On non-success status codes after retries exhausted.
            ConnectionError: When unable to connect.
            TimeoutError: When request times out.
        """
        import asyncio

        timeout = self._get_timeout(request_options)
        max_retries = self._get_max_retries(request_options)

        # Build full URL if client doesn't have base_url set
        url = path if self._client.base_url else f"{self.base_url}{path}"

        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    timeout=timeout,
                )

                # Check if we should retry based on status code
                if self._should_retry(response.status_code, attempt, max_retries):
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue

                # Raise exception for error status codes
                if response.status_code >= 400:
                    try:
                        body = response.json()
                    except Exception:
                        body = response.text
                    raise_for_status(response.status_code, body)

                return response

            except httpx.ConnectError as e:
                last_exception = e
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise ConnectionError(f"Failed to connect to {self.base_url}: {e}") from e

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise TimeoutError(f"Request timed out after {timeout}s") from e

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in request retry loop")
