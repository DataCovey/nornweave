"""Event model (for Phase 3 webhooks)."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for outbound webhooks."""

    THREAD_NEW_MESSAGE = "thread.new_message"
    INBOX_CREATED = "inbox.created"
    INBOX_DELETED = "inbox.deleted"
    MESSAGE_SENT = "message.sent"


class EventCreate(BaseModel):
    """Payload to create an event (id and created_at set by storage)."""

    type: EventType = Field(..., description="Event type")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )

    model_config = {"extra": "forbid"}


class Event(BaseModel):
    """Event entity with id and timestamp."""

    id: str = Field(..., description="Event id")
    type: EventType = Field(..., description="Event type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload",
    )

    model_config = {"extra": "forbid"}
