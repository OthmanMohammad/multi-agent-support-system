---
name: 🐳 Docker Infrastructure & Container Optimization
about: Production-grade container architecture with multi-stage builds, BuildKit optimization, and best practices
title: '[SUB-ISSUE] Optimize Docker Infrastructure'
labels: ['sub-issue', 'docker', 'infrastructure', 'priority:medium']
assignees: []
---

# 🐳 Docker Infrastructure & Container Optimization

> **Issue ID:** CICD-002
> **Parent Epic:** CICD-001 (CI/CD Pipeline)
> **Priority:** Medium
> **Estimated Effort:** 1 week
> **Team:** DevOps / Infrastructure

---

## 📋 Overview

### Purpose
Build a **production-grade container infrastructure** with optimized Docker images, multi-stage builds, efficient caching, and comprehensive docker-compose configurations for all environments (development, testing, production).

### Business Value
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Build Time (cold)** | ~5 min | ~2 min | **60% faster** |
| **Build Time (cached)** | ~2 min | ~30 sec | **75% faster** |
| **Image Size** | ~450MB | ~350MB | **22% smaller** |
| **Deployment Speed** | ~3 min | ~1 min | **67% faster** |
| **Developer Onboarding** | Manual setup | One command | **10x easier** |

### Why This Matters
- ⚡ **Faster builds** = faster feedback = faster shipping
- 📦 **Smaller images** = faster deployment = less bandwidth
- 🔄 **Better caching** = 90% of builds use cache
- 🛠️ **Multi-environment** = dev, test, prod all configured
- 🚀 **One command** = `docker-compose up` and you're ready

---

## 🏗️ Architecture

### Docker File Structure

```
multi-agent-support-system/
├── Dockerfile                           # Production-optimized build
├── docker-compose.yml                   # Production stack
├── docker-compose.dev.yml               # Development overrides
├── docker-compose.test.yml              # Testing environment
├── .dockerignore                        # Optimize build context
│
├── deployment/
│   └── docker/
│       ├── backend.Dockerfile           # Backend (if split needed)
│       ├── frontend.Dockerfile          # Frontend (if split needed)
│       └── nginx/
│           ├── nginx.conf              # Production nginx config
│           └── Dockerfile.nginx        # Custom nginx if needed
│
└── .github/
    └── workflows/
        └── docker-build.yml            # Automated builds
```

### Multi-Stage Build Strategy

```dockerfile
# Stage 1: Base - Shared dependencies
FROM python:3.11-slim AS base
# Install system-level dependencies common to all stages

# Stage 2: Builder - Build dependencies
FROM base AS builder
# Compile Python packages
# Create virtual environment
# Install all dependencies

# Stage 3: Development - Hot reload, debugging tools
FROM base AS development
# Copy venv from builder
# Install dev tools (ipython, debugpy, pytest)
# Mount source code as volume (hot reload)

# Stage 4: Testing - Minimal test environment
FROM development AS testing
# Copy tests
# Run tests (optional in build)

# Stage 5: Production - Minimal runtime
FROM base AS production
# Copy only venv and source code
# No dev dependencies
# Run as non-root user
# Health checks
# Optimized for size and security
```

---

## 📦 Components

### 1. Production Dockerfile

**File:** `Dockerfile`

**Key Features:**
- ✅ Multi-stage build (5 stages)
- ✅ BuildKit syntax for advanced caching
- ✅ Multi-platform (AMD64 + ARM64)
- ✅ Non-root user
- ✅ Health checks
- ✅ Optimized layer caching
- ✅ Security scanning ready

**Stages:**
```dockerfile
1. base       → Common system dependencies
2. builder    → Python package compilation
3. development → Dev tools + hot reload
4. testing    → Test execution environment
5. production → Minimal runtime (DEFAULT)
```

**Build Options:**
```bash
# Production build (default)
docker build -t app:latest .

# Development build (with dev tools)
docker build --target development -t app:dev .

# Testing build
docker build --target testing -t app:test .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t app:latest .
```

---

### 2. Docker Compose Configurations

#### docker-compose.yml (Production)
**Purpose:** Full production stack

**Services:**
```yaml
- fastapi (backend API)
- postgres (database)
- redis (cache + Celery broker)
- nginx (reverse proxy)
- celery-worker (background tasks)
- celery-beat (scheduler)
- flower (Celery monitoring)
- prometheus (metrics)
- grafana (dashboards)
- exporters (node, postgres, redis)
```

