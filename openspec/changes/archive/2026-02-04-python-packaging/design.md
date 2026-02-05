## Context

NornWeave is currently developed using `uv` locally but has never been published to PyPI. The documentation references `pip install nornweave[mcp]` in multiple places, but this package doesn't exist. Additionally, the base dependencies in `pyproject.toml` include PostgreSQL libraries (`asyncpg`, `psycopg2-binary`) which forces users to install these even for SQLite-only development.

**Current state:**
- Package defined in `pyproject.toml` with hatchling build backend
- Extras already defined: `[mcp]`, `[attachments]`, `[search]`, `[ratelimit]`, `[all]`, `[dev]`
- PostgreSQL deps (`asyncpg`, `psycopg2-binary`) in base dependencies
- `urdr/adapters/` has `PostgresAdapter` and `SQLiteAdapter`, both imported unconditionally in `dependencies.py`
- MCP config differs between `installation.md` and `quickstart.md`

**Constraints:**
- Must maintain backward compatibility for existing users cloning the repo
- SQLite must work out-of-the-box without extra deps
- PostgreSQL imports must not fail when drivers aren't installed
- Package must be installable from PyPI

## Goals / Non-Goals

**Goals:**
- Publish `nornweave` package to PyPI
- SQLite works with base install (`pip install nornweave`)
- PostgreSQL works with extra (`pip install nornweave[postgres]`)
- MCP works with extra (`pip install nornweave[mcp]`)
- All installation paths validated via e2e tests
- Documentation is consistent and accurate

**Non-Goals:**
- Provider-specific extras (deps are common enough to keep in base)
- Changing the API or behavior
- Supporting alternative package registries (only PyPI)
- Automated version bumping or changelog generation

## Decisions

### D1: Package extras structure

**Decision:** Restructure extras as follows:

| Extra | Dependencies | Use case |
|-------|--------------|----------|
| (base) | FastAPI, SQLAlchemy, aiosqlite, httpx, etc. | SQLite-only, minimal install |
| `[postgres]` | asyncpg, psycopg2-binary | Production PostgreSQL |
| `[mcp]` | mcp, fastmcp | AI agent integration |
| `[attachments]` | pypdf, python-magic | Attachment processing |
| `[search]` | pgvector, openai | Semantic search |
| `[ratelimit]` | redis | Rate limiting |
| `[all]` | All of the above | Full installation |
| `[dev]` | pytest, ruff, mypy, etc. | Development |

**Rationale:** PostgreSQL is the only storage backend with significant extra dependencies. Email providers share common deps (`httpx`, `markdown`, `cryptography`, `svix`) already in base—no benefit to splitting.

**Alternative considered:** Keep PostgreSQL in base. Rejected because it adds ~15MB of dependencies and compile requirements that SQLite-only users don't need.

### D2: Graceful PostgreSQL import handling

**Decision:** Use lazy imports with clear error messages in `dependencies.py`:

```python
def get_storage(session, settings) -> StorageInterface:
    if settings.db_driver == "postgres":
        try:
            from nornweave.urdr.adapters.postgres import PostgresAdapter
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires additional dependencies. "
                "Install with: pip install nornweave[postgres]"
            ) from e
        return PostgresAdapter(session)
    else:
        from nornweave.urdr.adapters.sqlite import SQLiteAdapter
        return SQLiteAdapter(session)
```

**Rationale:** Lazy imports allow the base package to load without PostgreSQL deps. Clear error message guides users to the correct fix.

**Alternative considered:** Optional import with `TYPE_CHECKING` guards everywhere. Rejected because it spreads complexity across many files and makes the codebase harder to understand.

### D3: Alembic migrations without psycopg2

**Decision:** Keep `psycopg2-binary` in `[postgres]` extra and document that migrations require PostgreSQL deps.

Current Alembic config uses sync psycopg2 for migrations. For SQLite-only users, migrations work with aiosqlite. PostgreSQL migrations require the `[postgres]` extra installed.

**Rationale:** Alembic migrations are a developer/ops concern, not end-user. It's acceptable to require extra deps for PostgreSQL migrations.

### D4: PyPI publishing workflow

**Decision:** Use GitHub Actions with trusted publishing (OIDC):

1. Manual trigger workflow for releases
2. Build with `hatch build`
3. Publish to PyPI using `pypa/gh-action-pypi-publish`
4. Version comes from `pyproject.toml` (manual bump before release)

**Rationale:** Trusted publishing is more secure than API tokens. Manual trigger ensures intentional releases. Aligns with standard Python packaging practices.

**Alternative considered:** Automatic publish on tag. Rejected because it's easy to accidentally push tags, and we want human review before each release.

### D5: Documentation MCP config alignment

**Decision:** Standardize on the minimal config from `installation.md`:

```json
{
  "mcpServers": {
    "nornweave": {
      "command": "nornweave",
      "args": ["mcp"],
      "env": {
        "NORNWEAVE_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Rationale:** The `--api-url` flag in quickstart.md is redundant since `NORNWEAVE_API_URL` env var is the standard way. Config should be consistent across all docs.

### D6: E2E installation validation

**Decision:** Create a test script that validates:

1. Base install works and can import `nornweave`
2. Base install can run with SQLite (no PostgreSQL deps)
3. `[postgres]` extra enables PostgreSQL adapter
4. `[mcp]` extra enables MCP server
5. MCP server starts and responds to tool list

Test runs in CI using isolated virtual environments to ensure clean installs.

**Rationale:** Packaging issues are easy to miss. Automated validation catches missing deps, broken imports, and entry point issues.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Existing users expect PostgreSQL in base | Document migration path in CHANGELOG and README |
| Import errors confusing for new users | Clear error messages with installation hints |
| PyPI name squatting | Package name `nornweave` is available (verified) |
| Breaking Docker builds | Update Dockerfile to use `pip install .[postgres,mcp]` |
| Alembic migrations fail without psycopg2 | Document that `[postgres]` is needed for PostgreSQL migrations |

## Migration Plan

1. **Update pyproject.toml** - Move PostgreSQL deps to `[postgres]` extra
2. **Update dependencies.py** - Add lazy imports with error handling
3. **Update urdr/__init__.py** - Make PostgresAdapter import optional
4. **Update Dockerfile** - Change to `pip install .[postgres,mcp]`
5. **Update Makefile** - Add targets for different install flavors
6. **Fix documentation** - Align MCP configs, add extras documentation
7. **Add CI workflow** - PyPI publishing with trusted auth
8. **Add e2e tests** - Validate all installation paths
9. **Publish to PyPI** - Initial release as 0.1.0
10. **Update README** - Installation from PyPI as primary method

**Rollback:** If issues found, yank the PyPI release and guide users to install from git.

## Resolved Questions

1. **Version strategy**: Start at 0.1.1 (next version after latest tagged release on GitHub). The `vX.Y.Z` tag on the monorepo matches the main Python package version.
2. **TestPyPI**: Not needed—publish directly to PyPI.
