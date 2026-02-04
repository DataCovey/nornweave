## Why

NornWeave supports Mailgun and SendGrid as email providers, but AWS SES remains a stub. SES is the most cost-effective option for high-volume email (~$0.10/1000 emails) and is often already in use by AWS-native deployments. Completing the SES adapter expands provider choice and unlocks NornWeave for AWS-centric users.

## What Changes

- Implement `SESAdapter.send_email()` using AWS SES v2 API with raw MIME support for attachments
- Implement `SESAdapter.parse_inbound_webhook()` to handle SES→SNS→HTTP notification flow
- Add SNS subscription confirmation handling (required for SES inbound)
- Add webhook signature verification for SNS notifications
- Update `.env.example` with SES-specific configuration (SNS topic ARN, endpoint URL)
- Update `web/content/docs/guides/ses.md` setup guide covering domain verification, receipt rules, and SNS configuration

## Capabilities

### New Capabilities

- `ses-adapter`: AWS SES implementation of EmailProvider—send via SES v2 API, receive via SNS notifications, SNS signature verification

### Modified Capabilities

_None. This adds a new provider adapter without changing existing behavior._

## Impact

- **Code**: `src/nornweave/adapters/ses.py` (complete implementation), new SNS verification utilities
- **Dependencies**: Add `aioboto3` or use `httpx` with SES v2 REST API directly; `cryptography` for SNS signature verification
- **Config**: New env vars: `AWS_SES_CONFIGURATION_SET` (optional), `SES_SNS_TOPIC_ARN` (for inbound)
- **Webhooks**: New route or handler branch for SNS notification format (JSON, not multipart form)
- **Docs**: New SES setup guide with AWS Console/CLI instructions for receipt rules and SNS topics

## Non-goals

- SES SMTP interface (using API for programmatic control and async compatibility)
- SES event webhooks for delivery/bounce tracking (future enhancement)
- Automatic SNS topic/subscription provisioning (users configure manually per guide)
- SES v1 API support (v2 only)
