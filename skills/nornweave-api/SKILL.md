---
name: nornweave-api
description: Give AI agents their own email inboxes using the NornWeave API. Use when building email agents, sending/receiving emails programmatically, managing inboxes, retrieving threads, searching messages, or integrating with email providers (Mailgun, SES, SendGrid, Resend). NornWeave provides LLM-ready markdown parsing and conversation threading.
---

# NornWeave API

NornWeave is a self-hosted, open-source Inbox-as-a-Service API for AI agents. It provides a stateful email layer (Inboxes, Threads, History) and an intelligent layer (Markdown parsing, Semantic Search) optimized for LLMs.

## Installation

```bash
# Python client
pip install nornweave-client
```

## Setup

```python
from nornweave_client import NornWeave

# Sync client
client = NornWeave(base_url="http://localhost:8000")

# Or async client
from nornweave_client import AsyncNornWeave
client = AsyncNornWeave(base_url="http://localhost:8000")
```

## Inboxes

Create scalable inboxes on-demand. Each inbox has a unique email address based on your configured domain.

```python
# Create inbox with username and display name
inbox = client.inboxes.create(
    name="Support",
    email_username="support"
)
# Result: support@yourdomain.com

# List all inboxes (paginated)
for inbox in client.inboxes.list():
    print(inbox.email_address)

# Get inbox by ID
inbox = client.inboxes.get(inbox_id="inbox-uuid")

# Delete inbox
client.inboxes.delete(inbox_id="inbox-uuid")
```

### Async Usage

```python
# Create inbox
inbox = await client.inboxes.create(
    name="Support",
    email_username="support"
)

# List inboxes with async iteration
async for inbox in client.inboxes.list():
    print(inbox.email_address)

# Get and delete
inbox = await client.inboxes.get(inbox_id="inbox-uuid")
await client.inboxes.delete(inbox_id="inbox-uuid")
```

## Messages

Send and retrieve messages. NornWeave automatically converts content to Markdown for LLM consumption.

```python
# Send message (body is Markdown)
response = client.messages.send(
    inbox_id="inbox-uuid",
    to=["recipient@example.com"],
    subject="Hello from my AI agent",
    body="# Welcome\n\nThis is a **markdown** email."
)
print(f"Message ID: {response.id}, Status: {response.status}")

# Reply to existing thread
response = client.messages.send(
    inbox_id="inbox-uuid",
    to=["recipient@example.com"],
    subject="Re: Hello",
    body="Thanks for your message!",
    reply_to_thread_id="thread-uuid"
)

# List messages for an inbox (paginated)
for message in client.messages.list(inbox_id="inbox-uuid"):
    print(f"[{message.direction}] {message.content_clean[:100]}")

# Get single message by ID
message = client.messages.get(message_id="message-uuid")
print(message.content_clean)  # LLM-ready markdown content
```

### Async Usage

```python
# Send message
response = await client.messages.send(
    inbox_id="inbox-uuid",
    to=["recipient@example.com"],
    subject="Hello",
    body="Message content in **Markdown**"
)

# List messages
async for message in client.messages.list(inbox_id="inbox-uuid"):
    print(message.content_clean)
```

## Threads

Threads group related messages in conversations. Get thread details with LLM-ready conversation history.

```python
# List threads for an inbox (sorted by most recent activity)
for thread in client.threads.list(inbox_id="inbox-uuid"):
    print(f"{thread.subject} - Last activity: {thread.last_message_at}")

# Get thread with full conversation history (LLM-ready format)
thread = client.threads.get(thread_id="thread-uuid")
print(f"Subject: {thread.subject}")

# Messages are formatted for LLM context
for msg in thread.messages:
    print(f"[{msg.role}] {msg.author}: {msg.content}")
    # role is "user" for inbound, "assistant" for outbound
```

### Thread Response Format

The thread detail response is optimized for LLM context windows:

