"""Thread endpoints."""

from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from nornweave.core.interfaces import StorageInterface  # noqa: TC001 - needed at runtime
from nornweave.models.message import MessageDirection
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()


class ThreadMessageResponse(BaseModel):
    """Message within a thread response (LLM-ready format)."""

    role: str  # "user" for inbound, "assistant" for outbound
    author: str  # email address from metadata or inbox
    content: str  # clean markdown content
    timestamp: datetime | None


class ThreadDetailResponse(BaseModel):
    """Detailed thread response with messages (LLM context format per PRD)."""

    id: str
    subject: str
    summary: str | None = None
    messages: list[ThreadMessageResponse]


class ThreadSummaryResponse(BaseModel):
    """Thread summary for list views."""

    id: str
    inbox_id: str
    subject: str
    summary: str | None = None
    last_message_at: datetime | None
    participant_hash: str | None


class ThreadListResponse(BaseModel):
    """Response model for thread list."""

    items: list[ThreadSummaryResponse]
    count: int


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    inbox_id: str,
    limit: int = 20,
    offset: int = 0,
    storage: StorageInterface = Depends(get_storage),
) -> ThreadListResponse:
    """List threads for an inbox, ordered by most recent activity."""
    # Verify inbox exists
    inbox = await storage.get_inbox(inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {inbox_id} not found",
        )

    threads = await storage.list_threads_for_inbox(
        inbox_id,
        limit=limit,
        offset=offset,
    )

    return ThreadListResponse(
        items=[
            ThreadSummaryResponse(
                id=t.id,
                inbox_id=t.inbox_id,
                subject=t.subject,
                summary=t.summary,
                last_message_at=t.last_message_at,
                participant_hash=t.participant_hash,
            )
            for t in threads
        ],
        count=len(threads),
    )


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: str,
    limit: int = 100,
    offset: int = 0,
    storage: StorageInterface = Depends(get_storage),
) -> ThreadDetailResponse:
    """Get a thread with its messages in LLM-ready format.

    Returns a Markdown-formatted conversation history optimized for context windows,
    as specified in the PRD.
    """
    thread = await storage.get_thread(thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )

    # Get messages for the thread
    messages = await storage.list_messages_for_thread(
        thread_id,
        limit=limit,
        offset=offset,
    )

    # Get inbox for author mapping
    inbox = await storage.get_inbox(thread.inbox_id)
    inbox_email = inbox.email_address if inbox else "unknown@example.com"

    # Convert to LLM-ready format
    thread_messages = []
    for msg in messages:
        # Determine role and author based on direction
        if msg.direction == MessageDirection.INBOUND:
            role = "user"
            # Try to get from address from metadata (headers)
            metadata = msg.metadata or {}
            author = metadata.get("from", "unknown@example.com")
        else:
            role = "assistant"
            author = inbox_email

        thread_messages.append(
            ThreadMessageResponse(
                role=role,
                author=str(author),
                content=msg.content_clean or msg.content_raw,
                timestamp=msg.created_at,
            )
        )

    return ThreadDetailResponse(
        id=thread.id,
        subject=thread.subject,
        summary=thread.summary,
        messages=thread_messages,
    )
