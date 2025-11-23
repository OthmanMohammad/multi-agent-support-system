---
name: 📊 Monitoring & Observability Infrastructure
about: Production-grade monitoring with Prometheus, Grafana, alerts, and distributed tracing
title: '[SUB-ISSUE] Implement Monitoring & Observability Stack'
labels: ['sub-issue', 'monitoring', 'observability', 'priority:high']
assignees: []
---

# 📊 Monitoring & Observability Infrastructure

> **Issue ID:** CICD-004
> **Parent Epic:** CICD-001 (CI/CD Pipeline)
> **Priority:** High
> **Estimated Effort:** 1-2 weeks
> **Team:** DevOps / SRE

---

## 📋 Overview

### Purpose
Build a **comprehensive monitoring and observability stack** that provides real-time visibility into system health, performance, and errors across all services. Enable proactive incident detection, rapid troubleshooting, and data-driven capacity planning.

### Business Value
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **MTTD (Mean Time to Detect)** | Manual checks | <2 minutes | **Automated** |
| **MTTR (Mean Time to Resolve)** | Hours | <30 minutes | **80% faster** |
| **System Visibility** | Logs only | Metrics + Traces + Logs | **360° view** |
| **Alert Fatigue** | High noise | Smart routing | **90% less noise** |
| **Incident Prevention** | Reactive | Proactive | **Prevent 70% issues** |

### Why This Matters
- 🚨 **Proactive alerts** = Know about issues before users do
- 📈 **Real-time metrics** = Instant visibility into system health
- 🔍 **Distributed tracing** = Debug across 243 agents in seconds
- 📊 **Business insights** = Task success rates, latency trends
- 💰 **Cost optimization** = Right-size resources based on data

---

## 🏗️ Architecture

### Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRODUCTION SERVICES                         │
│  FastAPI │ PostgreSQL │ Redis │ Celery │ Nginx │ vLLM          │
└────┬──────────┬─────────┬───────┬────────┬───────┬──────────────┘
     │          │         │       │        │       │
     ├──────────┴─────────┴───────┴────────┴───────┘
     │                    METRICS
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PROMETHEUS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Node Exporter│  │Postgres Export│ │ Redis Export │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │Celery Export │  │ FastAPI /metrics (custom)                 │
│  └──────────────┘  └──────────────┘                            │
│                                                                  │
│  Retention: 15 days                                             │
│  Scrape Interval: 15s                                           │
└────┬─────────────────────────────────────────────────────────────┘
     │
     ├──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ GRAFANA  │  │ ALERTS   │  │ LOKI     │  │ SENTRY   │
│          │  │          │  │ (Logs)   │  │ (Errors) │
│ Dashboards│  │ PagerDuty│  │          │  │          │
│ Queries  │  │ Slack    │  │ 7 days   │  │ 90 days  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   ON-CALL ENGINEER  │
              │   (You)             │
              └─────────────────────┘
```

---

## 📦 Components

### 1. Prometheus (Metrics Collection)

**Purpose:** Collect, store, and query time-series metrics from all services

**Key Features:**
- ✅ Multi-target scraping (7 exporters)
- ✅ Custom metrics from FastAPI
- ✅ 15-day retention (15GB storage)
- ✅ High-performance queries (PromQL)
- ✅ Service discovery (Docker labels)

**Metrics Collected:**
```yaml
System Metrics:
  - CPU usage per service
  - Memory usage per service
  - Disk I/O and usage
  - Network traffic

Application Metrics:
  - HTTP request rate (requests/sec)
  - HTTP response latency (p50, p95, p99)
  - HTTP error rate (4xx, 5xx)
  - Active connections

Database Metrics:
  - PostgreSQL connections (active/idle)
  - Query execution time
  - Table sizes
  - Transaction rate
  - Cache hit ratio

Redis Metrics:
  - Memory usage
  - Connected clients
  - Commands/sec
  - Keyspace hits/misses
  - Evicted keys

Celery Metrics:
  - Tasks pending (per queue)
  - Tasks active (per worker)
  - Tasks succeeded/failed
  - Task execution time
  - Worker status

Business Metrics:
  - Total conversations created
  - Agent workflow completions
  - Average workflow duration
  - User satisfaction scores
  - API quota usage
