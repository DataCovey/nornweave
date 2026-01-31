---
title: Getting Started with NornWeave
description: "Install and configure NornWeave in minutes. Docker setup, environment configuration, and quickstart tutorial for AI agent email integration."
weight: 1
keywords:
  - NornWeave installation
  - Docker email API
  - email API setup
  - getting started guide
sitemap_priority: 0.9
sitemap_changefreq: weekly
---

Get NornWeave up and running in minutes.

{{< cards >}}
  {{< card link="installation" title="Installation" icon="download" subtitle="Install NornWeave using Docker or from source" >}}
  {{< card link="configuration" title="Configuration" icon="cog" subtitle="Environment variables and settings" >}}
  {{< card link="quickstart" title="Quickstart" icon="play" subtitle="Create your first inbox and send an email" >}}
{{< /cards >}}

## Prerequisites

- **Docker** and **Docker Compose** (recommended)
- Or: **Python 3.11+** and **PostgreSQL 15+**
- An email provider account (Mailgun, SendGrid, AWS SES, or Resend)

## Quick Install

```bash
# Clone the repository
git clone https://github.com/DataCovey/nornweave.git
cd nornweave

# Copy environment configuration
cp .env.example .env

# Start the stack
docker compose up -d
```

Continue to the [Installation Guide](installation) for detailed instructions.
