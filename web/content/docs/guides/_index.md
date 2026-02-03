---
title: Email Provider Setup Guides
description: "Step-by-step guides for integrating NornWeave with Mailgun, SendGrid, AWS SES, and Resend. Configure webhooks, DNS records, and API credentials."
weight: 4
keywords:
  - Mailgun setup guide
  - SendGrid integration
  - AWS SES email setup
  - Resend webhook
  - email provider configuration
  - webhook setup
sitemap_priority: 0.8
sitemap_changefreq: monthly
---

Detailed setup guides for each supported email provider.

{{< cards >}}
  {{< card link="mailgun" title="Mailgun" icon="mail" subtitle="Setup guide for Mailgun integration" >}}
  {{< card link="sendgrid" title="SendGrid" icon="mail" subtitle="Setup guide for SendGrid integration" >}}
  {{< card link="ses" title="AWS SES" icon="cloud" subtitle="Setup guide for Amazon SES integration" >}}
  {{< card link="resend" title="Resend" icon="mail" subtitle="Setup guide for Resend integration" >}}
{{< /cards >}}

## Provider Comparison

| Feature | Mailgun | SendGrid | AWS SES | Resend |
|---------|---------|----------|---------|--------|
| Sending | Yes | Yes | Yes | Yes |
| Receiving | Yes | Yes | Yes | Yes |
| Auto-Route Setup | Yes | Yes | Manual | Yes |
| Free Tier | 5k/month | 100/day | 62k/month | 3k/month |
| Webhook Parsing | JSON | JSON | SNS/JSON | JSON |

## General Setup Steps

1. **Create an account** with your chosen provider
2. **Verify your domain** for sending
3. **Configure DNS records** (SPF, DKIM, MX)
4. **Create API credentials**
5. **Set up inbound routes** to point to NornWeave webhooks
6. **Update NornWeave configuration** with your credentials
