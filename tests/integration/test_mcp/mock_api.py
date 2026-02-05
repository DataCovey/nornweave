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
_attachments: dict[str, dict[str, Any]] = {}


def reset_mock_data() -> None:
    """Reset all mock data."""
    global _inboxes, _threads, _messages, _attachments
    _inboxes = {}
    _threads = {}
    _messages = {}
    _attachments = {}


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

    # Create message with attachments
    _messages["msg_with_attachments"] = {
        "id": "msg_with_attachments",
        "thread_id": "th_test",
        "inbox_id": "ibx_test",
        "direction": "inbound",
        "content_raw": "Here is an attachment.",
        "content_clean": "Here is an attachment.",
        "metadata": {"from": "sender@example.com"},
        "created_at": datetime.now(UTC).isoformat(),
    }

    # Create test attachments
    import base64

    _attachments["att_test"] = {
        "id": "att_test",
        "message_id": "msg_with_attachments",
        "filename": "test.txt",
        "content_type": "text/plain",
        "size": 13,
        "disposition": "attachment",
        "content_id": None,
        "storage_backend": "local",
        "content_hash": "abc123",
        "created_at": datetime.now(UTC).isoformat(),
        "_content": base64.b64encode(b"Hello, World!").decode("ascii"),
    }

    _attachments["att_test_2"] = {
        "id": "att_test_2",
        "message_id": "msg_with_attachments",
        "filename": "image.png",
        "content_type": "image/png",
        "size": 1024,
        "disposition": "attachment",
        "content_id": None,
        "storage_backend": "local",
        "content_hash": "def456",
        "created_at": datetime.now(UTC).isoformat(),
        "_content": base64.b64encode(b"\x89PNG\r\n" + b"\x00" * 100).decode("ascii"),
    }


# Pydantic models for request/response
class InboxCreate(BaseModel):
    """Request to create an inbox."""

    name: str
    email_username: str


class AttachmentInput(BaseModel):
    """Attachment input for sending messages (matches API model)."""

    filename: str
    content_type: str
    content_base64: str  # Matches nornweave.models.attachment.AttachmentUpload


class SendMessage(BaseModel):
    """Request to send a message."""

    inbox_id: str
    to: list[str]
    subject: str
    body: str
    reply_to_thread_id: str | None = None
    attachments: list[AttachmentInput] | None = None


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
def list_messages(
    inbox_id: str | None = None,
    thread_id: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List and search messages with flexible filters."""
    # Require at least one filter
    if inbox_id is None and thread_id is None:
        raise HTTPException(
            status_code=422, detail="At least one filter (inbox_id or thread_id) is required"
        )

    # Validate inbox exists if provided
    if inbox_id and inbox_id not in _inboxes:
        raise HTTPException(status_code=404, detail="Inbox not found")

    # Validate thread exists if provided
    if thread_id and thread_id not in _threads:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Filter messages
    items = list(_messages.values())
    if inbox_id:
        items = [m for m in items if m["inbox_id"] == inbox_id]
    if thread_id:
        items = [m for m in items if m["thread_id"] == thread_id]

    # Apply text search if provided
    if q:
        q_lower = q.lower()
        filtered = []
        for m in items:
            # Search in subject, content_raw, from_address
            subject = m.get("subject", "") or ""
            content = m.get("content_raw", "") or ""
            from_addr = m.get("from_address", "") or m.get("metadata", {}).get("from", "") or ""
            if (
                q_lower in subject.lower()
                or q_lower in content.lower()
                or q_lower in from_addr.lower()
            ):
                filtered.append(m)
        items = filtered

    total = len(items)
    items = items[offset : offset + limit]
    return {"items": items, "count": len(items), "total": total}


@mock_app.post("/v1/messages")
def send_message(payload: SendMessage) -> dict[str, Any]:
    """Send a message."""
    import base64
    import binascii

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

    # Handle attachments
    if payload.attachments:
        for i, att in enumerate(payload.attachments):
            # Validate base64 content
            try:
                content_bytes = base64.b64decode(att.content_base64)
            except (binascii.Error, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid base64 content in attachment {i}: {e}",
                )

            att_id = f"att_{len(_attachments) + 1}"
            _attachments[att_id] = {
                "id": att_id,
                "message_id": message_id,
                "filename": att.filename,
                "content_type": att.content_type,
                "size": len(content_bytes),
                "disposition": "attachment",
                "content_id": None,
                "storage_backend": "local",
                "content_hash": f"hash_{att_id}",
                "created_at": datetime.now(UTC).isoformat(),
                "_content": att.content_base64,
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


# Attachment endpoints
@mock_app.get("/v1/attachments")
def list_attachments(
    message_id: str | None = None,
    thread_id: str | None = None,
    inbox_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """List attachments with filters."""
    # Require exactly one filter
    filters = [message_id, thread_id, inbox_id]
    if sum(f is not None for f in filters) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one filter (message_id, thread_id, or inbox_id) is required",
        )

    if message_id:
        if message_id not in _messages:
            raise HTTPException(status_code=404, detail="Message not found")
        items = [a for a in _attachments.values() if a["message_id"] == message_id]
    elif thread_id:
        if thread_id not in _threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        thread_messages = [m["id"] for m in _messages.values() if m["thread_id"] == thread_id]
        items = [a for a in _attachments.values() if a["message_id"] in thread_messages]
    else:  # inbox_id
        if inbox_id not in _inboxes:
            raise HTTPException(status_code=404, detail="Inbox not found")
        inbox_messages = [m["id"] for m in _messages.values() if m["inbox_id"] == inbox_id]
        items = [a for a in _attachments.values() if a["message_id"] in inbox_messages]

    # Remove internal _content field from response
    result_items = [
        {k: v for k, v in a.items() if not k.startswith("_")}
        for a in items[offset : offset + limit]
    ]
    return {"items": result_items, "count": len(result_items)}


@mock_app.get("/v1/attachments/{attachment_id}")
def get_attachment(attachment_id: str) -> dict[str, Any]:
    """Get attachment metadata."""
    if attachment_id not in _attachments:
        raise HTTPException(status_code=404, detail="Attachment not found")

    attachment = _attachments[attachment_id]
    # Generate a mock download URL
    result = {k: v for k, v in attachment.items() if not k.startswith("_")}
    result["download_url"] = (
        f"/v1/attachments/{attachment_id}/content?token=mock&expires=9999999999"
    )
    return result


@mock_app.get("/v1/attachments/{attachment_id}/content")
def get_attachment_content(
    attachment_id: str,
    format: str = "binary",
    token: str | None = None,  # noqa: ARG001 - accepted for API compatibility
    expires: int | None = None,  # noqa: ARG001 - accepted for API compatibility
) -> Any:
    """Get attachment content."""
    import base64

    from fastapi.responses import Response

    if attachment_id not in _attachments:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # In mock, we don't strictly verify token/expires
    attachment = _attachments[attachment_id]
    content_b64 = attachment.get("_content", "")

    if format == "base64":
        return {
            "content": content_b64,
            "content_type": attachment["content_type"],
            "filename": attachment["filename"],
        }
    else:
        content_bytes = base64.b64decode(content_b64)
        return Response(
            content=content_bytes,
            media_type=attachment["content_type"],
            headers={"Content-Disposition": f'attachment; filename="{attachment["filename"]}"'},
        )
