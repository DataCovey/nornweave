"""API key authentication middleware for REST API routes."""

from __future__ import annotations

import hmac
import re
from typing import TYPE_CHECKING

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.types import ASGIApp

_BEARER_PREFIX = "bearer "
_SIGNED_ATTACHMENT_CONTENT_PATH = re.compile(r"^/v1/attachments/[^/]+/content$")


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Require API key auth for protected REST API routes.

    Enforcement rules:
    - If ``api_key`` is empty, auth is disabled.
    - Only ``/v1/*`` routes are protected.
    - ``/v1/attachments/{id}/content`` is excluded because it uses signed URL auth.
    - ``/webhooks/*`` remains unaffected because it is outside ``/v1/*``.
    """

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key.strip()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Validate API key before dispatching protected requests."""
        if not self._api_key:
            return await call_next(request)

        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            return await call_next(request)

        provided_key = _extract_api_key(request)
        if provided_key is None or not hmac.compare_digest(provided_key, self._api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid API key"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    @staticmethod
    def _is_public_path(path: str) -> bool:
        """Return whether path is exempt from API key auth."""
        if not path.startswith("/v1"):
            return True
        return _SIGNED_ATTACHMENT_CONTENT_PATH.fullmatch(path) is not None


def _extract_api_key(request: Request) -> str | None:
    """Extract API key from ``X-API-Key`` or ``Authorization: Bearer``."""
    x_api_key = request.headers.get("x-api-key")
    if x_api_key:
        token = x_api_key.strip()
        return token or None

    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith(_BEARER_PREFIX):
        token = authorization[len(_BEARER_PREFIX) :].strip()
        return token or None

    return None
