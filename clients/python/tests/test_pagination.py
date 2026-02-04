"""Tests for pagination utilities."""

from __future__ import annotations

import pytest

from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._types import Inbox


class TestSyncPager:
    """Test synchronous pagination."""

    def test_pager_iteration(self) -> None:
        """Test iterating over all items."""

        # Mock fetch_page based on offset
        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            if offset == 0:
                return [
                    Inbox(id="1", email_address="a@test.com"),
                    Inbox(id="2", email_address="b@test.com"),
                ], 3
            elif offset == 2:
                return [Inbox(id="3", email_address="c@test.com")], 3
            else:
                return [], 3

        pager = SyncPager(fetch_page=fetch_page, limit=2, offset=0)
        items = list(pager)

        assert len(items) == 3
        assert items[0].id == "1"
        assert items[1].id == "2"
        assert items[2].id == "3"

    def test_pager_single_page(self) -> None:
        """Test pagination with single page."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 1

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)
        items = list(pager)

        assert len(items) == 1

    def test_pager_empty_results(self) -> None:
        """Test pagination with no results."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [], 0

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)
        items = list(pager)

        assert len(items) == 0

    def test_pager_items_property(self) -> None:
        """Test accessing items property."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 1

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)

        # First access fetches
        items = pager.items
        assert len(items) == 1

        # Second access uses cached value
        items2 = pager.items
        assert items is items2

    def test_pager_count_property(self) -> None:
        """Test accessing count property."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 10

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)
        assert pager.count == 10

    def test_pager_len(self) -> None:
        """Test len() on pager."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 10

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)
        assert len(pager) == 10

    def test_pager_iter_pages(self) -> None:
        """Test iterating page by page."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            if offset == 0:
                return [
                    Inbox(id="1", email_address="a@test.com"),
                    Inbox(id="2", email_address="b@test.com"),
                ], 3
            elif offset == 2:
                return [Inbox(id="3", email_address="c@test.com")], 3
            else:
                return [], 3

        pager = SyncPager(fetch_page=fetch_page, limit=2, offset=0)
        pages = list(pager.iter_pages())

        assert len(pages) == 2
        assert len(pages[0].items) == 2
        assert len(pages[1].items) == 1
        assert pages[0].count == 3

    def test_pager_to_list(self) -> None:
        """Test converting to list."""

        def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 1

        pager = SyncPager(fetch_page=fetch_page, limit=50, offset=0)
        items = pager.to_list()

        assert isinstance(items, list)
        assert len(items) == 1


class TestAsyncPager:
    """Test asynchronous pagination."""

    @pytest.mark.asyncio
    async def test_async_pager_iteration(self) -> None:
        """Test async iterating over all items."""

        async def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            if offset == 0:
                return [
                    Inbox(id="1", email_address="a@test.com"),
                    Inbox(id="2", email_address="b@test.com"),
                ], 3
            elif offset == 2:
                return [Inbox(id="3", email_address="c@test.com")], 3
            else:
                return [], 3

        pager = AsyncPager(fetch_page=fetch_page, limit=2, offset=0)
        items = []
        async for item in pager:
            items.append(item)

        assert len(items) == 3
        assert items[0].id == "1"

    @pytest.mark.asyncio
    async def test_async_pager_to_list(self) -> None:
        """Test async converting to list."""

        async def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 1

        pager = AsyncPager(fetch_page=fetch_page, limit=50, offset=0)
        items = await pager.to_list()

        assert isinstance(items, list)
        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_async_pager_iter_pages(self) -> None:
        """Test async iterating page by page."""

        async def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            if offset == 0:
                return [Inbox(id="1", email_address="a@test.com")], 2
            elif offset == 1:
                return [Inbox(id="2", email_address="b@test.com")], 2
            else:
                return [], 2

        pager = AsyncPager(fetch_page=fetch_page, limit=1, offset=0)
        pages = []
        async for page in pager.iter_pages():
            pages.append(page)

        assert len(pages) == 2

    @pytest.mark.asyncio
    async def test_async_pager_get_items(self) -> None:
        """Test async get_items method."""

        async def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 1

        pager = AsyncPager(fetch_page=fetch_page, limit=50, offset=0)
        items = await pager.get_items()

        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_async_pager_get_count(self) -> None:
        """Test async get_count method."""

        async def fetch_page(limit: int, offset: int) -> tuple[list[Inbox], int]:
            return [Inbox(id="1", email_address="a@test.com")], 10

        pager = AsyncPager(fetch_page=fetch_page, limit=50, offset=0)
        count = await pager.get_count()

        assert count == 10
