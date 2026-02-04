## Why

The SendGrid adapter in `src/nornweave/adapters/sendgrid.py` is currently a stub with `NotImplementedError` for both `send_email` and `parse_inbound_webhook` methods. SendGrid is one of the most popular transactional email providers, and full implementation is needed to support users who choose SendGrid as their email provider. The documentation guide exists but references functionality that doesn't work yet.

## What Changes

- **Implement `send_email` method**: Use httpx async client to call SendGrid's v3 Mail Send API (`POST /v3/mail/send`) with support for threading headers, CC/BCC, and attachments
- **Implement `parse_inbound_webhook` method**: Parse SendGrid Inbound Parse webhook payloads (multipart/form-data format) into standardized `InboundMessage`
- **Add attachment handling**: Parse `attachment-info` and `content-ids` JSON fields for inline images and regular attachments
- **Add webhook signature verification**: Implement optional signature verification using SendGrid's Event Webhook signing (if available for Inbound Parse)
- **Add helper methods**: `get_event_type`, `is_inbound_event` for consistency with other adapters
- **Update documentation**: Enhance the SendGrid Setup Guide with any implementation-specific details

## Capabilities

### New Capabilities

- `sendgrid-adapter`: Full implementation of the SendGrid email provider adapter with send and receive functionality

### Modified Capabilities

(none - this is implementing an existing stub, not modifying existing spec-level behavior)

## Impact

- **Code**: `src/nornweave/adapters/sendgrid.py` - full implementation
- **Tests**: New unit tests in `tests/unit/test_adapters_sendgrid.py`
- **Documentation**: `web/content/docs/guides/sendgrid.md` may need updates
- **Dependencies**: No new dependencies (uses existing httpx, markdown)
- **API**: No changes to external API - internal adapter implementation only
