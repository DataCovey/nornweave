"""Attachment storage integration tests.

These tests verify attachment storage and retrieval with different
storage backends (database blob and filesystem).

Uses in-memory SQLite for fast testing, similar to e2e tests.
For PostgreSQL-specific tests, see the separate postgresql test suite.
"""

import base64
import tempfile
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nornweave.core.config import Settings, get_settings
from nornweave.core.storage import AttachmentMetadata
from nornweave.models.attachment import AttachmentDisposition
from nornweave.models.inbox import Inbox
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.storage import DatabaseBlobStorage, LocalFilesystemStorage
from nornweave.urdr.adapters.sqlite import SQLiteAdapter
from nornweave.urdr.orm import Base
from nornweave.yggdrasil.dependencies import get_storage

pytestmark = pytest.mark.integration


# -----------------------------------------------------------------------------
# Database fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    """Create an in-memory SQLite async engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Create an async session."""
    async with session_factory() as sess:
        yield sess


@pytest.fixture
async def storage(session: AsyncSession) -> SQLiteAdapter:
    """Get a storage adapter."""
    return SQLiteAdapter(session)


# -----------------------------------------------------------------------------
# Test data fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def test_content() -> bytes:
    """Sample binary content for testing."""
    return b"This is test attachment content with some binary data: \x00\x01\x02\xff"


@pytest.fixture
def test_content_base64(test_content: bytes) -> str:
    """Base64 encoded test content."""
    return base64.b64encode(test_content).decode()


@pytest.fixture
async def test_inbox(storage: SQLiteAdapter, session: AsyncSession) -> dict[str, Any]:
    """Create a test inbox."""
    inbox_model = Inbox(
        id=str(uuid.uuid4()),
        name="Test Inbox",
        email_address="test@example.com",
    )
    inbox = await storage.create_inbox(inbox_model)
    await session.commit()
    return {"id": inbox.id, "email_address": inbox.email_address}


@pytest.fixture
async def test_thread(
    storage: SQLiteAdapter, session: AsyncSession, test_inbox: dict[str, Any]
) -> dict[str, Any]:
    """Create a test thread."""
    thread_model = Thread(
        id=str(uuid.uuid4()),
        inbox_id=test_inbox["id"],
        subject="Test Thread",
        senders=["sender@example.com"],
        recipients=["test@example.com"],
        timestamp=datetime.now(UTC),
    )
    thread = await storage.create_thread(thread_model)
    await session.commit()
    return {"id": thread.id, "inbox_id": test_inbox["id"]}


@pytest.fixture
async def test_message(
    storage: SQLiteAdapter, session: AsyncSession, test_thread: dict[str, Any]
) -> dict[str, Any]:
    """Create a test message."""
    message_model = Message(
        id=str(uuid.uuid4()),
        thread_id=test_thread["id"],
        inbox_id=test_thread["inbox_id"],
        from_address="sender@example.com",
        to_addresses=["test@example.com"],
        subject="Test Message",
        text="Test message body",
        html="<p>Test message body</p>",
        direction=MessageDirection.INBOUND,
        timestamp=datetime.now(UTC),
    )
    message = await storage.create_message(message_model)
    await session.commit()
    return {
        "id": message.id,
        "thread_id": test_thread["id"],
        "inbox_id": test_thread["inbox_id"],
    }


# -----------------------------------------------------------------------------
# Database blob storage tests
# -----------------------------------------------------------------------------


