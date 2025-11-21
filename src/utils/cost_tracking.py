"""
Cost Tracking Module

Tracks and calculates costs for different LLM backends:
- Anthropic API (per-token pricing)
- vLLM (per-hour GPU pricing)

Provides real-time cost monitoring and budget enforcement.

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

from typing import Dict, Optional
from datetime import datetime
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)


@dataclass
class CostEntry:
    """Single cost entry for tracking"""
    backend: str
    cost: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Optional[Dict] = None


class CostCalculator:
    """
    Calculate costs for different LLM backends.

    Pricing as of November 2024:
    - Anthropic Claude 3 Haiku: $0.25 / $1.25 per 1M tokens (input/output)
    - Anthropic Claude 3.5 Sonnet: $3.00 / $15.00 per 1M tokens
    - Anthropic Claude 3 Opus: $15.00 / $75.00 per 1M tokens
    - vLLM (Vast.ai RTX 3090): ~$0.15/hour average
    """

    # Pricing per 1M tokens (input, output)
    ANTHROPIC_PRICING = {
        "claude-3-haiku-20240307": (0.25, 1.25),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-3-opus-20240229": (15.00, 75.00),
    }

    # vLLM pricing per hour (Vast.ai average)
    VLLM_HOURLY_RATE = 0.16  # RTX 3090 average

    @staticmethod
    def calculate_anthropic_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Calculate cost for Anthropic API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Examples:
            >>> calc = CostCalculator()
            >>> cost = calc.calculate_anthropic_cost(
            ...     "claude-3-haiku-20240307",
            ...     1000,
            ...     500
            ... )
            >>> print(f"${cost:.6f}")
            $0.000875
        """
        # Get pricing for model, fallback to Haiku if unknown
        input_price, output_price = CostCalculator.ANTHROPIC_PRICING.get(
            model,
            CostCalculator.ANTHROPIC_PRICING["claude-3-haiku-20240307"]
        )

        # Calculate cost
        cost = (
            (input_tokens / 1_000_000) * input_price +
            (output_tokens / 1_000_000) * output_price
        )

        return round(cost, 6)

    @staticmethod
    def calculate_vllm_cost(runtime_seconds: int) -> float:
        """
        Calculate cost for vLLM session.

        Args:
            runtime_seconds: Runtime in seconds

        Returns:
            Cost in USD

        Examples:
            >>> calc = CostCalculator()
            >>> # 1 hour runtime
            >>> cost = calc.calculate_vllm_cost(3600)
            >>> print(f"${cost:.6f}")
            $0.160000
        """
        hourly_rate = CostCalculator.VLLM_HOURLY_RATE
        cost = (runtime_seconds / 3600) * hourly_rate
        return round(cost, 6)

    @staticmethod
    def estimate_vllm_hourly_cost() -> float:
        """Get estimated vLLM hourly cost"""
        return CostCalculator.VLLM_HOURLY_RATE


