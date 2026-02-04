## Context

NornWeave currently has three working email provider adapters (Mailgun, SendGrid, Resend) plus a stub SES adapter. All existing adapters use `httpx` for async HTTP, implement the `EmailProvider` interface, and follow a similar pattern: `send_email()` calls the provider's REST API, `parse_inbound_webhook()` converts provider-specific webhook payloads to `InboundMessage`.

AWS SES differs from other providers in how it handles inbound email:
- **SendGrid/Mailgun/Resend**: Direct HTTP webhook with email content in payload
- **SES**: Receipt Rule → SNS Topic → HTTP Subscription (indirect, with SNS envelope)

The stub implementation exists at `src/nornweave/adapters/ses.py` with `NotImplementedError` placeholders.

## Goals / Non-Goals

**Goals:**
- Implement `SESAdapter.send_email()` supporting all `EmailProvider` interface features (attachments, threading headers, CC/BCC)
- Implement `SESAdapter.parse_inbound_webhook()` to handle SNS notification payloads containing SES email data
- Handle SNS subscription confirmation automatically
- Verify SNS message signatures for security
- Update `.env.example` with SES configuration
- Create setup guide for domain verification, receipt rules, and SNS configuration

**Non-Goals:**
- SES SMTP interface (API-only for async compatibility)
- S3-based email storage (SNS content delivery only; S3 support is future work)
- SES event webhooks for bounces/complaints (future enhancement)
- Automatic AWS resource provisioning (manual setup per guide)
- SES v1 API support

## Decisions

### Decision 1: HTTP Client — httpx with AWS SigV4 signing

**Choice**: Use `httpx` with manual AWS Signature Version 4 signing

**Alternatives considered**:
- `aioboto3` / `aiobotocore`: Full AWS SDK, but heavyweight dependency (~15MB), brings boto3's sync-first design patterns
- `httpx-auth-awssigv4`: Convenience library, but adds another dependency and may not be maintained

**Rationale**: 
- Consistent with existing adapters (all use httpx)
- SigV4 signing is well-documented and straightforward to implement (~50 lines)
- Keeps dependency footprint minimal
- Full control over async behavior

### Decision 2: Send Email API — SES v2 with Content.Simple

**Choice**: Use SES v2 API `SendEmail` action with `Content.Simple` (including Headers and Attachments)

**Alternatives considered**:
- SES v2 `Content.Raw`: Full MIME control but requires manual MIME construction
- SES v1 `SendRawEmail`: Works but v1 is legacy

**Rationale**:
- SES v2 `Content.Simple` now supports custom `Headers` array (Message-ID, In-Reply-To, References)
- SES v2 `Content.Simple` now supports `Attachments` array with ContentId for inline images
- Simpler than raw MIME construction while meeting all requirements
- v2 API is the current standard

**Implementation**:
```python
# Send via SES v2 API
POST https://email.{region}.amazonaws.com/v2/email/outbound-emails
Content-Type: application/json
{
    "FromEmailAddress": "sender@example.com",
    "Destination": {
        "ToAddresses": ["recipient@example.com"],
        "CcAddresses": [...],
        "BccAddresses": [...]
    },
    "ReplyToAddresses": ["reply@example.com"],
    "Content": {
        "Simple": {
            "Subject": {"Data": "Subject", "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": "Plain text", "Charset": "UTF-8"},
                "Html": {"Data": "<p>HTML</p>", "Charset": "UTF-8"}
            },
            "Headers": [
                {"Name": "Message-ID", "Value": "<custom-id@example.com>"},
                {"Name": "In-Reply-To", "Value": "<parent-id@example.com>"},
                {"Name": "References", "Value": "<ref1> <ref2>"}
            ],
            "Attachments": [
                {
                    "FileName": "doc.pdf",
                    "ContentType": "application/pdf",
                    "RawContent": "base64-encoded-content",
                    "ContentDisposition": "attachment",
                    "ContentId": "cid:image1"  // for inline
                }
            ]
        }
    },
    "ConfigurationSetName": "optional-config-set"
}
```

**Note**: Response returns `MessageId` which is the SES message identifier.

### Decision 3: Inbound Email — SNS notifications with content included

**Choice**: Support SES Receipt Rule → SNS action with email content included in notification

**Alternatives considered**:
- S3 action + SNS notification with S3 location: More complex, requires S3 access
- Lambda function: Adds infrastructure complexity

**Rationale**:
- Simplest setup path (no S3 bucket required)
- SNS content action includes full email up to 150KB (sufficient for most emails)
- Consistent webhook pattern with other adapters
- Can add S3 support later for large emails

