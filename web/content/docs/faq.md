---
title: Frequently Asked Questions (FAQ)
slug: faq
description: >-
  Find answers to common questions about NornWeave, from core concepts to
  integration and best practices.
weight: 5
keywords:
  - NornWeave FAQ
  - inbox as a service
  - AI agent email
  - MCP email
  - self-hosted email API
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

Answers to common questions about NornWeave.

{{% details title="What is NornWeave?" closed="true" %}}
NornWeave is an **open-source, self-hosted** Inbox-as-a-Service API built for AI agents that need to communicate over email. Unlike traditional email APIs built for one-way notifications, NornWeave is built for **two-way conversations**: it gives your agents first-class support for **Inboxes**, **Threads**, and **Messages**, with HTML converted to clean Markdown and threading preserved. You can integrate via the **REST API** or the **MCP (Model Context Protocol)** server so Claude, Cursor, and other LLM clients can read, search, and send email directly.
{{% /details %}}

{{% details title="How is NornWeave different from services like AWS SES or Mailgun?" closed="true" %}}
SendGrid, Mailgun, Resend, and AWS SES are excellent for **transactional email** (receipts, password resets, marketing). NornWeave does **not** replace them---it sits **on top** of them. You bring your own provider (Mailgun, SendGrid, SES, Resend, or **IMAP/SMTP**); NornWeave adds a **conversational layer**: stateful **threads**, **inboxes** as first-class entities, HTML-to-Markdown parsing, semantic search, and MCP tools so agents can have two-way email conversations. Think of NornWeave as the brain that turns your existing provider into an agent-ready email backend.
{{% /details %}}

{{% details title="Can I use NornWeave without a transactional email provider?" closed="true" %}}
Yes! NornWeave supports a built-in **IMAP/SMTP** provider (`EMAIL_PROVIDER=imap-smtp`) that connects directly to any standard mail server---Gmail, Office 365, Fastmail, or self-hosted Postfix/Dovecot. Instead of webhooks, NornWeave polls the IMAP mailbox for new messages and sends outbound via SMTP. This is ideal when you don't want a dedicated transactional email account. See the [IMAP/SMTP Setup Guide]({{< relref "guides/imap-smtp" >}}) for details.
{{% /details %}}

{{% details title="Can I use my own custom domain to send and receive email?" closed="true" %}}
Yes. NornWeave is self-hosted and **provider-agnostic**. You configure your **own domain** with whichever provider you use (Mailgun, SendGrid, AWS SES, Resend, or IMAP/SMTP). For webhook-based providers, domain verification, DNS records, and sending/receiving are set up in that provider's dashboard. For IMAP/SMTP, you simply point NornWeave at your mail server. See the [Provider Guides]({{< relref "guides" >}}) for step-by-step setup per provider.
{{% /details %}}

{{% details title="How do I avoid ending up in spam?" closed="true" %}}
Deliverability is determined by your **email provider** and your **domain/DNS** setup (SPF, DKIM, DMARC). Because NornWeave uses your chosen provider (Mailgun, SendGrid, SES, Resend), follow that provider's deliverability and domain authentication guides. Use a verified domain, avoid spammy content and high complaint rates, and adhere to your provider's sending best practices.
{{% /details %}}