```

---

### 2. Grafana (Visualization)

**Purpose:** Beautiful, interactive dashboards for metrics visualization

**Dashboards to Create:**

#### Dashboard 1: System Overview
```yaml
Panels:
  - Service Health Matrix (up/down status)
  - Total Requests/sec (last 5 min)
  - Error Rate (4xx, 5xx) %
  - P95 Response Latency (ms)
  - CPU Usage by Service (%)
  - Memory Usage by Service (GB)
  - Disk I/O (MB/s)
  - Network Traffic (Mbps)

Time Range: Last 6 hours (default)
Refresh: 10s
```

#### Dashboard 2: FastAPI Performance
```yaml
Panels:
  - Request Rate by Endpoint
  - Latency Heatmap (all endpoints)
  - Top 10 Slowest Endpoints
  - Error Rate by Endpoint
  - Active WebSocket Connections
  - Request Duration Percentiles (p50, p90, p95, p99)
  - Throughput (requests/min)
  - Concurrent Requests

Filters:
  - Endpoint (dropdown)
  - Status Code (dropdown)
  - Time Range (picker)
```

#### Dashboard 3: Database Performance
```yaml
Panels:
  - PostgreSQL Connections (active/idle/waiting)
  - Query Execution Time (p95)
  - Transactions/sec
  - Cache Hit Ratio (should be >95%)
  - Table Sizes (top 10)
  - Slow Queries (>1s)
  - Deadlocks (count)
  - Replication Lag (if applicable)

Alerts:
  - Cache hit ratio <90% (warning)
  - Active connections >80% of max (critical)
  - Slow queries >10/min (warning)
```

#### Dashboard 4: Celery Task Monitoring
```yaml
Panels:
  - Tasks by Status (pie chart: pending/active/success/failure)
  - Task Throughput (tasks/min)
  - Task Duration by Type (boxplot)
  - Queue Lengths (high/default/low)
  - Worker Status (online/offline)
  - Failed Tasks (last 1h)
  - Retry Count Distribution
  - Task Age in Queue (histogram)

Linked to Flower: Click task ID → Flower details
```

#### Dashboard 5: Business Metrics
```yaml
Panels:
  - Conversations Created (last 24h)
  - Agent Workflow Completions (by type)
  - Average Workflow Duration (trend)
  - User Satisfaction Score (gauge)
  - API Quota Usage (%)
  - Revenue Impact (if applicable)
  - Top Users by Activity
  - Peak Usage Hours (heatmap)
```

---

### 3. Alerting (Prometheus Alertmanager)

**Purpose:** Smart, actionable alerts with proper routing and deduplication

**Alert Rules:**

#### Critical Alerts (PagerDuty + Slack)
```yaml
- alert: ServiceDown
  expr: up{job=~"fastapi|postgres|redis"} == 0
  for: 1m
  severity: critical
  message: "{{ $labels.job }} is DOWN"

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 3m
  severity: critical
  message: "Error rate >5% on {{ $labels.endpoint }}"

- alert: DatabaseConnectionsExhausted
  expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
  for: 2m
  severity: critical
  message: "PostgreSQL connections at {{ $value }}%"

- alert: DiskSpaceLow
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 5m
  severity: critical
  message: "Disk space <10% on {{ $labels.mountpoint }}"
```

#### Warning Alerts (Slack only)
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 10m
  severity: warning
  message: "P95 latency >2s on {{ $labels.endpoint }}"

- alert: CeleryQueueBacklog
  expr: celery_queue_length{queue="default"} > 100
  for: 15m
  severity: warning
  message: "Celery queue backlog: {{ $value }} tasks"

- alert: HighMemoryUsage
  expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
  for: 10m
  severity: warning
  message: "{{ $labels.name }} memory >85%"

- alert: CacheHitRatioLow
  expr: redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) < 0.9
  for: 15m
  severity: warning
  message: "Redis cache hit ratio <90%"
```

#### Info Alerts (Slack only, no page)
```yaml
- alert: DeploymentDetected
  expr: changes(container_start_time_seconds[2m]) > 0
  severity: info
  message: "New deployment: {{ $labels.name }}"

- alert: DatabaseBackupCompleted
  expr: postgresql_backup_last_success_timestamp_seconds > 0
  severity: info
  message: "Database backup completed"
```

