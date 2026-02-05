## 1. Package Structure (pyproject.toml)

- [x] 1.1 Move `asyncpg` from base dependencies to `[postgres]` extra
- [x] 1.2 Move `psycopg2-binary` from base dependencies to `[postgres]` extra
- [x] 1.3 Update `[all]` extra to include `postgres` in the list
- [x] 1.4 Bump version to `0.1.1` in pyproject.toml
- [x] 1.5 Verify package builds cleanly with `uv build`

## 2. Graceful Import Handling

- [x] 2.1 Update `dependencies.py` to use lazy import for `PostgresAdapter` with clear error message
- [x] 2.2 Update `urdr/__init__.py` to make `PostgresAdapter` import optional (try/except)
- [x] 2.3 Verify `import nornweave` works without asyncpg installed
- [x] 2.4 Verify clear error message when `DB_DRIVER=postgres` without `[postgres]` extra

## 3. Docker & Build Updates

- [x] 3.1 Update `Dockerfile` to use `pip install .[postgres,mcp]` for production image
- [x] 3.2 Update `Makefile` install targets to document extra options
- [x] 3.3 Verify Docker build succeeds with updated installation

## 4. Documentation Alignment

- [x] 4.1 Update `installation.md` MCP section to use standard config format
- [x] 4.2 Update `quickstart.md` MCP section to match `installation.md` exactly
- [x] 4.3 Verify `api/mcp.md` uses consistent MCP config (already correct)
- [x] 4.4 Add package extras documentation to `installation.md` (base, postgres, mcp, all)
- [x] 4.5 Update `README.md` with PyPI installation as primary method
- [x] 4.6 Update `CONTRIBUTING.md` release process to document PyPI publishing workflow

## 5. CI/CD Workflow

- [x] 5.1 Create `.github/workflows/pypi-publish.yml` for PyPI publishing
- [x] 5.2 Configure workflow to trigger on `vX.Y.Z` tag push
- [x] 5.3 Use `pypa/gh-action-pypi-publish` with trusted publishing (OIDC)
- [x] 5.4 Add build step using `hatch build`

## 6. E2E Validation Tests

- [x] 6.1 Create `scripts/validate_install.py` for installation validation
- [x] 6.2 Add test: base package imports without PostgreSQL deps
- [x] 6.3 Add test: `[postgres]` extra installs asyncpg
- [x] 6.4 Add test: `[mcp]` extra enables MCP server
- [x] 6.5 Add test: CLI entry point works (`nornweave --help`)
- [x] 6.6 Run validation locally in isolated venv to confirm

## 7. Local Validation

- [x] 7.1 Build and install package locally with `uv pip install .`
- [x] 7.2 Verify SQLite mode works with base install
- [x] 7.3 Install `[mcp]` extra and verify MCP server starts
- [x] 7.4 Run MCP server in Docker and verify it responds
- [x] 7.5 Run existing test suite to ensure no regressions

## 8. Release & Documentation

- [x] 8.1 Update CHANGELOG.md with 0.1.1 release notes documenting packaging changes
