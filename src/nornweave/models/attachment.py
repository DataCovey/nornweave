"""Attachment models for email attachments.

Attachment models for file handling in messages.
"""

import base64
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AttachmentDisposition(str, Enum):
    """Content disposition of attachment."""

    INLINE = "inline"
    ATTACHMENT = "attachment"


class AttachmentBase(BaseModel):
    """Base attachment fields shared across models."""

    filename: str | None = Field(None, description="Filename of attachment")
    content_type: str | None = Field(None, description="MIME content type")
    content_disposition: AttachmentDisposition | None = Field(
        None, description="Content disposition (inline or attachment)"
    )
    content_id: str | None = Field(
        None, description="Content-ID for inline attachments (cid: references)"
    )


class Attachment(AttachmentBase):
    """
    Full attachment model for storage and API responses.
    """

    attachment_id: str = Field(..., description="Unique ID of attachment")
    size: int = Field(..., description="Size of attachment in bytes")

    model_config = {"extra": "forbid"}


class AttachmentResponse(AttachmentBase):
    """
    Attachment response with download URL.

    API response model with download URL.
    """

    attachment_id: str
    size: int
    download_url: str = Field(..., description="URL to download the attachment")
    expires_at: datetime = Field(..., description="Time at which the download URL expires")

    model_config = {"extra": "forbid"}


class SendAttachment(BaseModel):
    """
    Attachment for outbound emails.

    Attachment payload for outbound messages.
    """

    filename: str | None = None
    content_type: str | None = None
    content_disposition: AttachmentDisposition | None = None
    content_id: str | None = Field(None, description="For inline attachments")
    content: str | None = Field(None, description="Base64 encoded content of attachment")
    url: str | None = Field(None, description="URL to the attachment (alternative to content)")

    model_config = {"extra": "forbid"}

    def get_content_bytes(self) -> bytes | None:
        """Decode base64 content to bytes."""
        if self.content:
            return base64.b64decode(self.content)
        return None


class AttachmentUpload(BaseModel):
    """Attachment upload for outbound emails via API."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1)
    content_base64: str = Field(..., description="Base64-encoded file content")
    disposition: AttachmentDisposition = Field(default=AttachmentDisposition.ATTACHMENT)
    content_id: str | None = Field(None, description="For inline attachments")

    model_config = {"extra": "forbid"}

    def get_content_bytes(self) -> bytes:
        """Decode base64 content to bytes."""
        return base64.b64decode(self.content_base64)

    @property
    def size_bytes(self) -> int:
        """Calculate size from base64 content."""
        return len(self.get_content_bytes())


class AttachmentCreate(BaseModel):
    """Internal model for creating attachments in storage."""

    message_id: str
    filename: str
    content_type: str
    size_bytes: int
    disposition: AttachmentDisposition = AttachmentDisposition.ATTACHMENT
    content_id: str | None = None
    content: bytes | None = None
    storage_path: str | None = None
    storage_backend: str | None = None

    model_config = {"extra": "forbid", "arbitrary_types_allowed": True}


class AttachmentMeta(BaseModel):
    """
    Lightweight attachment metadata for listing/display without content.

    Used in thread summaries and message listings.
    """

    attachment_id: str
    filename: str | None
    content_type: str | None
    size: int
    disposition: AttachmentDisposition = AttachmentDisposition.ATTACHMENT
    content_id: str | None = None

    model_config = {"extra": "forbid"}
