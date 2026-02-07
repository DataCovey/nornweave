## 1. Configuration

- [x] 1.1 Add `inbound_domain_allowlist`, `inbound_domain_blocklist`, `outbound_domain_allowlist`, `outbound_domain_blocklist` fields (type `str`, default `""`) to `Settings` in `src/nornweave/core/config.py` with corresponding env-var aliases
- [x] 1.2 Add a `@model_validator` that attempts to compile all four lists as regex patterns at startup, raising a clear `ValueError` if any pattern is invalid

## 2. Core Filter Module

- [x] 2.1 Create `src/nornweave/core/domain_filter.py` with a `DomainFilter` class that takes an allowlist string and a blocklist string, splits on commas, and compiles each pattern via `re.compile()`
- [x] 2.2 Implement `DomainFilter.is_allowed(domain: str) -> bool` using blocklist-first evaluation with `re.fullmatch()` semantics
- [x] 2.3 Implement `DomainFilter.check(email_address: str) -> bool` convenience method that extracts the domain (after `@`) and delegates to `is_allowed`
- [x] 2.4 Add INFO-level logging for rejections (direction, domain, matching pattern) and DEBUG-level logging for allow-throughs

## 3. Inbound Integration

- [x] 3.1 Add `"domain_blocked"` to the `IngestResult.status` literal type in `src/nornweave/verdandi/ingest.py`
- [x] 3.2 Insert domain filter check in `ingest_message()` after inbox lookup (step 1) and before duplicate detection (step 2) — return `IngestResult(status="domain_blocked")` on rejection
- [x] 3.3 Construct the inbound `DomainFilter` from `settings.inbound_domain_allowlist` and `settings.inbound_domain_blocklist`

## 4. Outbound Integration

- [x] 4.1 Insert domain filter check in `send_message()` route in `src/nornweave/yggdrasil/routes/v1/messages.py` after inbox lookup but before `email_provider.send_email()`
- [x] 4.2 Check every domain in `payload.to`; if any are blocked, raise `HTTPException(403)` with a body listing all blocked domains
- [x] 4.3 Construct the outbound `DomainFilter` from `settings.outbound_domain_allowlist` and `settings.outbound_domain_blocklist`

## 5. Unit Tests

- [x] 5.1 Create `tests/unit/core/test_domain_filter.py` with tests for `DomainFilter`: empty lists (allow all), allowlist-only, blocklist-only, both lists (blocklist wins), full-match semantics (no partial match), wildcard subdomain patterns, invalid regex raises error
- [x] 5.2 Add tests for the `check()` convenience method (extracts domain from full email address)

## 6. Integration Tests

- [x] 6.1 Add inbound integration test: ingest with blocked sender domain → `status="domain_blocked"`, no message/thread created
- [x] 6.2 Add inbound integration test: ingest with allowed sender domain → normal processing
- [x] 6.3 Add outbound integration test: send to blocked recipient domain → HTTP 403, no email sent
- [x] 6.4 Add outbound integration test: send with mixed recipients (one blocked) → HTTP 403 for entire request
- [x] 6.5 Add outbound integration test: send to allowed recipient domain → normal send

## 7. Documentation

- [x] 7.1 Add "Domain Filtering" section to the configuration guide in `web/content/docs/getting-started/configuration.md`
- [x] 7.2 Add a "Domain Filtering" feature card to the Features grid on the landing page (`web/content/_index.md`)
- [x] 7.3 Add a FAQ entry to `web/content/docs/faq.md` explaining how to allow/block email domains (with env-var examples)
- [x] 7.4 Document the changes in `/CHANGELOG.md`
