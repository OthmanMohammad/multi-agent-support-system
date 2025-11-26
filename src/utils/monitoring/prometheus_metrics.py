"""
Prometheus Metrics Collection

Comprehensive metrics collection for monitoring and observability.
Uses Prometheus client library for metrics export.

Metrics Categories:
- HTTP requests (counter, histogram)
- Agent executions (counter, histogram, gauge)
- Workflow executions (counter, histogram)
- Database queries (counter, histogram)
- External API calls (counter, histogram)
- Business metrics (conversations, customers, etc.)
- System metrics (memory, CPU, etc.)

Part of: Phase 5 - Monitoring & Observability
"""

import time
from functools import wraps

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


# =============================================================================
# PROMETHEUS REGISTRY
# =============================================================================

# Create custom registry (or use default)
registry = CollectorRegistry()


# =============================================================================
# HTTP METRICS
# =============================================================================

# HTTP request counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

# HTTP request duration
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry,
)

# HTTP requests in progress
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=registry,
)


# =============================================================================
# AGENT EXECUTION METRICS
# =============================================================================

# Agent execution counter
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_name", "tier", "status"],
    registry=registry,
)

# Agent execution duration
agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name", "tier"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry,
)

# Agent tokens used
agent_tokens_used_total = Counter(
    "agent_tokens_used_total",
    "Total LLM tokens used by agents",
    ["agent_name", "model"],
    registry=registry,
)

# Active agent executions
agent_executions_in_progress = Gauge(
    "agent_executions_in_progress",
    "Agent executions currently in progress",
    ["agent_name"],
    registry=registry,
)


# =============================================================================
# WORKFLOW EXECUTION METRICS
# =============================================================================

# Workflow execution counter
workflow_executions_total = Counter(
    "workflow_executions_total",
    "Total workflow executions",
    ["workflow_type", "status"],
    registry=registry,
)

# Workflow execution duration
workflow_execution_duration_seconds = Histogram(
    "workflow_execution_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=registry,
)

# Active workflow executions
workflow_executions_in_progress = Gauge(
    "workflow_executions_in_progress",
    "Workflow executions currently in progress",
    ["workflow_type"],
    registry=registry,
)


# =============================================================================
# DATABASE METRICS
# =============================================================================

# Database query counter
db_queries_total = Counter(
    "db_queries_total", "Total database queries", ["operation", "table"], registry=registry
)

# Database query duration
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry,
)

# Database connection pool
db_connections_active = Gauge(
    "db_connections_active", "Active database connections", registry=registry
)

db_connections_idle = Gauge("db_connections_idle", "Idle database connections", registry=registry)


# =============================================================================
# BUSINESS METRICS
# =============================================================================

# Conversations
conversations_total = Gauge(
    "conversations_total", "Total conversations", ["status"], registry=registry
)

conversations_created_total = Counter(
    "conversations_created_total", "Total conversations created", registry=registry
)

conversations_resolved_total = Counter(
    "conversations_resolved_total", "Total conversations resolved", registry=registry
)

# Customers
customers_total = Gauge("customers_total", "Total customers", ["plan", "status"], registry=registry)

customers_created_total = Counter(
    "customers_created_total", "Total customers created", ["plan"], registry=registry
)

# Messages
messages_total = Counter("messages_total", "Total messages", ["role"], registry=registry)


# =============================================================================
# EXTERNAL API METRICS
# =============================================================================

# External API calls
external_api_calls_total = Counter(
    "external_api_calls_total",
    "Total external API calls",
    ["service", "endpoint", "status_code"],
    registry=registry,
)

# External API duration
external_api_duration_seconds = Histogram(
    "external_api_duration_seconds",
    "External API call duration in seconds",
    ["service", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry,
)


# =============================================================================
# AUTHENTICATION METRICS
# =============================================================================

# Authentication attempts
auth_attempts_total = Counter(
    "auth_attempts_total", "Total authentication attempts", ["method", "status"], registry=registry
)

# Active sessions
active_sessions = Gauge("active_sessions", "Active user sessions", registry=registry)

# Rate limit hits
rate_limit_hits_total = Counter(
    "rate_limit_hits_total", "Total rate limit hits", ["tier", "endpoint"], registry=registry
)


# =============================================================================
# SYSTEM METRICS
# =============================================================================

# Application info
app_info = Info("app", "Application information", registry=registry)

# Set application info
app_info.info(
    {"version": "1.0.0", "environment": "production", "name": "multi-agent-support-system"}
)


# =============================================================================
# METRIC DECORATORS
# =============================================================================


def track_http_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment in-progress gauge
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status_code = getattr(result, "status_code", 200)

                # Record metrics
                duration = time.time() - start_time
                http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
                    duration
                )

                http_requests_total.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).inc()

                return result

            except Exception:
                # Record error
                http_requests_total.labels(method=method, endpoint=endpoint, status_code=500).inc()
                raise

            finally:
                # Decrement in-progress gauge
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        return wrapper

    return decorator


def track_agent_execution(agent_name: str, tier: str):
    """Decorator to track agent execution metrics"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment in-progress gauge
            agent_executions_in_progress.labels(agent_name=agent_name).inc()

            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # Track token usage if available
                if hasattr(result, "tokens_used"):
                    agent_tokens_used_total.labels(
                        agent_name=agent_name, model=getattr(result, "model_used", "unknown")
                    ).inc(result.tokens_used)

                return result

            except Exception:
                status = "failed"
                raise

            finally:
                # Record metrics
                duration = time.time() - start_time
                agent_execution_duration_seconds.labels(agent_name=agent_name, tier=tier).observe(
                    duration
                )

                agent_executions_total.labels(agent_name=agent_name, tier=tier, status=status).inc()

                # Decrement in-progress gauge
                agent_executions_in_progress.labels(agent_name=agent_name).dec()

        return wrapper

    return decorator


# =============================================================================
# METRICS ENDPOINT
# =============================================================================


def get_metrics() -> Response:
    """
    Get Prometheus metrics in text format.

    Returns metrics in Prometheus exposition format for scraping.
    """
    logger.debug("metrics_endpoint_accessed")

    metrics_data = generate_latest(registry)

    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


# =============================================================================
# METRIC RECORDING FUNCTIONS
# =============================================================================


def record_conversation_created():
    """Record conversation creation"""
    conversations_created_total.inc()
    conversations_total.labels(status="open").inc()


def record_conversation_resolved():
    """Record conversation resolution"""
    conversations_resolved_total.inc()
    conversations_total.labels(status="open").dec()
    conversations_total.labels(status="resolved").inc()


def record_customer_created(plan: str):
    """Record customer creation"""
    customers_created_total.labels(plan=plan).inc()
    customers_total.labels(plan=plan, status="active").inc()


def record_message_created(role: str):
    """Record message creation"""
    messages_total.labels(role=role).inc()


def record_auth_attempt(method: str, success: bool):
    """Record authentication attempt"""
    status = "success" if success else "failed"
    auth_attempts_total.labels(method=method, status=status).inc()


def record_rate_limit_hit(tier: str, endpoint: str):
    """Record rate limit hit"""
    rate_limit_hits_total.labels(tier=tier, endpoint=endpoint).inc()


def record_db_query(operation: str, table: str, duration: float):
    """Record database query"""
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def update_db_connections(active: int, idle: int):
    """Update database connection pool metrics"""
    db_connections_active.set(active)
    db_connections_idle.set(idle)


logger.info("prometheus_metrics_initialized", registry_collectors=len(registry._collector_to_names))
