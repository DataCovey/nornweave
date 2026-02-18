"""Demo/sandbox-only endpoints.

Available only when EMAIL_PROVIDER=demo. Simulate inbound mail for testing
and wait_for_reply flows without a real mail server.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import (  # noqa: TC001 - needed at runtime for FastAPI Depends
    EmailProvider,
    StorageInterface,
)
from nornweave.verdandi.ingest import ingest_message
from nornweave.yggdrasil.dependencies import get_email_provider, get_storage

router = APIRouter()


class DemoInboundRequest(BaseModel):
    """Request body for POST /v1/demo/inbound."""

    to_address: str | None = None
    inbox_id: str | None = None
    from_address: str
    subject: str
    body_plain: str
    body_html: str | None = None
    message_id: str | None = None
    in_reply_to: str | None = None
    references: list[str] | None = None


@router.post("/demo/inbound", status_code=status.HTTP_200_OK)
async def demo_inbound(
    body: DemoInboundRequest,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> dict[str, str]:
    """Simulate an inbound email (demo mode only).

    Delivers a message into the specified inbox as if it were received via
    webhook. Requires EMAIL_PROVIDER=demo. Provide either to_address or
    inbox_id (inbox's email address is used as to_address).
    """
    if settings.email_provider != "demo":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo inbound is only available when EMAIL_PROVIDER=demo.",
        )
    to_address = body.to_address
    if to_address is None and body.inbox_id:
        inbox = await storage.get_inbox(body.inbox_id)
        if inbox is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inbox {body.inbox_id} not found.",
            )
        to_address = inbox.email_address
    if to_address is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either to_address or inbox_id.",
        )
    payload: dict[str, Any] = {
        "from_address": body.from_address,
        "to_address": to_address,
        "subject": body.subject,
        "body_plain": body.body_plain,
        "body_html": body.body_html,
        "message_id": body.message_id,
        "in_reply_to": body.in_reply_to,
        "references": body.references or [],
    }
    inbound = email_provider.parse_inbound_webhook(payload)
    result = await ingest_message(inbound, storage, settings)
    return {
        "status": result.status,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
    }
