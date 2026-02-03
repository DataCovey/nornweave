"""Mock NornWeave API server for MCP tests.

This module provides a FastAPI-based mock server that simulates
the NornWeave REST API for testing the MCP server.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# In-memory storage for mock data
_inboxes: dict[str, dict[str, Any]] = {}
_threads: dict[str, dict[str, Any]] = {}
_messages: dict[str, dict[str, Any]] = {}


def reset_mock_data() -> None:
    """Reset all mock data."""
    global _inboxes, _threads, _messages
    _inboxes = {}
    _threads = {}
    _messages = {}


def seed_mock_data() -> None:
    """Seed mock data for tests."""
    reset_mock_data()

    # Create a test inbox
    _inboxes["ibx_test"] = {
        "id": "ibx_test",
        "email_address": "test@mail.example.com",
        "name": "Test Inbox",
        "provider_config": {},
    }

    # Create a test thread
    _threads["th_test"] = {
        "id": "th_test",
        "inbox_id": "ibx_test",
        "subject": "Test Thread",
        "last_message_at": datetime.now(UTC).isoformat(),
        "participant_hash": "abc123",
    }

    # Create test messages
    _messages["msg_1"] = {
        "id": "msg_1",
        "thread_id": "th_test",
        "inbox_id": "ibx_test",
        "direction": "inbound",
        "content_raw": "Hello, this is a test message.",
        "content_clean": "Hello, this is a test message.",
        "metadata": {"from": "sender@example.com"},
        "created_at": datetime.now(UTC).isoformat(),
    }

    _messages["msg_2"] = {
        "id": "msg_2",
        "thread_id": "th_test",
        "inbox_id": "ibx_test",
        "direction": "outbound",
        "content_raw": "Thanks for your message!",
        "content_clean": "Thanks for your message!",
        "metadata": {"to": "sender@example.com"},
        "created_at": datetime.now(UTC).isoformat(),
    }


# Pydantic models for request/response
class InboxCreate(BaseModel):
    """Request to create an inbox."""

    name: str
    email_username: str


class SendMessage(BaseModel):
    """Request to send a message."""

    inbox_id: str
    to: list[str]
    subject: str
    body: str
    reply_to_thread_id: str | None = None


class SearchRequest(BaseModel):
    """Request to search messages."""

    query: str
    inbox_id: str
    limit: int = 50
    offset: int = 0


# Create the mock FastAPI app
mock_app = FastAPI(title="Mock NornWeave API")


@mock_app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Inbox endpoints
@mock_app.post("/v1/inboxes")
def create_inbox(payload: InboxCreate) -> dict[str, Any]:
    """Create a new inbox."""
    inbox_id = f"ibx_{len(_inboxes) + 1}"
    email = f"{payload.email_username}@mail.example.com"

    # Check for duplicate
    for inbox in _inboxes.values():
        if inbox["email_address"] == email:
            raise HTTPException(status_code=409, detail="Email already exists")

    inbox = {
        "id": inbox_id,
        "email_address": email,
        "name": payload.name,
        "provider_config": {},
    }
    _inboxes[inbox_id] = inbox
    return inbox


@mock_app.get("/v1/inboxes")
def list_inboxes(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List all inboxes."""
    items = list(_inboxes.values())[offset : offset + limit]
    return {"items": items, "count": len(items)}


@mock_app.get("/v1/inboxes/{inbox_id}")
def get_inbox(inbox_id: str) -> dict[str, Any]:
    """Get an inbox by ID."""
    if inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")
    return _inboxes[inbox_id]


# Thread endpoints
@mock_app.get("/v1/threads")
def list_threads(inbox_id: str, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """List threads for an inbox."""
    if inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")

    items = [t for t in _threads.values() if t["inbox_id"] == inbox_id][offset : offset + limit]
    return {"items": items, "count": len(items)}


@mock_app.get("/v1/threads/{thread_id}")
def get_thread(thread_id: str) -> dict[str, Any]:
    """Get a thread with messages."""
    if thread_id not in _threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread = _threads[thread_id]
    messages = [m for m in _messages.values() if m["thread_id"] == thread_id]

    # Format messages for LLM-ready format
    formatted_messages = []
    for msg in messages:
        role = "user" if msg["direction"] == "inbound" else "assistant"
        author = msg["metadata"].get("from", msg["metadata"].get("to", "unknown"))
        formatted_messages.append(
            {
                "role": role,
                "author": author,
                "content": msg["content_clean"],
                "timestamp": msg["created_at"],
            }
        )

    return {
        "id": thread["id"],
        "subject": thread["subject"],
        "messages": formatted_messages,
    }


# Message endpoints
@mock_app.get("/v1/messages")
def list_messages(inbox_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """List messages for an inbox."""
    if inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")

    items = [m for m in _messages.values() if m["inbox_id"] == inbox_id][offset : offset + limit]
    return {"items": items, "count": len(items)}


@mock_app.post("/v1/messages")
def send_message(payload: SendMessage) -> dict[str, Any]:
    """Send a message."""
    if payload.inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")

    # Create or get thread
    if payload.reply_to_thread_id:
        if payload.reply_to_thread_id not in _threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        thread_id = payload.reply_to_thread_id
    else:
        thread_id = f"th_{len(_threads) + 1}"
        _threads[thread_id] = {
            "id": thread_id,
            "inbox_id": payload.inbox_id,
            "subject": payload.subject,
            "last_message_at": datetime.now(UTC).isoformat(),
            "participant_hash": None,
        }

    # Create message
    message_id = f"msg_{len(_messages) + 1}"
    _messages[message_id] = {
        "id": message_id,
        "thread_id": thread_id,
        "inbox_id": payload.inbox_id,
        "direction": "outbound",
        "content_raw": payload.body,
        "content_clean": payload.body,
        "metadata": {"to": ",".join(payload.to)},
        "created_at": datetime.now(UTC).isoformat(),
    }

    return {
        "id": message_id,
        "thread_id": thread_id,
        "provider_message_id": f"provider_{message_id}",
        "status": "sent",
    }


# Search endpoint
@mock_app.post("/v1/search")
def search_messages(payload: SearchRequest) -> dict[str, Any]:
    """Search messages."""
    if payload.inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")

    # Simple search: match query in content
    query_lower = payload.query.lower()
    matches = []
    for msg in _messages.values():
        if msg["inbox_id"] != payload.inbox_id:
            continue
        if query_lower in msg["content_clean"].lower():
            matches.append(msg)

    items = matches[payload.offset : payload.offset + payload.limit]
    return {
        "items": items,
        "count": len(items),
        "query": payload.query,
    }