class TestDatabaseBlobStorage:
    """Integration tests for database blob storage backend."""

    @pytest.mark.asyncio
    async def test_store_returns_correct_result(self, test_content: bytes) -> None:
        """Test that DatabaseBlobStorage.store returns correct StorageResult."""
        storage = DatabaseBlobStorage(signing_secret="test-secret")

        metadata = AttachmentMetadata(
            attachment_id="att-123",
            message_id="msg-456",
            filename="test.txt",
            content_type="text/plain",
            content_disposition="attachment",
        )

        result = await storage.store("att-123", test_content, metadata)

        assert result.storage_key == "att-123"
        assert result.size_bytes == len(test_content)
        assert result.backend == "database"
        assert result.content_hash is not None

    @pytest.mark.asyncio
    async def test_signed_url_generation(self) -> None:
        """Test that database backend generates valid signed URLs."""
        storage = DatabaseBlobStorage(
            serve_url_prefix="/v1/attachments",
            signing_secret="test-secret",
        )

        url = await storage.get_download_url("att-123", filename="test.txt")

        assert url.startswith("/v1/attachments/att-123/download?")
        assert "token=" in url
        assert "expires=" in url
        assert "filename=test.txt" in url

    @pytest.mark.asyncio
    async def test_signed_url_verification(self) -> None:
        """Test that signed URLs can be verified."""
        storage = DatabaseBlobStorage(signing_secret="test-secret")

        url = await storage.get_download_url("att-123")

        # Extract token and expires from URL
        import urllib.parse

        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        token = params["token"][0]
        expires = int(params["expires"][0])

        # Verify the signature
        assert storage.verify_signed_url("att-123", token, expires) is True

        # Invalid token should fail
        assert storage.verify_signed_url("att-123", "invalid-token", expires) is False

    @pytest.mark.asyncio
    async def test_attachment_stored_in_database(
        self,
        storage: SQLiteAdapter,
        session: AsyncSession,
        test_message: dict[str, Any],
        test_content: bytes,
    ) -> None:
        """Test that attachment content is stored in database content column."""
        attachment_id = await storage.create_attachment(
            message_id=test_message["id"],
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=len(test_content),
            disposition=AttachmentDisposition.ATTACHMENT.value,
            storage_backend="database",
            storage_path="att-id-123",
            content_hash="abc123",
            content=test_content,
        )
        await session.commit()

        # Retrieve and verify - get_attachment returns a dict
        retrieved = await storage.get_attachment(attachment_id)
        assert retrieved is not None
        assert retrieved["content"] == test_content
        assert retrieved["storage_backend"] == "database"


# -----------------------------------------------------------------------------
# Filesystem storage tests
# -----------------------------------------------------------------------------


class TestFilesystemStorage:
    """Integration tests for filesystem storage backend."""

    @pytest.mark.asyncio
    async def test_store_creates_file(self, test_content: bytes) -> None:
        """Test that LocalFilesystemStorage.store creates file on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFilesystemStorage(
                base_path=tmpdir,
                signing_secret="test-secret",
            )

            metadata = AttachmentMetadata(
                attachment_id="att-123",
                message_id="msg-456",
                filename="test.txt",
                content_type="text/plain",
                content_disposition="attachment",
            )

            result = await storage.store("att-123", test_content, metadata)

            assert result.backend == "local"
            assert result.size_bytes == len(test_content)

            # Verify file exists
            import os

            assert os.path.exists(os.path.join(tmpdir, result.storage_key))

    @pytest.mark.asyncio
    async def test_retrieve_returns_content(self, test_content: bytes) -> None:
        """Test that stored content can be retrieved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFilesystemStorage(base_path=tmpdir)

            metadata = AttachmentMetadata(
                attachment_id="att-123",
                message_id="msg-456",
                filename="test.txt",
                content_type="text/plain",
                content_disposition="attachment",
            )

            result = await storage.store("att-123", test_content, metadata)
            retrieved = await storage.retrieve(result.storage_key)

            assert retrieved == test_content

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, test_content: bytes) -> None:
        """Test that delete removes the file from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFilesystemStorage(base_path=tmpdir)

            metadata = AttachmentMetadata(
                attachment_id="att-123",
                message_id="msg-456",
                filename="test.txt",
                content_type="text/plain",
                content_disposition="attachment",
            )

            result = await storage.store("att-123", test_content, metadata)
            deleted = await storage.delete(result.storage_key)

            assert deleted is True
            assert await storage.exists(result.storage_key) is False

    @pytest.mark.asyncio
    async def test_signed_url_generation_filesystem(self) -> None:
        """Test that filesystem backend generates valid signed URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFilesystemStorage(
                base_path=tmpdir,
                serve_url_prefix="/v1/attachments",
                signing_secret="test-secret",
            )

            url = await storage.get_download_url("path/to/file.txt", filename="file.txt")

            assert "/v1/attachments/" in url
            assert "token=" in url
            assert "expires=" in url

    @pytest.mark.asyncio
    async def test_attachment_metadata_in_database(
        self,
        storage: SQLiteAdapter,
        session: AsyncSession,
        test_message: dict[str, Any],
        test_content: bytes,
    ) -> None:
        """Test that attachment metadata is stored in database with filesystem backend."""
        attachment_id = await storage.create_attachment(
            message_id=test_message["id"],
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=len(test_content),
            disposition=AttachmentDisposition.ATTACHMENT.value,
            storage_backend="local",
            storage_path="2024/01/01/test.pdf",
            content_hash="abc123",
            content=None,  # Content stored in filesystem, not database
        )
        await session.commit()

        # Retrieve and verify - get_attachment returns a dict
        retrieved = await storage.get_attachment(attachment_id)
        assert retrieved is not None
        assert retrieved["storage_backend"] == "local"
        assert retrieved["storage_path"] == "2024/01/01/test.pdf"
        assert retrieved["content"] is None  # Content not in DB for filesystem backend


