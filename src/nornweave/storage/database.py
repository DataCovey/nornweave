"""Database blob storage backend for attachments.

Stores attachment content directly in the database as BLOBs.
Suitable for simple deployments with small attachments.
Not recommended for large files or high-volume scenarios.
"""

import hashlib
import hmac
import time
from datetime import timedelta
from urllib.parse import urlencode

from nornweave.core.storage import AttachmentMetadata, AttachmentStorageBackend, StorageResult


class DatabaseBlobStorage(AttachmentStorageBackend):
    """Store attachments as BLOBs in database.

    This backend stores attachment content directly in the attachments
    table's 'content' column. Download URLs point to an API endpoint
    that retrieves content from the database.

    Good for:
    - Simple deployments without external storage
    - Small attachments
    - Development/testing

    Not recommended for:
    - Large files (>1MB)
    - High-volume production systems
    """

    def __init__(
        self,
        serve_url_prefix: str = "/v1/attachments",
        signing_secret: str | None = None,
    ) -> None:
        """
        Initialize database storage.

        Args:
            serve_url_prefix: URL prefix for download URLs
            signing_secret: Secret for signing download URLs
        """
        self.serve_url_prefix = serve_url_prefix.rstrip("/")
        self._signing_secret = signing_secret or "default-signing-secret"

    @property
    def backend_name(self) -> str:
        return "database"

    async def store(
        self,
        attachment_id: str,
        content: bytes,
        _metadata: AttachmentMetadata,
    ) -> StorageResult:
        """
        Store attachment in database.

        Note: The actual database write is handled by the storage layer
        that creates the AttachmentORM record. This method just returns
        the storage result with the attachment_id as the key.

        The caller is responsible for setting the 'content' column
        on the AttachmentORM model before committing.
        """
        return StorageResult(
            storage_key=attachment_id,  # Use attachment_id as the key
            size_bytes=len(content),
            content_hash=self.compute_hash(content),
            backend=self.backend_name,
        )

    async def retrieve(self, storage_key: str) -> bytes:
        """
        Retrieve attachment from database.

        Note: This method would normally query the database, but since
        we want to avoid direct database access in the storage backend,
        the actual retrieval should be done through the storage layer.

        This implementation is a placeholder that should be overridden
        by the application code that has access to the database session.
        """
        raise NotImplementedError(
            "Database storage retrieval should be done through the storage layer"
        )

    async def delete(self, storage_key: str) -> bool:
        """
        Delete attachment from database.

        Note: The actual database delete is handled by cascade when
        the message is deleted, or explicitly through the storage layer.
        """
        raise NotImplementedError(
            "Database storage deletion should be done through the storage layer"
        )

    async def get_download_url(
        self,
        storage_key: str,
        expires_in: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """Generate a signed download URL for API-based retrieval."""
        attachment_id = storage_key

        # Create signed token
        expiry = int(time.time() + expires_in.total_seconds())
        signature = self._sign_url(attachment_id, expiry)

        # Build URL with query params
        params = {"token": signature, "expires": str(expiry)}
        if filename:
            params["filename"] = filename

        return f"{self.serve_url_prefix}/{attachment_id}/download?{urlencode(params)}"

    async def exists(self, storage_key: str) -> bool:
        """
        Check if attachment exists in database.

        Note: Should be done through the storage layer with database access.
        """
        raise NotImplementedError(
            "Database storage existence check should be done through the storage layer"
        )

    def _sign_url(self, attachment_id: str, expiry: int) -> str:
        """Create HMAC signature for URL."""
        message = f"{attachment_id}:{expiry}"
        signature = hmac.new(
            self._signing_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:32]
        return signature

    def verify_signed_url(
        self,
        attachment_id: str,
        token: str,
        expires: int,
    ) -> bool:
        """
        Verify a signed download URL.

        Args:
            attachment_id: The attachment ID from the URL
            token: The signature token from the URL
            expires: The expiry timestamp from the URL

        Returns:
            True if signature is valid and not expired
        """
        # Check expiry
        if expires < time.time():
            return False

        # Verify signature
        expected = self._sign_url(attachment_id, expires)
        return hmac.compare_digest(token, expected)
