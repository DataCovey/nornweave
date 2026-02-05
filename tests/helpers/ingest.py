"""Inbound message ingestion helper for E2E tests.

Simulates webhook processing by:
1. Resolving thread using verdandi's JWZ algorithm
2. Creating the message in storage
3. Updating thread's last_message_at

This helper bypasses the webhook routes (which are placeholders) and
directly exercises the ingestion logic.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.verdandi.content import extract_content, generate_preview
from nornweave.verdandi.summarize import generate_thread_summary
from nornweave.verdandi.threading import (
    compute_participant_hash,
    normalize_subject,
    resolve_thread,
)

if TYPE_CHECKING:
    from nornweave.core.interfaces import InboundMessage, StorageInterface


async def ingest_inbound_message(
    storage: StorageInterface,
    inbox_id: str,
    inbound: InboundMessage,
    *,
    create_attachments: bool = True,
) -> Message:
    """
    Ingest an inbound email message into storage.

    This function simulates what the webhook endpoint would do:
    1. Parse the inbound message (already done - we receive InboundMessage)
    2. Resolve thread using JWZ algorithm (References/In-Reply-To/subject)
    3. Create or update the thread
    4. Create the message record
    5. Optionally store attachments

    Args:
        storage: Storage interface for persistence
        inbox_id: ID of the inbox receiving the message
        inbound: Parsed inbound message
        create_attachments: Whether to create attachment records

    Returns:
        The created Message object
    """
    # Get inbox to verify it exists and get the email address
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise ValueError(f"Inbox {inbox_id} not found")

    # Extract clean content (remove quotes, signatures)
    content_result = extract_content(
        body_plain=inbound.body_plain,
        body_html=inbound.body_html,
    )
    content_clean = content_result.extracted_text if content_result else inbound.body_plain

    # Generate preview
    preview = generate_preview(content_clean or inbound.body_plain, max_length=150)

    # Resolve thread using verdandi threading algorithm
    thread_result = await resolve_thread(
        storage,
        inbox_id,
        message_id=inbound.message_id,
        in_reply_to=inbound.in_reply_to,
        references=inbound.references,
        subject=inbound.subject,
        timestamp=inbound.timestamp,
        from_address=inbound.from_address,
        to_addresses=[inbound.to_address, *inbound.cc_addresses],
    )

    # Compute participant hash for thread metadata
    participant_hash = compute_participant_hash(
        from_address=inbound.from_address,
        to_addresses=[inbound.to_address],
        cc_addresses=inbound.cc_addresses,
    )

    # Create or update thread
    if thread_result.is_new_thread:
        thread = Thread(
            thread_id=thread_result.thread_id,
            inbox_id=inbox_id,
            subject=inbound.subject,
            timestamp=inbound.timestamp,
            participant_hash=participant_hash,
            normalized_subject=normalize_subject(inbound.subject),
            senders=[inbound.from_address],
            recipients=[inbound.to_address, *inbound.cc_addresses],
            message_count=1,
            preview=preview,
        )
        await storage.create_thread(thread)
    else:
        # Update existing thread
        thread = await storage.get_thread(thread_result.thread_id)
        if thread is None:
            raise ValueError(f"Thread {thread_result.thread_id} not found")

        # Update thread metadata
        thread.timestamp = inbound.timestamp
        thread.message_count = (thread.message_count or 0) + 1
        thread.preview = preview

        # Add sender if not already in senders list
        if inbound.from_address not in (thread.senders or []):
            thread.senders = (thread.senders or []) + [inbound.from_address]

        await storage.update_thread(thread)

    # Build message metadata from headers
    metadata = dict(inbound.headers) if inbound.headers else {}
    metadata.update(
        {
            "from": inbound.from_address,
            "to": inbound.to_address,
            "subject": inbound.subject,
            "thread_matched_by": thread_result.matched_by,
        }
    )
    if inbound.cc_addresses:
        metadata["cc"] = ",".join(inbound.cc_addresses)
    if inbound.message_id:
        metadata["message_id"] = inbound.message_id
    if inbound.in_reply_to:
        metadata["in_reply_to"] = inbound.in_reply_to
    if inbound.references:
        metadata["references"] = " ".join(inbound.references)

    # Create message
    message_id = str(uuid.uuid4())
    message = Message(
        message_id=message_id,
        thread_id=thread_result.thread_id,
        inbox_id=inbox_id,
        direction=MessageDirection.INBOUND,
        provider_message_id=inbound.message_id,
        text=inbound.body_plain,
        html=inbound.body_html,
        extracted_text=content_clean,
        extracted_html=content_result.extracted_html if content_result else None,
        subject=inbound.subject,
        from_address=inbound.from_address,
        to=[inbound.to_address],
        cc=inbound.cc_addresses if inbound.cc_addresses else None,
        preview=preview,
        timestamp=inbound.timestamp,
        created_at=datetime.utcnow(),
        headers=metadata,
        size=len(inbound.body_plain.encode("utf-8")),
        in_reply_to=inbound.in_reply_to,
        references=inbound.references if inbound.references else None,
    )

    created_message = await storage.create_message(message)

    # Fire-and-forget thread summarization (non-blocking)
    await generate_thread_summary(storage, thread_result.thread_id)

    # Create attachment records if requested
    if create_attachments and inbound.attachments:
        for attachment in inbound.attachments:
            await storage.create_attachment(
                message_id=message_id,
                filename=attachment.filename,
                content_type=attachment.content_type,
                size_bytes=attachment.size_bytes,
                disposition=attachment.disposition.value,
                content_id=attachment.content_id,
            )

    return created_message


async def create_outbound_message(
    storage: StorageInterface,
    inbox_id: str,
    thread_id: str,
    *,
    to: list[str],
    subject: str,
    body: str,
    provider_message_id: str,
    in_reply_to: str | None = None,
    references: list[str] | None = None,
    cc: list[str] | None = None,
) -> Message:
    """
    Create an outbound message record in storage.

    This is a helper for creating outbound messages that the mock provider
    "sent" - useful for setting up test scenarios.

    Args:
        storage: Storage interface
        inbox_id: Inbox ID
        thread_id: Thread ID
        to: Recipients
        subject: Email subject
        body: Message body (markdown)
        provider_message_id: The Message-ID from the provider
        in_reply_to: Parent message ID for threading
        references: Reference chain for threading
        cc: CC recipients

    Returns:
        Created Message
    """
    # Get inbox for from_address
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise ValueError(f"Inbox {inbox_id} not found")

    # Generate preview
    preview = generate_preview(body, max_length=150)

    # Build metadata
    metadata = {
        "from": inbox.email_address,
        "to": ",".join(to),
        "subject": subject,
    }
    if cc:
        metadata["cc"] = ",".join(cc)
    if in_reply_to:
        metadata["in_reply_to"] = in_reply_to
    if references:
        metadata["references"] = " ".join(references)

    # Create message
    message_id = str(uuid.uuid4())
    message = Message(
        message_id=message_id,
        thread_id=thread_id,
        inbox_id=inbox_id,
        direction=MessageDirection.OUTBOUND,
        provider_message_id=provider_message_id,
        text=body,
        extracted_text=body,  # Outbound messages are already clean
        subject=subject,
        from_address=inbox.email_address,
        to=to,
        cc=cc,
        preview=preview,
        timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
        headers=metadata,
        size=len(body.encode("utf-8")),
        in_reply_to=in_reply_to,
        references=references,
    )

    created_message = await storage.create_message(message)

    # Update thread
    thread = await storage.get_thread(thread_id)
    if thread:
        thread.timestamp = message.timestamp
        thread.message_count = (thread.message_count or 0) + 1
        thread.preview = preview
        await storage.update_thread(thread)

    # Fire-and-forget thread summarization (non-blocking)
    await generate_thread_summary(storage, thread_id)

    return created_message
