"""Pagination utilities for NornWeave API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Generic, Iterator, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

T = TypeVar("T", bound=BaseModel)


class PageResponse(BaseModel, Generic[T]):
    """A page of results from a paginated endpoint."""

    items: list[T]
    count: int


class SyncPager(Generic[T]):
    """Synchronous paginator for list endpoints.

    Supports iteration over all items across pages, or page-by-page iteration.

    Example:
        # Iterate over all items
        for item in client.inboxes.list():
            print(item.name)

        # Iterate page by page
        for page in client.inboxes.list().iter_pages():
            print(f"Page with {len(page.items)} items")
    """

    def __init__(
        self,
        *,
        fetch_page: Callable[[int, int], tuple[list[T], int]],
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        """Initialize the pager.

        Args:
            fetch_page: Function to fetch a page, takes (limit, offset) and returns (items, total).
            limit: Number of items per page.
            offset: Starting offset.
        """
        self._fetch_page = fetch_page
        self._limit = limit
        self._offset = offset
        self._items: list[T] | None = None
        self._count: int | None = None
        self._fetched = False

    def _ensure_fetched(self) -> None:
        """Fetch the first page if not already fetched."""
        if not self._fetched:
            items, count = self._fetch_page(self._limit, self._offset)
            self._items = items
            self._count = count
            self._fetched = True

    @property
    def items(self) -> list[T]:
        """Get the items from the current page."""
        self._ensure_fetched()
        return self._items or []

    @property
    def count(self) -> int:
        """Get the total count of items across all pages."""
        self._ensure_fetched()
        return self._count or 0

    def __iter__(self) -> Iterator[T]:
        """Iterate over all items across all pages."""
        offset = self._offset
        while True:
            items, total = self._fetch_page(self._limit, offset)
            yield from items
            offset += len(items)
            if offset >= total or len(items) == 0:
                break

    def __len__(self) -> int:
        """Return the total count of items."""
        return self.count

    def iter_pages(self) -> Iterator[PageResponse[T]]:
        """Iterate over pages of results.

        Yields:
            PageResponse objects containing items and count.
        """
        offset = self._offset
        while True:
            items, total = self._fetch_page(self._limit, offset)
            yield PageResponse[T](items=items, count=total)
            offset += len(items)
            if offset >= total or len(items) == 0:
                break

    def to_list(self) -> list[T]:
        """Fetch all items and return as a list.

        Warning: This fetches all pages, which may be slow for large datasets.
        """
        return list(self)


class AsyncPager(Generic[T]):
    """Asynchronous paginator for list endpoints.

    Supports async iteration over all items across pages, or page-by-page iteration.

    Example:
        # Iterate over all items
        async for item in client.inboxes.list():
            print(item.name)

        # Iterate page by page
        async for page in client.inboxes.list().iter_pages():
            print(f"Page with {len(page.items)} items")
    """

    def __init__(
        self,
        *,
        fetch_page: Callable[[int, int], Any],  # Returns Awaitable[tuple[list[T], int]]
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        """Initialize the async pager.

        Args:
            fetch_page: Async function to fetch a page, takes (limit, offset) and returns (items, total).
            limit: Number of items per page.
            offset: Starting offset.
        """
        self._fetch_page = fetch_page
        self._limit = limit
        self._offset = offset
        self._items: list[T] | None = None
        self._count: int | None = None
        self._fetched = False

    async def _ensure_fetched(self) -> None:
        """Fetch the first page if not already fetched."""
        if not self._fetched:
            items, count = await self._fetch_page(self._limit, self._offset)
            self._items = items
            self._count = count
            self._fetched = True

    async def get_items(self) -> list[T]:
        """Get the items from the current page."""
        await self._ensure_fetched()
        return self._items or []

    async def get_count(self) -> int:
        """Get the total count of items across all pages."""
        await self._ensure_fetched()
        return self._count or 0

    async def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over all items across all pages."""
        offset = self._offset
        while True:
            items, total = await self._fetch_page(self._limit, offset)
            for item in items:
                yield item
            offset += len(items)
            if offset >= total or len(items) == 0:
                break

    async def iter_pages(self) -> AsyncIterator[PageResponse[T]]:
        """Iterate over pages of results.

        Yields:
            PageResponse objects containing items and count.
        """
        offset = self._offset
        while True:
            items, total = await self._fetch_page(self._limit, offset)
            yield PageResponse[T](items=items, count=total)
            offset += len(items)
            if offset >= total or len(items) == 0:
                break

    async def to_list(self) -> list[T]:
        """Fetch all items and return as a list.

        Warning: This fetches all pages, which may be slow for large datasets.
        """
        result: list[T] = []
        async for item in self:
            result.append(item)
        return result
