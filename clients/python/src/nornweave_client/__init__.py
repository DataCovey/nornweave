"""NornWeave Python Client SDK.

A Python client library for the NornWeave Inbox-as-a-Service API.
"""

from nornweave_client._client import AsyncNornWeave, NornWeave
from nornweave_client._exceptions import (
    ApiError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from nornweave_client._pagination import AsyncPager, SyncPager
from nornweave_client._raw_response import RawResponse
from nornweave_client._types import (
    HealthResponse,
    Inbox,
    InboxListResponse,
    Message,
    MessageListResponse,
    RequestOptions,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SendMessageRequest,
    SendMessageResponse,
    ThreadDetail,
    ThreadListResponse,
    ThreadMessage,
    ThreadSummary,
)

__all__ = [
    # Clients
    "NornWeave",
    "AsyncNornWeave",
    # Exceptions
    "ApiError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # Pagination
    "SyncPager",
    "AsyncPager",
    # Raw response
    "RawResponse",
    # Types
    "RequestOptions",
    "HealthResponse",
    "Inbox",
    "InboxListResponse",
    "Message",
    "MessageListResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "ThreadSummary",
    "ThreadMessage",
    "ThreadDetail",
    "ThreadListResponse",
    "SearchRequest",
    "SearchResultItem",
    "SearchResponse",
]

__version__ = "0.1.0"
