# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

Older versions may receive best-effort support. Upgrade to a supported version when possible.

## Reporting a Vulnerability

We take security seriously. If you believe you have found a security vulnerability in NornWeave, please report it responsibly.

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead:

1. **Email** the maintainers with a description of the vulnerability and steps to reproduce. You can find contact information in the repository metadata or GitHub profile of the project owners.

2. **Include** as much of the following as possible:
   - Type of vulnerability
   - Full path of affected source file(s)
   - Step-by-step instructions to reproduce
   - Proof-of-concept or exploit code (if available)
   - Impact of the vulnerability

3. **Allow** a reasonable time for a fix before any public disclosure (we aim for 90 days or less).

We will acknowledge receipt of your report and will send updates on our progress. We may ask for additional information or guidance.

## Security Considerations

When deploying NornWeave:

- **API keys**: Use strong, randomly generated API keys. Never commit `.env` or secrets to version control.
- **Database**: Use a dedicated database user with minimal required privileges. Prefer TLS for connections in production.
- **Webhooks**: Validate webhook signatures (e.g., Mailgun, SendGrid) before processing. Use HTTPS for webhook URLs.
- **Email providers**: Store provider API keys in environment variables or a secrets manager, not in code or config files.
- **Network**: Run the API behind a reverse proxy (e.g., nginx, Caddy) and restrict access to admin or internal endpoints as needed.

## Out of Scope

The following are generally out of scope for our security policy:

- Issues in third-party dependencies (report to the upstream project; we will update dependencies when fixes are released)
- Social engineering or physical access
- Denial of service that does not involve a software defect (e.g., volumetric traffic)

Thank you for helping keep NornWeave and its users safe.
