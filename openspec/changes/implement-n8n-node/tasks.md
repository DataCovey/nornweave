## 1. Package Setup

- [x] 1.1 Create `packages/n8n-nodes-nornweave/` directory in monorepo
- [x] 1.2 Initialize package using n8n-nodes-starter template (copy and adapt)
- [x] 1.3 Configure package.json with name `n8n-nodes-nornweave`, keywords including `n8n-community-node-package`
- [x] 1.4 Set up TypeScript configuration (tsconfig.json)
- [x] 1.5 Configure ESLint and Prettier for n8n conventions
- [x] 1.6 Add npm scripts: build, lint, dev, prepublishOnly

## 2. Credential Type

- [x] 2.1 Create `credentials/NornWeaveApi.credentials.ts`
- [x] 2.2 Implement baseUrl field (required, string, URL validation)
- [x] 2.3 Implement apiKey field (optional, string, password type)
- [x] 2.4 Configure header auth to send `X-API-Key` when apiKey is present
- [x] 2.5 Add credential test method (GET /health endpoint)
- [x] 2.6 Register credential in package.json n8n.credentials

## 3. Action Node Structure

- [x] 3.1 Create `nodes/NornWeave/NornWeave.node.ts` with declarative style
- [x] 3.2 Define node metadata (name, icon, description, version: 1)
- [x] 3.3 Implement Resource parameter with options: Inbox, Message, Thread, Search
- [x] 3.4 Implement Operation parameter with displayOptions per resource
- [x] 3.5 Register node in package.json n8n.nodes

## 4. Inbox Operations

- [x] 4.1 Implement Inbox > Create operation (POST /v1/inboxes)
- [x] 4.2 Add parameters: name (required), email_username (required)
- [x] 4.3 Implement Inbox > Delete operation (DELETE /v1/inboxes/{inbox_id})
- [x] 4.4 Add parameter: inbox_id (required)
- [x] 4.5 Implement Inbox > Get operation (GET /v1/inboxes/{inbox_id})
- [x] 4.6 Add parameter: inbox_id (required)
- [x] 4.7 Implement Inbox > Get Many operation (GET /v1/inboxes)
- [x] 4.8 Add pagination parameters: returnAll, limit

## 5. Message Operations

- [x] 5.1 Implement Message > Get operation (GET /v1/messages/{message_id})
- [x] 5.2 Add parameter: message_id (required)
- [x] 5.3 Implement Message > Get Many operation (GET /v1/messages)
- [x] 5.4 Add parameters: inbox_id (required), returnAll, limit
- [x] 5.5 Implement Message > Send operation (POST /v1/messages)
- [x] 5.6 Add parameters: inbox_id (required), to (required, array), subject (required), body (required, markdown)
- [x] 5.7 Add optional parameter: reply_to_thread_id for threading

## 6. Thread Operations

- [x] 6.1 Implement Thread > Get operation (GET /v1/threads/{thread_id})
- [x] 6.2 Add parameter: thread_id (required)
- [x] 6.3 Implement Thread > Get Many operation (GET /v1/threads)
- [x] 6.4 Add parameters: inbox_id (required), returnAll, limit

## 7. Search Operations

- [x] 7.1 Implement Search > Query operation (POST /v1/search)
- [x] 7.2 Add parameters: query (required), inbox_id (required)
- [x] 7.3 Add optional parameter: limit

## 8. Trigger Node

- [x] 8.1 Create `nodes/NornWeaveTrigger/NornWeaveTrigger.node.ts` with programmatic style
- [x] 8.2 Define trigger node metadata (name, icon, description, version: 1)
- [x] 8.3 Implement webhook method to generate test and production URLs
- [x] 8.4 Add Events parameter (multi-select) with options: email.received, email.sent, email.delivered, email.bounced, email.opened, email.clicked
- [x] 8.5 Implement event filtering logic (only trigger for selected event types)
- [x] 8.6 Transform incoming webhook payload to n8n execution data format
- [x] 8.7 Register trigger node in package.json n8n.nodes

## 9. Error Handling

- [x] 9.1 Create error transformation utility for API errors
- [x] 9.2 Handle HTTP 404 with resource-specific messages
- [x] 9.3 Handle HTTP 409 conflict errors (duplicate inbox)
- [x] 9.4 Handle HTTP 422 validation errors with field details
- [x] 9.5 Handle network errors with connection troubleshooting hints

## 10. Testing

- [x] 10.1 Set up Jest test configuration
- [x] 10.2 Write unit tests for credential validation
- [x] 10.3 Write unit tests for action node operations (mock HTTP)
- [x] 10.4 Write unit tests for trigger node event filtering
- [ ] 10.5 Manual test: install node in local n8n instance
- [ ] 10.6 Manual test: verify all operations against running NornWeave
- [ ] 10.7 Run n8n linter (`npm run lint`) and fix any issues

## 11. Documentation

- [x] 11.1 Write comprehensive README.md for npm package
- [x] 11.2 Include installation instructions in README
- [x] 11.3 Include credential setup guide in README
- [x] 11.4 Include webhook setup instructions in README (manual provider config)
- [x] 11.5 Create `web/content/docs/integrations/n8n.md` guide for NornWeave docs
- [x] 11.6 Add integration to docs site navigation
- [x] 11.7 Document changes in CHANGELOG.md
