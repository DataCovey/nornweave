## Context

NornWeave provides a REST API for managing email inboxes, threads, and messages. n8n is a popular workflow automation platform that allows users to connect services via "nodes." Community nodes are npm packages that extend n8n's capabilities.

Currently, n8n users must use the generic HTTP Request node to interact with NornWeave, which requires manual configuration of endpoints, authentication, and response handling. A native node would provide a better UX with pre-configured operations, proper typing, and trigger support.

**Stakeholders**: n8n users building email automation workflows, NornWeave users wanting low-code integrations.

## Goals / Non-Goals

**Goals:**
- Provide a native n8n node that exposes all NornWeave v1 API operations
- Support webhook-based triggers for real-time workflow activation on new emails
- Follow n8n community node standards for potential verification
- Zero runtime dependencies (per n8n verification guidelines)
- TypeScript implementation with full type safety

**Non-Goals:**
- MCP integration within n8n (n8n has its own AI features)
- Polling-based triggers (NornWeave supports webhooks natively)
- Custom domain management via n8n (out of scope for initial release)
- Supporting NornWeave versions < 1.0

## Decisions

### 1. Package Location: Monorepo under `packages/`

**Decision**: Create `packages/n8n-nodes-nornweave/` in the NornWeave repository, scaffolded from the official [n8n-nodes-starter](https://github.com/n8n-io/n8n-nodes-starter).

**Alternatives considered**:
- Separate repository: Would complicate keeping the node in sync with API changes
- npm-only (no source in repo): Loses version control and contribution workflow

**Rationale**: Monorepo allows atomic changes when API evolves, shared CI/CD, and easier contributor experience. The package is still published independently to npm.

### 2. Implementation Style: Declarative for Action Node

**Decision**: Use the [Declarative Style](https://docs.n8n.io/integrations/creating-nodes/build/declarative-style/) for the action node. Define operations in JSON-like structure using `routing` properties rather than writing raw HTTP request code.

**Alternatives considered**:
- Programmatic style: More flexible but requires ~80% more code
- Mixed approach: Unnecessary complexity for a straightforward REST API

**Rationale**: NornWeave has a clean REST API that maps perfectly to declarative style. Benefits:
- Reduces boilerplate significantly
- Authentication handled automatically via credential routing
- Standardized error handling
- Easier to maintain and extend

The trigger node will use programmatic style since webhook handling requires custom logic.

### 3. Node Architecture: One Action Node + One Trigger Node

**Decision**: Create two nodes:
1. `NornWeave` - Action node with resource/operation pattern (declarative)
2. `NornWeave Trigger` - Webhook trigger node for inbound events (programmatic)

**Alternatives considered**:
- Single node with trigger mode: n8n convention separates action and trigger nodes
- Multiple action nodes per resource: Increases maintenance burden

**Rationale**: Follows n8n patterns (e.g., Slack node + Slack Trigger). Resource/operation pattern is standard for REST APIs with multiple resources.

### 4. Trigger Implementation: Webhook-based

**Decision**: Implement `NornWeaveTrigger` as a webhook node that:
1. Registers a webhook URL with NornWeave when workflow activates
2. Receives POST requests when emails arrive or delivery events occur
3. Deregisters webhook when workflow deactivates

**Alternatives considered**:
- Polling trigger: Inefficient and adds latency
- Manual webhook setup: Poor UX, requires users to configure webhooks themselves

**Rationale**: NornWeave already has webhook infrastructure. Dynamic webhook registration provides the best UX. This requires adding a webhook registration API to NornWeave (see Risks).

### 5. Credential Type: Base URL + Header Auth

**Decision**: Create `NornWeaveApi` credential type using n8n's built-in Header Auth pattern:
- `baseUrl` (string, required): NornWeave instance URL
- `apiKey` (string, optional): API key sent as `X-API-Key` header

**Rationale**: 
- NornWeave is self-hosted, so base URL must be configurable
- Using n8n's built-in auth types handles security automatically
- API key is optional for forward compatibility (auth not fully implemented yet)
- Header auth is the standard pattern for API keys

### 6. Resource/Operation Structure

**Decision**: Organize the action node with these resources and operations:

| Resource | Operations |
|----------|------------|
| Inbox | Create, Delete, Get, Get Many |
| Message | Get, Get Many, Send |
| Thread | Get, Get Many |
| Search | Query |

Each parameter includes:
- Clear `description` for tooltips
- Explicit `type` and `default` values
- `options` arrays for fixed-choice fields (dropdowns)

**Rationale**: Maps directly to NornWeave's v1 API structure. "Get Many" naming follows n8n convention for list operations.

### 7. Pagination: Built-in "Get Many" Pattern

**Decision**: Implement pagination for all list operations using n8n's standard pattern:
- Add `returnAll` boolean parameter (default: false)
- Add `limit` parameter when `returnAll` is false
- Use declarative `routing.send.paginate` for automatic pagination

**Alternatives considered**:
- Manual offset handling: More code, inconsistent UX
- No pagination: Would limit usefulness for large datasets

**Rationale**: NornWeave uses limit/offset pagination. n8n's declarative pagination handles this automatically when configured correctly. Users can choose to fetch all items or a specific count.

### 8. Output Typing: Array of Objects

**Decision**: All operations return `INodeExecutionData[]`, even for single-item responses. Wrap single objects in arrays.

**Rationale**: n8n requires consistent output typing. Returning arrays ensures compatibility with downstream nodes and iteration patterns.

### 9. Node Versioning

**Decision**: Start at version 1. Use n8n's [versioning system](https://docs.n8n.io/integrations/creating-nodes/build/reference/versioning/) for breaking changes.

**Implementation**:
- Set `version: 1` in node definition
- Increment version for breaking parameter changes
- Maintain backwards compatibility using version-specific defaults

**Rationale**: Allows existing workflows to continue working when the node is updated. Critical for community trust.

### 10. Build Tooling: n8n-node CLI

**Decision**: Use `n8n-node` CLI tool for scaffolding, linting, and local testing.

**Alternatives considered**:
- Manual setup: Error-prone, may miss n8n conventions
- Custom build scripts: Unnecessary when official tooling exists

**Rationale**: n8n strongly recommends this tool for nodes intended for verification. Ensures correct structure and simplifies testing.

### 11. No Runtime Dependencies

**Decision**: Implement all HTTP calls using n8n's built-in `IHttpRequestHelper` utilities and declarative routing.

**Alternatives considered**:
- axios/got: Would fail n8n verification requirements
- fetch polyfill: Unnecessary complexity

**Rationale**: n8n verification guidelines prohibit runtime dependencies. Declarative style with routing handles this automatically.

## Risks / Trade-offs

### Risk: Webhook Registration API Doesn't Exist

**Risk**: NornWeave currently doesn't have an API for registering/deregistering webhooks dynamically. Workflows need this to auto-configure.

**Mitigation**: 
- Phase 1: Document manual webhook setup (user configures webhook URL in their email provider)
- Phase 2: Add webhook registration API to NornWeave (`POST /v1/webhooks`, `DELETE /v1/webhooks/{id}`)

### Risk: Breaking API Changes

**Risk**: NornWeave API is pre-1.0; changes could break the node.

**Mitigation**: 
- Pin to v1 API prefix
- Monorepo structure allows coordinated updates
- Semantic versioning for the npm package

### Risk: n8n Verification Rejection

**Risk**: n8n may reject verification if the node competes with paid features or doesn't meet UX standards.

**Mitigation**:
- Follow all technical and UX guidelines
- Email functionality is common in community nodes (e.g., IMAP, Gmail triggers exist)
- Ensure proper documentation and error handling

### Trade-off: Manual Webhook Setup (Phase 1)

**Trade-off**: Users must manually configure their email provider to POST to the n8n webhook URL.

**Acceptance**: This is acceptable for Phase 1. Many community nodes work this way. Can improve in Phase 2 with dynamic registration.

## Open Questions

1. **Attachment handling**: Should the trigger node include attachment content or just metadata? Large attachments could exceed n8n's 16MB webhook payload limit.
   - *Proposed*: Include metadata only; add "Download Attachment" operation to fetch content on demand.

2. **Event filtering**: Should the trigger node support filtering by event type (e.g., only `email.received`, not delivery events)?
   - *Proposed*: Yes, add an "Events" multi-select parameter with sensible defaults.

3. **Thread context**: Should "Send Message" operation auto-fetch thread context for AI workflows?
   - *Proposed*: No, keep operations simple. Users can chain Get Thread → AI Node → Send Message.

## References

**Starter template:**
- [n8n-nodes-starter](https://github.com/n8n-io/n8n-nodes-starter) - Official boilerplate with build tools and examples

**Documentation:**
- [Declarative Style Guide](https://docs.n8n.io/integrations/creating-nodes/build/declarative-style/) - Primary implementation approach
- [UI Elements Reference](https://docs.n8n.io/integrations/creating-nodes/build/reference/ui-elements/) - Available input types
- [Node Versioning](https://docs.n8n.io/integrations/creating-nodes/build/reference/versioning/) - Breaking change handling
- [Publishing to npm](https://docs.n8n.io/integrations/community-nodes/installation/pub-to-npm/) - Release process

**Example nodes to study:**
- [GithubIssues.node.ts](https://github.com/n8n-io/n8n-nodes-starter/blob/master/nodes/GithubIssues/GithubIssues.node.ts) - Declarative style example
- [n8n-nodes-mastodon](https://github.com/n8n-community-node/n8n-nodes-mastodon) - OAuth + complex API patterns
- [awesome-n8n](https://github.com/restyler/awesome-n8n) - Community node collection for reference
