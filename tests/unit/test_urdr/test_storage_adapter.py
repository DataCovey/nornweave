"""Tests for URDR storage adapters (SQLite and Postgres via SQLite).

Uses in-memory SQLite for fast CI testing. Both adapters share the same
base implementation, so testing SQLiteAdapter covers the common code paths.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from nornweave.models.event import Event, EventType
from nornweave.models.inbox import Inbox
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.urdr.adapters.sqlite import SQLiteAdapter

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def storage(sqlite_session: AsyncSession) -> SQLiteAdapter:
    """Create a SQLiteAdapter with the test session."""
    return SQLiteAdapter(sqlite_session)


# =============================================================================
# Inbox Tests
# =============================================================================
class TestInboxOperations:
    """Tests for inbox CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_inbox(self, storage: SQLiteAdapter) -> None:
        """Test creating an inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="test@example.com",
            name="Test Inbox",
            provider_config={"route_id": "123"},
        )

        created = await storage.create_inbox(inbox)

        assert created.id == inbox.id
        assert created.email_address == "test@example.com"
        assert created.name == "Test Inbox"
        assert created.provider_config == {"route_id": "123"}

    @pytest.mark.asyncio
    async def test_get_inbox(self, storage: SQLiteAdapter) -> None:
        """Test getting an inbox by ID."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="get@example.com",
            name="Get Test",
            provider_config={},
        )
        await storage.create_inbox(inbox)

        result = await storage.get_inbox(inbox.id)

        assert result is not None
        assert result.id == inbox.id
        assert result.email_address == "get@example.com"

    @pytest.mark.asyncio
    async def test_get_inbox_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting a non-existent inbox returns None."""
        result = await storage.get_inbox("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_inbox_by_email(self, storage: SQLiteAdapter) -> None:
        """Test getting an inbox by email address."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="byemail@example.com",
            name="Email Test",
            provider_config={},
        )
        await storage.create_inbox(inbox)

        result = await storage.get_inbox_by_email("byemail@example.com")

        assert result is not None
        assert result.id == inbox.id

    @pytest.mark.asyncio
    async def test_get_inbox_by_email_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting by non-existent email returns None."""
        result = await storage.get_inbox_by_email("nonexistent@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_inbox(self, storage: SQLiteAdapter) -> None:
        """Test deleting an inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="delete@example.com",
            name="Delete Test",
            provider_config={},
        )
        await storage.create_inbox(inbox)

        deleted = await storage.delete_inbox(inbox.id)

        assert deleted is True
        assert await storage.get_inbox(inbox.id) is None

    @pytest.mark.asyncio
    async def test_delete_inbox_not_found(self, storage: SQLiteAdapter) -> None:
        """Test deleting a non-existent inbox returns False."""
        deleted = await storage.delete_inbox("non-existent-id")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_inboxes(self, storage: SQLiteAdapter) -> None:
        """Test listing inboxes."""
        # Create multiple inboxes
        for i in range(3):
            inbox = Inbox(
                id=str(uuid.uuid4()),
                email_address=f"list{i}@example.com",
                name=f"List Test {i}",
                provider_config={},
            )
            await storage.create_inbox(inbox)

        inboxes = await storage.list_inboxes(limit=10, offset=0)

        assert len(inboxes) >= 3

    @pytest.mark.asyncio
    async def test_list_inboxes_pagination(self, storage: SQLiteAdapter) -> None:
        """Test inbox list pagination."""
        # Create 5 inboxes
        for i in range(5):
            inbox = Inbox(
                id=str(uuid.uuid4()),
                email_address=f"page{i}@example.com",
                name=f"Page Test {i}",
                provider_config={},
            )
            await storage.create_inbox(inbox)

        # Get first 2
        page1 = await storage.list_inboxes(limit=2, offset=0)
        assert len(page1) == 2

        # Get next 2
        page2 = await storage.list_inboxes(limit=2, offset=2)
        assert len(page2) == 2

        # Verify different results
        assert page1[0].id != page2[0].id


