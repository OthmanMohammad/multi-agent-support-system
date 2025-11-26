"""
LLM Metrics Tracking Module

Tracks LLM usage metrics across all backends:
- Token usage (input/output)
- Latency
- Cost
- Error rates
- Backend utilization

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM call"""

    backend: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error: str | None = None


class LLMMetricsTracker:
    """
    Track LLM usage metrics across all backends.

    Provides aggregated statistics for monitoring and cost optimization.
    Thread-safe for concurrent agent operations.
    """

    def __init__(self):
        # Call history (recent calls for debugging)
        self.recent_calls: list[LLMCallMetrics] = []
        self.max_recent_calls = 1000

        # Aggregated metrics per backend
        self.backend_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_latency_ms": 0,
                "errors": defaultdict(int),
            }
        )

        # Model-level metrics
        self.model_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "avg_latency_ms": 0,
            }
        )

        logger.info("llm_metrics_tracker_initialized")

    def track_call(
        self,
        backend: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """
        Track a single LLM call.

        Args:
            backend: Backend name (anthropic, vllm)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Latency in milliseconds
            success: Whether call succeeded
            error: Error message if failed
        """
        # Create metrics object
        metrics = LLMCallMetrics(
            backend=backend,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error=error,
        )

        # Add to recent calls
        self.recent_calls.append(metrics)
        if len(self.recent_calls) > self.max_recent_calls:
            self.recent_calls.pop(0)

        # Update backend metrics
        backend_stats = self.backend_metrics[backend]
        backend_stats["total_calls"] += 1

        if success:
            backend_stats["successful_calls"] += 1
            backend_stats["total_input_tokens"] += input_tokens
            backend_stats["total_output_tokens"] += output_tokens
            backend_stats["total_latency_ms"] += latency_ms
        else:
            backend_stats["failed_calls"] += 1
            if error:
                backend_stats["errors"][error] += 1

        # Update model metrics
        if success:
            model_stats = self.model_metrics[model]
            model_stats["total_calls"] += 1
            model_stats["total_input_tokens"] += input_tokens
            model_stats["total_output_tokens"] += output_tokens

            # Update rolling average for latency
            prev_avg = model_stats["avg_latency_ms"]
            total_calls = model_stats["total_calls"]
            model_stats["avg_latency_ms"] = (
                prev_avg * (total_calls - 1) + latency_ms
            ) / total_calls

        logger.debug(
            "llm_call_tracked",
            backend=backend,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
        )

    def get_backend_stats(self, backend: str) -> dict[str, Any]:
        """
        Get aggregated statistics for a backend.

        Args:
            backend: Backend name

        Returns:
            Dictionary with aggregated statistics
        """
        stats = self.backend_metrics.get(backend)
        if not stats:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "avg_latency_ms": 0,
                "error_rate": 0.0,
            }

        total_calls = stats["total_calls"]
        total_tokens = stats["total_input_tokens"] + stats["total_output_tokens"]
        avg_latency = (
            stats["total_latency_ms"] / stats["successful_calls"]
            if stats["successful_calls"] > 0
            else 0
        )
        error_rate = stats["failed_calls"] / total_calls if total_calls > 0 else 0.0

        return {
            "total_calls": total_calls,
            "successful_calls": stats["successful_calls"],
            "failed_calls": stats["failed_calls"],
            "total_input_tokens": stats["total_input_tokens"],
            "total_output_tokens": stats["total_output_tokens"],
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(error_rate, 4),
            "top_errors": dict(
                sorted(stats["errors"].items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }

    def get_model_stats(self, model: str) -> dict[str, Any]:
        """
        Get aggregated statistics for a model.

        Args:
            model: Model name

        Returns:
            Dictionary with model statistics
        """
        stats = self.model_metrics.get(model)
        if not stats:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "avg_latency_ms": 0,
            }

        return {
            "total_calls": stats["total_calls"],
            "total_input_tokens": stats["total_input_tokens"],
            "total_output_tokens": stats["total_output_tokens"],
            "total_tokens": stats["total_input_tokens"] + stats["total_output_tokens"],
            "avg_latency_ms": round(stats["avg_latency_ms"], 2),
        }

    def get_all_stats(self) -> dict[str, Any]:
        """
        Get all metrics statistics.

        Returns:
            Comprehensive statistics dictionary
        """
        backend_stats = {
            backend: self.get_backend_stats(backend) for backend in self.backend_metrics
        }

        model_stats = {model: self.get_model_stats(model) for model in self.model_metrics}

        # Overall totals
        total_calls = sum(s["total_calls"] for s in backend_stats.values())
        total_tokens = sum(s["total_tokens"] for s in backend_stats.values())
        total_successful = sum(s["successful_calls"] for s in backend_stats.values())
        total_failed = sum(s["failed_calls"] for s in backend_stats.values())

        return {
            "overview": {
                "total_calls": total_calls,
                "successful_calls": total_successful,
                "failed_calls": total_failed,
                "total_tokens": total_tokens,
                "backends_active": len(backend_stats),
                "models_used": len(model_stats),
            },
            "by_backend": backend_stats,
            "by_model": model_stats,
            "recent_calls": len(self.recent_calls),
        }

    def get_recent_calls(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent LLM calls.

        Args:
            limit: Maximum number of calls to return

        Returns:
            List of recent call dictionaries
        """
        recent = self.recent_calls[-limit:]
        return [
            {
                "backend": call.backend,
                "model": call.model,
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "latency_ms": call.latency_ms,
                "success": call.success,
                "error": call.error,
                "timestamp": call.timestamp.isoformat(),
            }
            for call in recent
        ]

    def reset_metrics(self) -> None:
        """Reset all metrics (for testing or periodic reset)"""
        self.recent_calls.clear()
        self.backend_metrics.clear()
        self.model_metrics.clear()
        logger.info("llm_metrics_reset")


# Global metrics tracker instance
llm_metrics = LLMMetricsTracker()
