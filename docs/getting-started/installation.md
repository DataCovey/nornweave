# Installation

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker and Docker Compose (for local PostgreSQL/Redis)

## Install with uv

```bash
git clone https://github.com/nornweave/nornweave.git
cd nornweave
uv sync
```

For development (with dev dependencies):

```bash
uv sync --extra dev
```

## Install with pip

```bash
pip install nornweave
```

Or from source:

```bash
git clone https://github.com/nornweave/nornweave.git
cd nornweave
pip install -e ".[dev]"
```

## Optional extras

- MCP server: `uv sync --extra mcp`
- Attachments (PDF/CSV): `uv sync --extra attachments`
- Semantic search: `uv sync --extra search`
- Rate limiting (Redis): `uv sync --extra ratelimit`
- All: `uv sync --extra all`