{{% details title="Do you have SDKs or clients available?" closed="true" %}}
Yes. We provide an official **Python client** (`nornweave-client`) in the [clients/python](https://github.com/DataCovey/nornweave/tree/main/clients/python) directory, with sync and async support, pagination, and full API coverage. For **AI agents**, the **MCP server** is the primary interface: Claude, Cursor, and other MCP clients can use NornWeave's tools and resources without writing REST calls. See the [API Reference]({{< relref "api" >}}) for REST and [MCP Integration]({{< relref "api/mcp" >}}) for MCP setup.
{{% /details %}}

{{% details title="Can I allow or block specific email domains?" closed="true" %}}
Yes! NornWeave supports **domain-level allow/blocklists** for both inbound and outbound email via environment variables. Each list accepts comma-separated **regex patterns** matched against the domain portion of email addresses.

**Environment variables:**

| Variable | Direction | Effect |
|---|---|---|
| `INBOUND_DOMAIN_ALLOWLIST` | Receiving | Only accept mail from matching sender domains |
| `INBOUND_DOMAIN_BLOCKLIST` | Receiving | Reject mail from matching sender domains |
| `OUTBOUND_DOMAIN_ALLOWLIST` | Sending | Only send to matching recipient domains |
| `OUTBOUND_DOMAIN_BLOCKLIST` | Sending | Reject sends to matching recipient domains |

**Example — only accept email from your company:**
```bash
INBOUND_DOMAIN_ALLOWLIST=(.*\.)?yourcompany\.com
```

**Example — block spam domains:**
```bash
INBOUND_DOMAIN_BLOCKLIST=spam\.com,junk\.org
```

Blocklist always takes precedence: a domain on the blocklist is rejected even if it also matches the allowlist. Empty lists mean "no restriction." See the [Configuration Guide]({{< relref "getting-started/configuration#domain-filtering-allowblocklists" >}}) for full details.
{{% /details %}}

{{% details title="Can I rate-limit how many emails NornWeave sends?" closed="true" %}}
Yes. NornWeave supports **global send rate limiting** via two environment variables:

| Variable | Effect |
|---|---|
| `GLOBAL_SEND_RATE_LIMIT_PER_MINUTE` | Max outbound emails per rolling minute (`0` = unlimited) |
| `GLOBAL_SEND_RATE_LIMIT_PER_HOUR` | Max outbound emails per rolling hour (`0` = unlimited) |

Both windows are enforced independently. When a limit is exceeded, the API returns **HTTP 429 Too Many Requests** with a `Retry-After` header so callers know when to retry.

**Example — cap at 10 per minute and 200 per hour:**
```bash
GLOBAL_SEND_RATE_LIMIT_PER_MINUTE=10
GLOBAL_SEND_RATE_LIMIT_PER_HOUR=200
```

Rate-limit state is in-memory (no Redis required) and resets on process restart. See the [Configuration Guide]({{< relref "getting-started/configuration#rate-limiting" >}}) for details.
{{% /details %}}

{{% details title="What do I need to get NornWeave running?" closed="true" %}}
**Docker** (recommended) or **Python 3.14+**, a database (**PostgreSQL** for production or **SQLite** for local dev), and an account with a supported email provider (Mailgun, SendGrid, AWS SES, Resend) or any IMAP/SMTP server. With Docker Compose you can be up and running in minutes. See the [Installation guide]({{< relref "getting-started/installation" >}}) and [Quickstart]({{< relref "getting-started/quickstart" >}}).
{{% /details %}}

{{% details title="How does NornWeave format emails for my LLM?" closed="true" %}}
Inbound HTML is converted to **clean Markdown** with reply cruft (quoted blocks, signatures) stripped out. When you fetch a thread, messages are returned with `user` (inbound) and `assistant` (outbound) roles so you can feed them straight into an LLM conversation. All of this happens automatically in the **Verdandi** ingestion engine.
{{% /details %}}

{{% details title="Does NornWeave handle attachments?" closed="true" %}}
Yes. Inbound attachments are stored alongside their message and exposed via the API. When sending, you can include attachments in the `POST /v1/messages` request. Supported storage backends include local disk and cloud storage (S3, GCS) with presigned download URLs.
{{% /details %}}

{{% details title="Is NornWeave self-hosted? Where is my data stored?" closed="true" %}}
Yes. NornWeave is **self-hosted** and **open-source**. You run the server and the database (PostgreSQL or SQLite) on your own infrastructure. All inbox, thread, and message data stays in **your** storage; no email content is sent to third parties except through the provider you configure (e.g. Mailgun, SendGrid, or IMAP/SMTP) for sending and receiving.
{{% /details %}}
