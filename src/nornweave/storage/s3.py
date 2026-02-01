"""AWS S3 storage backend for attachments."""

from datetime import timedelta
from typing import Any, cast

from nornweave.core.storage import AttachmentMetadata, AttachmentStorageBackend, StorageResult


class S3Storage(AttachmentStorageBackend):
    """Store attachments in AWS S3.

    Recommended for production deployments.
    Uses presigned URLs for secure downloads.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "attachments",
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            prefix: Key prefix for attachments
            region: AWS region
            access_key: AWS access key (uses IAM role if not set)
            secret_key: AWS secret key (uses IAM role if not set)
            endpoint_url: Custom endpoint URL (for S3-compatible services)
        """
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._endpoint_url = endpoint_url
        self._client: Any = None

    @property
    def backend_name(self) -> str:
        return "s3"

    def _get_client(self) -> Any:
        """Get or create S3 client (lazy initialization)."""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                )

            client_kwargs: dict[str, Any] = {
                "service_name": "s3",
                "region_name": self.region,
            }

            if self._access_key and self._secret_key:
                client_kwargs["aws_access_key_id"] = self._access_key
                client_kwargs["aws_secret_access_key"] = self._secret_key

            if self._endpoint_url:
                client_kwargs["endpoint_url"] = self._endpoint_url

            self._client = boto3.client(**client_kwargs)

        return self._client

    def _build_key(self, attachment_id: str, filename: str) -> str:
        """Build S3 object key."""
        return f"{self.prefix}/{attachment_id}/{filename}"

    async def store(
        self,
        attachment_id: str,
        content: bytes,
        metadata: AttachmentMetadata,
    ) -> StorageResult:
        """Store attachment in S3."""
        client = self._get_client()
        storage_key = self._build_key(attachment_id, metadata.filename)

        # Upload with metadata
        client.put_object(
            Bucket=self.bucket,
            Key=storage_key,
            Body=content,
            ContentType=metadata.content_type,
            Metadata={
                "message_id": metadata.message_id,
                "content_disposition": metadata.content_disposition,
                "content_id": metadata.content_id or "",
            },
        )

        return StorageResult(
            storage_key=storage_key,
            size_bytes=len(content),
            content_hash=self.compute_hash(content),
            backend=self.backend_name,
        )

    async def retrieve(self, storage_key: str) -> bytes:
        """Retrieve attachment from S3."""
        client = self._get_client()

        try:
            response = client.get_object(Bucket=self.bucket, Key=storage_key)
            return cast("bytes", response["Body"].read())
        except client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"Attachment not found: {storage_key}")

    async def delete(self, storage_key: str) -> bool:
        """Delete attachment from S3."""
        client = self._get_client()

        try:
            # Check if exists first
            client.head_object(Bucket=self.bucket, Key=storage_key)
        except client.exceptions.ClientError:
            return False

        client.delete_object(Bucket=self.bucket, Key=storage_key)
        return True

    async def get_download_url(
        self,
        storage_key: str,
        expires_in: timedelta = timedelta(hours=1),
        filename: str | None = None,
    ) -> str:
        """Generate presigned download URL."""
        client = self._get_client()

        params: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": storage_key,
        }

        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        url = client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=int(expires_in.total_seconds()),
        )

        return cast("str", url)

    async def exists(self, storage_key: str) -> bool:
        """Check if attachment exists in S3."""
        client = self._get_client()

        try:
            client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except client.exceptions.ClientError:
            return False
