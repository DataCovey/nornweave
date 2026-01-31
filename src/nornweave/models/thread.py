"""Thread model."""

from datetime import datetime
from pydantic import BaseModel, Field


class ThreadBase(BaseModel):
    """Shared thread fields."""

    inbox_id: str = Field(..., description="Owning inbox id")
    subject: str = Field(..., description="Thread subject")
    last_message_at: datetime | None = Field(None, description="Last message timestamp")
    participant_hash: str | None = Field(None, description="Hash of participants for grouping")


class Thread(ThreadBase):
    """Thread entity with id."""

    id: str = Field(..., description="Unique thread id")

    model_config = {"extra": "forbid"}


class ThreadSummary(BaseModel):
    """Summary for list views (e.g. recent threads)."""

    id: str
    subject: str
    last_message_at: datetime | None
    message_count: int = 0

    model_config = {"extra": "forbid"}