**Resource Limits:**
```yaml
Total Memory: 24GB (Oracle Cloud)
- FastAPI: 2GB
- PostgreSQL: 6GB
- Redis: 2GB
- Prometheus: 2GB
- Grafana: 1GB
- Celery: 1GB
- Nginx: 512MB
- Others: 1.5GB
- Buffer: ~8GB
```

---

#### docker-compose.dev.yml (Development Overrides)
**Purpose:** Local development with hot reload

**Overrides:**
```yaml
fastapi:
  build:
    target: development  # Use dev stage
  command: uvicorn src.api.main:app --reload --host 0.0.0.0
  volumes:
    - ./src:/app/src:cached  # Mount source for hot reload
    - ./tests:/app/tests:cached
  environment:
    LOG_LEVEL: DEBUG
    ENVIRONMENT: development

postgres:
  ports:
    - "5432:5432"  # Expose for local DB tools

redis:
  ports:
    - "6379:6379"  # Expose for local Redis clients

# Remove resource limits for local dev
# Remove health checks (faster startup)
# Add debug ports (debugpy on 5678)
```

**Usage:**
```bash
# Start dev environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or with shortcut
docker-compose --profile dev up
```

---

#### docker-compose.test.yml (Testing)
**Purpose:** Run tests in isolated environment

**Configuration:**
```yaml
fastapi:
  build:
    target: testing
  command: pytest tests/ -v --cov=src --cov-report=xml
  environment:
    ENVIRONMENT: testing
    DATABASE_URL: postgresql://test:test@postgres-test:5432/test_db

postgres-test:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: test_db
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
  tmpfs:
    - /var/lib/postgresql/data  # In-memory DB for speed

redis-test:
  image: redis:7-alpine
  tmpfs:
    - /data  # In-memory cache for speed
```

**Usage:**
```bash
# Run tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# CI/CD usage
docker-compose -f docker-compose.test.yml up --exit-code-from fastapi
```

---

### 3. .dockerignore

**File:** `.dockerignore`

**Purpose:** Exclude unnecessary files from build context (faster builds)

```
# Version control
.git
.gitignore
.github

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# Testing
.pytest_cache
.coverage
htmlcov/
test-results/

# IDE
.vscode
.idea
*.swp
*.swo

# Logs
*.log
logs/

# Documentation
*.md
docs/
!README.md

# CI/CD
Jenkinsfile
.github/

# Docker
docker-compose*.yml
Dockerfile*

# Large files
*.mp4
*.mov
*.zip
*.tar.gz

# Development
.env.local
.env.development
```

---

### 4. Build Optimization Techniques

#### BuildKit Cache Mounts
```dockerfile
# Before (slow - downloads every time)
RUN pip install -r requirements.txt

# After (fast - caches pip downloads)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

#### Multi-Platform Builds
```dockerfile
# Support both AMD64 and ARM64
FROM --platform=$BUILDPLATFORM python:3.11-slim AS base

# Use BuildKit automatic platform args
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building for $TARGETPLATFORM on $BUILDPLATFORM"
```

#### Layer Caching Optimization
```dockerfile
# Bad (invalidates cache on any code change)
COPY . /app
RUN pip install -r requirements.txt

# Good (cache persists unless requirements.txt changes)
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
```

---

## 🎯 Detailed Implementation

### Step 1: Create Production Dockerfile

**File:** `Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1.4

ARG PYTHON_VERSION=3.11

# ====================
# Stage 1: Base
# ====================
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ====================
# Stage 2: Builder
# ====================
FROM base AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /tmp
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ====================
# Stage 3: Development
# ====================
FROM base AS development

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        git \
        vim \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        flake8 \
        mypy \
        ipython \
        debugpy

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ====================
# Stage 4: Testing
# ====================
FROM development AS testing

COPY . /app

RUN pytest tests/unit/ -v

# ====================
# Stage 5: Production
# ====================
FROM base AS production

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        tini \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/logs /app/.cache && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HF_HOME=/app/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

### Step 2: Create .dockerignore

**File:** `.dockerignore`

(Content shown above in Components section)

---

### Step 3: Update docker-compose.yml

Replace current docker-compose.yml with production-optimized version including Celery services.

---

### Step 4: Create Development Override

**File:** `docker-compose.dev.yml`

