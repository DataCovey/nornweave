"""Inbox endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from nornweave.core.config import Settings, get_settings
from nornweave.core.interfaces import StorageInterface  # noqa: TC001 - needed at runtime
from nornweave.models.inbox import Inbox, InboxCreate
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()


class InboxResponse(BaseModel):
    """Response model for inbox."""

    id: str
    email_address: str
    name: str | None
    provider_config: dict[str, Any]


class InboxListResponse(BaseModel):
    """Response model for inbox list."""

    items: list[InboxResponse]
    count: int


@router.post("/inboxes", response_model=InboxResponse, status_code=status.HTTP_201_CREATED)
async def create_inbox(
    payload: InboxCreate,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> InboxResponse:
    """Create a new inbox.

    The email address is constructed from the username and configured domain.
    """
    # Validate that email domain is configured
    if not settings.email_domain:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "EMAIL_DOMAIN is not configured. "
                "Set EMAIL_DOMAIN in your .env file to the domain used by your email provider "
                "(e.g. EMAIL_DOMAIN=mail.yourdomain.com). "
                "See the Configuration docs for details."
            ),
        )

    # Construct full email address
    email_address = f"{payload.email_username}@{settings.email_domain}"

    # Check if email already exists
    existing = await storage.get_inbox_by_email(email_address)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inbox with email {email_address} already exists",
        )

    # Create inbox
    inbox = Inbox(
        id=str(uuid.uuid4()),
        email_address=email_address,
        name=payload.name,
        provider_config={},
    )

    created = await storage.create_inbox(inbox)
    return InboxResponse(
        id=created.id,
        email_address=created.email_address,
        name=created.name,
        provider_config=created.provider_config,
    )


@router.get("/inboxes", response_model=InboxListResponse)
async def list_inboxes(
    limit: int = 50,
    offset: int = 0,
    storage: StorageInterface = Depends(get_storage),
) -> InboxListResponse:
    """List all inboxes."""
    inboxes = await storage.list_inboxes(limit=limit, offset=offset)
    return InboxListResponse(
        items=[
            InboxResponse(
                id=i.id,
                email_address=i.email_address,
                name=i.name,
                provider_config=i.provider_config,
            )
            for i in inboxes
        ],
        count=len(inboxes),
    )


@router.get("/inboxes/{inbox_id}", response_model=InboxResponse)
async def get_inbox(
    inbox_id: str,
    storage: StorageInterface = Depends(get_storage),
) -> InboxResponse:
    """Get an inbox by ID."""
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {inbox_id} not found",
        )
    return InboxResponse(
        id=inbox.id,
        email_address=inbox.email_address,
        name=inbox.name,
        provider_config=inbox.provider_config,
    )


@router.delete("/inboxes/{inbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inbox(
    inbox_id: str,
    storage: StorageInterface = Depends(get_storage),
) -> None:
    """Delete an inbox."""
    deleted = await storage.delete_inbox(inbox_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {inbox_id} not found",
        )


class SyncResponse(BaseModel):
    """Response model for IMAP sync."""

    status: str
    new_messages: int


@router.post("/inboxes/{inbox_id}/sync", response_model=SyncResponse)
async def sync_inbox(
    inbox_id: str,
    storage: StorageInterface = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> SyncResponse:
    """Trigger an immediate IMAP sync for a specific inbox.

    Only available when EMAIL_PROVIDER is imap-smtp.
    """
    # Check provider
    if settings.email_provider != "imap-smtp":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IMAP sync is only available with the imap-smtp provider",
        )

    # Verify inbox exists
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {inbox_id} not found",
        )

    # Trigger sync
    from nornweave.yggdrasil.app import get_imap_poller

    poller = get_imap_poller()
    if poller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IMAP poller is not running",
        )

    try:
        new_messages = await poller.sync_inbox(inbox_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"IMAP connection failure: {e}",
        ) from e

    return SyncResponse(status="synced", new_messages=new_messages)
