"""
Overage Alert Agent - TASK-3013

Alerts customers approaching or exceeding plan limits to prevent surprise bills.
Provides proactive notifications with upgrade recommendations.
"""

from datetime import datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("overage_alert", tier="revenue", category="monetization")
class OverageAlert(BaseAgent):
    """
    Overage Alert Agent - Proactive usage limit notifications.

    Handles:
    - Monitor usage against plan limits
    - Send alerts at threshold milestones (80%, 90%, 100%, 110%)
    - Predict overage before period end
    - Recommend plan upgrades or add-ons
    - Calculate potential overage costs
    - Prevent surprise billing
    - Track alert acknowledgments
    - Escalate repeat overages
    """

    # Alert thresholds (percentage of limit)
    ALERT_THRESHOLDS = [
        {"level": "warning", "percentage": 80, "priority": "medium"},
        {"level": "urgent", "percentage": 90, "priority": "high"},
        {"level": "critical", "percentage": 100, "priority": "critical"},
        {"level": "overage", "percentage": 110, "priority": "critical"},
    ]

    # Recommended actions by usage level
    RECOMMENDED_ACTIONS = {
        "warning": ["Monitor usage closely", "Optimize usage patterns", "Consider upgrading plan"],
        "urgent": [
            "Upgrade plan immediately to avoid overages",
            "Purchase usage add-on",
            "Optimize usage to stay within limits",
        ],
        "critical": [
            "Immediate plan upgrade recommended",
            "Overage charges will apply",
            "Contact billing team for assistance",
        ],
        "overage": [
            "Upgrade plan to prevent future overages",
            "Review usage optimization opportunities",
            "Consider annual plan with higher limits",
        ],
    }

    # Usage optimization tips by metric
    OPTIMIZATION_TIPS = {
        "api_calls": [
            "Implement API call caching",
            "Use batch API endpoints",
            "Optimize polling frequency",
            "Review unnecessary API calls",
        ],
        "storage_gb": [
            "Archive old data",
            "Delete unnecessary files",
            "Compress large files",
            "Review storage usage policies",
        ],
        "seats_active": [
            "Remove inactive users",
            "Share accounts where appropriate",
            "Audit user list regularly",
            "Optimize team structure",
        ],
        "tickets_created": [
            "Consolidate related tickets",
            "Use self-service resources",
            "Batch similar requests",
            "Optimize ticket creation workflow",
        ],
    }

    def __init__(self):
        config = AgentConfig(
            name="overage_alert",
            type=AgentType.SPECIALIST,
            # Fast for real-time alerts
            temperature=0.3,
            max_tokens=400,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="monetization",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Check usage and send overage alerts if needed.

        Args:
            state: Current agent state with usage data

        Returns:
            Updated state with alert information
        """
        self.logger.info("overage_alert_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("current_usage", customer_metadata.get("usage_data", {}))

        # Check which metrics are approaching or exceeding limits
        alerts_needed = self._check_usage_thresholds(usage_data, customer_metadata)

        # Predict if overage likely before period end
        overage_predictions = self._predict_period_end_overages(usage_data, customer_metadata)

        # Calculate potential overage costs
        overage_costs = self._calculate_overage_costs(
            usage_data, customer_metadata, overage_predictions
        )

        # Generate upgrade recommendations
        upgrade_recommendations = self._generate_upgrade_recommendations(
            alerts_needed, overage_costs, customer_metadata
        )

        # Get optimization tips
        optimization_tips = self._get_optimization_tips(alerts_needed)

        # Determine alert priority
        alert_priority = self._determine_alert_priority(alerts_needed)

        # Check if customer has been alerted before
        alert_history = customer_metadata.get("alert_history", [])
        is_repeat_offender = len([a for a in alert_history if a.get("type") == "overage"]) >= 3

        # Search KB for usage optimization
        kb_results = await self.search_knowledge_base(
            "usage optimization plan limits", category="monetization", limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_alert_response(
            message,
            alerts_needed,
            overage_predictions,
            overage_costs,
            upgrade_recommendations,
            optimization_tips,
            alert_priority,
            is_repeat_offender,
            kb_results,
            customer_metadata,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.90
        state["alerts_needed"] = alerts_needed
        state["overage_predictions"] = overage_predictions
        state["overage_costs"] = overage_costs
        state["upgrade_recommendations"] = upgrade_recommendations
        state["optimization_tips"] = optimization_tips
        state["alert_priority"] = alert_priority
        state["status"] = "resolved"

        # Escalate if critical
        if alert_priority == "critical" or is_repeat_offender:
            state["should_escalate"] = True
            state["escalation_reason"] = (
                "Critical usage overage"
                if alert_priority == "critical"
                else "Repeat overage offender"
            )

        self.logger.info(
            "overage_alert_completed",
            alerts_count=len(alerts_needed),
            alert_priority=alert_priority,
            predicted_overages=len(overage_predictions),
        )

        return state

    def _check_usage_thresholds(
        self, usage_data: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Check which metrics have crossed alert thresholds"""
        alerts = []
        plan_limits = customer_metadata.get("plan_limits", {})

        for metric, usage_value in usage_data.items():
            limit_key = f"{metric}_limit"
            limit = plan_limits.get(limit_key)

            if not limit or limit == float("inf"):
                continue

            usage_percentage = (usage_value / limit) * 100 if limit > 0 else 0

            # Check against thresholds in reverse order to match highest threshold first
            for threshold in reversed(self.ALERT_THRESHOLDS):
                if usage_percentage >= threshold["percentage"]:
                    alerts.append(
                        {
                            "metric": metric,
                            "current_usage": usage_value,
                            "limit": limit,
                            "usage_percentage": round(usage_percentage, 2),
                            "threshold_level": threshold["level"],
                            "priority": threshold["priority"],
                            "remaining": max(0, limit - usage_value),
                            "overage_amount": max(0, usage_value - limit),
                        }
                    )
                    break  # Only trigger highest threshold crossed

        return sorted(alerts, key=lambda x: x["usage_percentage"], reverse=True)

    def _predict_period_end_overages(
        self, usage_data: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Predict which metrics will exceed limits by period end"""
        predictions = []
        plan_limits = customer_metadata.get("plan_limits", {})

        # Get billing period info
        period_start = datetime.fromisoformat(
            customer_metadata.get("current_period_start", datetime.now().isoformat())
        )
        period_end = datetime.fromisoformat(
            customer_metadata.get(
                "current_period_end", (datetime.now() + timedelta(days=30)).isoformat()
            )
        )
        (period_end - period_start).days
        days_elapsed = (datetime.now() - period_start).days
        days_remaining = max(0, (period_end - datetime.now()).days)

        if days_elapsed == 0 or days_remaining == 0:
            return predictions

        for metric, usage_value in usage_data.items():
            limit_key = f"{metric}_limit"
            limit = plan_limits.get(limit_key)

            if not limit or limit == float("inf"):
                continue

            # Project usage to period end based on current rate
            daily_rate = usage_value / days_elapsed if days_elapsed > 0 else 0
            projected_usage = usage_value + (daily_rate * days_remaining)
            projected_percentage = (projected_usage / limit) * 100 if limit > 0 else 0

            if projected_usage > limit:
                predictions.append(
                    {
                        "metric": metric,
                        "current_usage": usage_value,
                        "projected_usage": round(projected_usage, 2),
                        "limit": limit,
                        "projected_overage": round(projected_usage - limit, 2),
                        "projected_percentage": round(projected_percentage, 2),
                        "days_remaining": days_remaining,
                        "confidence": "high" if days_remaining <= 7 else "medium",
                    }
                )

        return predictions

    def _calculate_overage_costs(
        self, usage_data: dict, customer_metadata: dict, predictions: list[dict]
    ) -> dict[str, Any]:
        """Calculate estimated overage costs"""
        costs = {"current_overage_cost": 0.0, "projected_overage_cost": 0.0, "by_metric": {}}

        overage_pricing = customer_metadata.get("overage_pricing", {})

        # Current overages
        for metric, usage_value in usage_data.items():
            limit = customer_metadata.get("plan_limits", {}).get(f"{metric}_limit")
            if limit and usage_value > limit:
                overage_amount = usage_value - limit
                rate = overage_pricing.get(metric, {}).get("rate", 0)
                cost = overage_amount * rate
                costs["current_overage_cost"] += cost
                costs["by_metric"][metric] = {"current_cost": round(cost, 2)}

        # Projected overages
        for prediction in predictions:
            metric = prediction["metric"]
            projected_overage = prediction["projected_overage"]
            rate = overage_pricing.get(metric, {}).get("rate", 0)
            projected_cost = projected_overage * rate
            costs["projected_overage_cost"] += projected_cost

            if metric not in costs["by_metric"]:
                costs["by_metric"][metric] = {}
            costs["by_metric"][metric]["projected_cost"] = round(projected_cost, 2)

        costs["current_overage_cost"] = round(costs["current_overage_cost"], 2)
        costs["projected_overage_cost"] = round(costs["projected_overage_cost"], 2)

        return costs

    def _generate_upgrade_recommendations(
        self, alerts: list[dict], overage_costs: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Generate plan upgrade recommendations"""
        recommendations = []

        if not alerts:
            return recommendations

        current_plan = customer_metadata.get("plan_name", "Unknown")
        current_plan_cost = customer_metadata.get("base_plan_cost", 0)

        # Recommend upgrade if projected overage cost > 50% of upgrade cost
        if overage_costs["projected_overage_cost"] > current_plan_cost * 0.5:
            recommendations.append(
                {
                    "type": "plan_upgrade",
                    "reason": "Overage costs exceed upgrade economics",
                    "current_plan": current_plan,
                    "recommended_plan": "Next tier up",
                    "potential_savings": round(
                        overage_costs["projected_overage_cost"] - (current_plan_cost * 0.5), 2
                    ),
                    "priority": "high",
                }
            )

        # Recommend usage add-ons for specific metrics
        for alert in alerts:
            if alert["threshold_level"] in ["urgent", "critical", "overage"]:
                recommendations.append(
                    {
                        "type": "usage_add_on",
                        "metric": alert["metric"],
                        "reason": f"Approaching/exceeding {alert['metric']} limit",
                        "priority": alert["priority"],
                    }
                )

        return recommendations

    def _get_optimization_tips(self, alerts: list[dict]) -> list[str]:
        """Get usage optimization tips for alerting metrics"""
        tips = []
        seen_metrics = set()

        for alert in alerts[:3]:  # Top 3 alerts
            metric = alert["metric"]
            if metric in self.OPTIMIZATION_TIPS and metric not in seen_metrics:
                tips.extend(self.OPTIMIZATION_TIPS[metric][:2])  # Top 2 tips per metric
                seen_metrics.add(metric)

        return tips

    def _determine_alert_priority(self, alerts: list[dict]) -> str:
        """Determine overall alert priority"""
        if not alerts:
            return "none"

        priorities = [a["priority"] for a in alerts]

        if "critical" in priorities:
            return "critical"
        elif "high" in priorities:
            return "high"
        elif "medium" in priorities:
            return "medium"
        else:
            return "low"

    async def _generate_alert_response(
        self,
        message: str,
        alerts: list[dict],
        predictions: list[dict],
        overage_costs: dict,
        recommendations: list[dict],
        optimization_tips: list[str],
        alert_priority: str,
        is_repeat_offender: bool,
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate overage alert response"""

        # Build alert context
        alert_context = ""
        if alerts:
            alert_context = "\n\nUsage Alerts:\n"
            for alert in alerts[:3]:  # Top 3
                alert_context += f"- {alert['metric']}: {alert['usage_percentage']:.1f}% of limit ({alert['threshold_level']})\n"

        # Build prediction context
        prediction_context = ""
        if predictions:
            prediction_context = "\n\nProjected Overages by Period End:\n"
            for pred in predictions[:2]:  # Top 2
                prediction_context += f"- {pred['metric']}: Projected {pred['projected_percentage']:.1f}% (overage: {pred['projected_overage']})\n"

        # Build cost context
        cost_context = ""
        if overage_costs["current_overage_cost"] > 0 or overage_costs["projected_overage_cost"] > 0:
            cost_context = f"""
Overage Costs:
- Current overage charges: ${overage_costs["current_overage_cost"]:.2f}
- Projected period-end charges: ${overage_costs["projected_overage_cost"]:.2f}
"""

        # Build recommendation context
        recommendation_context = ""
        if recommendations:
            recommendation_context = "\n\nRecommended Actions:\n"
            for rec in recommendations[:2]:  # Top 2
                recommendation_context += f"- {rec['type']}: {rec['reason']}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nUsage Optimization Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are an Overage Alert specialist helping customers avoid surprise bills.

Customer: {customer_metadata.get("company", "Customer")}
Plan: {customer_metadata.get("plan_name", "Unknown")}
Alert Priority: {alert_priority.upper()}
Repeat Offender: {"Yes" if is_repeat_offender else "No"}
{alert_context}
{prediction_context}
{cost_context}
{recommendation_context}

Your response should:
1. Alert customer about usage approaching/exceeding limits
2. Be clear and urgent but not alarmist
3. Provide specific numbers and percentages
4. Explain potential overage costs
5. Recommend specific actions (upgrade, optimize, add-ons)
6. Provide optimization tips to reduce usage
7. Make it easy to take action
8. Be helpful and solution-oriented"""

        user_prompt = f"""Customer message: {message}

Optimization Tips:
{chr(10).join(f"- {tip}" for tip in optimization_tips[:4])}

{kb_context}

Generate an urgent but helpful overage alert."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Overage alerts are standalone notifications
        )
        return response