# =============================================================================
# Thread Tests
# =============================================================================
class TestThreadOperations:
    """Tests for thread CRUD operations."""

    @pytest.fixture
    async def inbox(self, storage: SQLiteAdapter) -> Inbox:
        """Create a test inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="thread-test@example.com",
            name="Thread Test Inbox",
            provider_config={},
        )
        return await storage.create_inbox(inbox)

    @pytest.mark.asyncio
    async def test_create_thread(self, storage: SQLiteAdapter, inbox: Inbox) -> None:
        """Test creating a thread."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Test Subject",
            last_message_at=datetime.now(UTC),
            participant_hash="abc123",
        )

        created = await storage.create_thread(thread)

        assert created.id == thread.id
        assert created.inbox_id == inbox.id
        assert created.subject == "Test Subject"
        assert created.participant_hash == "abc123"

    @pytest.mark.asyncio
    async def test_get_thread(self, storage: SQLiteAdapter, inbox: Inbox) -> None:
        """Test getting a thread by ID."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Get Test",
            last_message_at=None,
            participant_hash=None,
        )
        await storage.create_thread(thread)

        result = await storage.get_thread(thread.id)

        assert result is not None
        assert result.id == thread.id

    @pytest.mark.asyncio
    async def test_get_thread_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting a non-existent thread returns None."""
        result = await storage.get_thread("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_thread_by_participant_hash(
        self, storage: SQLiteAdapter, inbox: Inbox
    ) -> None:
        """Test getting a thread by participant hash."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Participant Test",
            last_message_at=None,
            participant_hash="unique-hash-123",
        )
        await storage.create_thread(thread)

        result = await storage.get_thread_by_participant_hash(inbox.id, "unique-hash-123")

        assert result is not None
        assert result.id == thread.id

    @pytest.mark.asyncio
    async def test_get_thread_by_participant_hash_not_found(
        self, storage: SQLiteAdapter, inbox: Inbox
    ) -> None:
        """Test getting by non-existent participant hash returns None."""
        result = await storage.get_thread_by_participant_hash(inbox.id, "non-existent-hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_thread(self, storage: SQLiteAdapter, inbox: Inbox) -> None:
        """Test updating a thread."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Original Subject",
            last_message_at=None,
            participant_hash=None,
        )
        created = await storage.create_thread(thread)

        # Update the thread
        created.subject = "Updated Subject"
        created.last_message_at = datetime.now(UTC)
        updated = await storage.update_thread(created)

        assert updated.subject == "Updated Subject"
        assert updated.last_message_at is not None

    @pytest.mark.asyncio
    async def test_list_threads_for_inbox(self, storage: SQLiteAdapter, inbox: Inbox) -> None:
        """Test listing threads for an inbox, ordered by last_message_at DESC."""
        # Create threads with different timestamps
        now = datetime.now(UTC)
        for i in range(3):
            thread = Thread(
                id=str(uuid.uuid4()),
                inbox_id=inbox.id,
                subject=f"Thread {i}",
                last_message_at=now.replace(hour=i),
                participant_hash=None,
            )
            await storage.create_thread(thread)

        threads = await storage.list_threads_for_inbox(inbox.id, limit=10, offset=0)

        assert len(threads) >= 3
        # Should be ordered by last_message_at DESC
        if len(threads) >= 2 and threads[0].last_message_at and threads[1].last_message_at:
            assert threads[0].last_message_at >= threads[1].last_message_at


