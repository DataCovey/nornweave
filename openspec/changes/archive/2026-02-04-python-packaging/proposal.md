## Why

The documentation references `pip install nornweave[mcp]` but the package isn't published to PyPI. Additionally, the base dependencies include PostgreSQL libraries (`asyncpg`, `psycopg2-binary`) which aren't needed for SQLite-only deployments. This creates a confusing onboarding experience and unnecessary dependency bloat for simple use cases.

## What Changes

- **Restructure package extras** to support modular installation:
  - Core package with SQLite-only support (minimal dependencies)
  - `[postgres]` extra for PostgreSQL deployments
  - `[mcp]` extra for MCP server support (already defined, needs refinement)
  - Keep existing `[attachments]`, `[search]`, `[ratelimit]` extras
  - `[all]` meta-extra for full installation
- **Publish to PyPI** with proper build configuration
- **Fix documentation conflicts** between installation.md and quickstart.md MCP configs
- **Add e2e validation tests** for installation and MCP server functionality
- **Update all docs** to reflect correct package installation

## Non-Goals

- **Email provider flavors**: Analysis shows providers share common dependencies (`httpx`, `markdown`, `cryptography`, `svix`). Splitting would add complexity without meaningful benefit—all providers can stay in the base package.
- **Breaking API changes**: This is purely a packaging/distribution change
- **Changing MCP server behavior**: Only fixing documentation and ensuring installation works

## Capabilities

### New Capabilities
- `python-packaging`: Package structure, PyPI publication, installation extras, and e2e validation

### Modified Capabilities
- None (this doesn't change spec-level requirements)

## Impact

**Code Changes:**
- `pyproject.toml`: Restructure dependencies (move `asyncpg`/`psycopg2-binary` to `[postgres]`)
- `src/nornweave/urdr/`: Add graceful handling for missing PostgreSQL drivers
- `Dockerfile`: Update to use `[postgres,mcp]` extras
- `Makefile`: Update install targets

**Documentation:**
- `web/content/docs/getting-started/installation.md`: Fix MCP section, document extras
- `web/content/docs/getting-started/quickstart.md`: Align MCP config with installation.md
- `web/content/docs/api/mcp.md`: Ensure consistent installation instructions
- `README.md`: Update installation instructions
- `CONTRIBUTING.md`: Update release process for PyPI publishing

**CI/CD:**
- `.github/workflows/`: Add PyPI publish workflow
- Add e2e test for installation validation

**Testing:**
- New e2e tests validating:
  - Base package installs without PostgreSQL
  - `[postgres]` extra adds PostgreSQL support
  - `[mcp]` extra enables MCP server
  - MCP server runs in Docker and responds to health check
