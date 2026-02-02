"""Mailgun webhook handler."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from nornweave.adapters.mailgun import MailgunAdapter
from nornweave.core.interfaces import StorageInterface
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.verdandi.parser import html_to_markdown
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/mailgun", status_code=status.HTTP_200_OK)
async def mailgun_webhook(
    request: Request,
    storage: StorageInterface = Depends(get_storage),
) -> dict[str, str]:
    """Handle inbound email webhook from Mailgun.

    Mailgun sends inbound emails as multipart/form-data.
    This handler:
    1. Parses the webhook payload
    2. Finds the inbox by recipient email
    3. Creates or resolves a thread
    4. Stores the message
    """
    # Parse form data from Mailgun
    form_data = await request.form()
    payload = {key: value for key, value in form_data.items()}

    logger.info("Received Mailgun webhook for recipient: %s", payload.get("recipient"))
    logger.debug("Mailgun payload keys: %s", list(payload.keys()))

    # Parse the webhook payload using the Mailgun adapter
    adapter = MailgunAdapter(api_key="", domain="")  # Keys not needed for parsing
    try:
        inbound = adapter.parse_inbound_webhook(payload)
    except Exception as e:
        logger.error("Failed to parse Mailgun webhook: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse webhook payload: {e}",
        )

    # Find inbox by recipient email address
    inbox = await storage.get_inbox_by_email(inbound.to_address)
    if inbox is None:
        logger.warning("No inbox found for recipient: %s", inbound.to_address)
        # Return 200 to prevent Mailgun from retrying, but log the issue
        return {"status": "no_inbox"}

    logger.info("Found inbox %s for recipient %s", inbox.id, inbound.to_address)

    # Try to find existing thread by Message-ID references (for replies)
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

    # If no thread found, create a new one
    if thread_id:
        thread = await storage.get_thread(thread_id)
    else:
        # Create new thread
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

    # Convert HTML to Markdown for clean content
    content_clean = inbound.stripped_text or inbound.body_plain
    if inbound.stripped_html:
        content_clean = html_to_markdown(inbound.stripped_html)
    elif inbound.body_html:
        content_clean = html_to_markdown(inbound.body_html)

    # Create the message
    message = Message(
        message_id=str(uuid.uuid4()),
        thread_id=thread_id,
        inbox_id=inbox.id,
        provider_message_id=inbound.message_id,
        direction=MessageDirection.INBOUND,
        from_address=inbound.from_address,
        to=[inbound.to_address],
        subject=inbound.subject,
        text=inbound.body_plain,
        html=inbound.body_html,
        extracted_text=content_clean,
        extracted_html=inbound.stripped_html,
        in_reply_to=inbound.in_reply_to,
        references=inbound.references if inbound.references else None,
        headers=inbound.headers,
        timestamp=inbound.timestamp,
        created_at=datetime.now(UTC),
    )

    created_message = await storage.create_message(message)
    logger.info("Created message %s in thread %s", created_message.id, thread_id)

    # Update thread's last_message_at
    if thread:
        thread.last_message_at = created_message.created_at
        thread.received_timestamp = created_message.created_at
        await storage.update_thread(thread)

    return {"status": "received", "message_id": created_message.id, "thread_id": thread_id}
