"""Shared ingestion pipeline for all email providers.

Extracts the common ingestion logic (inbox lookup, dedup, threading, message
creation, attachment storage, thread update, summarization) into a single
reusable function used by both webhook handlers and the IMAP poller.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from nornweave.core.storage import AttachmentMetadata, create_attachment_storage
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.verdandi.parser import html_to_markdown
from nornweave.verdandi.summarize import generate_thread_summary

if TYPE_CHECKING:
    from nornweave.core.config import Settings
    from nornweave.core.interfaces import InboundMessage, StorageInterface

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Result of the ingestion pipeline."""

    status: Literal["received", "duplicate", "no_inbox"]
    message_id: str = ""
    thread_id: str = ""
    warning: str | None = None
    extra: dict[str, str] = field(default_factory=dict)


async def ingest_message(
    inbound: InboundMessage,
    storage: StorageInterface,
    settings: Settings,
) -> IngestResult:
    """Shared ingestion: find inbox -> dedup -> thread -> parse -> store -> summarize.

    This is the single entry point for all inbound email processing, regardless
    of whether the email arrived via webhook (Mailgun, SES, SendGrid, Resend)
    or via IMAP polling.

    Args:
        inbound: Standardized inbound email message.
        storage: Storage adapter for database operations.
        settings: Application settings.

    Returns:
        IngestResult with status, message_id, and thread_id.
    """
    # -------------------------------------------------------------------------
    # 1. Find inbox by recipient email address
    # -------------------------------------------------------------------------
    inbox = await storage.get_inbox_by_email(inbound.to_address)
    if inbox is None:
        logger.warning("No inbox found for recipient: %s", inbound.to_address)
        return IngestResult(status="no_inbox")

    logger.info("Found inbox %s for recipient %s", inbox.id, inbound.to_address)

    # -------------------------------------------------------------------------
    # 2. Duplicate detection (idempotency)
    # -------------------------------------------------------------------------
    if inbound.message_id:
        existing_msg = await storage.get_message_by_provider_id(inbox.id, inbound.message_id)
        if existing_msg:
            logger.info(
                "Duplicate detected: message %s already exists for provider_message_id %s",
                existing_msg.id,
                inbound.message_id,
            )
            return IngestResult(
                status="duplicate",
                message_id=existing_msg.id,
                thread_id=existing_msg.thread_id,
            )

    # -------------------------------------------------------------------------
    # 3. Thread resolution (In-Reply-To -> References -> new thread)
    # -------------------------------------------------------------------------
    thread_id: str | None = None

    # Check In-Reply-To header first
    if inbound.in_reply_to:
        existing_msg = await storage.get_message_by_provider_id(inbox.id, inbound.in_reply_to)
        if existing_msg:
            thread_id = existing_msg.thread_id
            logger.debug("Found thread via In-Reply-To: %s", thread_id)

    # Check References header
    if not thread_id and inbound.references:
        for ref in inbound.references:
            existing_msg = await storage.get_message_by_provider_id(inbox.id, ref)
            if existing_msg:
                thread_id = existing_msg.thread_id
                logger.debug("Found thread via References: %s", thread_id)
                break

    # Create or retrieve thread
    if thread_id:
        thread = await storage.get_thread(thread_id)
    else:
        new_thread = Thread(
            thread_id=str(uuid.uuid4()),
            inbox_id=inbox.id,
            subject=inbound.subject,
            timestamp=inbound.timestamp,
            senders=[inbound.from_address],
            recipients=[inbound.to_address],
        )
        thread = await storage.create_thread(new_thread)
        thread_id = thread.id
        logger.info("Created new thread %s for subject: %s", thread_id, inbound.subject)

    # -------------------------------------------------------------------------
    # 4. Content extraction (HTML -> Markdown)
    # -------------------------------------------------------------------------
    content_clean = inbound.stripped_text or inbound.body_plain
    extracted_html = inbound.stripped_html or inbound.body_html
    if inbound.stripped_html:
        content_clean = html_to_markdown(inbound.stripped_html)
    elif inbound.body_html:
        content_clean = html_to_markdown(inbound.body_html)

    # -------------------------------------------------------------------------
    # 5. Create message
    # -------------------------------------------------------------------------
    message = Message(
        message_id=str(uuid.uuid4()),
        thread_id=thread_id,
        inbox_id=inbox.id,
        provider_message_id=inbound.message_id,
        direction=MessageDirection.INBOUND,
        from_address=inbound.from_address,
        to=[inbound.to_address, *inbound.cc_addresses],
        subject=inbound.subject,
        text=inbound.body_plain,
        html=inbound.body_html,
        extracted_text=content_clean,
        extracted_html=extracted_html,
        in_reply_to=inbound.in_reply_to,
        references=inbound.references if inbound.references else None,
        headers=inbound.headers,
        timestamp=inbound.timestamp,
        created_at=datetime.now(UTC),
    )

    created_message = await storage.create_message(message)
    logger.info("Created message %s in thread %s", created_message.id, thread_id)

    # -------------------------------------------------------------------------
    # 6. Store attachments
    # -------------------------------------------------------------------------
    if inbound.attachments:
        storage_backend = create_attachment_storage(settings)

        for att in inbound.attachments:
            if att.content and att.size_bytes > 0:
                try:
                    attachment_id = str(uuid.uuid4())

                    metadata = AttachmentMetadata(
                        attachment_id=attachment_id,
                        message_id=created_message.id,
                        filename=att.filename,
                        content_type=att.content_type,
                        content_disposition=att.disposition.value,
                        content_id=att.content_id,
                    )

                    storage_result = await storage_backend.store(
                        attachment_id=attachment_id,
                        content=att.content,
                        metadata=metadata,
                    )

                    await storage.create_attachment(
                        message_id=created_message.id,
                        filename=att.filename,
                        content_type=att.content_type,
                        size_bytes=storage_result.size_bytes,
                        disposition=att.disposition.value,
                        content_id=att.content_id,
                        storage_path=storage_result.storage_key,
                        storage_backend=storage_result.backend,
                        content_hash=storage_result.content_hash,
                        content=att.content if storage_result.backend == "database" else None,
                    )
                    logger.info(
                        "Stored attachment %s (%s, %d bytes) via %s backend",
                        att.filename,
                        att.content_type,
                        storage_result.size_bytes,
                        storage_result.backend,
                    )
                except (ValueError, RuntimeError) as e:
                    logger.warning("Failed to store attachment %s: %s", att.filename, e)

    # -------------------------------------------------------------------------
    # 7. Update thread and trigger summarization
    # -------------------------------------------------------------------------
    if thread:
        thread.last_message_at = created_message.created_at
        thread.received_timestamp = created_message.created_at
        await storage.update_thread(thread)

    if thread_id:
        await generate_thread_summary(storage, thread_id)

    return IngestResult(
        status="received",
        message_id=created_message.id,
        thread_id=thread_id or "",
    )
