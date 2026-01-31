# Contributing to NornWeave

Thank you for your interest in contributing to NornWeave! This document provides guidelines and information for contributors.

## Table of Contents

- [Contributing to NornWeave](#contributing-to-nornweave)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Finding Issues](#finding-issues)
  - [Development Setup](#development-setup)
  - [Making Changes](#making-changes)
    - [Branch Naming](#branch-naming)
    - [Commit Messages](#commit-messages)
  - [Coding Standards](#coding-standards)
    - [Python Style](#python-style)
    - [Code Quality Checks](#code-quality-checks)
    - [Architecture Guidelines](#architecture-guidelines)
  - [Testing](#testing)
    - [Running Tests](#running-tests)
    - [Writing Tests](#writing-tests)
  - [Documentation](#documentation)
    - [Docstrings](#docstrings)
    - [Updating Documentation](#updating-documentation)
  - [Submitting Changes](#submitting-changes)
    - [Pull Request Process](#pull-request-process)
    - [PR Description Template](#pr-description-template)
  - [Release Process](#release-process)
  - [Questions?](#questions)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker and Docker Compose (for local development)
- Git

### Finding Issues

- Look for issues labeled [`good first issue`](https://github.com/DataCovey/nornweave/labels/good%20first%20issue) for beginner-friendly tasks
- Issues labeled [`help wanted`](https://github.com/DataCovey/nornweave/labels/help%20wanted) are looking for contributors
- Feel free to ask questions on any issue before starting work

## Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/nornweave.git
   cd nornweave
   ```

2. **Install dependencies**

   ```bash
   # Using uv (recommended)
   make install-dev

   # Or with pip
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks**

   ```bash
   make setup
   ```

4. **Start the development stack**

   ```bash
   # Start PostgreSQL and Redis
   docker compose up -d postgres redis

   # Copy environment file
   cp .env.example .env

   # Run migrations
   make migrate

   # Start the development server
   make dev
   ```

5. **Verify your setup**

   ```bash
   # Run tests
   make test

   # Run linter
   make lint
   ```

## Making Changes

### Branch Naming

Use descriptive branch names following this pattern:

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions or fixes

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/). Format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(yggdrasil): add rate limiting middleware
fix(verdandi): handle malformed HTML in email parsing
docs(readme): update installation instructions
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use type hints for all functions and methods
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

### Code Quality Checks

Before submitting, ensure all checks pass:

```bash
# Run all checks
make check

# Individual checks
make lint        # Linting
make format      # Formatting
make typecheck   # Type checking
```

### Architecture Guidelines

NornWeave uses a modular architecture with clear boundaries:

| Module | Responsibility |
|--------|----------------|
| `core/` | Shared interfaces, config, exceptions |
| `models/` | Pydantic and SQLAlchemy models |
| `urdr/` | Storage adapters (PostgreSQL, SQLite) |
| `verdandi/` | Email parsing and processing |
| `skuld/` | Outbound sending and rate limiting |
| `yggdrasil/` | FastAPI routes and middleware |
| `adapters/` | Email provider adapters |
| `huginn/` | MCP read operations |
| `muninn/` | MCP write operations |

**Key Principles:**
- Depend on abstractions, not implementations
- Each module should have a clear, single responsibility
- Use dependency injection for testability
- Keep business logic separate from infrastructure

## Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage
make test-cov
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Aim for high coverage on business logic

**Test Structure:**
```python
import pytest
from nornweave.verdandi.parser import parse_email_content


class TestParseEmailContent:
    """Tests for email content parsing."""

    def test_converts_html_to_markdown(self) -> None:
        """HTML should be converted to clean Markdown."""
        html = "<p>Hello <strong>World</strong></p>"
        result = parse_email_content(html)
        assert result == "Hello **World**"

    def test_removes_reply_cruft(self) -> None:
        """Reply quotes should be stripped."""
        content = "Thanks!\n\nOn Jan 1, 2024, John wrote:\n> Original message"
        result = parse_email_content(content)
        assert "On Jan 1" not in result
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def send_email(
    to: list[str],
    subject: str,
    body: str,
    *,
    thread_id: str | None = None,
) -> str:
    """Send an email through the configured provider.

    Args:
        to: List of recipient email addresses.
        subject: Email subject line.
        body: Email body in Markdown format.
        thread_id: Optional thread ID for replies.

    Returns:
        The provider's message ID.

    Raises:
        EmailProviderError: If sending fails.
        ValidationError: If recipients are invalid.
    """
```

### Updating Documentation

Documentation is in the `docs/` directory using MkDocs:

```bash
# Serve locally
make docs

# Build
make docs-build
```

## Submitting Changes

### Pull Request Process

1. **Create a PR** with a clear title and description
2. **Link related issues** using keywords (e.g., "Fixes #123")
3. **Ensure CI passes** - all checks must be green
4. **Request review** from maintainers
5. **Address feedback** and update as needed
6. **Squash and merge** once approved

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How were these changes tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG updated (for user-facing changes)
```

## Release Process

Releases are managed by maintainers following [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Questions?

- Open a [GitHub Discussion](https://github.com/DataCovey/nornweave/discussions)
- Check existing [issues](https://github.com/DataCovey/nornweave/issues)
- Read the [documentation](https://nornweave.github.io/nornweave/)

Thank you for contributing to NornWeave!