**Alert Routing:**
```yaml
route:
  receiver: 'default-slack'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  routes:
    # Critical alerts → PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true

    - match:
        severity: critical
      receiver: 'slack-critical'

    # Warnings → Slack only
    - match:
        severity: warning
      receiver: 'slack-warnings'

    # Info → Slack (quiet channel)
    - match:
        severity: info
      receiver: 'slack-info'

receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_SERVICE_KEY>'

  - name: 'slack-critical'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK_URL>'
        channel: '#alerts-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK_URL>'
        channel: '#alerts-warnings'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'

  - name: 'slack-info'
    slack_configs:
      - api_url: '<SLACK_WEBHOOK_URL>'
        channel: '#alerts-info'
        title: 'ℹ️ INFO: {{ .GroupLabels.alertname }}'
```

---

### 4. Loki (Log Aggregation)

**Purpose:** Centralized log collection and querying (like Prometheus for logs)

**Architecture:**
```yaml
Services → promtail (log shipper) → Loki → Grafana (visualization)
```

**Log Sources:**
```yaml
- FastAPI application logs (structlog JSON)
- Nginx access logs
- Nginx error logs
- PostgreSQL logs
- Redis logs
- Celery worker logs
- Celery beat logs
- Container logs (Docker)
```

**Log Structure (JSON):**
```json
{
  "timestamp": "2025-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "src.api.routes.conversations",
  "message": "Conversation created",
  "conversation_id": "conv_abc123",
  "user_id": "user_xyz789",
  "workflow_type": "sequential",
  "duration_ms": 234,
  "agent_count": 3,
  "trace_id": "trace_123abc",
  "span_id": "span_456def"
}
```

**LogQL Queries:**
```logql
# All errors in last 1 hour
{job="fastapi"} |= "ERROR"

# Slow requests (>2s)
{job="fastapi"} | json | duration_ms > 2000

# Failed Celery tasks
{job="celery-worker"} |= "FAILURE"

# 5xx errors by endpoint
sum by (endpoint) (rate({job="nginx"} |= "status=5" [5m]))

# User activity
{job="fastapi"} | json | user_id="user_xyz789"
```

**Loki Configuration:**
```yaml
Retention: 7 days
Compression: gzip
Storage: 50GB (SSD)
Ingestion Rate: 4MB/s
Query Limit: 1000 lines (default)
```

---

### 5. Sentry (Error Tracking)

**Purpose:** Real-time error tracking, stack traces, and release tracking

**Integration:**
```python
# src/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,  # production/staging/development
    release=settings.git_commit_sha,
    traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
    profiles_sample_rate=0.1,  # 10% of transactions for profiling
    integrations=[
        FastApiIntegration(),
        RedisIntegration(),
        CeleryIntegration(),
    ],
    before_send=filter_sensitive_data,  # Scrub PII
)
```

**Error Context:**
```python
with sentry_sdk.configure_scope() as scope:
    scope.set_user({
        "id": user.id,
        "email": user.email,  # Scrubbed in production
        "username": user.username
    })
    scope.set_context("conversation", {
        "id": conversation.id,
        "workflow_type": conversation.workflow_type,
        "agent_count": len(conversation.agents)
    })
    scope.set_tag("workflow_type", conversation.workflow_type)
```

**Sentry Features:**
```yaml
- Stack traces with source code
- Breadcrumbs (events leading to error)
- Release tracking (correlate errors with deployments)
- Performance monitoring (transaction traces)
- Session replays (user actions before error)
- Issue grouping (similar errors grouped)
- Alert rules (Slack/email on new errors)
```

---

### 6. Flower (Celery Monitoring)

**Purpose:** Real-time Celery task monitoring and management UI

**URL:** `http://your-server:5555`

**Features:**
```yaml
- Real-time task monitoring
- Task history (success/failure/retry)
- Worker status and stats
- Queue lengths and routing
- Task execution graphs
- Manual task retry
- Worker pool restarts
- Task result inspection
- Broker monitoring (Redis)
```

