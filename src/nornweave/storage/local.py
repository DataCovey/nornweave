"""Local filesystem storage backend for attachments."""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

from nornweave.core.storage import AttachmentMetadata, AttachmentStorageBackend, StorageResult


class LocalFilesystemStorage(AttachmentStorageBackend):
    """Store attachments on local filesystem.

    Good for development and simple deployments.
    Files are organized by date: base_path/YYYY/MM/DD/attachment_id/filename
    """

    def __init__(
        self,
        base_path: str = "./data/attachments",
        serve_url_prefix: str = "/v1/attachments",
        signing_secret: str | None = None,
    ) -> None:
        """
        Initialize local storage.

        Args:
            base_path: Base directory for attachment storage
            serve_url_prefix: URL prefix for download URLs
            signing_secret: Secret for signing download URLs (uses app secret if not set)
        """
        self.base_path = Path(base_path)
        self.serve_url_prefix = serve_url_prefix.rstrip("/")
        self._signing_secret = signing_secret or "default-signing-secret"

    @property
    def backend_name(self) -> str:
        return "local"

    async def store(
        self,
        attachment_id: str,
        content: bytes,
        metadata: AttachmentMetadata,
    ) -> StorageResult:
        """Store attachment on local filesystem."""
        # Create date-based path
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        storage_key = f"{date_path}/{attachment_id}/{metadata.filename}"

        full_path = self.base_path / storage_key
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        full_path.write_bytes(content)

        return StorageResult(
            storage_key=storage_key,
            size_bytes=len(content),
            content_hash=self.compute_hash(content),
            backend=self.backend_name,
        )

    async def retrieve(self, storage_key: str) -> bytes:
        """Retrieve attachment from filesystem."""
        full_path = self.base_path / storage_key

        if not full_path.exists():
            raise FileNotFoundError(f"Attachment not found: {storage_key}")

        return full_path.read_bytes()

    async def delete(self, storage_key: str) -> bool:
        """Delete attachment from filesystem."""
        full_path = self.base_path / storage_key

        if not full_path.exists():
            return False

        full_path.unlink()

        # Try to clean up empty parent directories
        import contextlib

        with contextlib.suppress(OSError):
            full_path.parent.rmdir()

        return True

    async def get_download_url(
        self,
        storage_key: str,
        expires_in: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """Generate a signed download URL."""
        # Extract attachment_id from storage key
        parts = storage_key.split("/")
        attachment_id = parts[-2] if len(parts) >= 2 else storage_key

        # Create signed token
        expiry = int(time.time() + expires_in.total_seconds())
        signature = self._sign_url(attachment_id, expiry)

        # Build URL with query params
        params = {"token": signature, "expires": str(expiry)}
        if filename:
            params["filename"] = filename

        return f"{self.serve_url_prefix}/{attachment_id}/download?{urlencode(params)}"

    async def exists(self, storage_key: str) -> bool:
        """Check if attachment exists."""
        full_path = self.base_path / storage_key
        return full_path.exists()

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
