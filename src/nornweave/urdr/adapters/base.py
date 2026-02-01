"""Base storage adapter with shared SQLAlchemy functionality."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import or_, select

from nornweave.core.interfaces import StorageInterface
from nornweave.urdr.orm import AttachmentORM, EventORM, InboxORM, MessageORM, ThreadORM

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from nornweave.models.event import Event, EventType
    from nornweave.models.inbox import Inbox
    from nornweave.models.message import Message
    from nornweave.models.thread import Thread


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class BaseSQLAlchemyAdapter(StorageInterface):
    """Base adapter with shared SQLAlchemy logic for Postgres and SQLite."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    # -------------------------------------------------------------------------
    # Inbox methods
    # -------------------------------------------------------------------------
    async def create_inbox(self, inbox: Inbox) -> Inbox:
        """Create an inbox."""
        orm_inbox = InboxORM.from_pydantic(inbox)
        if not orm_inbox.id:
            orm_inbox.id = generate_uuid()
        self._session.add(orm_inbox)
        await self._session.flush()
        await self._session.refresh(orm_inbox)
        return orm_inbox.to_pydantic()

    async def get_inbox(self, inbox_id: str) -> Inbox | None:
        """Get an inbox by id."""
        result = await self._session.get(InboxORM, inbox_id)
        return result.to_pydantic() if result else None

    async def get_inbox_by_email(self, email_address: str) -> Inbox | None:
        """Get an inbox by email address."""
        stmt = select(InboxORM).where(InboxORM.email_address == email_address)
        result = await self._session.execute(stmt)
        orm_inbox = result.scalar_one_or_none()
        return orm_inbox.to_pydantic() if orm_inbox else None

    async def delete_inbox(self, inbox_id: str) -> bool:
        """Delete an inbox."""
        orm_inbox = await self._session.get(InboxORM, inbox_id)
        if orm_inbox is None:
            return False
        await self._session.delete(orm_inbox)
        await self._session.flush()
        return True

    async def list_inboxes(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Inbox]:
        """List all inboxes."""
        stmt = select(InboxORM).order_by(InboxORM.email_address).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    # -------------------------------------------------------------------------
    # Thread methods
    # -------------------------------------------------------------------------
    async def create_thread(self, thread: Thread) -> Thread:
        """Create a thread."""
        orm_thread = ThreadORM.from_pydantic(thread)
        if not orm_thread.id:
            orm_thread.id = generate_uuid()
        self._session.add(orm_thread)
        await self._session.flush()
        await self._session.refresh(orm_thread)
        return orm_thread.to_pydantic()

    async def get_thread(self, thread_id: str) -> Thread | None:
        """Get a thread by id."""
        result = await self._session.get(ThreadORM, thread_id)
        return result.to_pydantic() if result else None

    async def get_thread_by_participant_hash(
        self,
        inbox_id: str,
        participant_hash: str,
    ) -> Thread | None:
        """Get a thread by inbox and participant hash."""
        stmt = select(ThreadORM).where(
            ThreadORM.inbox_id == inbox_id,
            ThreadORM.participant_hash == participant_hash,
        )
        result = await self._session.execute(stmt)
        orm_thread = result.scalar_one_or_none()
        return orm_thread.to_pydantic() if orm_thread else None

    async def update_thread(self, thread: Thread) -> Thread:
        """Update a thread."""
        orm_thread = await self._session.get(ThreadORM, thread.id)
        if orm_thread is None:
            raise ValueError(f"Thread {thread.id} not found")
        orm_thread.subject = thread.subject
        orm_thread.last_message_at = thread.last_message_at
        orm_thread.participant_hash = thread.participant_hash
        await self._session.flush()
        await self._session.refresh(orm_thread)
        return orm_thread.to_pydantic()

    async def list_threads_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Thread]:
        """List threads for an inbox, ordered by last_message_at DESC."""
        stmt = (
            select(ThreadORM)
            .where(ThreadORM.inbox_id == inbox_id)
            .order_by(ThreadORM.last_message_at.desc().nulls_last())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    # -------------------------------------------------------------------------
    # Message methods
    # -------------------------------------------------------------------------
    async def create_message(self, message: Message) -> Message:
        """Create a message."""
        orm_message = MessageORM.from_pydantic(message)
        if not orm_message.id:
            orm_message.id = generate_uuid()
        if orm_message.created_at is None:
            orm_message.created_at = datetime.now(UTC)
        self._session.add(orm_message)
        await self._session.flush()
        await self._session.refresh(orm_message)
        return orm_message.to_pydantic()

    async def get_message(self, message_id: str) -> Message | None:
        """Get a message by id."""
        result = await self._session.get(MessageORM, message_id)
        return result.to_pydantic() if result else None

    async def list_messages_for_inbox(
        self,
        inbox_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """List messages for an inbox, ordered by created_at."""
        stmt = (
            select(MessageORM)
            .where(MessageORM.inbox_id == inbox_id)
            .order_by(MessageORM.created_at)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    async def list_messages_for_thread(
        self,
        thread_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """List messages for a thread, ordered by created_at."""
        stmt = (
            select(MessageORM)
            .where(MessageORM.thread_id == thread_id)
            .order_by(MessageORM.created_at)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    async def search_messages(
        self,
        inbox_id: str,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Search messages by content. Override in subclass for dialect-specific search."""
        # Default implementation using LIKE (case-sensitive)
        # Subclasses can override for ILIKE (Postgres) or COLLATE NOCASE (SQLite)
        pattern = f"%{query}%"
        stmt = (
            select(MessageORM)
            .where(
                MessageORM.inbox_id == inbox_id,
                or_(
                    MessageORM.content_clean.like(pattern),
                    MessageORM.content_raw.like(pattern),
                ),
            )
            .order_by(MessageORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    # -------------------------------------------------------------------------
    # Event methods
    # -------------------------------------------------------------------------
    async def create_event(self, event: Event) -> Event:
        """Create an event."""
        orm_event = EventORM.from_pydantic(event)
        if not orm_event.id:
            orm_event.id = generate_uuid()
        if orm_event.created_at is None:
            orm_event.created_at = datetime.now(UTC)
        self._session.add(orm_event)
        await self._session.flush()
        await self._session.refresh(orm_event)
        return orm_event.to_pydantic()

    async def get_event(self, event_id: str) -> Event | None:
        """Get an event by id."""
        result = await self._session.get(EventORM, event_id)
        return result.to_pydantic() if result else None

    async def list_events(
        self,
        *,
        event_type: EventType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Event]:
        """List events, optionally filtered by type, ordered by created_at DESC."""
        stmt = select(EventORM)
        if event_type is not None:
            stmt = stmt.where(EventORM.type == event_type.value)
        stmt = stmt.order_by(EventORM.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [row.to_pydantic() for row in result.scalars().all()]

    # -------------------------------------------------------------------------
    # Attachment methods
    # -------------------------------------------------------------------------
    async def create_attachment(
        self,
        message_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        *,
        disposition: str = "attachment",
        content_id: str | None = None,
        storage_path: str | None = None,
        storage_backend: str | None = None,
        content_hash: str | None = None,
        content: bytes | None = None,
    ) -> str:
        """Create an attachment record."""
        attachment_id = generate_uuid()
        orm_attachment = AttachmentORM(
            id=attachment_id,
            message_id=message_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            disposition=disposition,
            content_id=content_id,
            storage_path=storage_path,
            storage_backend=storage_backend,
            content_hash=content_hash,
            content=content,
            created_at=datetime.now(UTC),
        )
        self._session.add(orm_attachment)
        await self._session.flush()
        return attachment_id

    async def get_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        """Get an attachment by id."""
        result = await self._session.get(AttachmentORM, attachment_id)
        if result is None:
            return None
        return {
            "id": result.id,
            "message_id": result.message_id,
            "filename": result.filename,
            "content_type": result.content_type,
            "size_bytes": result.size_bytes,
            "disposition": result.disposition,
            "content_id": result.content_id,
            "storage_path": result.storage_path,
            "storage_backend": result.storage_backend,
            "content_hash": result.content_hash,
            "content": result.content,
            "created_at": result.created_at,
        }

    async def list_attachments_for_message(self, message_id: str) -> list[dict[str, Any]]:
        """List attachments for a message."""
        stmt = select(AttachmentORM).where(AttachmentORM.message_id == message_id)
        result = await self._session.execute(stmt)
        return [
            {
                "id": row.id,
                "message_id": row.message_id,
                "filename": row.filename,
                "content_type": row.content_type,
                "size_bytes": row.size_bytes,
                "disposition": row.disposition,
                "content_id": row.content_id,
                "storage_path": row.storage_path,
                "storage_backend": row.storage_backend,
                "content_hash": row.content_hash,
                "created_at": row.created_at,
            }
            for row in result.scalars().all()
        ]

    async def delete_attachment(self, attachment_id: str) -> bool:
        """Delete an attachment."""
        orm_attachment = await self._session.get(AttachmentORM, attachment_id)
        if orm_attachment is None:
            return False
        await self._session.delete(orm_attachment)
        await self._session.flush()
        return True

    # -------------------------------------------------------------------------
    # Additional threading/message lookup methods
    # -------------------------------------------------------------------------
    async def get_message_by_provider_id(
        self,
        inbox_id: str,
        provider_message_id: str,
    ) -> Message | None:
        """Get a message by provider message ID (e.g., Mailgun ID, SES ID)."""
        stmt = select(MessageORM).where(
            MessageORM.inbox_id == inbox_id,
            MessageORM.provider_message_id == provider_message_id,
        )
        result = await self._session.execute(stmt)
        orm_message = result.scalar_one_or_none()
        return orm_message.to_pydantic() if orm_message else None

    async def get_thread_by_subject(
        self,
        inbox_id: str,
        normalized_subject: str,
        *,
        since: datetime | None = None,
    ) -> Thread | None:
        """Get a thread by normalized subject within a time window."""
        if since is None:
            since = datetime.now(UTC) - timedelta(days=7)

        stmt = (
            select(ThreadORM)
            .where(
                ThreadORM.inbox_id == inbox_id,
                ThreadORM.normalized_subject == normalized_subject,
                ThreadORM.last_message_at >= since,
            )
            .order_by(ThreadORM.last_message_at.desc())
        )
        result = await self._session.execute(stmt)
        orm_thread = result.scalar_one_or_none()
        return orm_thread.to_pydantic() if orm_thread else None