**Security:**
```yaml
# Enable authentication
flower:
  environment:
    FLOWER_BASIC_AUTH: "admin:${FLOWER_PASSWORD}"
    FLOWER_PORT: 5555
    FLOWER_URL_PREFIX: /flower  # Behind Nginx reverse proxy
```

**Integration with Grafana:**
- Embed Flower in Grafana iframe
- Link from task panels to Flower task details

---

## 🎯 Detailed Implementation

### Step 1: Update Prometheus Configuration

**File:** `deployment/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    region: 'us-west-1'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - '/etc/prometheus/alerts/*.yml'

scrape_configs:
  # FastAPI application metrics
  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node (system) metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Celery metrics
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-exporter:9808']

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

---

### Step 2: Create Alert Rules

**File:** `deployment/monitoring/alerts/application.yml`

```yaml
groups:
  - name: application
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) > 0.05
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.endpoint }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s on {{ $labels.endpoint }}"

      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 100
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backlog"
          description: "Queue {{ $labels.queue }} has {{ $value }} pending tasks"
```

**File:** `deployment/monitoring/alerts/infrastructure.yml`

```yaml
groups:
  - name: infrastructure
    interval: 30s
    rules:
      - alert: ServiceDown
        expr: up{job=~"fastapi|postgres|redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.job }} has been down for 1 minute"

      - alert: HighMemoryUsage
        expr: |
          (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "{{ $labels.name }} is using {{ $value | humanizePercentage }} memory"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value | humanizePercentage }} disk space remaining"

      - alert: DatabaseConnectionsHigh
        expr: |
          pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections high"
          description: "PostgreSQL using {{ $value | humanizePercentage }} of max connections"
```

---

### Step 3: Configure Grafana Dashboards

**File:** `deployment/monitoring/grafana/provisioning/dashboards/system-overview.json`

```json
{
  "dashboard": {
    "title": "System Overview",
    "tags": ["overview", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Health",
        "type": "stat",
        "targets": [{
          "expr": "up",
          "legendFormat": "{{ job }}"
        }],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [{
          "expr": "sum(rate(http_requests_total[5m]))",
          "legendFormat": "Requests/sec"
        }]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [{
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m]))",
          "legendFormat": "5xx Errors/sec"
        }]
      },
      {
        "id": 4,
        "title": "P95 Latency",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "P95"
        }]
      }
    ]
  }
}
```

---

### Step 4: Add Custom Metrics to FastAPI

**File:** `src/core/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

# Business metrics
conversations_created_total = Counter(
    'conversations_created_total',
    'Total conversations created',
    ['workflow_type']
)

