---
title: NornWeave
layout: hextra-home
---

<div style="margin-top: 2rem; margin-bottom: 2rem;">
{{< hextra/hero-headline >}}
  Inbox-as-a-Service for AI Agents
{{< /hextra/hero-headline >}}
</div>

<div style="margin-bottom: 3rem;">
{{< hextra/hero-subtitle >}}
  Open-source, self-hosted API that turns standard email providers into intelligent, stateful email for LLMs via REST or MCP.
{{< /hextra/hero-subtitle >}}
</div>

<div style="margin-bottom: 4rem;">
{{< hextra/hero-button text="Get Started" link="docs/getting-started" >}}
{{< hextra/hero-button text="GitHub" link="https://github.com/DataCovey/nornweave" style="outline" >}}
</div>

<div style="margin-top: 3rem; margin-bottom: 2rem; display: flex; justify-content: center;">
  <img src="/images/Nornorna_spinner.jpg" alt="The Norns weaving fate at Yggdrasil" style="max-width: 50%; border-radius: 0.5rem;" />
</div>

<div style="text-align: center; margin-bottom: 5rem;">
  <p style="font-size: 0.875rem; color: #6b7280; font-style: italic;">
    "Thaer log logdu, thaer lif voldu..."<br/>
    "Laws they made there, and life allotted / To the sons of men, and set their fates."
  </p>
  <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
    — Voluspa (The Prophecy of the Seeress), Poetic Edda, Stanza 20
  </p>
  <p style="font-size: 0.75rem; color: #9ca3af; margin-top: 1rem;">
    Image: "Nornorna spinner odets tradar vid Yggdrasil" by L. B. Hansen — 
    <a href="https://commons.wikimedia.org/w/index.php?curid=164065" target="_blank" style="text-decoration: underline;">Public Domain</a>
  </p>
</div>

<div style="margin-bottom: 4rem;">
{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="The Story"
    subtitle="In Norse mythology, the Norns (Urdr, Verdandi, and Skuld) dwell at the base of Yggdrasil, the World Tree. They weave the tapestry of fate for all beings. NornWeave acts as the Norns for AI Agents — taking raw email data and weaving it into coherent, structured context."
  >}}
{{< /hextra/feature-grid >}}
</div>

<div style="margin-top: 5rem; margin-bottom: 2.5rem;">
{{< hextra/hero-headline >}}
  Features
{{< /hextra/hero-headline >}}
</div>

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Virtual Inboxes"
    subtitle="Create dedicated email addresses for your AI agents. Each inbox can receive and send emails independently."
    link="docs/getting-started"
    icon="inbox"
  >}}
  {{< hextra/feature-card
    title="Webhook Ingestion"
    subtitle="Receive emails from Mailgun, AWS SES, SendGrid, and Resend through webhook endpoints."
    link="docs/guides"
    icon="cloud-download"
  >}}
  {{< hextra/feature-card
    title="Smart Threading"
    subtitle="Automatic conversation grouping using email headers. Messages are organized into threads."
    link="docs/concepts"
    icon="collection"
  >}}
  {{< hextra/feature-card
    title="REST API"
    subtitle="Full REST API for inbox, thread, and message management. LLM-optimized response formats."
    link="docs/api/rest"
    icon="code"
  >}}
  {{< hextra/feature-card
    title="MCP Integration"
    subtitle="Connect directly to Claude, Cursor, and other MCP clients. Read and send email with natural language."
    link="docs/api/mcp"
    icon="chip"
  >}}
  {{< hextra/feature-card
    title="Clean Architecture"
    subtitle="Modular design with storage and provider adapters."
    link="docs/concepts/architecture"
    icon="template"
  >}}
{{< /hextra/feature-grid >}}

<div style="margin-top: 5rem; margin-bottom: 2.5rem;">
{{< hextra/hero-headline >}}
  Current Capabilities
{{< /hextra/hero-headline >}}
</div>

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Phase 1: Foundation"
    subtitle="**The Mail Proxy** — Virtual Inboxes for AI agents, webhook ingestion from providers, PostgreSQL persistent storage, email sending via configured provider, and API key authentication."
    icon="check-circle"
    style="background: radial-gradient(ellipse at 50% 80%,rgba(45,212,191,0.15),hsla(0,0%,100%,0));"
  >}}
  {{< hextra/feature-card
    title="Phase 2: Intelligence"
    subtitle="**The Agent Layer** — HTML to clean Markdown parsing, automatic cruft removal, smart conversation threading, MCP server for Claude/Cursor, and attachment text extraction."
    icon="check-circle"
    style="background: radial-gradient(ellipse at 50% 80%,rgba(120,119,198,0.15),hsla(0,0%,100%,0));"
  >}}
{{< /hextra/feature-grid >}}

<div style="margin-top: 5rem; margin-bottom: 2.5rem;">
{{< hextra/hero-headline >}}
  Quick Start
{{< /hextra/hero-headline >}}
</div>

```bash
# Clone the repository
git clone https://github.com/DataCovey/nornweave.git
cd nornweave

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys

# Start the stack
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head
```

<div style="margin-top: 2rem;">
{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Installation Guide"
    subtitle="Step-by-step installation with Docker or from source."
    link="docs/getting-started/installation"
    icon="book-open"
  >}}
  {{< hextra/feature-card
    title="Quickstart Tutorial"
    subtitle="Create your first inbox and send an email in minutes."
    link="docs/getting-started/quickstart"
    icon="play"
  >}}
  {{< hextra/feature-card
    title="Provider Setup"
    subtitle="Configure Mailgun, SendGrid, AWS SES, or Resend."
    link="docs/guides"
    icon="cog"
  >}}
{{< /hextra/feature-grid >}}
</div>
