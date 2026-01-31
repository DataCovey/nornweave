"""SQLAlchemy ORM models for Urðr storage layer."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from nornweave.models.event import Event as PydanticEvent
from nornweave.models.event import EventType
from nornweave.models.inbox import Inbox as PydanticInbox
from nornweave.models.message import Message as PydanticMessage
from nornweave.models.message import MessageDirection
from nornweave.models.thread import Thread as PydanticThread


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class InboxORM(Base):
    """Inbox table."""

    __tablename__ = "inboxes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    email_address: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    threads: Mapped[list["ThreadORM"]] = relationship(
        "ThreadORM",
        back_populates="inbox",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list["MessageORM"]] = relationship(
        "MessageORM",
        back_populates="inbox",
        cascade="all, delete-orphan",
    )

    def to_pydantic(self) -> PydanticInbox:
        """Convert ORM model to Pydantic model."""
        return PydanticInbox(
            id=self.id,
            email_address=self.email_address,
            name=self.name,
            provider_config=self.provider_config or {},
        )

    @classmethod
    def from_pydantic(cls, inbox: PydanticInbox) -> "InboxORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=inbox.id,
            email_address=inbox.email_address,
            name=inbox.name,
            provider_config=inbox.provider_config,
        )


class ThreadORM(Base):
    """Thread table."""

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    inbox_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("inboxes.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    participant_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # Relationships
    inbox: Mapped["InboxORM"] = relationship("InboxORM", back_populates="threads")
    messages: Mapped[list["MessageORM"]] = relationship(
        "MessageORM",
        back_populates="thread",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        # list_threads_for_inbox: ORDER BY last_message_at DESC
        Index("ix_threads_inbox_last_message", "inbox_id", last_message_at.desc()),
        # get_thread_by_participant_hash: lookup by inbox + participant_hash
        Index("ix_threads_inbox_participant_hash", "inbox_id", "participant_hash"),
    )

    def to_pydantic(self) -> PydanticThread:
        """Convert ORM model to Pydantic model."""
        return PydanticThread(
            id=self.id,
            inbox_id=self.inbox_id,
            subject=self.subject,
            last_message_at=self.last_message_at,
            participant_hash=self.participant_hash,
        )

    @classmethod
    def from_pydantic(cls, thread: PydanticThread) -> "ThreadORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=thread.id,
            inbox_id=thread.inbox_id,
            subject=thread.subject,
            last_message_at=thread.last_message_at,
            participant_hash=thread.participant_hash,
        )


class MessageORM(Base):
    """Message table."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    inbox_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("inboxes.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content_raw: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_clean: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",  # Column name in DB is still "metadata"
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )

    # Relationships
    thread: Mapped["ThreadORM"] = relationship("ThreadORM", back_populates="messages")
    inbox: Mapped["InboxORM"] = relationship("InboxORM", back_populates="messages")

    # Indexes for performance
    __table_args__ = (
        # list_messages_for_thread: ORDER BY created_at
        Index("ix_messages_thread_created", "thread_id", "created_at"),
        # list_messages_for_inbox: ORDER BY created_at
        Index("ix_messages_inbox_created", "inbox_id", "created_at"),
        # search_messages: filter by inbox
        Index("ix_messages_inbox_id", "inbox_id"),
        # Deduplication: unique provider_message_id per inbox (optional)
        Index(
            "ix_messages_inbox_provider_msg",
            "inbox_id",
            "provider_message_id",
            unique=True,
            postgresql_where=("provider_message_id IS NOT NULL"),
        ),
    )

    def to_pydantic(self) -> PydanticMessage:
        """Convert ORM model to Pydantic model."""
        return PydanticMessage(
            id=self.id,
            thread_id=self.thread_id,
            inbox_id=self.inbox_id,
            provider_message_id=self.provider_message_id,
            direction=MessageDirection(self.direction),
            content_raw=self.content_raw,
            content_clean=self.content_clean,
            metadata=self.message_metadata or {},
            created_at=self.created_at,
        )

    @classmethod
    def from_pydantic(cls, message: PydanticMessage) -> "MessageORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=message.id,
            thread_id=message.thread_id,
            inbox_id=message.inbox_id,
            provider_message_id=message.provider_message_id,
            direction=message.direction.value,
            content_raw=message.content_raw,
            content_clean=message.content_clean,
            message_metadata=message.metadata,
            created_at=message.created_at,
        )


class EventORM(Base):
    """Event table (Phase 3 webhooks)."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Indexes for performance
    __table_args__ = (
        # list_events: ORDER BY created_at DESC
        Index("ix_events_created_at", created_at.desc()),
        # list_events(type=...): filter by type, ORDER BY created_at DESC
        Index("ix_events_type_created", "type", created_at.desc()),
    )

    def to_pydantic(self) -> PydanticEvent:
        """Convert ORM model to Pydantic model."""
        return PydanticEvent(
            id=self.id,
            type=EventType(self.type),
            created_at=self.created_at,
            payload=self.payload or {},
        )

    @classmethod
    def from_pydantic(cls, event: PydanticEvent) -> "EventORM":
        """Create ORM model from Pydantic model."""
        return cls(
            id=event.id,
            type=event.type.value,
            created_at=event.created_at,
            payload=event.payload,
        )
