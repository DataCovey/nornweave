# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 0.1.1

### Added

- SendGrid webhook and sending implementation
- Resend webhook and sending implementation

### Changed

- (None yet)

### Deprecated

- (None yet)

### Removed

- (None yet)

### Fixed

- (None yet)

### Security

- (None yet)

---

## [0.1.0] - 2026-02-02

Initial release. See [Unreleased] for current development.

### Added

- Mailgun webhook and sending implementation
- Implemented **Yggdrasil**: receives the webhook and routes to the appropriate handler
- Implemented **Verdandi** for message and thread parsing
- Implemented **Skuld**, basic API
- Implemented **Urdr**, basic Storage (PSQL and SQLite)
- E2E testing

[Unreleased]: https://github.com/DataCovey/nornweave/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DataCovey/nornweave/releases/tag/v0.1.0
