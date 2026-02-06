"""Resend webhook handler."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from nornweave.adapters.resend import ResendAdapter, ResendWebhookError
from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (
    StorageInterface,  # noqa: TC001 - needed at runtime for FastAPI
)
from nornweave.verdandi.ingest import ingest_message
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

    Fetches full email content from Resend API, then delegates to
    the shared ingestion pipeline.
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

    # Delegate to shared ingestion pipeline
    result = await ingest_message(inbound, storage, settings)

    response: dict[str, str] = {
        "status": result.status,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
        "email_id": email_id,
    }

    if content_fetch_failed:
        response["warning"] = (
            "Email content could not be fetched from Resend API. "
            "Message was created with metadata only (no body content). "
            "Ensure your API key has 'Full access' permission."
        )

    return response


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