agent_workflow_duration_seconds = Histogram(
    'agent_workflow_duration_seconds',
    'Agent workflow execution time',
    ['workflow_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# System metrics
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

# Application info
app_info = Info('app', 'Application information')
app_info.info({
    'version': settings.app_version,
    'environment': settings.environment,
    'git_commit': settings.git_commit_sha
})


def track_request_metrics(func):
    """Decorator to track HTTP request metrics"""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()

        try:
            response = await func(request, *args, **kwargs)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time

            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

        return response

    return wrapper
```

**File:** `src/api/main.py` (add metrics endpoint)

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Add middleware to track all requests
@app.middleware("http")
async def track_metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

---

### Step 5: Update docker-compose.yml with Monitoring Stack

**File:** `docker-compose.yml` (monitoring services)

```yaml
  # Prometheus
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    volumes:
      - ./deployment/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./deployment/monitoring/alerts:/etc/prometheus/alerts:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:10.2.3
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./deployment/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./deployment/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
      - GF_SERVER_ROOT_URL=http://localhost:3001
    ports:
      - "3001:3000"
    networks:
      - app-network
    depends_on:
      - prometheus
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
    restart: unless-stopped

  # Loki (log aggregation)
  loki:
    image: grafana/loki:2.9.3
    container_name: loki
    volumes:
      - ./deployment/monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    restart: unless-stopped

  # Promtail (log shipper)
  promtail:
    image: grafana/promtail:2.9.3
    container_name: promtail
    volumes:
      - ./deployment/monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - app-network
    depends_on:
      - loki
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    restart: unless-stopped

  # Alertmanager
  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: alertmanager
    volumes:
      - ./deployment/monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - app-network
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    restart: unless-stopped

  # Flower (Celery monitoring)
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flower
    command: celery -A src.celery.celery_app flower --port=5555
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
      - FLOWER_BASIC_AUTH=admin:${FLOWER_PASSWORD:-admin}
    ports:
      - "5555:5555"
    networks:
      - app-network
    depends_on:
      - redis
      - celery-worker
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
  alertmanager-data:
```

---

## ✅ Acceptance Criteria

### Metrics Collection
- [ ] Prometheus collecting metrics from all 7 exporters
- [ ] Custom FastAPI metrics implemented (/metrics endpoint)
- [ ] 15-day retention configured
- [ ] Metrics scraping every 15 seconds
- [ ] Service discovery working (Docker labels)

### Dashboards
- [ ] 5 Grafana dashboards created and working
- [ ] System Overview dashboard complete
- [ ] FastAPI Performance dashboard complete
- [ ] Database Performance dashboard complete
- [ ] Celery Task Monitoring dashboard complete
- [ ] Business Metrics dashboard complete
- [ ] Auto-refresh configured (10s interval)

### Alerting
- [ ] 10+ alert rules configured
- [ ] Alert routing working (PagerDuty + Slack)
- [ ] Alert grouping and deduplication working
- [ ] No alert fatigue (smart thresholds)
- [ ] Test alerts sent successfully

### Logging
- [ ] Loki collecting logs from all services
- [ ] Promtail shipping logs correctly
- [ ] JSON log format implemented
- [ ] 7-day retention configured
- [ ] Log queries working in Grafana

### Error Tracking
- [ ] Sentry integrated with FastAPI
- [ ] Sentry integrated with Celery
- [ ] Error context (user, conversation) captured
- [ ] Release tracking configured
- [ ] Source maps uploaded (if applicable)
- [ ] Alert rules configured (Slack on new errors)

### Celery Monitoring
- [ ] Flower UI accessible
- [ ] Real-time task monitoring working
- [ ] Task history visible
- [ ] Worker status displayed
- [ ] Queue lengths tracked
- [ ] Authentication enabled

### Documentation
- [ ] Runbook for common alerts created
- [ ] Dashboard usage guide created
- [ ] Alert response procedures documented
- [ ] Troubleshooting guide created

---

## 📊 Success Metrics

```yaml
MTTD (Mean Time to Detect):
  Target: <2 minutes
  Measured: ___

MTTR (Mean Time to Resolve):
  Target: <30 minutes
  Measured: ___

Alert Accuracy:
  Target: >95% (low false positives)
  Measured: ___

Dashboard Load Time:
  Target: <2 seconds
  Measured: ___

Metrics Collection Coverage:
  Target: 100% of services
  Measured: ___

Uptime Monitoring:
  Target: 99.9% visibility
  Measured: ___
```

---

## 🗺️ Implementation Timeline

### Week 1: Core Monitoring Setup
**Days 1-2:** Prometheus & Exporters
- Deploy Prometheus
- Configure all exporters
- Test metric collection

**Days 3-4:** Grafana Dashboards
- Create 5 core dashboards
- Configure data sources
- Set up auto-refresh

**Day 5:** Testing & Validation
- Verify all metrics flowing
- Test dashboard queries
- Document any issues

### Week 2: Alerting & Advanced Features
**Days 1-2:** Alert Configuration
- Create alert rules
- Configure Alertmanager
- Set up Slack/PagerDuty integration
- Test alert routing

**Days 3-4:** Logging & Error Tracking
- Deploy Loki and Promtail
- Integrate Sentry
- Configure log retention
- Create log dashboards

**Day 5:** Documentation & Handoff
- Write runbooks
- Document alert responses
- Create troubleshooting guide
- Team training

---

## 📚 Related Issues

- **CICD-001:** Main CI/CD Pipeline (Parent)
- **CICD-002:** Docker Infrastructure
- **CICD-003:** Celery Background Processing

---

## 🔗 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Flower Documentation](https://flower.readthedocs.io/)

---

**Issue Author:** DevOps / SRE Team
**Created:** 2025-01-15
**Last Updated:** 2025-01-15
