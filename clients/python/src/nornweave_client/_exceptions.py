"""Exception classes for NornWeave API errors."""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    """Base exception for all NornWeave API errors.

    Attributes:
        status_code: HTTP status code from the response.
        body: Response body (parsed JSON if available).
        message: Human-readable error message.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.message = message

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(status_code={self.status_code}, message={self.message!r})"
        )


class NotFoundError(ApiError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found", *, body: Any = None) -> None:
        super().__init__(message, status_code=404, body=body)


class ValidationError(ApiError):
    """Raised when request validation fails (422)."""

    def __init__(self, message: str = "Validation error", *, body: Any = None) -> None:
        super().__init__(message, status_code=422, body=body)


class RateLimitError(ApiError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded", *, body: Any = None) -> None:
        super().__init__(message, status_code=429, body=body)


class ServerError(ApiError):
    """Raised when a server error occurs (5xx)."""

    def __init__(
        self,
        message: str = "Internal server error",
        *,
        status_code: int = 500,
        body: Any = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)


class ConnectionError(ApiError):
    """Raised when unable to connect to the server."""

    def __init__(self, message: str = "Failed to connect to server") -> None:
        super().__init__(message, status_code=0, body=None)


class TimeoutError(ApiError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message, status_code=0, body=None)


def raise_for_status(status_code: int, body: Any = None) -> None:
    """Raise an appropriate exception based on status code.

    Args:
        status_code: HTTP status code.
        body: Response body for error details.

    Raises:
        NotFoundError: For 404 responses.
        ValidationError: For 422 responses.
        RateLimitError: For 429 responses.
        ServerError: For 5xx responses.
        ApiError: For other 4xx responses.
    """
    if status_code < 400:
        return

    # Extract message from body if available
    message: str = "API error"
    if isinstance(body, dict):
        detail = body.get("detail", body.get("message"))
        message = str(detail) if detail is not None else str(body)
    elif body is not None:
        message = str(body)

    if status_code == 404:
        raise NotFoundError(message, body=body)
    elif status_code == 422:
        raise ValidationError(message, body=body)
    elif status_code == 429:
        raise RateLimitError(message, body=body)
    elif status_code >= 500:
        raise ServerError(message, status_code=status_code, body=body)
    else:
        raise ApiError(message, status_code=status_code, body=body)
