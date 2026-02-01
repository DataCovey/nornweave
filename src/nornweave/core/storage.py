"""Attachment storage backend interface and factory.

NornWeave supports multiple storage backends for attachments:
- Local filesystem (default, good for development)
- AWS S3 (production)
- Google Cloud Storage (production)
- Database blob (simple deployment)

Configure via environment variables:
    NORNWEAVE_ATTACHMENT_STORAGE_BACKEND=local|s3|gcs|database
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nornweave.core.config import Settings


@dataclass
class AttachmentMetadata:
    """Metadata stored alongside attachment content."""

    attachment_id: str
    message_id: str
    filename: str
    content_type: str
    content_disposition: str
    content_id: str | None = None


@dataclass
class StorageResult:
    """Result of storing an attachment."""

    storage_key: str
    size_bytes: int
    content_hash: str
    backend: str


class AttachmentStorageBackend(ABC):
    """Abstract interface for attachment storage backends."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of this backend."""
        ...

    @abstractmethod
    async def store(
        self,
        attachment_id: str,
        content: bytes,
        metadata: AttachmentMetadata,
    ) -> StorageResult:
        """
        Store attachment content.

        Args:
            attachment_id: Unique attachment ID
            content: Binary content to store
            metadata: Attachment metadata

        Returns:
            StorageResult with storage key and metadata
        """
        ...

    @abstractmethod
    async def retrieve(self, storage_key: str) -> bytes:
        """
        Retrieve attachment content by storage key.

        Args:
            storage_key: Key returned from store()

        Returns:
            Binary content

        Raises:
            FileNotFoundError: If attachment not found
        """
        ...

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """
        Delete attachment.

        Args:
            storage_key: Key returned from store()

        Returns:
            True if deleted, False if not found
        """
        ...

    @abstractmethod
    async def get_download_url(
        self,
        storage_key: str,
        expires_in: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """
        Generate a download URL for the attachment.

        Args:
            storage_key: Key returned from store()
            expires_in: How long the URL should be valid
            filename: Optional filename for Content-Disposition header

        Returns:
            URL string (signed for cloud, API path for local/db)
        """
        ...

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """
        Check if attachment exists in storage.

        Args:
            storage_key: Key returned from store()

        Returns:
            True if exists
        """
        ...

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()


def create_attachment_storage(settings: Settings) -> AttachmentStorageBackend:
    """
    Factory function to create configured storage backend.

    Args:
        settings: Application settings

    Returns:
        Configured AttachmentStorageBackend instance

    Raises:
        ValueError: If unknown backend specified
    """
    from nornweave.storage import (
        DatabaseBlobStorage,
        GCSStorage,
        LocalFilesystemStorage,
        S3Storage,
    )

    backend = getattr(settings, "attachment_storage_backend", "local").lower()

    if backend == "local":
        return LocalFilesystemStorage(
            base_path=getattr(settings, "attachment_local_path", "./data/attachments"),
            serve_url_prefix=getattr(settings, "attachment_serve_url_prefix", "/v1/attachments"),
        )
    elif backend == "s3":
        bucket = getattr(settings, "attachment_s3_bucket", None)
        if not bucket:
            raise ValueError("ATTACHMENT_S3_BUCKET required for S3 backend")
        return S3Storage(
            bucket=bucket,
            prefix=getattr(settings, "attachment_s3_prefix", "attachments"),
            region=getattr(settings, "attachment_s3_region", "us-east-1"),
            access_key=getattr(settings, "attachment_s3_access_key", None),
            secret_key=getattr(settings, "attachment_s3_secret_key", None),
        )
    elif backend == "gcs":
        bucket = getattr(settings, "attachment_gcs_bucket", None)
        if not bucket:
            raise ValueError("ATTACHMENT_GCS_BUCKET required for GCS backend")
        return GCSStorage(
            bucket=bucket,
            prefix=getattr(settings, "attachment_gcs_prefix", "attachments"),
            credentials_path=getattr(settings, "attachment_gcs_credentials_path", None),
        )
    elif backend == "database":
        return DatabaseBlobStorage()
    else:
        raise ValueError(f"Unknown storage backend: {backend}")
