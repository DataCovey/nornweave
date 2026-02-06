"""Mailgun webhook handler."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from nornweave.adapters.mailgun import MailgunAdapter
from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (
    StorageInterface,  # noqa: TC001 - needed at runtime for FastAPI
)
from nornweave.verdandi.ingest import ingest_message
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()
logger = logging.getLogger(__name__)


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

    # Parse the webhook payload using the Mailgun adapter
    adapter = MailgunAdapter(api_key="", domain="")  # Keys not needed for parsing
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
