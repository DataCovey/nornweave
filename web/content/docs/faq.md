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
SendGrid, Mailgun, Resend, and AWS SES are excellent for **transactional email** (receipts, password resets, marketing). NornWeave does **not** replace them—it sits **on top** of them. You bring your own provider (Mailgun, SendGrid, SES, or Resend); NornWeave adds a **conversational layer**: stateful **threads**, **inboxes** as first-class entities, HTML→Markdown parsing, semantic search, and MCP tools so agents can have two-way email conversations. Think of NornWeave as the brain that turns your existing provider into an agent-ready email backend.
{{% /details %}}

{{% details title="Can I use my own custom domain to send and receive email?" closed="true" %}}
Yes. NornWeave is self-hosted and **provider-agnostic**. You configure your **own domain** with whichever provider you use (Mailgun, SendGrid, AWS SES, or Resend). Domain verification, DNS records, and sending/receiving are all set up in that provider’s dashboard; NornWeave receives inbound mail via webhooks and sends outbound mail via the provider’s API. See the [Provider Guides]({{< relref "guides" >}}) for step-by-step setup per provider.
{{% /details %}}

{{% details title="How do I avoid ending up in spam?" closed="true" %}}
Deliverability is determined by your **email provider** and your **domain/DNS** setup (SPF, DKIM, DMARC). Because NornWeave uses your chosen provider (Mailgun, SendGrid, SES, Resend), follow that provider’s deliverability and domain authentication guides. Use a verified domain, avoid spammy content and high complaint rates, and adhere to your provider’s sending best practices.
{{% /details %}}

{{% details title="Do you have SDKs or clients available?" closed="true" %}}
Yes. We provide an official **Python client** (`nornweave-client`) in the [clients/python](https://github.com/DataCovey/nornweave/tree/main/clients/python) directory, with sync and async support, pagination, and full API coverage. For **AI agents**, the **MCP server** is the primary interface: Claude, Cursor, and other MCP clients can use NornWeave’s tools and resources without writing REST calls. See the [API Reference]({{< relref "api" >}}) for REST and [MCP Integration]({{< relref "api/mcp" >}}) for MCP setup.
{{% /details %}}

{{% details title="Is NornWeave self-hosted? Where is my data stored?" closed="true" %}}
Yes. NornWeave is **self-hosted** and **open-source**. You run the server and the database (PostgreSQL or SQLite) on your own infrastructure. All inbox, thread, and message data stays in **your** storage; no email content is sent to third parties except through the provider you configure (e.g. Mailgun or SendGrid) for sending and receiving.
{{% /details %}}
