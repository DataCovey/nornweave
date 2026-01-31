"""Main client classes for NornWeave API."""

from __future__ import annotations

from typing import Any

import httpx

from nornweave_client._base_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    BaseAsyncClient,
    BaseSyncClient,
)
from nornweave_client._types import HealthResponse, RequestOptions
from nornweave_client.resources.inboxes import AsyncInboxesResource, InboxesResource
from nornweave_client.resources.messages import AsyncMessagesResource, MessagesResource
from nornweave_client.resources.search import AsyncSearchResource, SearchResource
from nornweave_client.resources.threads import AsyncThreadsResource, ThreadsResource


class NornWeave:
    """Synchronous client for the NornWeave API.

    Example:
        from nornweave_client import NornWeave

        client = NornWeave(base_url="http://localhost:8000")
        inbox = client.inboxes.create(name="Support", email_username="support")
        print(inbox.email_address)

    Attributes:
        inboxes: Inbox management operations.
        messages: Message operations.
        threads: Thread operations.
        search: Search operations.
    """

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the NornWeave client.

        Args:
            base_url: Base URL for the NornWeave API.
            timeout: Default timeout in seconds for requests.
            max_retries: Maximum retry attempts for transient errors.
            httpx_client: Optional custom httpx.Client for proxy/transport config.
        """
        self._base_client = BaseSyncClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            httpx_client=httpx_client,
        )

        # Initialize resources
        self.inboxes = InboxesResource(self._base_client)
        self.messages = MessagesResource(self._base_client)
        self.threads = ThreadsResource(self._base_client)
        self.search = SearchResource(self._base_client)

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._base_client.base_url

    def health(self, *, request_options: RequestOptions | None = None) -> HealthResponse:
        """Check the health of the NornWeave API.

        Args:
            request_options: Optional request configuration.

        Returns:
            HealthResponse with status field.
        """
        response = self._base_client.request(
            "GET",
            "/health",
            request_options=request_options,
        )
        return HealthResponse.model_validate(response.json())

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._base_client.close()

    def __enter__(self) -> NornWeave:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncNornWeave:
    """Asynchronous client for the NornWeave API.

    Example:
        import asyncio
        from nornweave_client import AsyncNornWeave

        async def main():
            client = AsyncNornWeave(base_url="http://localhost:8000")
            inbox = await client.inboxes.create(name="Support", email_username="support")
            print(inbox.email_address)
            await client.close()

        asyncio.run(main())

    Attributes:
        inboxes: Inbox management operations.
        messages: Message operations.
        threads: Thread operations.
        search: Search operations.
    """

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the async NornWeave client.

        Args:
            base_url: Base URL for the NornWeave API.
            timeout: Default timeout in seconds for requests.
            max_retries: Maximum retry attempts for transient errors.
            httpx_client: Optional custom httpx.AsyncClient for proxy/transport config.
        """
        self._base_client = BaseAsyncClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            httpx_client=httpx_client,
        )

        # Initialize resources
        self.inboxes = AsyncInboxesResource(self._base_client)
        self.messages = AsyncMessagesResource(self._base_client)
        self.threads = AsyncThreadsResource(self._base_client)
        self.search = AsyncSearchResource(self._base_client)

    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._base_client.base_url

    async def health(self, *, request_options: RequestOptions | None = None) -> HealthResponse:
        """Check the health of the NornWeave API.

        Args:
            request_options: Optional request configuration.

        Returns:
            HealthResponse with status field.
        """
        response = await self._base_client.request(
            "GET",
            "/health",
            request_options=request_options,
        )
        return HealthResponse.model_validate(response.json())

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._base_client.close()

    async def __aenter__(self) -> AsyncNornWeave:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
