"""Pydantic models for NornWeave API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class RequestOptions(TypedDict, total=False):
    """Options that can be passed to any request."""

    timeout: float
    """Request timeout in seconds."""

    max_retries: int
    """Maximum number of retries for transient errors."""


# =============================================================================
# Health
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(extra="allow")

    status: str


# =============================================================================
# Inbox Models
# =============================================================================


class Inbox(BaseModel):
    """Inbox resource."""

    model_config = ConfigDict(extra="allow")

    id: str
    email_address: str
    name: str | None = None
    provider_config: dict[str, Any] = Field(default_factory=dict)


class InboxListResponse(BaseModel):
    """Paginated list of inboxes."""

    model_config = ConfigDict(extra="allow")

    items: list[Inbox]
    count: int


# =============================================================================
# Message Models
# =============================================================================


class Message(BaseModel):
    """Message resource."""

    model_config = ConfigDict(extra="allow")

    id: str
    thread_id: str
    inbox_id: str
    direction: str
    provider_message_id: str | None = None
    content_raw: str = ""
    content_clean: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class MessageListResponse(BaseModel):
    """Paginated list of messages."""

    model_config = ConfigDict(extra="allow")

    items: list[Message]
    count: int


class SendMessageRequest(BaseModel):
    """Request to send an outbound message."""

    model_config = ConfigDict(extra="allow")

    inbox_id: str
    to: list[str] = Field(min_length=1)
    subject: str = Field(min_length=1)
    body: str
    reply_to_thread_id: str | None = None


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    model_config = ConfigDict(extra="allow")

    id: str
    thread_id: str
    provider_message_id: str | None = None
    status: str


# =============================================================================
# Thread Models
# =============================================================================


class ThreadSummary(BaseModel):
    """Thread summary for list views."""

    model_config = ConfigDict(extra="allow")

    id: str
    inbox_id: str
    subject: str
    last_message_at: datetime | None = None
    participant_hash: str | None = None
    message_count: int = 0


class ThreadMessage(BaseModel):
    """Message within a thread, formatted for LLM consumption."""

    model_config = ConfigDict(extra="allow")

    role: str  # "user" for inbound, "assistant" for outbound
    author: str  # email address
    content: str  # clean markdown content
    timestamp: datetime | None = None


class ThreadDetail(BaseModel):
    """Thread with messages."""

    model_config = ConfigDict(extra="allow")

    id: str
    subject: str
    messages: list[ThreadMessage] = Field(default_factory=list)


class ThreadListResponse(BaseModel):
    """Paginated list of threads."""

    model_config = ConfigDict(extra="allow")

    items: list[ThreadSummary]
    count: int


# =============================================================================
# Search Models
# =============================================================================


class SearchRequest(BaseModel):
    """Search request parameters."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(min_length=1)
    inbox_id: str
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResultItem(BaseModel):
    """A single search result."""

    model_config = ConfigDict(extra="allow")

    id: str
    thread_id: str
    inbox_id: str
    direction: str
    content_clean: str
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response."""

    model_config = ConfigDict(extra="allow")

    items: list[SearchResultItem]
    count: int
    query: str