class CostTracker:
    """
    Track cumulative costs across all LLM backends.

    Features:
    - Real-time cost tracking
    - Budget alerts
    - Cost breakdown by backend
    - Historical cost entries
    """

    def __init__(self, budget_limit: float = 15.0):
        """
        Initialize cost tracker.

        Args:
            budget_limit: Maximum budget in USD (default: $15)
        """
        self.costs: Dict[str, float] = {
            "anthropic": 0.0,
            "vllm": 0.0,
        }
        self.budget_limit = budget_limit
        self.cost_history: list[CostEntry] = []
        self.max_history = 10000

        logger.info(
            "cost_tracker_initialized",
            budget_limit=budget_limit,
        )

    def add_anthropic_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Track cost of Anthropic API call.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost of this call
        """
        cost = CostCalculator.calculate_anthropic_cost(
            model, input_tokens, output_tokens
        )

        self.costs["anthropic"] += cost

        # Add to history
        entry = CostEntry(
            backend="anthropic",
            cost=cost,
            details={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        self._add_to_history(entry)

        logger.info(
            "anthropic_cost_tracked",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            total_anthropic=self.costs["anthropic"],
            total_overall=self.get_total_cost(),
        )

        # Check budget
        self._check_budget()

        return cost

    def add_vllm_session(self, runtime_seconds: int) -> float:
        """
        Track cost of vLLM session.

        Args:
            runtime_seconds: Runtime in seconds

        Returns:
            Cost of this session
        """
        cost = CostCalculator.calculate_vllm_cost(runtime_seconds)

        self.costs["vllm"] += cost

        # Add to history
        entry = CostEntry(
            backend="vllm",
            cost=cost,
            details={
                "runtime_seconds": runtime_seconds,
                "runtime_hours": round(runtime_seconds / 3600, 2),
            }
        )
        self._add_to_history(entry)

        logger.info(
            "vllm_cost_tracked",
            runtime_seconds=runtime_seconds,
            runtime_hours=round(runtime_seconds / 3600, 2),
            cost=cost,
            total_vllm=self.costs["vllm"],
            total_overall=self.get_total_cost(),
        )

        # Check budget
        self._check_budget()

        return cost

    def get_total_cost(self) -> float:
        """Get total cost across all backends"""
        return sum(self.costs.values())

    def get_breakdown(self) -> Dict[str, float]:
        """
        Get cost breakdown by backend.

        Returns:
            Dictionary with costs per backend and total
        """
        total = self.get_total_cost()
        remaining = max(0, self.budget_limit - total)

        return {
            "anthropic": round(self.costs["anthropic"], 6),
            "vllm": round(self.costs["vllm"], 6),
            "total": round(total, 6),
            "budget_limit": self.budget_limit,
            "remaining": round(remaining, 6),
            "budget_used_percent": round((total / self.budget_limit) * 100, 2),
        }

    def get_budget_status(self) -> Dict[str, any]:
        """
        Get budget status with alerts.

        Returns:
            Dictionary with budget status and alert level
        """
        total = self.get_total_cost()
        percent_used = (total / self.budget_limit) * 100
        remaining = self.budget_limit - total

        # Determine alert level
        if percent_used >= 100:
            alert_level = "critical"
            message = "Budget exceeded!"
        elif percent_used >= 90:
            alert_level = "warning"
            message = "Budget at 90%+"
        elif percent_used >= 75:
            alert_level = "caution"
            message = "Budget at 75%+"
        else:
            alert_level = "ok"
            message = "Budget healthy"

        return {
            "alert_level": alert_level,
            "message": message,
            "total_spent": round(total, 6),
            "budget_limit": self.budget_limit,
            "remaining": round(remaining, 6),
            "percent_used": round(percent_used, 2),
        }

    def _check_budget(self) -> None:
        """Check budget and log warnings if approaching limit"""
        status = self.get_budget_status()

        if status["alert_level"] in ["warning", "critical"]:
            logger.warning(
                "budget_alert",
                alert_level=status["alert_level"],
                message=status["message"],
                total_spent=status["total_spent"],
                budget_limit=status["budget_limit"],
                percent_used=status["percent_used"],
            )

    def is_budget_exceeded(self) -> bool:
        """Check if budget limit has been exceeded"""
        return self.get_total_cost() >= self.budget_limit

    def get_remaining_budget(self) -> float:
        """Get remaining budget"""
        return max(0, self.budget_limit - self.get_total_cost())

    def _add_to_history(self, entry: CostEntry) -> None:
        """Add entry to history with size limit"""
        self.cost_history.append(entry)
        if len(self.cost_history) > self.max_history:
            self.cost_history.pop(0)

    def get_recent_costs(self, limit: int = 10) -> list[Dict]:
        """
        Get recent cost entries.

        Args:
            limit: Number of entries to return

        Returns:
            List of recent cost dictionaries
        """
        recent = self.cost_history[-limit:]
        return [
            {
                "backend": entry.backend,
                "cost": entry.cost,
                "timestamp": entry.timestamp.isoformat(),
                "details": entry.details,
            }
            for entry in recent
        ]

    def reset(self) -> None:
        """Reset all costs (for testing or new billing period)"""
        old_total = self.get_total_cost()

        self.costs = {
            "anthropic": 0.0,
            "vllm": 0.0,
        }
        self.cost_history.clear()

        logger.info(
            "cost_tracker_reset",
            previous_total=old_total,
        )

    def set_budget_limit(self, new_limit: float) -> None:
        """
        Update budget limit.

        Args:
            new_limit: New budget limit in USD
        """
        old_limit = self.budget_limit
        self.budget_limit = new_limit

        logger.info(
            "budget_limit_updated",
            old_limit=old_limit,
            new_limit=new_limit,
        )


# Global cost tracker instance
cost_tracker = CostTracker(budget_limit=15.0)
