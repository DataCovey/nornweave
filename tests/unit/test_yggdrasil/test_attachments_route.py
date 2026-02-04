"""Tests for attachment API routes."""

import base64
from datetime import UTC, datetime

from nornweave.yggdrasil.routes.v1.attachments import (
    AttachmentBase64Response,
    AttachmentDetail,
    AttachmentListResponse,
    AttachmentMeta,
    _sign_url,
    _verify_signed_url,
)


class TestUrlSigning:
    """Tests for URL signing utilities."""

    def test_sign_url_generates_token(self) -> None:
        """Test that sign_url generates a token."""
        attachment_id = "test-123"
        expiry = 1234567890
        secret = "test-secret"

        token = _sign_url(attachment_id, expiry, secret)

        assert len(token) == 32
        assert isinstance(token, str)

    def test_sign_url_consistent(self) -> None:
        """Test that sign_url generates consistent tokens."""
        attachment_id = "test-123"
        expiry = 1234567890
        secret = "test-secret"

        token1 = _sign_url(attachment_id, expiry, secret)
        token2 = _sign_url(attachment_id, expiry, secret)

        assert token1 == token2

    def test_sign_url_different_for_different_ids(self) -> None:
        """Test that different attachment IDs produce different tokens."""
        expiry = 1234567890
        secret = "test-secret"

        token1 = _sign_url("id-1", expiry, secret)
        token2 = _sign_url("id-2", expiry, secret)

        assert token1 != token2

    def test_verify_signed_url_valid(self) -> None:
        """Test verification of valid signed URL."""
        attachment_id = "test-123"
        secret = "test-secret"
        # Use a future timestamp
        import time

        expiry = int(time.time()) + 3600
        token = _sign_url(attachment_id, expiry, secret)

        result = _verify_signed_url(attachment_id, token, expiry, secret)

        assert result is True

    def test_verify_signed_url_expired(self) -> None:
        """Test verification of expired signed URL."""
        attachment_id = "test-123"
        secret = "test-secret"
        # Use a past timestamp
        expiry = 1000000000  # Way in the past
        token = _sign_url(attachment_id, expiry, secret)

        result = _verify_signed_url(attachment_id, token, expiry, secret)

        assert result is False

    def test_verify_signed_url_invalid_token(self) -> None:
        """Test verification with invalid token."""
        attachment_id = "test-123"
        secret = "test-secret"
        import time

        expiry = int(time.time()) + 3600

        result = _verify_signed_url(attachment_id, "invalid-token", expiry, secret)

        assert result is False

    def test_verify_signed_url_no_signature(self) -> None:
        """Test verification without signature (direct access)."""
        result = _verify_signed_url("test-123", None, None, "secret")
        assert result is True


class TestAttachmentListResponse:
    """Tests for attachment list response model."""

    def test_attachment_meta_model(self) -> None:
        """Test AttachmentMeta model creation."""
        meta = AttachmentMeta(
            id="att-123",
            message_id="msg-456",
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=datetime.now(UTC),
        )

        assert meta.id == "att-123"
        assert meta.filename == "test.pdf"
        assert meta.size == 1024

    def test_attachment_list_response_model(self) -> None:
        """Test AttachmentListResponse model creation."""
        response = AttachmentListResponse(
            items=[
                AttachmentMeta(
                    id="att-1",
                    message_id="msg-1",
                    filename="file1.txt",
                    content_type="text/plain",
                    size=100,
                ),
                AttachmentMeta(
                    id="att-2",
                    message_id="msg-1",
                    filename="file2.txt",
                    content_type="text/plain",
                    size=200,
                ),
            ],
            count=2,
        )

        assert len(response.items) == 2
        assert response.count == 2


class TestAttachmentDetail:
    """Tests for attachment detail response model."""

    def test_attachment_detail_model(self) -> None:
        """Test AttachmentDetail model with all fields."""
        detail = AttachmentDetail(
            id="att-123",
            message_id="msg-456",
            filename="document.pdf",
            content_type="application/pdf",
            size=2048,
            disposition="attachment",
            content_id=None,
            storage_backend="s3",
            content_hash="abc123def456",
            created_at=datetime.now(UTC),
            download_url="https://s3.example.com/presigned-url",
        )

        assert detail.id == "att-123"
        assert detail.storage_backend == "s3"
        assert detail.download_url is not None


class TestAttachmentBase64Response:
    """Tests for base64 content response model."""

    def test_base64_response_model(self) -> None:
        """Test AttachmentBase64Response model."""
        content = base64.b64encode(b"Hello, World!").decode("ascii")
        response = AttachmentBase64Response(
            content=content,
            content_type="text/plain",
            filename="hello.txt",
        )

        assert response.content == content
        assert response.content_type == "text/plain"
        assert response.filename == "hello.txt"

        # Verify content can be decoded
        decoded = base64.b64decode(response.content)
        assert decoded == b"Hello, World!"
