"""Message model."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageDirection(str, Enum):
    """Message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageBase(BaseModel):
    """Shared message fields."""

    thread_id: str = Field(..., description="Thread id")
    inbox_id: str = Field(..., description="Inbox id")
    provider_message_id: str | None = Field(None, description="Provider Message-ID header")
    direction: MessageDirection = Field(..., description="Inbound or outbound")
    content_raw: str = Field("", description="Original HTML/plain text")
    content_clean: str = Field("", description="LLM-ready Markdown")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Headers, token counts, sentiment, etc.",
    )


class MessageCreate(BaseModel):
    """Payload to send a message (outbound via API)."""

    inbox_id: str
    to: list[str] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., description="Markdown body")
    reply_to_thread_id: str | None = None

    model_config = {"extra": "forbid"}


class MessageInCreate(MessageBase):
    """Payload to create a message on ingestion (inbound webhook)."""

    model_config = {"extra": "forbid"}


class Message(MessageBase):
    """Message entity with id and timestamps."""

    id: str = Field(..., description="Unique message id")
    created_at: datetime | None = Field(None, description="Creation time")

    model_config = {"extra": "forbid"}
