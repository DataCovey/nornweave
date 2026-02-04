"""Resend webhook handler."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from nornweave.adapters.resend import ResendAdapter, ResendWebhookError
from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (
    StorageInterface,  # noqa: TC001 - needed at runtime for FastAPI
)
from nornweave.core.storage import AttachmentMetadata, create_attachment_storage
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.verdandi.parser import html_to_markdown
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()
logger = logging.getLogger(__name__)


# Event types for email delivery tracking
DELIVERY_EVENT_TYPES = frozenset(
    {
        "email.sent",
        "email.delivered",
        "email.bounced",
        "email.complained",
        "email.failed",
        "email.opened",
        "email.clicked",
        "email.delivery_delayed",
        "email.scheduled",
        "email.suppressed",
    }
)


def _get_resend_adapter(settings: Settings) -> ResendAdapter:
    """Create ResendAdapter with settings."""
    return ResendAdapter(
        api_key=settings.resend_api_key,
        webhook_secret=settings.resend_webhook_secret,
    )


@router.post("/resend", status_code=status.HTTP_200_OK)
async def resend_webhook(
    request: Request,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Handle webhook from Resend.

    Resend sends webhooks as JSON with Svix signature headers.
    This handler:
    1. Verifies the webhook signature (if secret is configured)
    2. Routes to appropriate handler based on event type
    3. For email.received: fetches full content, creates/resolves thread, stores message
    4. For delivery events: logs the event for tracking

    Supported event types:
    - email.received: Inbound email (primary for NornWeave)
    - email.sent: Outbound email accepted
    - email.delivered: Successfully delivered
    - email.bounced: Permanently rejected
    - email.complained: Marked as spam
    - email.failed: Failed to send
    - email.opened: Recipient opened email
    - email.clicked: Recipient clicked link
    - email.delivery_delayed: Temporary delivery issue
    - email.scheduled: Email scheduled
    - email.suppressed: Suppressed by Resend
    """
    # Get raw body for signature verification
    raw_body = await request.body()

    # Parse JSON payload
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as e:
        logger.error("Failed to parse JSON payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from e

    # Create adapter
    adapter = _get_resend_adapter(settings)

    # Verify webhook signature if secret is configured
    if settings.resend_webhook_secret:
        try:
            headers = {k.lower(): v for k, v in request.headers.items()}
            adapter.verify_webhook_signature(raw_body, headers)
            logger.debug("Webhook signature verified successfully")
        except ResendWebhookError as e:
            logger.warning("Webhook signature verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e
    else:
        logger.warning("Webhook secret not configured, skipping signature verification")

    # Get event type
    event_type = ResendAdapter.get_event_type(payload)
    logger.info("Received Resend webhook: %s", event_type)

    # Route based on event type
    if event_type == "email.received":
        return await _handle_inbound_email(adapter, payload, storage, settings)
    elif event_type in DELIVERY_EVENT_TYPES:
        return _handle_delivery_event(event_type, payload)
    else:
        logger.warning("Unknown event type: %s", event_type)
        return {"status": "unknown_event", "event_type": event_type}


async def _handle_inbound_email(
    adapter: ResendAdapter,
    payload: dict[str, Any],
    storage: StorageInterface,
    settings: Settings,
) -> dict[str, str]:
    """Handle email.received event.

    Fetches full email content from Resend API and stores the message.
    Stores attachments using the configured storage backend.
    """
    data = payload.get("data", {})
    email_id = data.get("email_id", "unknown")

    logger.info(
        "Processing inbound email %s from %s to %s",
        email_id,
        data.get("from"),
        data.get("to"),
    )

    # Parse webhook and fetch full content
    content_fetch_failed = False
    try:
        inbound = await adapter.parse_inbound_webhook_with_content(
            payload,
            fetch_attachments=True,
        )
    except httpx.HTTPStatusError as e:
        # If content fetch fails (e.g., API key lacks read permission),
        # fall back to webhook metadata only and continue processing.
        # This ensures the message is still created, but with limited content.
        if e.response.status_code == 401:
            logger.warning(
                "Could not fetch full email content (API key restricted). "
                "Processing with webhook metadata only. "
                "To get full email content, use an API key with 'Full access' permission."
            )
            content_fetch_failed = True
            inbound = adapter.parse_inbound_webhook(payload)
        elif e.response.status_code == 404:
            logger.warning(
                "Email %s not found in Resend API. Processing with webhook metadata only.",
                email_id,
            )
            content_fetch_failed = True
            inbound = adapter.parse_inbound_webhook(payload)
        else:
            logger.error("Failed to fetch email content: %s", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process email: {e}",
            ) from e
    except ValueError as e:
        logger.error("Failed to parse webhook payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse webhook: {e}",
        ) from e

    # Find inbox by recipient email address
    inbox = await storage.get_inbox_by_email(inbound.to_address)
    if inbox is None:
        logger.warning("No inbox found for recipient: %s", inbound.to_address)
        # Return 200 to prevent Resend from retrying, but log the issue
        return {"status": "no_inbox", "recipient": inbound.to_address}

    logger.info("Found inbox %s for recipient %s", inbox.id, inbound.to_address)

    # Check for duplicate webhook delivery (idempotency)
    if inbound.message_id:
        existing_msg = await storage.get_message_by_provider_id(inbox.id, inbound.message_id)
        if existing_msg:
            logger.info(
                "Duplicate webhook detected: message %s already exists for provider_message_id %s",
                existing_msg.id,
                inbound.message_id,
            )
            return {
                "status": "duplicate",
                "message_id": existing_msg.id,
                "thread_id": existing_msg.thread_id,
                "email_id": email_id,
            }

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
    # Use stripped versions if available (Mailgun), fall back to full body (Resend)
    content_clean = inbound.stripped_text or inbound.body_plain
    extracted_html = inbound.stripped_html or inbound.body_html
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

    # Store attachments if present - using the configured storage backend
    if inbound.attachments:
        # Create storage backend for attachments
        storage_backend = create_attachment_storage(settings)

        for att in inbound.attachments:
            if att.content and att.size_bytes > 0:
                try:
                    # Generate attachment ID
                    attachment_id = str(uuid.uuid4())

                    # Create metadata for storage backend
                    metadata = AttachmentMetadata(
                        attachment_id=attachment_id,
                        message_id=created_message.id,
                        filename=att.filename,
                        content_type=att.content_type,
                        content_disposition=att.disposition.value,
                        content_id=att.content_id,
                    )

                    # Store in configured backend (local, s3, gcs, or database)
                    storage_result = await storage_backend.store(
                        attachment_id=attachment_id,
                        content=att.content,
                        metadata=metadata,
                    )

                    # Create database record with storage info
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
                        # For database backend, also store the content
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

    # Update thread's last_message_at
    if thread:
        thread.last_message_at = created_message.created_at
        thread.received_timestamp = created_message.created_at
        await storage.update_thread(thread)

    result = {
        "status": "received",
        "message_id": created_message.id,
        "thread_id": thread_id or "",
        "email_id": email_id,
    }

    if content_fetch_failed:
        result["warning"] = (
            "Email content could not be fetched from Resend API. "
            "Message was created with metadata only (no body content). "
            "Ensure your API key has 'Full access' permission."
        )

    return result


def _handle_delivery_event(event_type: str, payload: dict[str, Any]) -> dict[str, str]:
    """Handle delivery-related events (sent, delivered, bounced, etc.).

    These events are useful for tracking outbound email delivery status.
    For now, we just log them. In the future, these could update message status.
    """
    data = payload.get("data", {})
    email_id = data.get("email_id", "unknown")
    created_at = payload.get("created_at", "")

    # Log event details
    logger.info(
        "Resend delivery event: %s for email %s at %s",
        event_type,
        email_id,
        created_at,
    )

    # For bounced/complained events, log additional details
    if event_type == "email.bounced":
        bounce_info = data.get("bounce", {})
        logger.warning(
            "Email %s bounced: type=%s, subType=%s, message=%s",
            email_id,
            bounce_info.get("type"),
            bounce_info.get("subType"),
            bounce_info.get("message"),
        )
    elif event_type == "email.complained":
        logger.warning(
            "Email %s marked as spam by recipient: %s",
            email_id,
            data.get("to", []),
        )
    elif event_type == "email.failed":
        logger.error(
            "Email %s failed to send: subject=%s, to=%s",
            email_id,
            data.get("subject"),
            data.get("to", []),
        )

    return {
        "status": "acknowledged",
        "event_type": event_type,
        "email_id": email_id,
    }
