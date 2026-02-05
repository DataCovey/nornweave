## ADDED Requirements

### Requirement: Base package installs without PostgreSQL dependencies

The base `nornweave` package SHALL install and run with only SQLite support, without requiring PostgreSQL drivers (`asyncpg`, `psycopg2-binary`).

#### Scenario: Install base package in clean environment
- **WHEN** user runs `pip install nornweave` in a fresh virtual environment
- **THEN** installation succeeds without errors
- **AND** `asyncpg` is NOT installed
- **AND** `psycopg2` is NOT installed

#### Scenario: Import nornweave without PostgreSQL
- **WHEN** user runs `import nornweave` after base install
- **THEN** import succeeds without ImportError
- **AND** no PostgreSQL-related warnings are shown

#### Scenario: Run API with SQLite after base install
- **WHEN** user sets `DB_DRIVER=sqlite` and runs `nornweave api`
- **THEN** the API server starts successfully
- **AND** SQLite database is created and usable

### Requirement: PostgreSQL extra provides PostgreSQL support

The `[postgres]` extra SHALL provide all dependencies needed for PostgreSQL deployments.

#### Scenario: Install postgres extra
- **WHEN** user runs `pip install nornweave[postgres]`
- **THEN** `asyncpg` is installed
- **AND** `psycopg2-binary` is installed

#### Scenario: Run API with PostgreSQL after postgres extra install
- **WHEN** user has `[postgres]` extra installed
- **AND** sets `DB_DRIVER=postgres` with valid PostgreSQL connection
- **THEN** the API server connects to PostgreSQL successfully

#### Scenario: Clear error when PostgreSQL requested without extra
- **WHEN** user sets `DB_DRIVER=postgres` without `[postgres]` extra
- **AND** runs `nornweave api`
- **THEN** a clear ImportError is raised
- **AND** error message includes: "Install with: pip install nornweave[postgres]"

### Requirement: MCP extra provides MCP server support

The `[mcp]` extra SHALL provide all dependencies needed for the MCP server.

#### Scenario: Install mcp extra
- **WHEN** user runs `pip install nornweave[mcp]`
- **THEN** `mcp` package is installed
- **AND** `fastmcp` package is installed

#### Scenario: Run MCP server after mcp extra install
- **WHEN** user has `[mcp]` extra installed
- **AND** runs `nornweave mcp`
- **THEN** MCP server starts successfully in stdio mode

#### Scenario: Clear error when MCP requested without extra
- **WHEN** user runs `nornweave mcp` without `[mcp]` extra
- **THEN** a clear error message is shown
- **AND** error message includes: "Install with: pip install nornweave[mcp]"

### Requirement: All extra installs complete feature set

The `[all]` extra SHALL install all optional dependencies for full functionality.

#### Scenario: Install all extra
- **WHEN** user runs `pip install nornweave[all]`
- **THEN** all extras are installed: postgres, mcp, attachments, search, ratelimit

### Requirement: Package publishes to PyPI

The `nornweave` package SHALL be published to PyPI and installable via pip.

#### Scenario: Install from PyPI
- **WHEN** user runs `pip install nornweave`
- **THEN** the package is downloaded from PyPI and installed

#### Scenario: Install specific version from PyPI
- **WHEN** user runs `pip install nornweave==0.1.1`
- **THEN** version 0.1.1 is installed

#### Scenario: GitHub release triggers PyPI publish
- **WHEN** maintainer creates a git tag `vX.Y.Z` and pushes to GitHub
- **THEN** GitHub Actions workflow builds the package
- **AND** publishes to PyPI using trusted publishing (OIDC)

### Requirement: Version matches GitHub tag

The package version in `pyproject.toml` SHALL match the `vX.Y.Z` tag format used for GitHub releases.

#### Scenario: Version alignment check
- **WHEN** a release is prepared with tag `v0.1.1`
- **THEN** `pyproject.toml` contains `version = "0.1.1"`

### Requirement: CLI entry point works after pip install

The `nornweave` CLI command SHALL be available after pip installation.

#### Scenario: CLI available after install
- **WHEN** user runs `pip install nornweave`
- **THEN** `nornweave --help` displays the CLI help
- **AND** `nornweave --version` displays the version

#### Scenario: API subcommand works
- **WHEN** user runs `nornweave api --help`
- **THEN** API server options are displayed

#### Scenario: MCP subcommand shows install hint without extra
- **WHEN** user runs `nornweave mcp` without `[mcp]` extra
- **THEN** error message suggests installing with `pip install nornweave[mcp]`

### Requirement: Documentation shows consistent MCP configuration

All documentation SHALL show the same MCP client configuration format.

#### Scenario: Installation guide MCP config
- **WHEN** user reads `installation.md` MCP section
- **THEN** configuration uses `"args": ["mcp"]` format
- **AND** includes `NORNWEAVE_API_URL` environment variable

#### Scenario: Quickstart guide MCP config
- **WHEN** user reads `quickstart.md` MCP section
- **THEN** configuration matches `installation.md` exactly

#### Scenario: MCP guide configuration
- **WHEN** user reads `api/mcp.md` configuration section
- **THEN** configuration matches `installation.md` exactly

### Requirement: Documentation shows correct installation commands

All documentation SHALL use correct pip install commands with extras syntax.

#### Scenario: MCP installation command
- **WHEN** documentation shows MCP installation
- **THEN** command is `pip install nornweave[mcp]`

#### Scenario: Full installation command
- **WHEN** documentation shows full installation
- **THEN** command is `pip install nornweave[all]`

#### Scenario: PostgreSQL installation command
- **WHEN** documentation shows PostgreSQL setup
- **THEN** command includes `pip install nornweave[postgres]`

### Requirement: Docker image uses correct extras

The Dockerfile SHALL install the appropriate extras for production deployment.

#### Scenario: Docker build includes postgres and mcp
- **WHEN** Docker image is built
- **THEN** installation command uses `pip install .[postgres,mcp]` or equivalent

### Requirement: CONTRIBUTING.md documents PyPI release process

The CONTRIBUTING.md file SHALL document the PyPI publishing workflow.

#### Scenario: Release process documented
- **WHEN** maintainer reads CONTRIBUTING.md release section
- **THEN** steps for PyPI publishing are documented
- **AND** tag format `vX.Y.Z` is specified
- **AND** trusted publishing (OIDC) is mentioned

#### Scenario: Version alignment documented
- **WHEN** maintainer reads CONTRIBUTING.md
- **THEN** it documents that `vX.Y.Z` tag matches PyPI version
