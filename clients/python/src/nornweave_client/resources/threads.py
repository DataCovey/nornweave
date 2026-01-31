"""Threads resource for managing email threads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._raw_response import RawResponse
from nornweave_client._types import RequestOptions, ThreadDetail, ThreadSummary
from nornweave_client.resources._base import (
    AsyncBaseResource,
    SyncBaseResource,
    make_raw_response,
)

if TYPE_CHECKING:
    from nornweave_client._base_client import BaseAsyncClient, BaseSyncClient


class ThreadsResource(SyncBaseResource):
    """Synchronous thread operations."""

    def __init__(self, client: BaseSyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = ThreadsWithRawResponse(self)

    def list(
        self,
        *,
        inbox_id: str,
        limit: int = 20,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SyncPager[ThreadSummary]:
        """List threads for an inbox with pagination.

        Args:
            inbox_id: The inbox ID to list threads for.
            limit: Maximum number of items per page (default: 20).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            A paginator that yields ThreadSummary objects.
        """

        def fetch_page(page_limit: int, page_offset: int) -> tuple[list[ThreadSummary], int]:
            response = self._request(
                "GET",
                "/v1/threads",
                params={"inbox_id": inbox_id, "limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [ThreadSummary.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return SyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    def get(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> ThreadDetail:
        """Get a thread with its messages.

        Args:
            thread_id: The thread ID.
            limit: Maximum number of messages to return (default: 100).
            offset: Starting offset for messages (default: 0).
            request_options: Optional request configuration.

        Returns:
            The ThreadDetail object with messages in LLM-ready format.
        """
        response = self._request(
            "GET",
            f"/v1/threads/{thread_id}",
            params={"limit": limit, "offset": offset},
            request_options=request_options,
        )
        return ThreadDetail.model_validate(response.json())


class ThreadsWithRawResponse:
    """Thread operations that return raw responses."""

    def __init__(self, resource: ThreadsResource) -> None:
        self._resource = resource

    def get(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[ThreadDetail]:
        """Get a thread with its messages and return raw response."""
        response = self._resource._request(
            "GET",
            f"/v1/threads/{thread_id}",
            params={"limit": limit, "offset": offset},
            request_options=request_options,
        )
        thread = ThreadDetail.model_validate(response.json())
        return make_raw_response(thread, response)


class AsyncThreadsResource(AsyncBaseResource):
    """Asynchronous thread operations."""

    def __init__(self, client: BaseAsyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = AsyncThreadsWithRawResponse(self)

    def list(
        self,
        *,
        inbox_id: str,
        limit: int = 20,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> AsyncPager[ThreadSummary]:
        """List threads for an inbox with pagination.

        Args:
            inbox_id: The inbox ID to list threads for.
            limit: Maximum number of items per page (default: 20).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            An async paginator that yields ThreadSummary objects.
        """

        async def fetch_page(page_limit: int, page_offset: int) -> tuple[list[ThreadSummary], int]:
            response = await self._request(
                "GET",
                "/v1/threads",
                params={"inbox_id": inbox_id, "limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [ThreadSummary.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return AsyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    async def get(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> ThreadDetail:
        """Get a thread with its messages.

        Args:
            thread_id: The thread ID.
            limit: Maximum number of messages to return (default: 100).
            offset: Starting offset for messages (default: 0).
            request_options: Optional request configuration.

        Returns:
            The ThreadDetail object with messages in LLM-ready format.
        """
        response = await self._request(
            "GET",
            f"/v1/threads/{thread_id}",
            params={"limit": limit, "offset": offset},
            request_options=request_options,
        )
        return ThreadDetail.model_validate(response.json())


class AsyncThreadsWithRawResponse:
    """Async thread operations that return raw responses."""

    def __init__(self, resource: AsyncThreadsResource) -> None:
        self._resource = resource

    async def get(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[ThreadDetail]:
        """Get a thread with its messages and return raw response."""
        response = await self._resource._request(
            "GET",
            f"/v1/threads/{thread_id}",
            params={"limit": limit, "offset": offset},
            request_options=request_options,
        )
        thread = ThreadDetail.model_validate(response.json())
        return make_raw_response(thread, response)