```python
{
    "id": "thread-uuid",
    "subject": "Question about my account",
    "messages": [
        {
            "role": "user",          # Inbound messages
            "author": "customer@example.com",
            "content": "# My Question\n\nI need help with...",  # Markdown
            "timestamp": "2026-01-15T10:30:00Z"
        },
        {
            "role": "assistant",     # Outbound messages
            "author": "support@yourdomain.com",
            "content": "Thank you for reaching out...",
            "timestamp": "2026-01-15T10:45:00Z"
        }
    ]
}
```

### Async Usage

```python
# List threads
async for thread in client.threads.list(inbox_id="inbox-uuid"):
    print(thread.subject)

# Get thread with messages
thread = await client.threads.get(thread_id="thread-uuid")
```

## Search

Search messages by content within an inbox.

```python
# Search messages (returns paginated results)
for result in client.search.query(
    inbox_id="inbox-uuid",
    query="password reset"
):
    print(f"Thread: {result.thread_id}")
    print(f"Content: {result.content_clean[:200]}")

# Get full search response with count
response = client.search.query_raw(
    inbox_id="inbox-uuid",
    query="invoice",
    limit=10
)
print(f"Found {response.count} messages")
for item in response.items:
    print(item.content_clean)
```

### Async Usage

```python
# Search with async iteration
async for result in client.search.query(
    inbox_id="inbox-uuid",
    query="urgent"
):
    print(result.content_clean)

# Get full response
response = await client.search.query_raw(
    inbox_id="inbox-uuid",
    query="billing"
)
```

## Health Check

```python
# Check API health
health = client.health()
print(health.status)  # "ok"
```

## Context Manager

Use context managers to ensure connections are properly closed:

```python
# Sync
with NornWeave(base_url="http://localhost:8000") as client:
    inbox = client.inboxes.create(name="Test", email_username="test")

# Async
async with AsyncNornWeave(base_url="http://localhost:8000") as client:
    inbox = await client.inboxes.create(name="Test", email_username="test")
```

## Pagination

All list endpoints support pagination with limit and offset:

```python
# Manual pagination
pager = client.inboxes.list(limit=10, offset=0)
first_page = list(pager)

# Or iterate through all pages automatically
for inbox in client.inboxes.list(limit=10):
    print(inbox.email_address)
```

## Error Handling

```python
from nornweave_client import NornWeaveError, NotFoundError, ConflictError

try:
    inbox = client.inboxes.get(inbox_id="nonexistent")
except NotFoundError as e:
    print(f"Inbox not found: {e}")
except ConflictError as e:
    print(f"Conflict: {e}")
except NornWeaveError as e:
    print(f"API error: {e}")
```

## REST API Reference

If not using the Python client, you can call the REST API directly:

### Inboxes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/inboxes` | Create inbox |
| GET | `/v1/inboxes` | List inboxes |
| GET | `/v1/inboxes/{inbox_id}` | Get inbox |
| DELETE | `/v1/inboxes/{inbox_id}` | Delete inbox |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/messages` | Send message |
| GET | `/v1/messages?inbox_id=...` | List messages |
| GET | `/v1/messages/{message_id}` | Get message |

### Threads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/threads?inbox_id=...` | List threads |
| GET | `/v1/threads/{thread_id}` | Get thread with messages |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/search` | Search messages |

## Webhooks

NornWeave receives inbound emails via webhooks from email providers. See the reference files for webhook configuration:

- [webhooks.md](references/webhooks.md) - Webhook setup for Mailgun, SES, SendGrid, and Resend

## MCP Integration

NornWeave includes built-in MCP (Model Context Protocol) support for direct integration with Claude, Cursor, and other AI tools:

- **Huginn** (Resources) - Read-only access to inboxes, threads, messages
- **Muninn** (Tools) - Actions like sending messages, creating inboxes

Configure NornWeave as an MCP server in your AI tool to give agents direct email capabilities.
