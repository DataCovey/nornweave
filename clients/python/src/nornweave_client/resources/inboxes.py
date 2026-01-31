"""Inbox resource for managing email inboxes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._raw_response import RawResponse
from nornweave_client._types import Inbox, RequestOptions
from nornweave_client.resources._base import (
    AsyncBaseResource,
    SyncBaseResource,
    make_raw_response,
)

if TYPE_CHECKING:
    from nornweave_client._base_client import BaseAsyncClient, BaseSyncClient


class InboxesResource(SyncBaseResource):
    """Synchronous inbox operations."""

    def __init__(self, client: BaseSyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = InboxesWithRawResponse(self)

    def create(
        self,
        *,
        name: str,
        email_username: str,
        request_options: RequestOptions | None = None,
    ) -> Inbox:
        """Create a new inbox.

        Args:
            name: Display name for the inbox.
            email_username: Local part of the email address.
            request_options: Optional request configuration.

        Returns:
            The created Inbox object.
        """
        response = self._request(
            "POST",
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
            request_options=request_options,
        )
        return Inbox.model_validate(response.json())

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SyncPager[Inbox]:
        """List all inboxes with pagination.

        Args:
            limit: Maximum number of items per page (default: 50).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            A paginator that yields Inbox objects.
        """

        def fetch_page(page_limit: int, page_offset: int) -> tuple[list[Inbox], int]:
            response = self._request(
                "GET",
                "/v1/inboxes",
                params={"limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [Inbox.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return SyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    def get(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> Inbox:
        """Get an inbox by ID.

        Args:
            inbox_id: The inbox ID.
            request_options: Optional request configuration.

        Returns:
            The Inbox object.
        """
        response = self._request(
            "GET",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )
        return Inbox.model_validate(response.json())

    def delete(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        """Delete an inbox.

        Args:
            inbox_id: The inbox ID to delete.
            request_options: Optional request configuration.
        """
        self._request(
            "DELETE",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )


class InboxesWithRawResponse:
    """Inbox operations that return raw responses."""

    def __init__(self, resource: InboxesResource) -> None:
        self._resource = resource

    def create(
        self,
        *,
        name: str,
        email_username: str,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Inbox]:
        """Create a new inbox and return raw response."""
        response = self._resource._request(
            "POST",
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
            request_options=request_options,
        )
        inbox = Inbox.model_validate(response.json())
        return make_raw_response(inbox, response)

    def get(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Inbox]:
        """Get an inbox by ID and return raw response."""
        response = self._resource._request(
            "GET",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )
        inbox = Inbox.model_validate(response.json())
        return make_raw_response(inbox, response)


class AsyncInboxesResource(AsyncBaseResource):
    """Asynchronous inbox operations."""

    def __init__(self, client: BaseAsyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = AsyncInboxesWithRawResponse(self)

    async def create(
        self,
        *,
        name: str,
        email_username: str,
        request_options: RequestOptions | None = None,
    ) -> Inbox:
        """Create a new inbox.

        Args:
            name: Display name for the inbox.
            email_username: Local part of the email address.
            request_options: Optional request configuration.

        Returns:
            The created Inbox object.
        """
        response = await self._request(
            "POST",
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
            request_options=request_options,
        )
        return Inbox.model_validate(response.json())

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> AsyncPager[Inbox]:
        """List all inboxes with pagination.

        Args:
            limit: Maximum number of items per page (default: 50).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            An async paginator that yields Inbox objects.
        """

        async def fetch_page(page_limit: int, page_offset: int) -> tuple[list[Inbox], int]:
            response = await self._request(
                "GET",
                "/v1/inboxes",
                params={"limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [Inbox.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return AsyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    async def get(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> Inbox:
        """Get an inbox by ID.

        Args:
            inbox_id: The inbox ID.
            request_options: Optional request configuration.

        Returns:
            The Inbox object.
        """
        response = await self._request(
            "GET",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )
        return Inbox.model_validate(response.json())

    async def delete(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        """Delete an inbox.

        Args:
            inbox_id: The inbox ID to delete.
            request_options: Optional request configuration.
        """
        await self._request(
            "DELETE",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )


class AsyncInboxesWithRawResponse:
    """Async inbox operations that return raw responses."""

    def __init__(self, resource: AsyncInboxesResource) -> None:
        self._resource = resource

    async def create(
        self,
        *,
        name: str,
        email_username: str,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Inbox]:
        """Create a new inbox and return raw response."""
        response = await self._resource._request(
            "POST",
            "/v1/inboxes",
            json={"name": name, "email_username": email_username},
            request_options=request_options,
        )
        inbox = Inbox.model_validate(response.json())
        return make_raw_response(inbox, response)

    async def get(
        self,
        inbox_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Inbox]:
        """Get an inbox by ID and return raw response."""
        response = await self._resource._request(
            "GET",
            f"/v1/inboxes/{inbox_id}",
            request_options=request_options,
        )
        inbox = Inbox.model_validate(response.json())
        return make_raw_response(inbox, response)
