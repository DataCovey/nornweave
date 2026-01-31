"""Raw response wrapper for accessing HTTP response details."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    import httpx

T = TypeVar("T")


class RawResponse(Generic[T]):
    """Wrapper providing access to both parsed data and raw HTTP response details.

    Attributes:
        data: The parsed response object.
        status_code: HTTP status code.
        headers: HTTP response headers.
        raw_response: The underlying httpx.Response object.

    Example:
        response = client.inboxes.with_raw_response.create(...)
        print(response.headers)      # httpx.Headers
        print(response.status_code)  # 201
        print(response.data)         # Inbox object
    """

    def __init__(
        self,
        *,
        data: T,
        raw_response: httpx.Response,
    ) -> None:
        self._data = data
        self._raw_response = raw_response

    @property
    def data(self) -> T:
        """Get the parsed response data."""
        return self._data

    @property
    def status_code(self) -> int:
        """Get the HTTP status code."""
        return self._raw_response.status_code

    @property
    def headers(self) -> httpx.Headers:
        """Get the HTTP response headers."""
        return self._raw_response.headers

    @property
    def raw_response(self) -> httpx.Response:
        """Get the underlying httpx.Response object."""
        return self._raw_response

    def __repr__(self) -> str:
        return (
            f"RawResponse(status_code={self.status_code}, "
            f"data={self._data.__class__.__name__})"
        )
