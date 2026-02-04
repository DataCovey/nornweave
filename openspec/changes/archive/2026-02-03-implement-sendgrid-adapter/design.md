## Context

NornWeave supports multiple email providers through an adapter pattern defined by the `EmailProvider` abstract base class. Currently implemented adapters include Resend (full implementation) and Mailgun (full implementation). The SendGrid adapter exists as a stub with `NotImplementedError` for both required methods.

SendGrid uses two distinct APIs:
- **Sending**: v3 Mail Send API (`POST /v3/mail/send`) - JSON payload with `personalizations` array structure
- **Receiving**: Inbound Parse Webhook - multipart/form-data POST similar to Mailgun's approach

Test fixtures already exist in `tests/fixtures/webhooks/` for SendGrid payloads, indicating the expected webhook structure.

## Goals / Non-Goals

**Goals:**
- Implement `send_email` method following the same patterns as Resend/Mailgun adapters
- Implement `parse_inbound_webhook` to handle Inbound Parse webhook payloads
- Implement ECDSA signature verification for webhook security
- Support threading headers (Message-ID, In-Reply-To, References) for email threading
- Support attachments (both regular and inline) for send and receive
- Support CC/BCC recipients
- Add helper methods for webhook event type detection
- Maintain consistency with existing adapter implementations

**Non-Goals:**
- Event Webhook handling (bounces, opens, clicks) - only Inbound Parse for receiving
- SendGrid template support (`template_id`, `dynamic_template_data`)
- Scheduled sends (`send_at`)
- IP pools, ASM groups, or tracking settings
- OAuth verification for webhooks (signature verification is simpler and sufficient)
- Automatic security policy creation via SendGrid API (users configure this themselves)

## Decisions

### 1. Use httpx directly instead of SendGrid SDK

**Decision**: Use `httpx.AsyncClient` to call SendGrid's REST API directly.

**Rationale**: 
- Consistency with Resend and Mailgun adapters which both use httpx
- The official `sendgrid` Python SDK is synchronous; using it would require running in a thread pool executor
- Direct API calls give us full control over the request/response handling
- Reduces dependency footprint (no need to add `sendgrid` package)

**Alternatives considered**:
- Use official SDK with `asyncio.to_thread()` - adds complexity and a new dependency

### 2. Map personalizations array to simple recipient list

**Decision**: Create a single personalizations entry with all recipients, rather than one per recipient.

**Rationale**:
- SendGrid's personalizations array is designed for mail merge scenarios
- For NornWeave's use case, all recipients receive the same email
- Simpler implementation that matches the `send_email` interface

**Request structure**:
```json
{
  "personalizations": [{ "to": [...], "cc": [...], "bcc": [...] }],
  "from": { "email": "..." },
  "subject": "...",
  "content": [{ "type": "text/plain", "value": "..." }, { "type": "text/html", "value": "..." }],
  "headers": { "Message-ID": "...", "In-Reply-To": "...", "References": "..." },
  "attachments": [{ "content": "base64...", "filename": "...", "type": "...", "disposition": "..." }]
}
```

### 3. Parse headers string into dict for Inbound Parse

**Decision**: Parse the `headers` field (newline-separated string) into a dictionary for easier access.

**Rationale**:
- SendGrid sends headers as a raw string, not JSON like the `envelope` or `charsets` fields
- Parsing enables easy extraction of Message-ID, In-Reply-To, References for threading
- Consistent with how we access headers in the `InboundMessage` structure

### 4. Handle attachments via attachment-info JSON

**Decision**: Use `attachment-info` JSON field to get attachment metadata, with actual files in separate form fields.

**Rationale**:
- SendGrid's Inbound Parse sends attachment metadata in `attachment-info` as JSON
- Actual file content comes as separate form fields (`attachment1`, `attachment2`, etc.)
- This matches the existing test fixture structure in `sendgrid_inline_image.json`
- `content-ids` JSON maps Content-ID to attachment field name for inline images

### 5. Implement ECDSA signature verification for webhooks

**Decision**: Implement signature verification for Inbound Parse webhooks using SendGrid's ECDSA signing mechanism.

**Rationale**:
- SendGrid supports cryptographic signature verification for Inbound Parse via security policies
- Uses ECDSA (Elliptic Curve Digital Signature Algorithm) with public/private key pair
- Headers provided: `X-Twilio-Email-Event-Webhook-Signature` and `X-Twilio-Email-Event-Webhook-Timestamp`
- Verification is optional but strongly recommended for production deployments

**Implementation approach**:
- Add `verify_webhook_signature(payload: bytes, headers: dict, public_key: str)` method
- Use Python's `cryptography` library for ECDSA verification (already in dependencies)
- Signature is computed over raw request body - must use unparsed multipart/form-data
- Public key is obtained when creating a security policy via SendGrid API and stored in config

**Alternatives considered**:
- OAuth verification - more complex setup, requires OAuth server; signature verification is simpler
- No verification - insecure for production use

## Risks / Trade-offs

**[Risk] Signature verification requires raw request body** → SendGrid's multipart/form-data payloads must be verified against the raw unparsed body. Some web frameworks auto-parse multipart data, which breaks verification. Document that FastAPI's `Request.body()` must be used before form parsing.

**[Risk] Public key management** → Users must store the ECDSA public key from their SendGrid security policy. If the key is rotated, the config must be updated. Document this in the setup guide.

**[Risk] SendGrid API rate limits** → The adapter doesn't implement rate limiting; this is handled at the Skuld (sender) layer. Document SendGrid's rate limits in the guide.

**[Risk] Large attachments in Inbound Parse** → SendGrid has a 30MB total message size limit. The adapter will parse whatever SendGrid sends; storage limits are enforced elsewhere.

**[Trade-off] No EU regional support** → The adapter uses `api.sendgrid.com`. EU users on SendGrid Pro+ would need `api.eu.sendgrid.com`. Could add as future enhancement via config option.

**[Trade-off] Signature verification is optional** → Unlike Resend (which uses Svix and always includes signatures), SendGrid requires users to explicitly configure a security policy. The adapter supports verification but doesn't require it.