**Regional availability**: Email receiving is only available in specific regions (us-east-1, us-east-2, us-west-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-2, etc.). Guide must document this limitation.

**SNS envelope wrapping SES notification**:
```json
{
    "Type": "Notification",
    "MessageId": "sns-message-id",
    "TopicArn": "arn:aws:sns:region:account:topic",
    "Subject": "Amazon SES Email Receipt Notification",
    "Message": "<JSON string - see below>",
    "Timestamp": "2024-01-01T00:00:00.000Z",
    "SignatureVersion": "1",
    "Signature": "base64-signature",
    "SigningCertURL": "https://sns.region.amazonaws.com/...",
    "UnsubscribeURL": "https://sns.region.amazonaws.com/..."
}
```

**SES notification (inside `Message` field, JSON-encoded)**:
```json
{
    "notificationType": "Received",
    "receipt": {
        "timestamp": "2024-01-01T00:00:00.000Z",
        "processingTimeMillis": 500,
        "recipients": ["inbox@example.com"],
        "spamVerdict": {"status": "PASS"},
        "virusVerdict": {"status": "PASS"},
        "spfVerdict": {"status": "PASS"},
        "dkimVerdict": {"status": "PASS"},
        "dmarcVerdict": {"status": "PASS"},
        "action": {"type": "SNS", "topicArn": "..."}
    },
    "mail": {
        "timestamp": "2024-01-01T00:00:00.000Z",
        "messageId": "ses-message-id",
        "source": "sender@example.com",
        "destination": ["inbox@example.com"],
        "headers": [...],
        "commonHeaders": {
            "from": ["sender@example.com"],
            "to": ["inbox@example.com"],
            "subject": "Email subject",
            "messageId": "<original-message-id>"
        }
    },
    "content": "raw MIME email content (base64 or UTF-8)"
}
```

**Key fields for parsing**:
- `receipt.spfVerdict.status`, `dkimVerdict.status`, `dmarcVerdict.status` → verification results
- `mail.commonHeaders` → extracted headers (from, to, subject, messageId, etc.)
- `content` → raw MIME email to parse for body and attachments

### Decision 4: SNS Message Handling — Auto-confirm subscriptions

**Choice**: Automatically confirm SNS subscription requests by fetching the `SubscribeURL`

**Rationale**:
- Required for SNS→HTTP to work
- Standard pattern for SNS integrations
- Safe because we verify signatures

**Message types to handle**:
1. `SubscriptionConfirmation`: GET the `SubscribeURL` to confirm
2. `Notification`: Parse the `Message` field containing SES email data
3. `UnsubscribeConfirmation`: Log and ignore

### Decision 5: SNS Signature Verification

**Choice**: Verify all SNS messages using X.509 certificate from `SigningCertURL`

**Implementation**:
1. Validate `SigningCertURL` is from `sns.{region}.amazonaws.com`
2. Fetch and cache the signing certificate
3. Reconstruct the canonical string-to-sign per SNS spec
4. Verify signature using certificate's public key

**Rationale**:
- Prevents spoofed webhook requests
- Standard security practice for SNS integrations
- Similar pattern to SendGrid's ECDSA verification

### Decision 6: Configuration Variables

**New environment variables**:
```bash
# Existing (already in .env.example)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# New
AWS_SES_CONFIGURATION_SET=  # Optional: for tracking/analytics
```

**Note**: No SNS-specific config needed—the adapter auto-detects SNS payloads by `Type` field.

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| SNS 150KB content limit | Large emails with attachments fail inbound | Document limit in guide; S3 support as future enhancement |
| SigV4 implementation bugs | Auth failures, hard to debug | Use AWS test credentials; comprehensive test coverage |
| SNS certificate caching | Memory growth if many certs | LRU cache with TTL; certificates are per-region so bounded |
| Region mismatch | Sending works, receiving fails | Validate region config in guide; clear error messages |
| Email receiving regional limits | Not all SES regions support inbound | Document supported regions in guide; fail fast with clear error if unsupported region |

## Open Questions

1. **Large email handling**: When email exceeds 150KB and bounces, the webhook won't reach NornWeave. Should the guide recommend S3 action with Lambda for production, or is SNS-only acceptable for MVP? Propose: SNS-only for MVP with clear documentation of the 150KB limit.

2. **MIME parsing library**: Use Python's built-in `email` module or a library like `mailparser`? The `email` module is sufficient and zero-dependency. Propose: use `email.parser.BytesParser` for parsing raw MIME content.
