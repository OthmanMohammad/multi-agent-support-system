"""
Usage Tracker Agent - TASK-3011

Tracks customer usage across all billable metrics for accurate usage-based billing.
Monitors API calls, storage, seats, and custom metrics in real-time.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("usage_tracker", tier="revenue", category="monetization")
class UsageTracker(BaseAgent):
    """
    Usage Tracker Agent - Monitors and tracks all billable usage metrics.

    Handles:
    - Real-time usage tracking across all billable dimensions
    - API call monitoring and aggregation
    - Storage usage calculation and tracking
    - Active seat counting and monitoring
    - Custom metric tracking (automations, integrations, etc.)
    - Usage anomaly detection
    - Usage forecasting for billing predictions
    - Historical usage reporting
    """

    # Billable metrics configuration
    BILLABLE_METRICS = {
        "api_calls": {
            "unit": "calls",
            "aggregation": "sum",
            "overage_threshold": 0.80  # Alert at 80% of limit
        },
        "storage_gb": {
            "unit": "GB",
            "aggregation": "max",  # Use peak storage
            "overage_threshold": 0.80
        },
        "seats_active": {
            "unit": "seats",
            "aggregation": "max",  # Use peak concurrent seats
            "overage_threshold": 0.90
        },
        "tickets_created": {
            "unit": "tickets",
            "aggregation": "sum",
            "overage_threshold": 0.80
        },
        "automations_run": {
            "unit": "automations",
            "aggregation": "sum",
            "overage_threshold": 0.80
        },
        "integrations_active": {
            "unit": "integrations",
            "aggregation": "count",
            "overage_threshold": 0.90
        }
    }

    # Usage anomaly thresholds
    ANOMALY_THRESHOLDS = {
        "spike": 3.0,  # 3x normal usage = spike
        "drop": 0.3,   # 30% of normal usage = drop
        "unusual_pattern": 2.0  # 2x standard deviation
    }

    # Forecasting windows
    FORECAST_WINDOWS = {
        "daily": 7,    # 7 days of data for daily forecast
        "weekly": 4,   # 4 weeks for weekly forecast
        "monthly": 3   # 3 months for monthly forecast
    }

    def __init__(self):
        config = AgentConfig(
            name="usage_tracker",
            type=AgentType.SPECIALIST,
             # Fast for real-time tracking
            temperature=0.2,  # Low for accurate metrics
            max_tokens=500,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="monetization",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Track and analyze customer usage metrics.

        Args:
            state: Current agent state with customer metadata

        Returns:
            Updated state with usage tracking results
        """
        self.logger.info("usage_tracker_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        customer_id = state.get("customer_id")

        # Extract current usage data
        current_usage = self._extract_current_usage(customer_metadata)

        # Calculate usage against plan limits
        usage_analysis = self._analyze_usage_vs_limits(
            current_usage,
            customer_metadata
        )

        # Detect usage anomalies
        anomalies = self._detect_usage_anomalies(
            current_usage,
            customer_metadata.get("historical_usage", [])
        )

        # Forecast future usage
        usage_forecast = self._forecast_usage(
            customer_metadata.get("historical_usage", []),
            current_usage
        )

        # Calculate billable amounts
        billable_usage = self._calculate_billable_usage(
            current_usage,
            customer_metadata
        )

        # Generate usage summary
        usage_summary = self._generate_usage_summary(
            current_usage,
            usage_analysis,
            anomalies,
            usage_forecast
        )

        # Search KB for usage best practices
        kb_results = await self.search_knowledge_base(
            "usage optimization billing metrics",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_usage_response(
            message,
            usage_summary,
            usage_analysis,
            anomalies,
            usage_forecast,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.92
        state["current_usage"] = current_usage
        state["usage_analysis"] = usage_analysis
        state["usage_anomalies"] = anomalies
        state["usage_forecast"] = usage_forecast
        state["billable_usage"] = billable_usage
        state["usage_summary"] = usage_summary
        state["status"] = "resolved"

        self.logger.info(
            "usage_tracker_completed",
            total_metrics=len(current_usage),
            anomalies_detected=len(anomalies),
            overage_risk=usage_analysis.get("overage_risk", "none")
        )

        return state

    def _extract_current_usage(self, customer_metadata: Dict) -> Dict[str, float]:
        """Extract current usage metrics from customer metadata"""
        usage = {}

        # Check if usage data is nested in usage_data key
        usage_data = customer_metadata.get("usage_data", customer_metadata)

        for metric in self.BILLABLE_METRICS.keys():
            # Get from usage_data or metadata or default to 0
            usage[metric] = usage_data.get(metric, 0)

        return usage

    def _analyze_usage_vs_limits(
        self,
        current_usage: Dict[str, float],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Analyze current usage against plan limits"""
        plan_limits = customer_metadata.get("plan_limits", {})
        analysis = {
            "metrics": {},
            "approaching_limit": [],
            "at_limit": [],
            "overage": [],
            "overage_risk": "none"
        }

        for metric, value in current_usage.items():
            limit = plan_limits.get(f"{metric}_limit", float('inf'))

            if limit == float('inf'):
                continue

            usage_percentage = (value / limit) * 100 if limit > 0 else 0
            threshold = self.BILLABLE_METRICS[metric]["overage_threshold"] * 100

            metric_analysis = {
                "current": value,
                "limit": limit,
                "usage_percentage": round(usage_percentage, 2),
                "remaining": max(0, limit - value),
                "status": "normal"
            }

            # Categorize usage
            if usage_percentage >= 100:
                metric_analysis["status"] = "overage"
                analysis["overage"].append(metric)
                analysis["overage_risk"] = "high"
            elif usage_percentage >= threshold:
                metric_analysis["status"] = "approaching_limit"
                analysis["approaching_limit"].append(metric)
                if analysis["overage_risk"] == "none":
                    analysis["overage_risk"] = "medium"
            elif usage_percentage >= 50:
                metric_analysis["status"] = "moderate"
            else:
                metric_analysis["status"] = "normal"

            analysis["metrics"][metric] = metric_analysis

        return analysis

    def _detect_usage_anomalies(
        self,
        current_usage: Dict[str, float],
        historical_usage: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Detect unusual usage patterns"""
        anomalies = []

        if not historical_usage or len(historical_usage) < 3:
            return anomalies

        for metric, current_value in current_usage.items():
            # Calculate historical average
            historical_values = [
                h.get(metric, 0) for h in historical_usage
            ]
            avg_usage = sum(historical_values) / len(historical_values)

            if avg_usage == 0:
                continue

            # Detect spikes
            spike_ratio = current_value / avg_usage
            if spike_ratio >= self.ANOMALY_THRESHOLDS["spike"]:
                anomalies.append({
                    "metric": metric,
                    "type": "spike",
                    "current": current_value,
                    "average": avg_usage,
                    "ratio": round(spike_ratio, 2),
                    "severity": "high" if spike_ratio >= 5.0 else "medium"
                })

            # Detect drops
            elif spike_ratio <= self.ANOMALY_THRESHOLDS["drop"]:
                anomalies.append({
                    "metric": metric,
                    "type": "drop",
                    "current": current_value,
                    "average": avg_usage,
                    "ratio": round(spike_ratio, 2),
                    "severity": "medium"
                })

        return anomalies

    def _forecast_usage(
        self,
        historical_usage: List[Dict],
        current_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """Forecast usage for next billing period"""
        forecast = {
            "next_period_estimate": {},
            "confidence": "medium",
            "method": "simple_average"
        }

        if not historical_usage or len(historical_usage) < 2:
            # Use current usage as baseline
            forecast["next_period_estimate"] = current_usage.copy()
            forecast["confidence"] = "low"
            return forecast

        # Simple moving average forecast
        for metric in current_usage.keys():
            historical_values = [h.get(metric, 0) for h in historical_usage[-4:]]  # Last 4 periods
            avg = sum(historical_values) / len(historical_values)

            # Weight current usage more heavily (70% current, 30% average)
            forecast["next_period_estimate"][metric] = round(
                current_usage[metric] * 0.7 + avg * 0.3,
                2
            )

        forecast["confidence"] = "high" if len(historical_usage) >= 6 else "medium"

        return forecast

    def _calculate_billable_usage(
        self,
        current_usage: Dict[str, float],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate billable usage amounts"""
        plan_limits = customer_metadata.get("plan_limits", {})
        overage_pricing = customer_metadata.get("overage_pricing", {})

        billable = {
            "base_plan_cost": customer_metadata.get("base_plan_cost", 0),
            "overage_charges": {},
            "total_overage": 0,
            "estimated_bill": 0
        }

        for metric, value in current_usage.items():
            limit = plan_limits.get(f"{metric}_limit", float('inf'))

            if value > limit and limit != float('inf'):
                overage_amount = value - limit
                # Get overage rate (default to $0 if not defined)
                overage_rate = overage_pricing.get(metric, {}).get("rate", 0)
                overage_cost = overage_amount * overage_rate

                billable["overage_charges"][metric] = {
                    "overage_amount": overage_amount,
                    "rate": overage_rate,
                    "cost": round(overage_cost, 2)
                }
                billable["total_overage"] += overage_cost

        billable["estimated_bill"] = billable["base_plan_cost"] + billable["total_overage"]

        return billable

    def _generate_usage_summary(
        self,
        current_usage: Dict[str, float],
        usage_analysis: Dict,
        anomalies: List[Dict],
        forecast: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive usage summary"""
        return {
            "total_metrics_tracked": len(current_usage),
            "metrics_approaching_limit": len(usage_analysis["approaching_limit"]),
            "metrics_at_limit": len(usage_analysis["at_limit"]),
            "metrics_in_overage": len(usage_analysis["overage"]),
            "anomalies_detected": len(anomalies),
            "overage_risk": usage_analysis["overage_risk"],
            "forecast_confidence": forecast["confidence"]
        }

    async def _generate_usage_response(
        self,
        message: str,
        usage_summary: Dict,
        usage_analysis: Dict,
        anomalies: List[Dict],
        forecast: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate usage tracking response"""

        # Build usage context
        usage_context = f"""
Usage Summary:
- Total metrics tracked: {usage_summary['total_metrics_tracked']}
- Metrics approaching limit: {usage_summary['metrics_approaching_limit']}
- Metrics in overage: {usage_summary['metrics_in_overage']}
- Overage risk: {usage_summary['overage_risk']}
- Anomalies detected: {usage_summary['anomalies_detected']}
"""

        # Build anomaly context
        anomaly_context = ""
        if anomalies:
            anomaly_context = "\n\nUsage Anomalies Detected:\n"
            for anomaly in anomalies[:3]:  # Top 3
                anomaly_context += f"- {anomaly['metric']}: {anomaly['type']} ({anomaly['ratio']}x normal)\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nUsage Optimization Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Usage Tracker specialist monitoring customer usage metrics.

Customer Plan: {customer_metadata.get('plan_name', 'Unknown')}
{usage_context}

Your response should:
1. Acknowledge the usage inquiry
2. Provide current usage status across key metrics
3. Highlight any metrics approaching limits
4. Alert about any anomalies or unusual patterns
5. Provide forecast for next billing period
6. Recommend actions if needed (optimize usage, upgrade plan, etc.)
7. Be data-driven and actionable
8. Help customer understand their usage patterns"""

        user_prompt = f"""Customer message: {message}

{anomaly_context}

Next Period Forecast Confidence: {forecast['confidence']}

{kb_context}

Generate a helpful usage tracking response."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Usage tracking uses metrics context
        )
        return response
