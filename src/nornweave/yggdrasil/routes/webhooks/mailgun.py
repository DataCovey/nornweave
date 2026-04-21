"""Mailgun webhook handler."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from nornweave.adapters.mailgun import MailgunAdapter, MailgunWebhookError
from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (
    StorageInterface,  # noqa: TC001 - needed at runtime for FastAPI
)
from nornweave.verdandi.ingest import ingest_message
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_mailgun_adapter(settings: Settings) -> MailgunAdapter:
    """Create MailgunAdapter with webhook verification config."""
    return MailgunAdapter(
        api_key=settings.mailgun_api_key,
        domain=settings.mailgun_domain,
        webhook_signing_key=settings.webhook_secret,
    )


@router.post("/mailgun", status_code=status.HTTP_200_OK)
async def mailgun_webhook(
    request: Request,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Handle inbound email webhook from Mailgun.

    Mailgun sends inbound emails as multipart/form-data.
    This handler:
    1. Parses the webhook payload
    2. Delegates to the shared ingestion pipeline
    """
    # Parse form data from Mailgun
    form_data = await request.form()
    payload = dict(form_data.items())

    logger.info("Received Mailgun webhook for recipient: %s", payload.get("recipient"))
    logger.debug("Mailgun payload keys: %s", list(payload.keys()))

    # Enforce webhook signature verification before parsing/ingestion.
    if not settings.webhook_secret:
        logger.error("WEBHOOK_SECRET is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mailgun webhook verification is not configured",
        )

    adapter = _get_mailgun_adapter(settings)
    try:
        adapter.verify_webhook_signature(payload)
    except MailgunWebhookError as e:
        logger.warning("Mailgun webhook signature verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    # Parse the webhook payload using the Mailgun adapter
    try:
        inbound = adapter.parse_inbound_webhook(payload)
    except Exception as e:
        logger.error("Failed to parse Mailgun webhook: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse webhook payload: {e}",
        ) from e

    # Delegate to shared ingestion pipeline
    result = await ingest_message(inbound, storage, settings)

    return {
        "status": result.status,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
    }
