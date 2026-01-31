# =============================================================================
# NornWeave Dockerfile
# Multi-stage build for development and production
# =============================================================================

# -----------------------------------------------------------------------------
# Base stage: Python with uv
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# -----------------------------------------------------------------------------
# Dependencies stage: Install dependencies
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies (without dev dependencies for production)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# -----------------------------------------------------------------------------
# Development stage: Full dev environment
# -----------------------------------------------------------------------------
FROM base AS development

# Install system dependencies for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and install with dev dependencies
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY alembic.ini ./

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Create non-root user
RUN useradd --create-home --shell /bin/bash nornweave
USER nornweave

# Expose port
EXPOSE 8000

# Default command for development
CMD ["uv", "run", "uvicorn", "nornweave.yggdrasil.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Production stage: Minimal production image
# -----------------------------------------------------------------------------
FROM base AS production

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from dependencies stage
COPY --from=dependencies /app/.venv /app/.venv

# Copy source code
COPY src/ ./src/
COPY alembic.ini ./

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash nornweave && \
    chown -R nornweave:nornweave /app
USER nornweave

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["python", "-m", "uvicorn", "nornweave.yggdrasil.app:app", "--host", "0.0.0.0", "--port", "8000"]
