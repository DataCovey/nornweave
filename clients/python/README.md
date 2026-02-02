# NornWeave Python Client

The NornWeave Python library provides convenient access to the NornWeave APIs from Python.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Async Client](#async-client)
- [Exception Handling](#exception-handling)
- [Advanced](#advanced)
  - [Access Raw Response Data](#access-raw-response-data)
  - [Retries](#retries)
  - [Timeouts](#timeouts)
  - [Custom Client](#custom-client)
- [Pagination](#pagination)

## Installation

```bash
pip install nornweave-client
```

Or install from source using [uv](https://docs.astral.sh/uv/) (recommended) or pip:

```bash
cd clients/python

# Using uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

Instantiate and use the client with the following:

```python
from nornweave_client import NornWeave

client = NornWeave(base_url="http://localhost:8000")

# Create an inbox
inbox = client.inboxes.create(name="Support", email_username="support")
print(f"Created inbox: {inbox.email_address}")

# List inboxes
for inbox in client.inboxes.list():
    print(inbox.name)

# Get an inbox
inbox = client.inboxes.get(inbox_id="...")

# Delete an inbox
client.inboxes.delete(inbox_id="...")

# Send a message
response = client.messages.send(
    inbox_id="...",
    to=["recipient@example.com"],
    subject="Hello",
    body="This is the message body in **Markdown**."
)

# List messages
for message in client.messages.list(inbox_id="..."):
    print(message.content_clean)

# List threads
for thread in client.threads.list(inbox_id="..."):
    print(f"{thread.subject} - {thread.message_count} messages")

# Get thread with messages
thread = client.threads.get(thread_id="...")
for msg in thread.messages:
    print(f"{msg.role}: {msg.content}")

# Search messages
results = client.search.query(query="invoice", inbox_id="...")
for result in results:
    print(result.content_clean)
```

## Async Client

The SDK also exports an `async` client so that you can make non-blocking calls to our API.

```python
import asyncio
from nornweave_client import AsyncNornWeave

client = AsyncNornWeave(base_url="http://localhost:8000")

async def main() -> None:
    inbox = await client.inboxes.create(name="Support", email_username="support")
    print(f"Created inbox: {inbox.email_address}")

asyncio.run(main())
```

## Exception Handling

When the API returns a non-success status code (4xx or 5xx response), a subclass of the following error will be thrown.

```python
from nornweave_client import ApiError

try:
    client.inboxes.get(inbox_id="nonexistent")
except ApiError as e:
    print(e.status_code)  # 404
    print(e.body)         # {"detail": "Inbox not found"}
```

Specific exception types:

- `NotFoundError` - 404 responses
- `ValidationError` - 422 responses (invalid request data)
- `RateLimitError` - 429 responses
- `ServerError` - 5xx responses

## Advanced

### Access Raw Response Data

The SDK provides access to raw response data, including headers, through the `.with_raw_response` property.

```python
response = client.inboxes.with_raw_response.create(
    name="Support",
    email_username="support"
)
print(response.headers)      # httpx.Headers
print(response.status_code)  # 201
print(response.data)         # Inbox object
```

### Retries

The SDK is instrumented with automatic retries with exponential backoff. A request will be retried as long as the request is deemed retryable and the number of retry attempts has not grown larger than the configured retry limit (default: 2).

A request is deemed retryable when any of the following HTTP status codes is returned:

- 408 (Timeout)
- 429 (Too Many Requests)
- 5XX (Internal Server Errors)

Use the `max_retries` request option to configure this behavior.

```python
client.inboxes.create(
    name="Support",
    email_username="support",
    request_options={"max_retries": 1}
)
```

### Timeouts

The SDK defaults to a 60 second timeout. You can configure this with a timeout option at the client or request level.

```python
from nornweave_client import NornWeave

# Client-level timeout
client = NornWeave(
    base_url="http://localhost:8000",
    timeout=20.0,
)

# Request-level timeout override
client.inboxes.create(
    name="Support",
    email_username="support",
    request_options={"timeout": 5.0}
)
```

### Custom Client

You can override the `httpx` client to customize it for your use-case. Some common use-cases include support for proxies and transports.

```python
import httpx
from nornweave_client import NornWeave

client = NornWeave(
    base_url="http://localhost:8000",
    httpx_client=httpx.Client(
        proxy="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

For async:

```python
import httpx
from nornweave_client import AsyncNornWeave

client = AsyncNornWeave(
    base_url="http://localhost:8000",
    httpx_client=httpx.AsyncClient(
        proxy="http://my.test.proxy.example.com",
    ),
)
```

## Pagination

Paginated requests will return a `SyncPager` or `AsyncPager`, which can be used as generators for the underlying objects.

```python
# Iterate over all items
for inbox in client.inboxes.list():
    print(inbox.name)

# Paginate page-by-page
for page in client.inboxes.list().iter_pages():
    print(f"Page with {len(page.items)} items")
    for inbox in page.items:
        print(inbox.name)

# Async iteration
async for inbox in async_client.inboxes.list():
    print(inbox.name)
```

## License

Apache-2.0
