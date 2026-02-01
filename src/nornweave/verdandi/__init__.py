"""Verdandi (The Loom): Ingestion engine.

The ingestion engine handles:
- Email parsing from provider webhooks
- HTML sanitization and Markdown conversion
- Thread resolution (JWZ algorithm)
- Attachment processing
- Content extraction (quote/signature removal)
"""

from nornweave.verdandi.attachments import (
    parse_mime_attachments,
    validate_attachments,
)
from nornweave.verdandi.content import (
    extract_content,
    generate_preview,
    init_talon,
)
from nornweave.verdandi.headers import (
    build_reply_headers,
    generate_message_id,
    parse_email_address,
)
from nornweave.verdandi.threading import (
    normalize_subject,
    resolve_thread,
)

__all__ = [
    # Header utilities
    "build_reply_headers",
    # Content extraction
    "extract_content",
    "generate_message_id",
    "generate_preview",
    "init_talon",
    # Threading
    "normalize_subject",
    "parse_email_address",
    # Attachment handling
    "parse_mime_attachments",
    "resolve_thread",
    "validate_attachments",
]
