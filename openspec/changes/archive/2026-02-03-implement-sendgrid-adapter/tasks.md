## 1. Setup and Scaffolding

- [x] 1.1 Add `SendGridWebhookError` exception class for webhook verification failures
- [x] 1.2 Add constants for SendGrid API URL and header names
- [x] 1.3 Update `__init__` to accept optional `webhook_public_key` parameter

## 2. Send Email Implementation

- [x] 2.1 Implement `send_email` method with httpx async POST to `/v3/mail/send`
- [x] 2.2 Build personalizations array with to, cc, bcc recipients
- [x] 2.3 Build content array with text/plain and text/html (convert Markdown if needed)
- [x] 2.4 Add threading headers support (Message-ID, In-Reply-To, References)
- [x] 2.5 Add attachment support with base64 encoding and disposition
- [x] 2.6 Add reply_to and custom headers support
- [x] 2.7 Handle API response and extract message ID from X-Message-Id header
- [x] 2.8 Add error handling for non-2xx responses

## 3. Inbound Webhook Parsing

- [x] 3.1 Implement `parse_inbound_webhook` method to parse multipart/form-data payload
- [x] 3.2 Parse sender address from "Name <email>" format
- [x] 3.3 Parse headers string into dictionary
- [x] 3.4 Extract threading headers (Message-ID, In-Reply-To, References) from parsed headers
- [x] 3.5 Parse `attachment-info` JSON for attachment metadata
- [x] 3.6 Parse `content-ids` JSON for inline attachment mapping
- [x] 3.7 Create `InboundAttachment` objects with proper disposition
- [x] 3.8 Build `content_id_map` for inline image resolution
- [x] 3.9 Extract SPF and DKIM verification results

## 4. Webhook Signature Verification

- [x] 4.1 Implement `verify_webhook_signature` method using ECDSA
- [x] 4.2 Extract signature and timestamp from X-Twilio-Email-Event-Webhook-* headers
- [x] 4.3 Validate timestamp is within acceptable tolerance (5 minutes)
- [x] 4.4 Verify ECDSA signature against raw payload using public key
- [x] 4.5 Raise `SendGridWebhookError` for validation failures

## 5. Helper Methods

- [x] 5.1 Implement `get_event_type` static method (returns "inbound")
- [x] 5.2 Implement `is_inbound_event` static method (returns True for Inbound Parse payloads)

## 6. Unit Tests

- [x] 6.1 Create `tests/unit/test_adapters_sendgrid.py` test file
- [x] 6.2 Add tests for `send_email` with various parameter combinations
- [x] 6.3 Add tests for `parse_inbound_webhook` using existing fixtures
- [x] 6.4 Add tests for attachment parsing (regular and inline)
- [x] 6.5 Add tests for `verify_webhook_signature` (valid, invalid, expired, missing)
- [x] 6.6 Add tests for helper methods

## 7. Documentation

- [x] 7.1 Update `web/content/docs/guides/sendgrid.md` with webhook security setup instructions
- [x] 7.2 Add security policy configuration steps to the guide
- [x] 7.3 Update `.env.example` with `SENDGRID_WEBHOOK_PUBLIC_KEY` and related config keys

## 8. Finalize

- [x] 8.1 Run linter and fix any issues
- [x] 8.2 Run type checker and fix any issues
- [x] 8.3 Document changes in CHANGELOG.md
