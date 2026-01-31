"""Search resource for searching messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._raw_response import RawResponse
from nornweave_client._types import RequestOptions, SearchResponse, SearchResultItem
from nornweave_client.resources._base import (
    AsyncBaseResource,
    SyncBaseResource,
    make_raw_response,
)

if TYPE_CHECKING:
    from nornweave_client._base_client import BaseAsyncClient, BaseSyncClient


class SearchResource(SyncBaseResource):
    """Synchronous search operations."""

    def __init__(self, client: BaseSyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = SearchWithRawResponse(self)

    def query(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SyncPager[SearchResultItem]:
        """Search messages by content.

        Args:
            query: The search query string.
            inbox_id: The inbox ID to search within.
            limit: Maximum number of results per page (default: 50, max: 100).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            A paginator that yields SearchResultItem objects.
        """

        def fetch_page(page_limit: int, page_offset: int) -> tuple[list[SearchResultItem], int]:
            response = self._request(
                "POST",
                "/v1/search",
                json={
                    "query": query,
                    "inbox_id": inbox_id,
                    "limit": page_limit,
                    "offset": page_offset,
                },
                request_options=request_options,
            )
            data = response.json()
            items = [SearchResultItem.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return SyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    def query_raw(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SearchResponse:
        """Search messages and return the full response object.

        Args:
            query: The search query string.
            inbox_id: The inbox ID to search within.
            limit: Maximum number of results (default: 50, max: 100).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            The SearchResponse object with items, count, and query echo.
        """
        response = self._request(
            "POST",
            "/v1/search",
            json={
                "query": query,
                "inbox_id": inbox_id,
                "limit": limit,
                "offset": offset,
            },
            request_options=request_options,
        )
        return SearchResponse.model_validate(response.json())


class SearchWithRawResponse:
    """Search operations that return raw responses."""

    def __init__(self, resource: SearchResource) -> None:
        self._resource = resource

    def query_raw(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[SearchResponse]:
        """Search messages and return raw response."""
        response = self._resource._request(
            "POST",
            "/v1/search",
            json={
                "query": query,
                "inbox_id": inbox_id,
                "limit": limit,
                "offset": offset,
            },
            request_options=request_options,
        )
        data = SearchResponse.model_validate(response.json())
        return make_raw_response(data, response)


class AsyncSearchResource(AsyncBaseResource):
    """Asynchronous search operations."""

    def __init__(self, client: BaseAsyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = AsyncSearchWithRawResponse(self)

    def query(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> AsyncPager[SearchResultItem]:
        """Search messages by content.

        Args:
            query: The search query string.
            inbox_id: The inbox ID to search within.
            limit: Maximum number of results per page (default: 50, max: 100).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            An async paginator that yields SearchResultItem objects.
        """

        async def fetch_page(
            page_limit: int, page_offset: int
        ) -> tuple[list[SearchResultItem], int]:
            response = await self._request(
                "POST",
                "/v1/search",
                json={
                    "query": query,
                    "inbox_id": inbox_id,
                    "limit": page_limit,
                    "offset": page_offset,
                },
                request_options=request_options,
            )
            data = response.json()
            items = [SearchResultItem.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return AsyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    async def query_raw(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SearchResponse:
        """Search messages and return the full response object.

        Args:
            query: The search query string.
            inbox_id: The inbox ID to search within.
            limit: Maximum number of results (default: 50, max: 100).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            The SearchResponse object with items, count, and query echo.
        """
        response = await self._request(
            "POST",
            "/v1/search",
            json={
                "query": query,
                "inbox_id": inbox_id,
                "limit": limit,
                "offset": offset,
            },
            request_options=request_options,
        )
        return SearchResponse.model_validate(response.json())


class AsyncSearchWithRawResponse:
    """Async search operations that return raw responses."""

    def __init__(self, resource: AsyncSearchResource) -> None:
        self._resource = resource

    async def query_raw(
        self,
        *,
        query: str,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[SearchResponse]:
        """Search messages and return raw response."""
        response = await self._resource._request(
            "POST",
            "/v1/search",
            json={
                "query": query,
                "inbox_id": inbox_id,
                "limit": limit,
                "offset": offset,
            },
            request_options=request_options,
        )
        data = SearchResponse.model_validate(response.json())
        return make_raw_response(data, response)
