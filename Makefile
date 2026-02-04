.PHONY: install dev test lint format typecheck migrate docker-up docker-down mcp docs clean help

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

# =============================================================================
# Installation & Setup
# =============================================================================

install: ## Install dependencies with uv
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	uv sync

install-dev: ## Install with all development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	uv sync --all-extras

install-all: ## Install with all optional dependencies
	@echo "$(BLUE)Installing all dependencies...$(RESET)"
	uv sync --extra all --extra dev --extra docs

setup: install-dev ## Initial project setup
	@echo "$(BLUE)Setting up pre-commit hooks...$(RESET)"
	uv run pre-commit install
	@echo "$(GREEN)Setup complete!$(RESET)"

# =============================================================================
# Development
# =============================================================================

dev: ## Run development server with hot reload
	@echo "$(BLUE)Starting development server...$(RESET)"
	uv run uvicorn nornweave.yggdrasil.app:app --reload --host 0.0.0.0 --port 8000

run: ## Run production server
	@echo "$(BLUE)Starting production server...$(RESET)"
	uv run uvicorn nornweave.yggdrasil.app:app --host 0.0.0.0 --port 8000

mcp: ## Run MCP server (for Cursor/Claude integration)
	@echo "$(BLUE)Starting MCP server...$(RESET)"
	uv run python -m nornweave.huginn.server

shell: ## Open Python shell with project context
	@echo "$(BLUE)Opening Python shell...$(RESET)"
	uv run python

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	uv run pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	uv run pytest tests/unit -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	uv run pytest tests/integration -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	uv run pytest --cov=src/nornweave --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	uv run pytest-watch

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linter (ruff)
	@echo "$(BLUE)Running linter...$(RESET)"
	uv run ruff check src tests

lint-fix: ## Run linter and fix issues
	@echo "$(BLUE)Running linter with auto-fix...$(RESET)"
	uv run ruff check src tests --fix

format: ## Format code (ruff)
	@echo "$(BLUE)Formatting code...$(RESET)"
	uv run ruff format src tests

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	uv run ruff format src tests --check

typecheck: ## Run type checker (mypy)
	@echo "$(BLUE)Running type checker...$(RESET)"
	uv run mypy src

check: lint format-check typecheck ## Run all code quality checks
	@echo "$(GREEN)All checks passed!$(RESET)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(RESET)"
	uv run pre-commit run --all-files

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(RESET)"
	uv run alembic upgrade head

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(RESET)"
	uv run alembic downgrade -1

migrate-new: ## Create a new migration (usage: make migrate-new MSG="migration message")
	@echo "$(BLUE)Creating new migration...$(RESET)"
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(RESET)"
	uv run alembic history

db-reset: ## Reset database (drop and recreate)
	@echo "$(YELLOW)Resetting database...$(RESET)"
	uv run alembic downgrade base
	uv run alembic upgrade head

# =============================================================================
# Docker
# =============================================================================

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(RESET)"
	docker compose up -d

docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(RESET)"
	docker compose down

docker-logs: ## Show Docker container logs
	docker compose logs -f

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(RESET)"
	docker compose build

docker-shell: ## Open shell in API container
	docker compose exec api /bin/bash

docker-reset: ## Reset Docker environment (remove volumes)
	@echo "$(YELLOW)Resetting Docker environment...$(RESET)"
	docker compose down -v
	docker compose up -d

# =============================================================================
# Web (Hugo landing page)
# =============================================================================

web-image: ## Copy hero image from res/ to web/static/images for landing page
	@mkdir -p web/static/images
	@if [ -f res/Nornorna_spinner.jpg ]; then cp res/Nornorna_spinner.jpg web/static/images/; \
	elif ls res/Nornorna_spinner*.jpg 1>/dev/null 2>&1; then cp res/Nornorna_spinner*.jpg web/static/images/; \
	else echo "No Nornorna_spinner image in res/ - add to web/static/images/ for hero"; fi

web-changelog: ## Copy CHANGELOG.md to web root for shortcode (not in content/ so no sidebar page)
	@cp CHANGELOG.md web/changelog_content.md

web-contributing: ## Copy CONTRIBUTING.md to web root for docs shortcode (single source of truth)
	@cp CONTRIBUTING.md web/contributing_content.md

web-build: web-image web-changelog web-contributing ## Build Hugo site (landing page)
	@command -v hugo >/dev/null 2>&1 || (echo "Install Hugo: https://gohugo.io"; exit 1)
	hugo --source web

web-serve: web-image web-changelog web-contributing ## Serve Hugo site locally
	@command -v hugo >/dev/null 2>&1 || (echo "Install Hugo: https://gohugo.io"; exit 1)
	hugo server --source web --disableFastRender

# =============================================================================
# Documentation
# =============================================================================

docs: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(RESET)"
	uv run mkdocs serve

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(RESET)"
	uv run mkdocs build

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "$(BLUE)Deploying documentation...$(RESET)"
	uv run mkdocs gh-deploy

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean ## Clean everything including dependencies
	@echo "$(YELLOW)Cleaning all including .venv...$(RESET)"
	rm -rf .venv/

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)NornWeave - Available Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(RESET)"
	@echo "  make setup          # Initial project setup"
	@echo "  make dev            # Start development server"
	@echo "  make test           # Run all tests"
	@echo "  make docker-up      # Start with Docker"
