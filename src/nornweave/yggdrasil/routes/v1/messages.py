"""Message endpoints."""

import contextlib
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from nornweave.core.interfaces import (  # noqa: TC001 - needed at runtime for FastAPI
    EmailProvider,
    StorageInterface,
)
from nornweave.models.message import Message, MessageDirection
from nornweave.models.thread import Thread
from nornweave.yggdrasil.dependencies import get_email_provider, get_storage

router = APIRouter()


class MessageResponse(BaseModel):
    """Response model for a message."""

    id: str
    thread_id: str
    inbox_id: str
    direction: str
    provider_message_id: str | None
    content_raw: str
    content_clean: str
    metadata: dict[str, Any]
    created_at: datetime | None


class MessageListResponse(BaseModel):
    """Response model for message list."""

    items: list[MessageResponse]
    count: int


class SendMessageRequest(BaseModel):
    """Request to send an outbound message."""

    inbox_id: str
    to: list[str] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., description="Markdown body content")
    reply_to_thread_id: str | None = None


class SendMessageResponse(BaseModel):
    """Response after sending a message."""

    id: str
    thread_id: str
    provider_message_id: str | None
    status: str


def _message_to_response(msg: Message) -> MessageResponse:
    """Convert Message model to response."""
    return MessageResponse(
        id=msg.id,
        thread_id=msg.thread_id,
        inbox_id=msg.inbox_id,
        direction=msg.direction.value,
        provider_message_id=msg.provider_message_id,
        content_raw=msg.content_raw,
        content_clean=msg.content_clean,
        metadata=msg.metadata,
        created_at=msg.created_at,
    )


@router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    inbox_id: str,
    limit: int = 50,
    offset: int = 0,
    storage: StorageInterface = Depends(get_storage),
) -> MessageListResponse:
    """List messages for an inbox."""
    # Verify inbox exists
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {inbox_id} not found",
        )

    messages = await storage.list_messages_for_inbox(
        inbox_id,
        limit=limit,
        offset=offset,
    )

    return MessageListResponse(
        items=[_message_to_response(m) for m in messages],
        count=len(messages),
    )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    storage: StorageInterface = Depends(get_storage),
) -> MessageResponse:
    """Get a message by ID."""
    message = await storage.get_message(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )
    return _message_to_response(message)


@router.post("/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: SendMessageRequest,
    storage: StorageInterface = Depends(get_storage),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> SendMessageResponse:
    """Send an outbound message.

    If reply_to_thread_id is provided, the message is added to that thread.
    Otherwise, a new thread is created.
    """
    # Get inbox
    inbox = await storage.get_inbox(payload.inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {payload.inbox_id} not found",
        )

    # Get or create thread
    thread_id: str
    if payload.reply_to_thread_id:
        thread = await storage.get_thread(payload.reply_to_thread_id)
        if thread is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread {payload.reply_to_thread_id} not found",
            )
        thread_id = thread.id
    else:
        # Create a new thread
        new_thread = Thread(
            thread_id=str(uuid.uuid4()),
            inbox_id=payload.inbox_id,
            subject=payload.subject,
            timestamp=datetime.now(UTC),
            participant_hash=None,  # Will be set when we have participants
        )
        created_thread = await storage.create_thread(new_thread)
        thread_id = created_thread.id

    # Send email via provider
    # Log error but continue to store the message attempt
    provider_message_id: str | None = None
    with contextlib.suppress(Exception):
        provider_message_id = await email_provider.send_email(
            to=payload.to,
            subject=payload.subject,
            body=payload.body,
            from_address=inbox.email_address,
        )

    # Create message record
    message = Message(
        message_id=str(uuid.uuid4()),
        thread_id=thread_id,
        inbox_id=payload.inbox_id,
        provider_message_id=provider_message_id,
        direction=MessageDirection.OUTBOUND,
        text=payload.body,
        extracted_text=payload.body,  # Already markdown
        headers={
            "to": ",".join(payload.to),  # Join list into comma-separated string
            "subject": payload.subject,
        },
        created_at=datetime.now(UTC),
    )
    created_message = await storage.create_message(message)

    # Update thread's last_message_at
    thread = await storage.get_thread(thread_id)
    if thread:
        thread.last_message_at = created_message.created_at
        await storage.update_thread(thread)

    return SendMessageResponse(
        id=created_message.id,
        thread_id=thread_id,
        provider_message_id=provider_message_id,
        status="sent" if provider_message_id else "pending",
    )
