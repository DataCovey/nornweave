## Why

The current Messages API returns a minimal response model missing essential email metadata like `subject`, `from_address`, `to_addresses`, `text`, and `timestamp`. This forces users to query the database directly or make additional API calls to get basic email information. Additionally, message search only supports filtering by `inbox_id` with a `q` parameter, but users need to search within specific threads or by message ID with text filtering.

## What Changes

- **Expand MessageResponse**: Add all essential email fields to `MessageResponse` including `subject`, `from_address`, `to_addresses`, `cc_addresses`, `bcc_addresses`, `text`, `html`, `timestamp`, `labels`, `preview`, `in_reply_to`, and `references`
- **Improve Search Filters**: Allow text search (`q` parameter) combined with `thread_id`, `inbox_id`, or both filters (single message retrieval uses existing `GET /v1/messages/{id}` endpoint)
- **Update MCP Tools**: Ensure MCP tools (`list_messages`, `search_messages`, `get_message`) expose the same filtering capabilities and return expanded message data

## Capabilities

### New Capabilities
- `message-search`: Defines search capabilities including text search with multi-filter support (thread_id, inbox_id, message_id combinations)

### Modified Capabilities
- `rest-api`: Update MessageResponse model to include all email metadata fields

## Impact

- **API Routes**: `yggdrasil/routes/v1/messages.py` - expand response model, update list/search endpoint parameters
- **MCP Tools**: `muninn/tools.py` - update message-related tools with new filters and response fields
- **MCP Client**: `huginn/client.py` - update client methods for new search parameters
- **Documentation**: `web/content/docs/api/rest.md`, `web/content/docs/api/mcp.md` - document new fields and filters
- **No breaking changes**: Existing API consumers continue to work (additive changes only)
