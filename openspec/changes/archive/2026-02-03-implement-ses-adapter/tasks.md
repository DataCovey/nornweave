## 1. AWS SigV4 Authentication

- [x] 1.1 Implement AWS Signature Version 4 signing utility function
- [x] 1.2 Create `_sign_request` method that adds Authorization and X-Amz-Date headers
- [x] 1.3 Add SES API endpoint URL construction based on region

## 2. Send Email Implementation

- [x] 2.1 Implement `send_email` method with basic recipients, subject, and body
- [x] 2.2 Add Markdown-to-HTML conversion when html_body not provided
- [x] 2.3 Add support for threading headers (Message-ID, In-Reply-To, References) via Headers array
- [x] 2.4 Add support for CC and BCC recipients via Destination object
- [x] 2.5 Add support for attachments via Attachments array (regular and inline)
- [x] 2.6 Add support for reply_to via ReplyToAddresses
- [x] 2.7 Add optional ConfigurationSetName from AWS_SES_CONFIGURATION_SET env var
- [x] 2.8 Implement error handling for SES API errors (AccountSuspendedException, etc.)

## 3. SNS Webhook Infrastructure

- [x] 3.1 Create `SESWebhookError` exception class
- [x] 3.2 Implement `get_sns_message_type` helper to identify SNS message types
- [x] 3.3 Implement SNS subscription confirmation handler (fetch SubscribeURL)
- [x] 3.4 Implement `is_inbound_event` and `get_event_type` helper methods

## 4. SNS Signature Verification

- [x] 4.1 Implement SigningCertURL validation (must be from sns.{region}.amazonaws.com)
- [x] 4.2 Implement certificate fetching with LRU cache
- [x] 4.3 Implement canonical string-to-sign construction per SNS spec
- [x] 4.4 Implement `verify_webhook_signature` using X.509 certificate

## 5. Inbound Email Parsing

- [x] 5.1 Implement SNS envelope unwrapping (extract Message field as JSON)
- [x] 5.2 Parse SES notification structure (notificationType, receipt, mail, content)
- [x] 5.3 Extract verification results from receipt (SPF, DKIM, DMARC verdicts)
- [x] 5.4 Parse mail.commonHeaders for from, to, subject, messageId, etc.
- [x] 5.5 Implement MIME content parsing using Python email.parser.BytesParser
- [x] 5.6 Extract body_plain and body_html from MIME parts
- [x] 5.7 Parse attachments from MIME parts with filename, content_type, content
- [x] 5.8 Handle inline attachments with Content-ID and build content_id_map
- [x] 5.9 Implement `parse_inbound_webhook` that assembles InboundMessage

## 6. Configuration

- [x] 6.1 Update `.env.example` with AWS_SES_CONFIGURATION_SET variable
- [x] 6.2 Add SES configuration to Settings/config if needed

## 7. Documentation

- [x] 7.1 Create/update `web/content/docs/guides/ses.md` setup guide
- [x] 7.2 Document SES domain verification and identity setup
- [x] 7.3 Document receipt rule and SNS topic configuration
- [x] 7.4 Document MX record setup for email receiving
- [x] 7.5 Document regional availability limitations for inbound email
- [x] 7.6 Document 150KB SNS content limit

## 8. Testing

- [x] 8.1 Create unit tests for SigV4 signing
- [x] 8.2 Create unit tests for send_email with various scenarios
- [x] 8.3 Create unit tests for SNS signature verification
- [x] 8.4 Create unit tests for subscription confirmation handling
- [x] 8.5 Create unit tests for MIME parsing
- [x] 8.6 Create unit tests for parse_inbound_webhook with various payloads
- [x] 8.7 Add test fixtures for SES/SNS notification payloads

## 9. Finalization

- [x] 9.1 Run linter and fix any issues
- [x] 9.2 Run type checker and fix any issues
- [x] 9.3 Document the changes in CHANGELOG.md
