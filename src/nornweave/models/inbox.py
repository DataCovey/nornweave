"""Inbox model."""

from pydantic import BaseModel, Field


class InboxBase(BaseModel):
    """Shared inbox fields."""

    email_address: str = Field(..., description="Full email address for this inbox")
    name: str | None = Field(None, description="Human-readable name")
    provider_config: dict[str, str | int | bool] = Field(
        default_factory=dict,
        description="Provider-specific metadata (e.g. route id)",
    )


class InboxCreate(BaseModel):
    """Payload to create an inbox."""

    name: str = Field(..., min_length=1, description="Display name")
    email_username: str = Field(..., min_length=1, description="Local part (e.g. support)")

    model_config = {"extra": "forbid"}


class Inbox(InboxBase):
    """Inbox entity with id."""

    id: str = Field(..., description="Unique inbox id (e.g. UUID)")

    model_config = {"extra": "forbid"}
