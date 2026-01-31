---
title: NornWeave
layout: hextra-home
---

{{< hextra/hero-badge >}}
  <div class="hx-w-2 hx-h-2 hx-rounded-full hx-bg-primary-400"></div>
  <span>Open Source</span>
  {{< icon name="arrow-circle-right" attributes="height=14" >}}
{{< /hextra/hero-badge >}}

<div class="hx-mt-8 hx-mb-8">
{{< hextra/hero-headline >}}
  Inbox-as-a-Service for AI Agents
{{< /hextra/hero-headline >}}
</div>

<div class="hx-mb-16">
{{< hextra/hero-subtitle >}}
  Open-source, self-hosted API that turns standard email providers into intelligent, stateful email for LLMs via REST or MCP.
{{< /hextra/hero-subtitle >}}
</div>

<div class="hx-mb-16">
{{< hextra/hero-button text="Get Started" link="docs/getting-started" >}}
{{< hextra/hero-button text="GitHub" link="https://github.com/DataCovey/nornweave" style="outline" >}}
</div>

<div class="hx-mt-12 hx-mb-8 hx-flex hx-justify-center">
  <img src="/images/Nornorna_spinner.jpg" alt="The Norns weaving fate at Yggdrasil" class="hx-max-w-xs md:hx-max-w-sm hx-rounded-lg" style="max-width: 33%;" />
</div>

<div class="hx-text-center hx-mb-20">
  <p class="hx-text-sm hx-text-gray-500 dark:hx-text-gray-400 hx-italic">
    "Thaer log logdu, thaer lif voldu..."<br/>
    "Laws they made there, and life allotted / To the sons of men, and set their fates."
  </p>
  <p class="hx-text-sm hx-text-gray-500 dark:hx-text-gray-400 hx-mt-2">
    — Voluspa (The Prophecy of the Seeress), Poetic Edda, Stanza 20
  </p>
  <p class="hx-text-xs hx-text-gray-400 dark:hx-text-gray-500 hx-mt-4">
    Image: "Nornorna spinner odets tradar vid Yggdrasil" by L. B. Hansen — 
    <a href="https://commons.wikimedia.org/w/index.php?curid=164065" target="_blank" class="hx-underline">Public Domain</a>
  </p>
</div>

<div class="hx-mb-16">
{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="The Story"
    subtitle="In Norse mythology, the Norns (Urdr, Verdandi, and Skuld) dwell at the base of Yggdrasil, the World Tree. They weave the tapestry of fate for all beings. NornWeave acts as the Norns for AI Agents — taking raw email data and weaving it into coherent, structured context."
  >}}
{{< /hextra/feature-grid >}}
</div>

<div class="hx-mt-20 hx-mb-10">
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
    subtitle="Thematic components inspired by Norse mythology. Modular design with storage and provider adapters."
    link="docs/concepts/architecture"
    icon="template"
  >}}
{{< /hextra/feature-grid >}}

<div class="hx-mt-20 hx-mb-10">
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

<div class="hx-mt-20 hx-mb-10">
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

<div class="hx-mt-8">
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
