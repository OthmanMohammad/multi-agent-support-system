"""
Monitoring and metrics for context enrichment.

Provides Prometheus metrics and performance tracking for the context enrichment system.
"""

import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


try:
    from prometheus_client import Counter, Gauge, Histogram, Summary

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client_not_available_metrics_disabled")


@dataclass
class ContextMetrics:
    """
    Context enrichment metrics tracker.

    Tracks performance and usage metrics for monitoring and alerting.
    """

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Latency metrics
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0

    # Provider metrics
    provider_calls: dict[str, int] = field(default_factory=dict)
    provider_failures: dict[str, int] = field(default_factory=dict)
    provider_timeouts: dict[str, int] = field(default_factory=dict)

    # Cache metrics
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0

    def record_request(self, success: bool, latency_ms: float, from_cache: bool = False):
        """Record enrichment request"""
        self.total_requests += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.total_latency_ms += latency_ms
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)

    def record_provider_call(self, provider_name: str, success: bool, timeout: bool = False):
        """Record provider call"""
        if provider_name not in self.provider_calls:
            self.provider_calls[provider_name] = 0
            self.provider_failures[provider_name] = 0
            self.provider_timeouts[provider_name] = 0

        self.provider_calls[provider_name] += 1

        if timeout:
            self.provider_timeouts[provider_name] += 1
        elif not success:
            self.provider_failures[provider_name] += 1

    def record_cache_access(self, tier: str, hit: bool):
        """Record cache access"""
        if tier == "l1":
            if hit:
                self.l1_hits += 1
            else:
                self.l1_misses += 1
        elif tier == "l2":
            if hit:
                self.l2_hits += 1
            else:
                self.l2_misses += 1

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency"""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_cache_accesses = self.cache_hits + self.cache_misses
        if total_cache_accesses == 0:
            return 0.0
        return self.cache_hits / total_cache_accesses

    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate"""
        total = self.l1_hits + self.l1_misses
        if total == 0:
            return 0.0
        return self.l1_hits / total

    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 cache hit rate"""
        total = self.l2_hits + self.l2_misses
        if total == 0:
            return 0.0
        return self.l2_hits / total

    def get_summary(self) -> dict[str, any]:
        """Get metrics summary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": self.min_latency_ms if self.min_latency_ms != float("inf") else 0.0,
            "max_latency_ms": self.max_latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "l1_hit_rate": self.l1_hit_rate,
            "l2_hit_rate": self.l2_hit_rate,
            "provider_calls": self.provider_calls,
            "provider_failures": self.provider_failures,
            "provider_timeouts": self.provider_timeouts,
        }


# Prometheus metrics (initialized if prometheus_client available)
if PROMETHEUS_AVAILABLE:
    # Request metrics
    context_enrichment_requests_total = Counter(
        "context_enrichment_requests_total",
        "Total context enrichment requests",
        ["agent_type", "status"],
    )

    context_enrichment_duration_seconds = Histogram(
        "context_enrichment_duration_seconds",
        "Context enrichment duration in seconds",
        ["agent_type"],
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    )

    context_enrichment_duration_summary = Summary(
        "context_enrichment_duration_summary", "Context enrichment duration summary", ["agent_type"]
    )

    # Provider metrics
    context_provider_calls_total = Counter(
        "context_provider_calls_total", "Total provider calls", ["provider_name", "status"]
    )

    context_provider_duration_seconds = Histogram(
        "context_provider_duration_seconds",
        "Provider execution duration in seconds",
        ["provider_name"],
        buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
    )

    # Cache metrics
    context_cache_hits_total = Counter("context_cache_hits_total", "Cache hits", ["cache_tier"])

    context_cache_misses_total = Counter(
        "context_cache_misses_total", "Cache misses", ["cache_tier"]
    )

    context_cache_size = Gauge("context_cache_size", "Current cache size", ["cache_tier"])

    # Error metrics
    context_enrichment_errors_total = Counter(
        "context_enrichment_errors_total",
        "Total enrichment errors",
        ["error_type", "provider_name"],
    )
else:
    # Stub metrics when Prometheus not available
    class _StubMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

    context_enrichment_requests_total = _StubMetric()
    context_enrichment_duration_seconds = _StubMetric()
    context_enrichment_duration_summary = _StubMetric()
    context_provider_calls_total = _StubMetric()
    context_provider_duration_seconds = _StubMetric()
    context_cache_hits_total = _StubMetric()
    context_cache_misses_total = _StubMetric()
    context_cache_size = _StubMetric()
    context_enrichment_errors_total = _StubMetric()


