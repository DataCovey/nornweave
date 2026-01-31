"""Search endpoint."""

from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from nornweave.core.interfaces import StorageInterface  # noqa: TC001 - needed at runtime
from nornweave.yggdrasil.dependencies import get_storage

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request payload."""

    query: str = Field(..., min_length=1, description="Search query")
    inbox_id: str = Field(..., description="Inbox to search in")
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResultItem(BaseModel):
    """Individual search result."""

    id: str
    thread_id: str
    inbox_id: str
    direction: str
    content_clean: str
    created_at: datetime | None
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    """Search response."""

    items: list[SearchResultItem]
    count: int
    query: str


@router.post("/search", response_model=SearchResponse)
async def search_messages(
    payload: SearchRequest,
    storage: StorageInterface = Depends(get_storage),
) -> SearchResponse:
    """Search messages by content.

    Phase 1: Uses SQL ILIKE/LIKE on content_clean and content_raw.
    Phase 3: Will use vector embeddings for semantic search.
    """
    # Verify inbox exists
    inbox = await storage.get_inbox(payload.inbox_id)
    if inbox is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inbox {payload.inbox_id} not found",
        )

    messages = await storage.search_messages(
        inbox_id=payload.inbox_id,
        query=payload.query,
        limit=payload.limit,
        offset=payload.offset,
    )

    return SearchResponse(
        items=[
            SearchResultItem(
                id=m.id,
                thread_id=m.thread_id,
                inbox_id=m.inbox_id,
                direction=m.direction.value,
                content_clean=m.content_clean,
                created_at=m.created_at,
                metadata=m.metadata,
            )
            for m in messages
        ],
        count=len(messages),
        query=payload.query,
    )
