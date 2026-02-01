"""Google Cloud Storage backend for attachments."""

from datetime import timedelta
from typing import Any, cast

from nornweave.core.storage import AttachmentMetadata, AttachmentStorageBackend, StorageResult


class GCSStorage(AttachmentStorageBackend):
    """Store attachments in Google Cloud Storage.

    Recommended for production deployments on GCP.
    Uses signed URLs for secure downloads.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "attachments",
        credentials_path: str | None = None,
        project: str | None = None,
    ) -> None:
        """
        Initialize GCS storage.

        Args:
            bucket: GCS bucket name
            prefix: Blob prefix for attachments
            credentials_path: Path to service account JSON (uses ADC if not set)
            project: GCP project ID
        """
        self.bucket_name = bucket
        self.prefix = prefix.strip("/")
        self._credentials_path = credentials_path
        self._project = project
        self._client: Any = None
        self._bucket: Any = None

    @property
    def backend_name(self) -> str:
        return "gcs"

    def _get_client(self) -> tuple[Any, Any]:
        """Get or create GCS client and bucket (lazy initialization)."""
        if self._client is None:
            try:
                from google.cloud import storage
            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCS storage. "
                    "Install with: pip install google-cloud-storage"
                )

            if self._credentials_path:
                self._client = storage.Client.from_service_account_json(
                    self._credentials_path,
                    project=self._project,
                )
            else:
                self._client = storage.Client(project=self._project)

            self._bucket = self._client.bucket(self.bucket_name)

        return self._client, self._bucket

    def _build_blob_name(self, attachment_id: str, filename: str) -> str:
        """Build GCS blob name."""
        return f"{self.prefix}/{attachment_id}/{filename}"

    async def store(
        self,
        attachment_id: str,
        content: bytes,
        metadata: AttachmentMetadata,
    ) -> StorageResult:
        """Store attachment in GCS."""
        _, bucket = self._get_client()
        storage_key = self._build_blob_name(attachment_id, metadata.filename)

        blob = bucket.blob(storage_key)
        blob.metadata = {
            "message_id": metadata.message_id,
            "content_disposition": metadata.content_disposition,
            "content_id": metadata.content_id or "",
        }

        blob.upload_from_string(
            content,
            content_type=metadata.content_type,
        )

        return StorageResult(
            storage_key=storage_key,
            size_bytes=len(content),
            content_hash=self.compute_hash(content),
            backend=self.backend_name,
        )

    async def retrieve(self, storage_key: str) -> bytes:
        """Retrieve attachment from GCS."""
        _, bucket = self._get_client()
        blob = bucket.blob(storage_key)

        if not blob.exists():
            raise FileNotFoundError(f"Attachment not found: {storage_key}")

        return cast("bytes", blob.download_as_bytes())

    async def delete(self, storage_key: str) -> bool:
        """Delete attachment from GCS."""
        _, bucket = self._get_client()
        blob = bucket.blob(storage_key)

        if not blob.exists():
            return False

        blob.delete()
        return True

    async def get_download_url(
        self,
        storage_key: str,
        expires_in: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """Generate signed download URL."""
        _, bucket = self._get_client()
        blob = bucket.blob(storage_key)

        kwargs: dict[str, Any] = {
            "expiration": expires_in,
        }

        if filename:
            kwargs["response_disposition"] = f'attachment; filename="{filename}"'

        url = blob.generate_signed_url(**kwargs)
        return cast("str", url)

    async def exists(self, storage_key: str) -> bool:
        """Check if attachment exists in GCS."""
        _, bucket = self._get_client()
        blob = bucket.blob(storage_key)
        return cast("bool", blob.exists())