# Global metrics instance
_metrics_instance: ContextMetrics | None = None


def get_metrics() -> ContextMetrics:
    """
    Get or create metrics instance.

    Returns:
        ContextMetrics instance

    Example:
        >>> metrics = get_metrics()
        >>> print(metrics.get_summary())
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = ContextMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """
    Reset metrics (for testing).

    Example:
        >>> reset_metrics()
    """
    global _metrics_instance
    _metrics_instance = ContextMetrics()


# Convenience functions for recording metrics
def record_enrichment(
    agent_type: str, success: bool, latency_ms: float, from_cache: bool = False
) -> None:
    """
    Record enrichment request.

    Args:
        agent_type: Agent type
        success: Whether request succeeded
        latency_ms: Latency in milliseconds
        from_cache: Whether result came from cache

    Example:
        >>> record_enrichment("general", True, 45.2, False)
    """
    # Update internal metrics
    metrics = get_metrics()
    metrics.record_request(success, latency_ms, from_cache)

    # Update Prometheus metrics
    status = "success" if success else "failure"
    context_enrichment_requests_total.labels(agent_type=agent_type, status=status).inc()

    context_enrichment_duration_seconds.labels(agent_type=agent_type).observe(latency_ms / 1000.0)

    context_enrichment_duration_summary.labels(agent_type=agent_type).observe(latency_ms / 1000.0)

    logger.debug(
        "enrichment_recorded",
        agent_type=agent_type,
        success=success,
        latency_ms=latency_ms,
        from_cache=from_cache,
    )


def record_provider_execution(
    provider_name: str, success: bool, duration_ms: float, timeout: bool = False
) -> None:
    """
    Record provider execution.

    Args:
        provider_name: Provider name
        success: Whether execution succeeded
        duration_ms: Duration in milliseconds
        timeout: Whether execution timed out

    Example:
        >>> record_provider_execution("CustomerIntelligence", True, 23.5)
    """
    # Update internal metrics
    metrics = get_metrics()
    metrics.record_provider_call(provider_name, success, timeout)

    # Update Prometheus metrics
    if timeout:
        status = "timeout"
    elif success:
        status = "success"
    else:
        status = "failure"

    context_provider_calls_total.labels(provider_name=provider_name, status=status).inc()

    context_provider_duration_seconds.labels(provider_name=provider_name).observe(
        duration_ms / 1000.0
    )

    logger.debug(
        "provider_execution_recorded",
        provider=provider_name,
        success=success,
        duration_ms=duration_ms,
        timeout=timeout,
    )


def record_cache_hit(tier: str = "l1") -> None:
    """
    Record cache hit.

    Args:
        tier: Cache tier (l1 or l2)

    Example:
        >>> record_cache_hit("l1")
    """
    metrics = get_metrics()
    metrics.record_cache_access(tier, True)

    context_cache_hits_total.labels(cache_tier=tier).inc()

    logger.debug("cache_hit_recorded", tier=tier)


def record_cache_miss(tier: str = "l1") -> None:
    """
    Record cache miss.

    Args:
        tier: Cache tier (l1 or l2)

    Example:
        >>> record_cache_miss("l1")
    """
    metrics = get_metrics()
    metrics.record_cache_access(tier, False)

    context_cache_misses_total.labels(cache_tier=tier).inc()

    logger.debug("cache_miss_recorded", tier=tier)


def record_error(error_type: str, provider_name: str = "unknown") -> None:
    """
    Record enrichment error.

    Args:
        error_type: Type of error
        provider_name: Provider that errored

    Example:
        >>> record_error("timeout", "CustomerIntelligence")
    """
    context_enrichment_errors_total.labels(error_type=error_type, provider_name=provider_name).inc()

    logger.warning("error_recorded", error_type=error_type, provider=provider_name)


class MetricsTimer:
    """
    Context manager for timing operations.

    Example:
        >>> with MetricsTimer() as timer:
        ...     # Do work
        ...     pass
        >>> print(f"Duration: {timer.duration_ms}ms")
    """

    def __init__(self):
        """Initialize timer"""
        self.start_time: float | None = None
        self.end_time: float | None = None

    def __enter__(self):
        """Start timer"""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer"""
        self.end_time = time.perf_counter()
        return False

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time is not None else time.perf_counter()
        return (end - self.start_time) * 1000.0

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return self.duration_ms / 1000.0
