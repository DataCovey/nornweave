"""Base resource class for API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

import httpx

from nornweave_client._raw_response import RawResponse
from nornweave_client._types import RequestOptions

if TYPE_CHECKING:
    from nornweave_client._base_client import BaseAsyncClient, BaseSyncClient

T = TypeVar("T")


class SyncBaseResource:
    """Base class for synchronous API resources."""

    def __init__(self, client: BaseSyncClient) -> None:
        self._client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> httpx.Response:
        """Make an HTTP request through the client."""
        return self._client.request(
            method,
            path,
            json=json,
            params=params,
            request_options=request_options,
        )


class AsyncBaseResource:
    """Base class for asynchronous API resources."""

    def __init__(self, client: BaseAsyncClient) -> None:
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request through the client."""
        return await self._client.request(
            method,
            path,
            json=json,
            params=params,
            request_options=request_options,
        )


class WithRawResponse(Generic[T]):
    """Wrapper that returns RawResponse objects instead of parsed models."""

    def __init__(self, resource: T) -> None:
        self._resource = resource


def make_raw_response(data: T, response: httpx.Response) -> RawResponse[T]:
    """Create a RawResponse wrapper."""
    return RawResponse(data=data, raw_response=response)