# =============================================================================
# Message Tests
# =============================================================================
class TestMessageOperations:
    """Tests for message CRUD operations."""

    @pytest.fixture
    async def inbox(self, storage: SQLiteAdapter) -> Inbox:
        """Create a test inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="message-test@example.com",
            name="Message Test Inbox",
            provider_config={},
        )
        return await storage.create_inbox(inbox)

    @pytest.fixture
    async def thread(self, storage: SQLiteAdapter, inbox: Inbox) -> Thread:
        """Create a test thread."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Message Test Thread",
            last_message_at=None,
            participant_hash=None,
        )
        return await storage.create_thread(thread)

    @pytest.mark.asyncio
    async def test_create_message(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test creating a message."""
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id="<msg123@provider.com>",
            direction=MessageDirection.INBOUND,
            content_raw="<p>Hello World</p>",
            content_clean="Hello World",
            metadata={"from": "sender@example.com"},
            created_at=datetime.now(UTC),
        )

        created = await storage.create_message(message)

        assert created.id == message.id
        assert created.thread_id == thread.id
        assert created.direction == MessageDirection.INBOUND
        assert created.content_clean == "Hello World"

    @pytest.mark.asyncio
    async def test_get_message(self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread) -> None:
        """Test getting a message by ID."""
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id=None,
            direction=MessageDirection.OUTBOUND,
            content_raw="Test",
            content_clean="Test",
            metadata={},
            created_at=datetime.now(UTC),
        )
        await storage.create_message(message)

        result = await storage.get_message(message.id)

        assert result is not None
        assert result.id == message.id

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting a non-existent message returns None."""
        result = await storage.get_message("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_messages_for_inbox(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test listing messages for an inbox."""
        for i in range(3):
            message = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                provider_message_id=None,
                direction=MessageDirection.INBOUND,
                content_raw=f"Message {i}",
                content_clean=f"Message {i}",
                metadata={},
                created_at=datetime.now(UTC),
            )
            await storage.create_message(message)

        messages = await storage.list_messages_for_inbox(inbox.id, limit=10, offset=0)

        assert len(messages) >= 3

    @pytest.mark.asyncio
    async def test_list_messages_for_thread(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test listing messages for a thread."""
        for i in range(3):
            message = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                provider_message_id=None,
                direction=MessageDirection.INBOUND,
                content_raw=f"Thread Message {i}",
                content_clean=f"Thread Message {i}",
                metadata={},
                created_at=datetime.now(UTC),
            )
            await storage.create_message(message)

        messages = await storage.list_messages_for_thread(thread.id, limit=10, offset=0)

        assert len(messages) >= 3

    @pytest.mark.asyncio
    async def test_search_messages_matching(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test searching messages with matching content."""
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id=None,
            direction=MessageDirection.INBOUND,
            content_raw="Important invoice attached",
            content_clean="Important invoice attached",
            metadata={},
            created_at=datetime.now(UTC),
        )
        await storage.create_message(message)

        results = await storage.search_messages(inbox.id, "invoice", limit=10, offset=0)

        assert len(results) >= 1
        assert any("invoice" in r.content_clean.lower() for r in results)

    @pytest.mark.asyncio
    async def test_search_messages_no_match(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test searching messages with no matching content."""
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id=None,
            direction=MessageDirection.INBOUND,
            content_raw="Hello there",
            content_clean="Hello there",
            metadata={},
            created_at=datetime.now(UTC),
        )
        await storage.create_message(message)

        results = await storage.search_messages(inbox.id, "xyznonexistent", limit=10, offset=0)

        assert len(results) == 0


# =============================================================================
# Event Tests
# =============================================================================
class TestEventOperations:
    """Tests for event CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_event(self, storage: SQLiteAdapter) -> None:
        """Test creating an event."""
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.INBOX_CREATED,
            created_at=datetime.now(UTC),
            payload={"inbox_id": "123", "email": "test@example.com"},
        )

        created = await storage.create_event(event)

        assert created.id == event.id
        assert created.type == EventType.INBOX_CREATED
        assert created.payload["inbox_id"] == "123"

    @pytest.mark.asyncio
    async def test_get_event(self, storage: SQLiteAdapter) -> None:
        """Test getting an event by ID."""
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.THREAD_NEW_MESSAGE,
            created_at=datetime.now(UTC),
            payload={},
        )
        await storage.create_event(event)

        result = await storage.get_event(event.id)

        assert result is not None
        assert result.id == event.id
        assert result.type == EventType.THREAD_NEW_MESSAGE

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting a non-existent event returns None."""
        result = await storage.get_event("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_events(self, storage: SQLiteAdapter) -> None:
        """Test listing events."""
        for i in range(3):
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.INBOX_CREATED,
                created_at=datetime.now(UTC),
                payload={"index": i},
            )
            await storage.create_event(event)

        events = await storage.list_events(limit=10, offset=0)

        assert len(events) >= 3

    @pytest.mark.asyncio
    async def test_list_events_filtered_by_type(self, storage: SQLiteAdapter) -> None:
        """Test listing events filtered by type."""
        # Create events of different types
        await storage.create_event(
            Event(
                id=str(uuid.uuid4()),
                type=EventType.INBOX_CREATED,
                created_at=datetime.now(UTC),
                payload={},
            )
        )
        await storage.create_event(
            Event(
                id=str(uuid.uuid4()),
                type=EventType.THREAD_NEW_MESSAGE,
                created_at=datetime.now(UTC),
                payload={},
            )
        )

        # Filter by type
        inbox_events = await storage.list_events(
            event_type=EventType.INBOX_CREATED, limit=10, offset=0
        )
        message_events = await storage.list_events(
            event_type=EventType.THREAD_NEW_MESSAGE, limit=10, offset=0
        )

        assert all(e.type == EventType.INBOX_CREATED for e in inbox_events)
        assert all(e.type == EventType.THREAD_NEW_MESSAGE for e in message_events)

    @pytest.mark.asyncio
    async def test_list_events_ordered_by_created_at_desc(self, storage: SQLiteAdapter) -> None:
        """Test events are ordered by created_at DESC."""
        now = datetime.now(UTC)
        for i in range(3):
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.INBOX_CREATED,
                created_at=now.replace(minute=i),
                payload={"minute": i},
            )
            await storage.create_event(event)

        events = await storage.list_events(limit=10, offset=0)

        # Should be ordered DESC (most recent first)
        if len(events) >= 2:
            assert events[0].created_at >= events[1].created_at


# =============================================================================
# Attachment Tests
# =============================================================================
class TestAttachmentOperations:
    """Tests for attachment CRUD operations."""

    @pytest.fixture
    async def inbox(self, storage: SQLiteAdapter) -> Inbox:
        """Create a test inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="attachment-test@example.com",
            name="Attachment Test Inbox",
            provider_config={},
        )
        return await storage.create_inbox(inbox)

    @pytest.fixture
    async def thread(self, storage: SQLiteAdapter, inbox: Inbox) -> Thread:
        """Create a test thread."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Attachment Test Thread",
            last_message_at=None,
            participant_hash=None,
        )
        return await storage.create_thread(thread)

    @pytest.fixture
    async def message(self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread) -> Message:
        """Create a test message."""
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id=None,
            direction=MessageDirection.INBOUND,
            content_raw="Test message with attachment",
            content_clean="Test message with attachment",
            metadata={},
            created_at=datetime.now(UTC),
        )
        return await storage.create_message(message)

    @pytest.mark.asyncio
    async def test_create_attachment(self, storage: SQLiteAdapter, message: Message) -> None:
        """Test creating an attachment."""
        attachment_id = await storage.create_attachment(
            message_id=message.id,
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            disposition="attachment",
            content_id=None,
            storage_path="/attachments/test.pdf",
            storage_backend="local",
            content_hash="abc123",
        )

        assert attachment_id is not None
        assert len(attachment_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_get_attachment(self, storage: SQLiteAdapter, message: Message) -> None:
        """Test getting an attachment by ID."""
        attachment_id = await storage.create_attachment(
            message_id=message.id,
            filename="get-test.txt",
            content_type="text/plain",
            size_bytes=512,
        )

        result = await storage.get_attachment(attachment_id)

        assert result is not None
        assert result["id"] == attachment_id
        assert result["filename"] == "get-test.txt"
        assert result["content_type"] == "text/plain"
        assert result["size_bytes"] == 512
        assert result["message_id"] == message.id

    @pytest.mark.asyncio
    async def test_get_attachment_not_found(self, storage: SQLiteAdapter) -> None:
        """Test getting a non-existent attachment returns None."""
        result = await storage.get_attachment("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_attachments_for_message(
        self, storage: SQLiteAdapter, message: Message
    ) -> None:
        """Test listing attachments for a message."""
        # Create multiple attachments
        for i in range(3):
            await storage.create_attachment(
                message_id=message.id,
                filename=f"file{i}.txt",
                content_type="text/plain",
                size_bytes=100 * (i + 1),
            )

        attachments = await storage.list_attachments_for_message(message.id)

        assert len(attachments) == 3
        assert all(a["message_id"] == message.id for a in attachments)

    @pytest.mark.asyncio
    async def test_list_attachments_for_thread(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test listing attachments for all messages in a thread."""
        # Create two messages in the thread
        for i in range(2):
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                provider_message_id=None,
                direction=MessageDirection.INBOUND,
                content_raw=f"Message {i}",
                content_clean=f"Message {i}",
                metadata={},
                created_at=datetime.now(UTC),
            )
            created_msg = await storage.create_message(msg)
            # Add attachment to each message
            await storage.create_attachment(
                message_id=created_msg.id,
                filename=f"thread-file{i}.pdf",
                content_type="application/pdf",
                size_bytes=200,
            )

        attachments = await storage.list_attachments_for_thread(thread.id)

        assert len(attachments) >= 2

    @pytest.mark.asyncio
    async def test_list_attachments_for_inbox(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test listing attachments for all messages in an inbox."""
        # Create message with attachment
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            provider_message_id=None,
            direction=MessageDirection.INBOUND,
            content_raw="Inbox message",
            content_clean="Inbox message",
            metadata={},
            created_at=datetime.now(UTC),
        )
        created_msg = await storage.create_message(msg)
        await storage.create_attachment(
            message_id=created_msg.id,
            filename="inbox-file.doc",
            content_type="application/msword",
            size_bytes=300,
        )

        attachments = await storage.list_attachments_for_inbox(inbox.id)

        assert len(attachments) >= 1
        assert attachments[0]["filename"] == "inbox-file.doc"

    @pytest.mark.asyncio
    async def test_delete_attachment(self, storage: SQLiteAdapter, message: Message) -> None:
        """Test deleting an attachment."""
        attachment_id = await storage.create_attachment(
            message_id=message.id,
            filename="delete-test.txt",
            content_type="text/plain",
            size_bytes=50,
        )

        deleted = await storage.delete_attachment(attachment_id)

        assert deleted is True
        assert await storage.get_attachment(attachment_id) is None

    @pytest.mark.asyncio
    async def test_delete_attachment_not_found(self, storage: SQLiteAdapter) -> None:
        """Test deleting a non-existent attachment returns False."""
        deleted = await storage.delete_attachment("non-existent-id")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_attachment_with_database_content(
        self, storage: SQLiteAdapter, message: Message
    ) -> None:
        """Test creating an attachment with content stored in database."""
        content = b"Hello, this is test content"
        attachment_id = await storage.create_attachment(
            message_id=message.id,
            filename="db-content.txt",
            content_type="text/plain",
            size_bytes=len(content),
            storage_backend="database",
            content=content,
        )

        result = await storage.get_attachment(attachment_id)

        assert result is not None
        assert result["content"] == content
        assert result["storage_backend"] == "database"


# =============================================================================
# Advanced Search Tests
# =============================================================================
class TestAdvancedMessageSearch:
    """Tests for search_messages_advanced method."""

    @pytest.fixture
    async def inbox(self, storage: SQLiteAdapter) -> Inbox:
        """Create a test inbox."""
        inbox = Inbox(
            id=str(uuid.uuid4()),
            email_address="search-test@example.com",
            name="Search Test Inbox",
            provider_config={},
        )
        return await storage.create_inbox(inbox)

    @pytest.fixture
    async def thread(self, storage: SQLiteAdapter, inbox: Inbox) -> Thread:
        """Create a test thread."""
        thread = Thread(
            id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject="Search Test Thread",
            last_message_at=None,
            participant_hash=None,
        )
        return await storage.create_thread(thread)

    @pytest.mark.asyncio
    async def test_search_by_inbox_id_only(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test searching messages by inbox_id only."""
        # Create messages
        for i in range(3):
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                direction=MessageDirection.INBOUND,
                subject=f"Message {i}",
                text=f"Body content {i}",
                from_address="sender@example.com",
                created_at=datetime.now(UTC),
            )
            await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(inbox_id=inbox.id)

        assert len(messages) == 3
        assert total == 3

    @pytest.mark.asyncio
    async def test_search_by_thread_id_only(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test searching messages by thread_id only."""
        # Create messages in the thread
        for i in range(2):
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                direction=MessageDirection.INBOUND,
                subject=f"Thread message {i}",
                created_at=datetime.now(UTC),
            )
            await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(thread_id=thread.id)

        assert len(messages) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_search_combined_inbox_and_thread(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test searching with both inbox_id and thread_id."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Combined filter test",
            created_at=datetime.now(UTC),
        )
        await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            thread_id=thread.id,
        )

        assert len(messages) == 1
        assert total == 1
        assert messages[0].subject == "Combined filter test"

    @pytest.mark.asyncio
    async def test_text_search_in_subject(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test text search matches subject."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Important invoice document",
            text="Generic body",
            created_at=datetime.now(UTC),
        )
        await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            query="invoice",
        )

        assert total >= 1
        assert any("invoice" in (m.subject or "").lower() for m in messages)

    @pytest.mark.asyncio
    async def test_text_search_in_body(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test text search matches body text."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Generic subject",
            text="This contains the special keyword contract",
            created_at=datetime.now(UTC),
        )
        await storage.create_message(msg)

        _messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            query="contract",
        )

        assert total >= 1

    @pytest.mark.asyncio
    async def test_text_search_in_from_address(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test text search matches from_address."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Email from special sender",
            from_address="vip-client@bigcorp.com",
            created_at=datetime.now(UTC),
        )
        await storage.create_message(msg)

        _messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            query="bigcorp",
        )

        assert total >= 1

    @pytest.mark.asyncio
    async def test_text_search_no_matches(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test text search with no matches returns empty."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Normal message",
            text="Normal content",
            created_at=datetime.now(UTC),
        )
        await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            query="nonexistent12345xyz",
        )

        assert total == 0
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_pagination_limit(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test pagination with limit."""
        # Create 5 messages
        for i in range(5):
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                direction=MessageDirection.INBOUND,
                subject=f"Pagination test {i}",
                created_at=datetime.now(UTC),
            )
            await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            limit=2,
        )

        assert len(messages) == 2
        assert total == 5  # Total count reflects all matches

    @pytest.mark.asyncio
    async def test_pagination_offset(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test pagination with offset."""
        # Create 3 messages
        for i in range(3):
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                inbox_id=inbox.id,
                direction=MessageDirection.INBOUND,
                subject=f"Offset test {i}",
                created_at=datetime.now(UTC),
            )
            await storage.create_message(msg)

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            limit=10,
            offset=2,
        )

        assert len(messages) == 1  # 3 total, offset 2 = 1 remaining
        assert total == 3

    @pytest.mark.asyncio
    async def test_text_search_in_attachment_filename(
        self, storage: SQLiteAdapter, inbox: Inbox, thread: Thread
    ) -> None:
        """Test text search matches attachment filenames."""
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            inbox_id=inbox.id,
            direction=MessageDirection.INBOUND,
            subject="Email with attachment",
            text="See attached file",
            created_at=datetime.now(UTC),
        )
        created_msg = await storage.create_message(msg)

        # Add attachment with searchable filename
        await storage.create_attachment(
            message_id=created_msg.id,
            filename="quarterly-report-2024.pdf",
            content_type="application/pdf",
            size_bytes=1000,
        )

        messages, total = await storage.search_messages_advanced(
            inbox_id=inbox.id,
            query="quarterly-report",
        )

        assert total >= 1
        assert any(m.id == created_msg.id for m in messages)
