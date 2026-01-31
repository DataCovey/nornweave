---
title: Contributing
weight: 10
---

Thank you for your interest in contributing to NornWeave! This page provides a quick overview of how to get started.

## Quick Start

1. Fork and clone the repository
2. Install dependencies with `uv sync --extra dev`
3. Run tests with `make test`
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/nornweave.git
cd nornweave

# Install with dev dependencies
uv sync --extra dev

# Install pre-commit hooks
pre-commit install

# Start PostgreSQL for testing
docker compose up -d postgres

# Run tests
make test
```

## Code Style

NornWeave uses:

- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Pre-commit** hooks for automated checks

Run all checks:

```bash
make lint      # Run ruff linter
make format    # Format code with ruff
make typecheck # Run mypy
make check     # Run all checks
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new inbox creation endpoint
fix: handle empty email body gracefully
docs: update API documentation
test: add unit tests for threading logic
refactor: extract email parsing to separate module
```

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Add tests for new functionality
4. Update documentation if needed
5. Ensure all checks pass
6. Open a pull request with a clear description

## Project Structure

```
nornweave/
├── src/nornweave/
│   ├── core/           # Shared interfaces and config
│   ├── urdr/           # Storage layer (PostgreSQL, SQLite)
│   ├── verdandi/       # Ingestion engine (parsing, threading)
│   ├── skuld/          # Outbound layer (sending, rate limiting)
│   ├── yggdrasil/      # API gateway (FastAPI routes)
│   ├── huginn/         # MCP resources
│   └── muninn/         # MCP tools
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
└── docs/               # Documentation
```

## Getting Help

- Open an [issue](https://github.com/DataCovey/nornweave/issues) for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and follow the [Code of Conduct](https://github.com/DataCovey/nornweave/blob/main/CODE_OF_CONDUCT.md)

## Full Guide

For more detailed information, see the [Contributing Guide](https://github.com/DataCovey/nornweave/blob/main/CONTRIBUTING.md) in the repository.