# -----------------------------------------------------------------------------
# API integration tests
# -----------------------------------------------------------------------------


class TestAttachmentAPIIntegration:
    """Integration tests for attachment API endpoints."""

    @pytest.fixture
    def test_settings(self) -> Settings:
        """Create test settings."""
        return Settings(
            environment="test",
            db_driver="sqlite",
            email_provider="mailgun",
            email_domain="test.local",
            attachment_storage_backend="database",
        )

    @pytest.fixture
    async def app_with_data(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        test_settings: Settings,
        test_message: dict[str, Any],
        test_content: bytes,
        storage: SQLiteAdapter,
        session: AsyncSession,
    ) -> AsyncGenerator[tuple[Any, str]]:
        """Create app with test data and return (app, attachment_id)."""
        get_settings.cache_clear()

        from nornweave.yggdrasil.app import create_app

        app = create_app()

        # Create attachment - returns attachment_id string
        attachment_id = await storage.create_attachment(
            message_id=test_message["id"],
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=len(test_content),
            disposition=AttachmentDisposition.ATTACHMENT.value,
            storage_backend="database",
            storage_path=str(uuid.uuid4()),
            content_hash="testhash123",
            content=test_content,
        )
        await session.commit()

        # Override dependencies
        async def override_get_storage() -> AsyncGenerator[SQLiteAdapter]:
            async with session_factory() as sess:
                yield SQLiteAdapter(sess)
                await sess.commit()

        def override_get_settings() -> Settings:
            return test_settings

        app.dependency_overrides[get_storage] = override_get_storage
        app.dependency_overrides[get_settings] = override_get_settings

        yield app, attachment_id

    @pytest.mark.asyncio
    async def test_list_attachments_by_message(
        self,
        app_with_data: tuple[Any, str],
        test_message: dict[str, Any],
    ) -> None:
        """Test listing attachments by message_id."""
        app, attachment_id = app_with_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/v1/attachments?message_id={test_message['id']}"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["id"] == attachment_id
        assert data["items"][0]["filename"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_attachment_metadata(
        self,
        app_with_data: tuple[Any, str],
    ) -> None:
        """Test getting attachment metadata."""
        app, attachment_id = app_with_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/attachments/{attachment_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == attachment_id
        assert data["filename"] == "test.pdf"
        assert data["storage_backend"] == "database"
        assert "download_url" in data
