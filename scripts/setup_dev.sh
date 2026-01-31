#!/usr/bin/env bash
# NornWeave development setup
set -euo pipefail

echo "=== NornWeave dev setup ==="

if ! command -v uv &>/dev/null; then
  echo "Install uv: https://docs.astral.sh/uv/"
  exit 1
fi

uv sync --extra dev
uv run pre-commit install 2>/dev/null || true

echo "Copy .env.example to .env and set your keys."
echo "Start PostgreSQL: docker compose up -d postgres"
echo "Run migrations: make migrate"
echo "Start server: make dev"
echo "Done."
