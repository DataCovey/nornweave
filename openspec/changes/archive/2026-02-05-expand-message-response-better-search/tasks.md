## 1. Expand MessageResponse Model

- [x] 1.1 Update `MessageResponse` in `yggdrasil/routes/v1/messages.py` with all email metadata fields
- [x] 1.2 Update `_message_to_response()` function to map all fields from Message model
- [x] 1.3 Add unit tests for MessageResponse field mapping

## 2. Add Search Filter Parameters

- [x] 2.1 Make `inbox_id` optional and add `thread_id` query parameter to list messages endpoint
- [x] 2.2 Add validation to require at least one filter parameter (inbox_id or thread_id)
- [x] 2.3 Implement filter chaining logic in the endpoint
- [x] 2.4 Add text search across subject, text, and from_address fields when `q` is provided
- [x] 2.5 Add `total` field to `MessageListResponse` for pagination support
- [x] 2.6 Add unit tests for filter combinations and validation

## 3. Update Storage Adapter

- [x] 3.1 Update storage adapter methods to support optional thread_id filter
- [x] 3.2 Implement text search query with ILIKE on subject, text, from_address, and attachment filenames
- [x] 3.3 Add method to get total count of matching messages for pagination
- [x] 3.4 Add unit tests for storage adapter filter methods

## 4. Update MCP Tools

- [x] 4.1 Update `list_messages` tool in `muninn/tools.py` to accept thread_id parameter
- [x] 4.2 Add `search_messages` tool for dedicated text search with filter options
- [x] 4.3 Update MCP tool response schemas to include expanded message fields
- [x] 4.4 Update `huginn/client.py` methods with new search parameters
- [x] 4.5 Add unit tests for MCP tools with new parameters

## 5. Integration Testing

- [x] 5.1 Add integration tests for message filtering by thread_id
- [x] 5.2 Add integration tests for combined filter scenarios (inbox_id + thread_id)
- [x] 5.3 Add integration tests for text search with filters

## 6. Documentation

- [x] 6.1 Update REST API documentation in `web/content/docs/api/rest.md`
- [x] 6.2 Update MCP documentation in `web/content/docs/api/mcp.md`
- [x] 6.3 Update CHANGELOG.md with new features
