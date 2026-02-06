---
title: NornWeave - Inbox-as-a-Service API for AI Agents
layout: hextra-home
description: "Open-source, self-hosted email API that turns standard email providers into intelligent, stateful email for LLMs. REST API and MCP integration for AI agents."
keywords:
  - AI email API
  - inbox as a service
  - MCP server
  - LLM email
  - AI agents email
  - self-hosted email API
  - email automation
  - Claude MCP
  - Cursor MCP
sitemap_priority: 1.0
sitemap_changefreq: daily
---

<style>
.nw-hero-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 2rem;
  margin-top: 0;
  margin-bottom: 0;
}
.nw-hero-row .nw-hero-image {
  flex: 0 0 min(34%, 315px);
  min-width: 0;
}
.nw-hero-row .nw-hero-image img {
  width: 100%;
  border-radius: 0.5rem;
  display: block;
}
.nw-hero-row .nw-hero-right {
  flex: 1 1 50%;
  min-width: 0;
}
.nw-hero-row .nw-hero-right .hextra-feature-grid {
  grid-template-columns: 1fr !important;
}
.nw-hero-row .nw-hero-quote,
.nw-hero-row .nw-hero-credits {
  text-align: left;
}
@media (max-width: 768px) {
  .nw-hero-row {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  .nw-hero-row .nw-hero-image {
    flex: 0 0 auto;
    width: 100%;
    max-width: 240px;
  }
  .nw-hero-row .nw-hero-right {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .nw-hero-row .nw-hero-quote,
  .nw-hero-row .nw-hero-credits {
    text-align: center;
  }
}
</style>

<div style="margin-bottom: 0.75rem;">
{{< hextra/hero-headline >}}
  Inbox-as-a-Service for AI Agents
{{< /hextra/hero-headline >}}
</div>

<div style="margin-bottom: 1.25rem;">
{{< hextra/hero-subtitle >}}
  Open-source, self-hosted API that turns standard email providers into intelligent, stateful email for LLMs via REST or MCP.
{{< /hextra/hero-subtitle >}}
</div>

<div style="margin-bottom: 1.5rem;">
{{< hextra/hero-button text="Get Started" link="docs/getting-started" >}}
{{< hextra/hero-button text="GitHub" link="https://github.com/DataCovey/nornweave" style="outline" >}}
</div>

<div class="nw-hero-row">
  <div class="nw-hero-image">
    <img src="/images/Nornorna_spinner.jpg" alt="The Norns weaving fate at Yggdrasil" />
  </div>
  <div class="nw-hero-right">
    <div class="nw-hero-quote" style="margin-bottom: 1.5rem;">
      <p style="font-size: 0.875rem; color: #6b7280; font-style: italic;">
        "Thaer log logdu, thaer lif voldu..."<br/>
        "Laws they made there, and life allotted / To the sons of men, and set their fates."
      </p>
      <p style="font-size: 0.875rem; color: #6b7280; margin-top: 0.5rem;">
        — Voluspa (The Prophecy of the Seeress), Poetic Edda, Stanza 20
      </p>
    </div>
    <div class="nw-hero-credits" style="margin-bottom: 2rem;">
      <p style="font-size: 0.75rem; color: #9ca3af;">
        Image: "Nornorna spinner odets tradar vid Yggdrasil" by L. B. Hansen —
        <a href="https://commons.wikimedia.org/w/index.php?curid=164065" target="_blank" style="text-decoration: underline;">Public Domain</a>
      </p>
    </div>
    <div style="width: 100%;">
      {{< hextra/feature-grid >}}
        {{< hextra/feature-card
          title="The Story"
          subtitle="In Norse mythology, the Norns (Urdr, Verdandi, and Skuld) dwell at the base of Yggdrasil, the World Tree. They weave the tapestry of fate for all beings. NornWeave acts as the Norns for AI Agents — taking raw email data and weaving it into coherent, structured context."
        >}}
      {{< /hextra/feature-grid >}}
    </div>
  </div>
</div>

<div style="margin-top: 2.5rem; margin-bottom: 1.5rem;">
{{< hextra/hero-headline >}}
  Features
{{< /hextra/hero-headline >}}
</div>

{{< hextra/feature-grid >}}
  {{< hextra/feature-card
    title="Virtual Inboxes"
    subtitle="Dedicated addresses for AI agents; receive and send via your provider. PostgreSQL-backed storage and API key authentication."
    link="docs/getting-started"
    icon="inbox"
  >}}
  {{< hextra/feature-card
    title="Webhook Ingestion"
    subtitle="Ingest from Mailgun, AWS SES, SendGrid, and Resend; send via your configured provider."
    link="docs/guides"
    icon="cloud-download"
  >}}
  {{< hextra/feature-card
    title="Smart Threading"
    subtitle="Thread by headers, HTML→Markdown parsing, and cruft removal. LLM thread summaries with your own OpenAI, Anthropic, or Gemini key."
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
    subtitle="Claude, Cursor, and other MCP clients. Read and send email; attachment text extraction included."
    link="docs/api/mcp"
    icon="chip"
  >}}
  {{< hextra/feature-card
    title="Clean Architecture"
    subtitle="Modular design with storage and provider adapters. Swap email providers with ease."
    link="docs/concepts/architecture"
    icon="template"
  >}}
{{< /hextra/feature-grid >}}

<div style="margin-top: 2.5rem; margin-bottom: 1.5rem;">
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
docker compose --profile storage_psql --profile mail_mailgun up -d

# Run migrations
docker compose --profile storage_psql exec api-psql uv run alembic upgrade head

# (Optional) Validate with Python SDK
cd clients/python
pip install -e .
python scripts/validate_local.py
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
