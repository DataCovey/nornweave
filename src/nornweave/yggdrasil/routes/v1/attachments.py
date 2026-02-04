"""Attachment endpoints."""

import base64
import hashlib
import hmac
import time
from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic
from enum import Enum
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import StorageInterface  # noqa: TC001 - needed at runtime
from nornweave.core.storage import create_attachment_storage
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------
class AttachmentMeta(BaseModel):
    """Lightweight attachment metadata for listings."""

    id: str
    message_id: str
    filename: str
    content_type: str
    size: int
    created_at: datetime | None = None


class AttachmentDetail(BaseModel):
    """Full attachment metadata."""

    id: str
    message_id: str
    filename: str
    content_type: str
    size: int
    disposition: str | None = None
    content_id: str | None = None
    storage_backend: str | None = None
    content_hash: str | None = None
    created_at: datetime | None = None
    download_url: str | None = None


class AttachmentListResponse(BaseModel):
    """Response model for attachment list."""

    items: list[AttachmentMeta]
    count: int


class AttachmentBase64Response(BaseModel):
    """Response model for base64 attachment content."""

    content: str
    content_type: str
    filename: str


class ContentFormat(str, Enum):
    """Content format options."""

    BINARY = "binary"
    BASE64 = "base64"


# -----------------------------------------------------------------------------
# URL Signing Utilities
# -----------------------------------------------------------------------------
def _get_signing_secret(settings: Settings) -> str:
    """Get the signing secret for URL verification."""
    return settings.webhook_secret or "default-signing-secret"


def _sign_url(attachment_id: str, expiry: int, secret: str) -> str:
    """Create HMAC signature for URL."""
    message = f"{attachment_id}:{expiry}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    return signature


def _verify_signed_url(
    attachment_id: str,
    token: str | None,
    expires: int | None,
    secret: str,
) -> bool:
    """Verify a signed download URL."""
    if token is None or expires is None:
        return True  # No signature required (direct access)

    # Check expiry
    if expires < time.time():
        return False

    # Verify signature
    expected = _sign_url(attachment_id, expires, secret)
    return hmac.compare_digest(token, expected)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.get("/attachments", response_model=AttachmentListResponse)
async def list_attachments(
    message_id: str | None = Query(None, description="Filter by message ID"),
    thread_id: str | None = Query(None, description="Filter by thread ID"),
    inbox_id: str | None = Query(None, description="Filter by inbox ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    storage: StorageInterface = Depends(get_storage),
) -> AttachmentListResponse:
    """List attachments with exactly one filter (message_id, thread_id, or inbox_id)."""
    # Validate exactly one filter is provided
    filters = [f for f in [message_id, thread_id, inbox_id] if f is not None]
    if len(filters) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one filter required: message_id, thread_id, or inbox_id",
        )
    if len(filters) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only one filter allowed: message_id, thread_id, or inbox_id",
        )

    # Get attachments based on filter
    if message_id:
        # Verify message exists
        message = await storage.get_message(message_id)
        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found",
            )
        attachments = await storage.list_attachments_for_message(message_id)
    elif thread_id:
        # Verify thread exists
        thread = await storage.get_thread(thread_id)
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread {thread_id} not found",
            )
        attachments = await storage.list_attachments_for_thread(
            thread_id, limit=limit, offset=offset
        )
    else:  # inbox_id
        # Verify inbox exists
        assert inbox_id is not None  # Guaranteed by filter logic above
        inbox = await storage.get_inbox(inbox_id)
        if inbox is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inbox {inbox_id} not found",
            )
        attachments = await storage.list_attachments_for_inbox(
            inbox_id,
            limit=limit,
            offset=offset,
        )

    return AttachmentListResponse(
        items=[
            AttachmentMeta(
                id=a["id"],
                message_id=a["message_id"],
                filename=a["filename"],
                content_type=a["content_type"],
                size=a["size_bytes"],
                created_at=a.get("created_at"),
            )
            for a in attachments
        ],
        count=len(attachments),
    )


@router.get("/attachments/{attachment_id}", response_model=AttachmentDetail)
async def get_attachment(
    attachment_id: str,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> AttachmentDetail:
    """Get attachment metadata by ID."""
    attachment = await storage.get_attachment(attachment_id)
    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment {attachment_id} not found",
        )

    # Generate download URL
    download_url: str | None = None
    storage_backend_name = attachment.get("storage_backend")

    if storage_backend_name in ("s3", "gcs") and attachment.get("storage_path"):
        # Use cloud provider's presigned URL
        try:
            storage_backend = create_attachment_storage(settings)
            download_url = await storage_backend.get_download_url(
                attachment["storage_path"],
                filename=attachment["filename"],
            )
        except Exception:
            pass  # Fall back to no download URL
    elif attachment.get("storage_path") or storage_backend_name == "database":
        # Generate signed URL for local/database storage
        expiry = int(time.time() + 3600)  # 1 hour
        secret = _get_signing_secret(settings)
        token = _sign_url(attachment_id, expiry, secret)
        download_url = f"/v1/attachments/{attachment_id}/content?token={token}&expires={expiry}"

    return AttachmentDetail(
        id=attachment["id"],
        message_id=attachment["message_id"],
        filename=attachment["filename"],
        content_type=attachment["content_type"],
        size=attachment["size_bytes"],
        disposition=attachment.get("disposition"),
        content_id=attachment.get("content_id"),
        storage_backend=storage_backend_name,
        content_hash=attachment.get("content_hash"),
        created_at=attachment.get("created_at"),
        download_url=download_url,
    )


@router.get("/attachments/{attachment_id}/content", response_model=None)
async def get_attachment_content(
    attachment_id: str,
    response_format: Literal["binary", "base64"] = Query(
        "binary", alias="format", description="Response format"
    ),
    token: str | None = Query(None, description="Signed URL token"),
    expires: int | None = Query(None, description="Signed URL expiry timestamp"),
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> Response | AttachmentBase64Response:
    """Download attachment content.

    For local/database storage, requires valid signed URL (token + expires).
    For cloud storage (S3/GCS), use the presigned URL from attachment metadata.
    """
    # Get attachment metadata
    attachment = await storage.get_attachment(attachment_id)
    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment {attachment_id} not found",
        )

    storage_backend_name = attachment.get("storage_backend")

    # Verify signed URL for local/database backends
    if storage_backend_name in ("local", "database", None):
        secret = _get_signing_secret(settings)
        if not _verify_signed_url(attachment_id, token, expires, secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired download URL",
            )

    # Retrieve content
    content: bytes
    if storage_backend_name == "database":
        # Content stored in database
        if attachment.get("content") is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment content not found in database",
            )
        content = attachment["content"]
    elif attachment.get("storage_path"):
        # Content stored externally
        try:
            storage_backend = create_attachment_storage(settings)
            content = await storage_backend.retrieve(attachment["storage_path"])
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment content not found in storage",
            ) from exc
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment content location unknown",
        )

    # Return in requested format
    if response_format == "base64":
        return AttachmentBase64Response(
            content=base64.b64encode(content).decode("ascii"),
            content_type=attachment["content_type"],
            filename=attachment["filename"],
        )
    else:
        # Binary response
        return Response(
            content=content,
            media_type=attachment["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{attachment["filename"]}"',
                "Content-Length": str(len(content)),
            },
        )
