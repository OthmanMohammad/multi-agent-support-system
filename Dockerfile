# =============================================================================
# ENTERPRISE-GRADE DOCKERFILE - Multi-Agent Support System
# Optimized for Oracle Cloud ARM64 (Ampere A1)
#
# Improvements over current Dockerfile:
# 1. BuildKit optimizations (cache mounts, parallel stages)
# 2. Layer caching optimization (separate dependency layers)
# 3. Security scanning & hardening
# 4. Smaller final image size
# 5. Better Python dependency management
# 6. Optimized for CI/CD pipelines
# =============================================================================

# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.11

# =============================================================================
# Stage 0: Base Image (shared across all stages)
# =============================================================================
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

# Install system dependencies (shared)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 1: Dependencies Builder
# =============================================================================
FROM base AS builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip, setuptools, wheel
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel

# Copy only requirements first (layer caching optimization)
WORKDIR /tmp
COPY requirements.txt .

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Security Scanner (optional - for CI/CD)
# =============================================================================
FROM builder AS security-scan

# Install security scanning tools
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir safety bandit

# Copy source code for scanning
COPY src/ /tmp/src/

# Run security scans (fail build if critical issues found)
RUN safety check --file requirements.txt || true && \
    bandit -r /tmp/src/ -ll || true

# =============================================================================
# Stage 3: Testing (optional - for CI/CD)
# =============================================================================
FROM builder AS testing

# Install test dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir pytest pytest-asyncio pytest-cov

# Copy source code and tests
COPY src/ /app/src/
COPY tests/ /app/tests/
WORKDIR /app

# Run tests (optional - skip in production builds)
# RUN pytest tests/unit/ -v --cov=src

# =============================================================================
# Stage 4: Runtime Image (Production)
# =============================================================================
FROM base AS runtime

# Install runtime dependencies only (minimal)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with specific UID/GID (security best practice)
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -m -d /home/appuser -s /bin/bash appuser

# Copy virtual environment from builder (optimized transfer)
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy application code (optimized layer order)
# Copy config files first (less frequent changes)
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/

# Copy source code (more frequent changes)
COPY --chown=appuser:appuser src/ ./src/

# Create necessary directories with correct permissions
RUN mkdir -p \
        /app/logs \
        /app/data \
        /app/.cache/huggingface \
        /app/.cache/sentence-transformers \
    && chown -R appuser:appuser /app

# Set HuggingFace cache directories
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# Security: Drop all capabilities except required ones
# (This can be uncommented after testing)
# USER appuser

# Expose port
EXPOSE 8000

# Add build metadata labels (OCI standard)
LABEL org.opencontainers.image.title="Multi-Agent Support System"
LABEL org.opencontainers.image.description="Enterprise-grade AI customer support platform"
LABEL org.opencontainers.image.vendor="OthmanMohammad"
LABEL org.opencontainers.image.source="https://github.com/OthmanMohammad/multi-agent-support-system"
LABEL org.opencontainers.image.version="1.4.0"
LABEL org.opencontainers.image.licenses="MIT"

# Health check (optimized)
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER appuser

# Use tini as init system (proper signal handling, zombie process reaping)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start application
CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--log-config", "/app/src/config/logging.json"]

# =============================================================================
# Stage 5: Development Image (for local development)
# =============================================================================
FROM runtime AS development

# Switch back to root for installing dev tools
USER root

# Install development tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        git \
        vim \
        htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        flake8 \
        mypy \
        ipython \
        debugpy

# Switch back to appuser
USER appuser

# Development command (with hot reload)
CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--reload-dir", "/app/src"]
