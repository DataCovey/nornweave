# REST API

Base URL: `/v1` (with optional prefix).

## Authentication

Send the API key in the header:

```
Authorization: Bearer YOUR_API_KEY
```

## Inboxes

- `POST /v1/inboxes` — Create inbox (body: `name`, `email_username`)
- `GET /v1/inboxes/{inbox_id}` — Get inbox
- `DELETE /v1/inboxes/{inbox_id}` — Delete inbox
- `GET /v1/inboxes/{inbox_id}/messages` — List messages (Phase 1)

## Threads

- `GET /v1/threads/{thread_id}` — Get thread (Markdown-formatted messages for LLM context)

## Messages

- `POST /v1/messages` — Send message (body: `inbox_id`, `to`, `subject`, `body`, optional `reply_to_thread_id`)
- `GET /v1/messages/{message_id}` — Get message (raw/parsed)

## Search

- `POST /v1/search` — Search (body: `query`, `inbox_id`). Phase 1: SQL ILIKE; Phase 3: vector search.

## Webhooks (inbound)

- `POST /webhooks/mailgun` — Mailgun inbound
- `POST /webhooks/sendgrid` — SendGrid inbound
- `POST /webhooks/ses` — AWS SES inbound (if applicable)

Configure these URLs in your provider dashboard to receive inbound email.