```yaml
version: '3.8'

# Development overrides for docker-compose.yml
# Usage: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

services:
  fastapi:
    build:
      target: development
    command: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
    volumes:
      - ./src:/app/src:cached
      - ./tests:/app/tests:cached
      - ./alembic:/app/alembic:cached
    ports:
      - "5678:5678"  # debugpy
    environment:
      LOG_LEVEL: DEBUG
      ENVIRONMENT: development
    # Remove resource limits for dev
    deploy: {}

  postgres:
    ports:
      - "5432:5432"
    volumes:
      - ./backups:/backups:cached

  redis:
    ports:
      - "6379:6379"

  # Remove monitoring stack in dev (too heavy)
  prometheus:
    profiles: ["monitoring"]

  grafana:
    profiles: ["monitoring"]
```

---

### Step 5: Create Test Configuration

**File:** `docker-compose.test.yml`

```yaml
version: '3.8'

# Testing environment
# Usage: docker-compose -f docker-compose.test.yml up --exit-code-from backend

services:
  backend:
    build:
      context: .
      target: testing
    command: pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
    environment:
      ENVIRONMENT: testing
      DATABASE_URL: postgresql+asyncpg://test:test@postgres-test:5432/test_db
      REDIS_URL: redis://redis-test:6379/0
    depends_on:
      - postgres-test
      - redis-test
    volumes:
      - ./test-results:/app/test-results
      - ./coverage:/app/coverage

  postgres-test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    tmpfs:
      - /var/lib/postgresql/data

  redis-test:
    image: redis:7-alpine
    tmpfs:
      - /data
```

---

## ✅ Acceptance Criteria

### Dockerfile
- [ ] Multi-stage Dockerfile created with 5 stages
- [ ] BuildKit syntax enabled
- [ ] Cache mounts configured for pip
- [ ] Non-root user configured
- [ ] Health check implemented
- [ ] Multi-platform build tested (AMD64 + ARM64)
- [ ] Image size <400MB
- [ ] Security scan passing (no critical/high vulns)

### Docker Compose
- [ ] Production docker-compose.yml with all services
- [ ] Development override (docker-compose.dev.yml) created
- [ ] Test environment (docker-compose.test.yml) created
- [ ] Resource limits configured
- [ ] Health checks for all services
- [ ] Proper dependency ordering (depends_on)

### Build Performance
- [ ] Cold build completes in <3 minutes
- [ ] Cached build completes in <1 minute
- [ ] BuildKit caching working (90%+ cache hit rate)
- [ ] Multi-arch build working

### Development Experience
- [ ] `docker-compose up` starts full stack
- [ ] Hot reload working in dev mode
- [ ] Source code mounted (no rebuild needed)
- [ ] Database accessible from host (port 5432)
- [ ] Redis accessible from host (port 6379)

### Testing
- [ ] `docker-compose -f docker-compose.test.yml up` runs tests
- [ ] Tests run in isolated environment
- [ ] Test results exported to host
- [ ] Coverage reports generated

### Documentation
- [ ] README.md updated with Docker usage
- [ ] Development setup guide created
- [ ] Troubleshooting guide created

---

## 📊 Success Metrics

```yaml
Build Time (Cold):
  Target: <3 minutes
  Measured: ___

Build Time (Cached):
  Target: <1 minute
  Measured: ___

Image Size:
  Target: <400MB
  Measured: ___

Cache Hit Rate:
  Target: >90%
  Measured: ___

Developer Onboarding:
  Target: <5 minutes (from clone to running app)
  Measured: ___
```

---

## 🗺️ Implementation Timeline

### Week 1: Docker Optimization
**Days 1-2:** Dockerfile Creation
- Create multi-stage Dockerfile
- Add BuildKit optimizations
- Test multi-platform builds

**Days 3-4:** Docker Compose
- Update production docker-compose.yml
- Create development override
- Create test environment

**Day 5:** Testing & Documentation
- Test all environments
- Measure performance improvements
- Write documentation

---

## 📚 Related Issues

- **CICD-001:** Main CI/CD Pipeline (Parent)
- **CICD-003:** Celery Background Processing
- **CICD-004:** Monitoring & Observability

---

## 🔗 Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose](https://docs.docker.com/compose/)

---

**Issue Author:** DevOps Team
**Created:** 2025-01-15
**Last Updated:** 2025-01-15
