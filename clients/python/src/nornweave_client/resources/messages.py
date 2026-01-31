"""Messages resource for managing email messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._raw_response import RawResponse
from nornweave_client._types import Message, RequestOptions, SendMessageResponse
from nornweave_client.resources._base import (
    AsyncBaseResource,
    SyncBaseResource,
    make_raw_response,
)

if TYPE_CHECKING:
    from nornweave_client._base_client import BaseAsyncClient, BaseSyncClient


class MessagesResource(SyncBaseResource):
    """Synchronous message operations."""

    def __init__(self, client: BaseSyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = MessagesWithRawResponse(self)

    def send(
        self,
        *,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SendMessageResponse:
        """Send an outbound message.

        Args:
            inbox_id: The inbox to send from.
            to: List of recipient email addresses.
            subject: Email subject.
            body: Message body in Markdown format.
            reply_to_thread_id: Optional thread ID to reply to.
            request_options: Optional request configuration.

        Returns:
            The send response with message ID and status.
        """
        payload: dict = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = self._request(
            "POST",
            "/v1/messages",
            json=payload,
            request_options=request_options,
        )
        return SendMessageResponse.model_validate(response.json())

    def list(
        self,
        *,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> SyncPager[Message]:
        """List messages for an inbox with pagination.

        Args:
            inbox_id: The inbox ID to list messages for.
            limit: Maximum number of items per page (default: 50).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            A paginator that yields Message objects.
        """

        def fetch_page(page_limit: int, page_offset: int) -> tuple[list[Message], int]:
            response = self._request(
                "GET",
                "/v1/messages",
                params={"inbox_id": inbox_id, "limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [Message.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return SyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    def get(
        self,
        message_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> Message:
        """Get a message by ID.

        Args:
            message_id: The message ID.
            request_options: Optional request configuration.

        Returns:
            The Message object.
        """
        response = self._request(
            "GET",
            f"/v1/messages/{message_id}",
            request_options=request_options,
        )
        return Message.model_validate(response.json())


class MessagesWithRawResponse:
    """Message operations that return raw responses."""

    def __init__(self, resource: MessagesResource) -> None:
        self._resource = resource

    def send(
        self,
        *,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[SendMessageResponse]:
        """Send an outbound message and return raw response."""
        payload: dict = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = self._resource._request(
            "POST",
            "/v1/messages",
            json=payload,
            request_options=request_options,
        )
        data = SendMessageResponse.model_validate(response.json())
        return make_raw_response(data, response)

    def get(
        self,
        message_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Message]:
        """Get a message by ID and return raw response."""
        response = self._resource._request(
            "GET",
            f"/v1/messages/{message_id}",
            request_options=request_options,
        )
        message = Message.model_validate(response.json())
        return make_raw_response(message, response)


class AsyncMessagesResource(AsyncBaseResource):
    """Asynchronous message operations."""

    def __init__(self, client: BaseAsyncClient) -> None:
        super().__init__(client)
        self.with_raw_response = AsyncMessagesWithRawResponse(self)

    async def send(
        self,
        *,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SendMessageResponse:
        """Send an outbound message.

        Args:
            inbox_id: The inbox to send from.
            to: List of recipient email addresses.
            subject: Email subject.
            body: Message body in Markdown format.
            reply_to_thread_id: Optional thread ID to reply to.
            request_options: Optional request configuration.

        Returns:
            The send response with message ID and status.
        """
        payload: dict = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = await self._request(
            "POST",
            "/v1/messages",
            json=payload,
            request_options=request_options,
        )
        return SendMessageResponse.model_validate(response.json())

    def list(
        self,
        *,
        inbox_id: str,
        limit: int = 50,
        offset: int = 0,
        request_options: RequestOptions | None = None,
    ) -> AsyncPager[Message]:
        """List messages for an inbox with pagination.

        Args:
            inbox_id: The inbox ID to list messages for.
            limit: Maximum number of items per page (default: 50).
            offset: Starting offset (default: 0).
            request_options: Optional request configuration.

        Returns:
            An async paginator that yields Message objects.
        """

        async def fetch_page(page_limit: int, page_offset: int) -> tuple[list[Message], int]:
            response = await self._request(
                "GET",
                "/v1/messages",
                params={"inbox_id": inbox_id, "limit": page_limit, "offset": page_offset},
                request_options=request_options,
            )
            data = response.json()
            items = [Message.model_validate(item) for item in data["items"]]
            return items, data["count"]

        return AsyncPager(fetch_page=fetch_page, limit=limit, offset=offset)

    async def get(
        self,
        message_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> Message:
        """Get a message by ID.

        Args:
            message_id: The message ID.
            request_options: Optional request configuration.

        Returns:
            The Message object.
        """
        response = await self._request(
            "GET",
            f"/v1/messages/{message_id}",
            request_options=request_options,
        )
        return Message.model_validate(response.json())


class AsyncMessagesWithRawResponse:
    """Async message operations that return raw responses."""

    def __init__(self, resource: AsyncMessagesResource) -> None:
        self._resource = resource

    async def send(
        self,
        *,
        inbox_id: str,
        to: list[str],
        subject: str,
        body: str,
        reply_to_thread_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[SendMessageResponse]:
        """Send an outbound message and return raw response."""
        payload: dict = {
            "inbox_id": inbox_id,
            "to": to,
            "subject": subject,
            "body": body,
        }
        if reply_to_thread_id:
            payload["reply_to_thread_id"] = reply_to_thread_id

        response = await self._resource._request(
            "POST",
            "/v1/messages",
            json=payload,
            request_options=request_options,
        )
        data = SendMessageResponse.model_validate(response.json())
        return make_raw_response(data, response)

    async def get(
        self,
        message_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> RawResponse[Message]:
        """Get a message by ID and return raw response."""
        response = await self._resource._request(
            "GET",
            f"/v1/messages/{message_id}",
            request_options=request_options,
        )
        message = Message.model_validate(response.json())
        return make_raw_response(message, response)
