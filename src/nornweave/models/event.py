"""Event model (for Phase 3 webhooks)."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event types for outbound webhooks."""

    THREAD_NEW_MESSAGE = "thread.new_message"
    INBOX_CREATED = "inbox.created"


class Event(BaseModel):
    """Event payload for webhook delivery."""

    id: str = Field(..., description="Event id")
    type: EventType = Field(..., description="Event type")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, str | int | bool | list | dict] = Field(
        default_factory=dict,
        description="Event payload",
    )

    model_config = {"extra": "forbid"}
