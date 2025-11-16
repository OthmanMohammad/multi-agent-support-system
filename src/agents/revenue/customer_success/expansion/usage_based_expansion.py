"""
Usage-Based Expansion Agent - TASK-2052

Monitors usage limits, predicts overages, and recommends tier upgrades
with ROI analysis to proactively manage usage-based expansion opportunities.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("usage_based_expansion", tier="revenue", category="customer_success")
class UsageBasedExpansionAgent(BaseAgent):
    """
    Usage-Based Expansion Agent.

    Manages usage-based expansion by:
    - Monitoring consumption against contracted limits
    - Predicting overage charges based on usage trends
    - Recommending proactive tier upgrades
    - Calculating ROI of expansion vs overage costs
    - Identifying optimal expansion timing
    - Generating usage forecasts
    """

    # Usage thresholds for alerts
    USAGE_THRESHOLDS = {
        "critical": 95,   # 95%+ of limit
        "warning": 85,    # 85-94% of limit
        "caution": 70,    # 70-84% of limit
        "healthy": 0      # <70% of limit
    }

    # Overage cost multipliers
    OVERAGE_MULTIPLIERS = {
        "api_calls": 1.5,        # 150% of contracted rate
        "storage": 2.0,          # 200% of contracted rate
        "compute_hours": 1.75,   # 175% of contracted rate
        "users": 1.25,           # 125% of contracted rate
        "transactions": 1.5      # 150% of contracted rate
    }

    # Expansion tier recommendations
    TIER_RECOMMENDATIONS = {
        "overage_risk_high": {
            "action": "immediate_upgrade",
            "timeline": "within_7_days",
            "savings_multiplier": 3.0
        },
        "overage_risk_medium": {
            "action": "planned_upgrade",
            "timeline": "within_30_days",
            "savings_multiplier": 2.0
        },
        "overage_risk_low": {
            "action": "monitor",
            "timeline": "next_renewal",
            "savings_multiplier": 1.5
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="usage_based_expansion",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            max_tokens=800,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="customer_success",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze usage-based expansion opportunities.

        Args:
            state: Current agent state with usage and contract data

        Returns:
            Updated state with usage analysis and expansion recommendations
        """
        self.logger.info("usage_based_expansion_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        usage_data = state.get("entities", {}).get("usage_data", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "usage_based_expansion_details",
            customer_id=customer_id,
            current_tier=contract_data.get("tier", "unknown")
        )

        # Analyze usage against limits
        usage_analysis = self._analyze_usage_vs_limits(
            usage_data,
            contract_data
        )

        # Predict overages
        overage_prediction = self._predict_overages(
            usage_analysis,
            usage_data,
            contract_data
        )

        # Calculate expansion ROI
        expansion_roi = self._calculate_expansion_roi(
            overage_prediction,
            usage_analysis,
            contract_data
        )

        # Generate expansion recommendations
        recommendations = self._generate_expansion_recommendations(
            usage_analysis,
            overage_prediction,
            expansion_roi,
            contract_data
        )

        # Create action plan
        action_plan = self._create_action_plan(
            usage_analysis,
            overage_prediction,
            recommendations
        )

        # Format response
        response = self._format_expansion_report(
            usage_analysis,
            overage_prediction,
            expansion_roi,
            recommendations,
            action_plan
        )

        state["agent_response"] = response
        state["usage_status"] = usage_analysis["overall_status"]
        state["overage_risk"] = overage_prediction["risk_level"]
        state["predicted_overage_cost"] = overage_prediction["total_projected_overage"]
        state["expansion_savings"] = expansion_roi["net_savings"]
        state["usage_analysis"] = usage_analysis
        state["response_confidence"] = 0.89
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "usage_based_expansion_completed",
            customer_id=customer_id,
            usage_status=usage_analysis["overall_status"],
            overage_risk=overage_prediction["risk_level"],
            savings_potential=expansion_roi["net_savings"]
        )

        return state

    def _analyze_usage_vs_limits(
        self,
        usage_data: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current usage against contracted limits.

        Args:
            usage_data: Current usage metrics
            contract_data: Contracted limits and tiers

        Returns:
            Detailed usage analysis
        """
        limits = contract_data.get("usage_limits", {})
        current_usage = usage_data.get("current_usage", {})

        usage_metrics = []
        highest_severity = "healthy"
        metrics_at_risk = []

        # Analyze each usage metric
        for metric, limit in limits.items():
            used = current_usage.get(metric, 0)

            if limit > 0:
                usage_pct = (used / limit) * 100
            else:
                usage_pct = 0

            # Determine status
            status = self._determine_usage_status(usage_pct)

            # Track highest severity
            severity_order = {"critical": 3, "warning": 2, "caution": 1, "healthy": 0}
            if severity_order.get(status, 0) > severity_order.get(highest_severity, 0):
                highest_severity = status

            metric_data = {
                "metric": metric,
                "used": used,
                "limit": limit,
                "usage_pct": round(usage_pct, 1),
                "status": status,
                "headroom": limit - used,
                "unit": self._get_metric_unit(metric)
            }

            usage_metrics.append(metric_data)

            if status in ["critical", "warning"]:
                metrics_at_risk.append(metric_data)

        # Calculate overall consumption
        if usage_metrics:
            avg_usage_pct = sum(m["usage_pct"] for m in usage_metrics) / len(usage_metrics)
        else:
            avg_usage_pct = 0

        # Calculate usage velocity (rate of consumption)
        usage_velocity = self._calculate_usage_velocity(
            current_usage,
            usage_data.get("previous_month_usage", {})
        )

        return {
            "overall_status": highest_severity,
            "average_usage_pct": round(avg_usage_pct, 1),
            "usage_metrics": usage_metrics,
            "metrics_at_risk": metrics_at_risk,
            "metrics_at_risk_count": len(metrics_at_risk),
            "usage_velocity": usage_velocity,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _determine_usage_status(self, usage_pct: float) -> str:
        """Determine usage status based on percentage."""
        if usage_pct >= self.USAGE_THRESHOLDS["critical"]:
            return "critical"
        elif usage_pct >= self.USAGE_THRESHOLDS["warning"]:
            return "warning"
        elif usage_pct >= self.USAGE_THRESHOLDS["caution"]:
            return "caution"
        else:
            return "healthy"

    def _get_metric_unit(self, metric: str) -> str:
        """Get display unit for metric."""
        unit_map = {
            "api_calls": "calls",
            "storage": "GB",
            "compute_hours": "hours",
            "users": "seats",
            "transactions": "txns",
            "bandwidth": "GB"
        }
        return unit_map.get(metric, "units")

    def _calculate_usage_velocity(
        self,
        current_usage: Dict[str, int],
        previous_usage: Dict[str, int]
    ) -> Dict[str, Any]:
        """Calculate rate of usage consumption."""
        velocities = {}
        total_growth = 0
        metrics_growing = 0

        for metric, current in current_usage.items():
            previous = previous_usage.get(metric, current)

            if previous > 0:
                growth_pct = ((current - previous) / previous) * 100
            else:
                growth_pct = 0

            velocities[metric] = round(growth_pct, 1)

            if growth_pct > 0:
                total_growth += growth_pct
                metrics_growing += 1

        avg_velocity = round(total_growth / max(metrics_growing, 1), 1) if metrics_growing > 0 else 0

        trend = "accelerating" if avg_velocity > 15 else "growing" if avg_velocity > 5 else "stable"

        return {
            "average_velocity": avg_velocity,
            "trend": trend,
            "metric_velocities": velocities,
            "metrics_growing": metrics_growing
        }

    def _predict_overages(
        self,
        usage_analysis: Dict[str, Any],
        usage_data: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict overage charges based on usage trends.

        Args:
            usage_analysis: Usage vs limits analysis
            usage_data: Historical usage data
            contract_data: Contract terms and pricing

        Returns:
            Overage predictions
        """
        overage_predictions = []
        total_projected_overage = 0
        risk_level = "low"

        limits = contract_data.get("usage_limits", {})
        current_usage = usage_data.get("current_usage", {})
        overage_rates = contract_data.get("overage_rates", {})

        # Calculate days remaining in billing period
        days_in_period = 30
        days_elapsed = usage_data.get("days_in_current_period", 15)
        days_remaining = days_in_period - days_elapsed

        for metric_data in usage_analysis["metrics_at_risk"]:
            metric = metric_data["metric"]
            used = metric_data["used"]
            limit = metric_data["limit"]

            # Project usage for rest of period
            if days_elapsed > 0:
                daily_usage = used / days_elapsed
                projected_total = daily_usage * days_in_period
                projected_overage = max(0, projected_total - limit)
            else:
                projected_overage = 0

            if projected_overage > 0:
                # Calculate overage cost
                base_rate = overage_rates.get(metric, 0)
                if base_rate == 0:
                    # Estimate based on contract value
                    base_rate = contract_data.get("contract_value", 0) / limit if limit > 0 else 0

                overage_multiplier = self.OVERAGE_MULTIPLIERS.get(metric, 1.5)
                overage_cost = projected_overage * base_rate * overage_multiplier

                overage_predictions.append({
                    "metric": metric,
                    "current_used": used,
                    "limit": limit,
                    "projected_total": int(projected_total),
                    "projected_overage": int(projected_overage),
                    "overage_percentage": round((projected_overage / limit) * 100, 1),
                    "estimated_overage_cost": int(overage_cost),
                    "days_to_limit": self._calculate_days_to_limit(used, limit, daily_usage)
                })

                total_projected_overage += int(overage_cost)

        # Determine overall risk level
        if total_projected_overage > contract_data.get("contract_value", 0) * 0.2:
            risk_level = "high"
        elif total_projected_overage > contract_data.get("contract_value", 0) * 0.1:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Calculate annual overage impact
        annual_overage_projection = total_projected_overage * 12

        return {
            "risk_level": risk_level,
            "overage_predictions": overage_predictions,
            "total_projected_overage": total_projected_overage,
            "annual_overage_projection": annual_overage_projection,
            "metrics_in_overage": len(overage_predictions),
            "days_remaining_in_period": days_remaining
        }

    def _calculate_days_to_limit(self, used: int, limit: int, daily_usage: float) -> int:
        """Calculate days until limit is reached."""
        if daily_usage <= 0:
            return 999
        remaining = limit - used
        if remaining <= 0:
            return 0
        return int(remaining / daily_usage)

    def _calculate_expansion_roi(
        self,
        overage_prediction: Dict[str, Any],
        usage_analysis: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate ROI of proactive expansion vs overage costs.

        Args:
            overage_prediction: Predicted overage costs
            usage_analysis: Usage analysis
            contract_data: Contract information

        Returns:
            ROI analysis for expansion
        """
        current_value = contract_data.get("contract_value", 50000)
        annual_overage = overage_prediction["annual_overage_projection"]

        # Calculate recommended expansion
        # Increase limits by 30% to provide headroom
        expansion_percentage = 30
        expansion_cost = int(current_value * (expansion_percentage / 100))

        # Calculate savings
        overage_avoided = annual_overage
        net_savings = overage_avoided - expansion_cost
        roi_percentage = (net_savings / expansion_cost * 100) if expansion_cost > 0 else 0

        # Calculate payback period (months)
        monthly_overage = overage_prediction["total_projected_overage"]
        if monthly_overage > 0:
            payback_months = expansion_cost / monthly_overage
        else:
            payback_months = 999

        # Determine recommendation strength
        if net_savings > expansion_cost:
            recommendation = "strongly_recommended"
        elif net_savings > 0:
            recommendation = "recommended"
        elif overage_prediction["risk_level"] == "high":
            recommendation = "consider"
        else:
            recommendation = "monitor"

        return {
            "current_annual_cost": current_value,
            "expansion_cost": expansion_cost,
            "expansion_percentage": expansion_percentage,
            "annual_overage_cost": annual_overage,
            "overage_avoided": overage_avoided,
            "net_savings": net_savings,
            "roi_percentage": round(roi_percentage, 1),
            "payback_months": round(payback_months, 1),
            "recommendation": recommendation,
            "break_even_point": f"{payback_months:.1f} months"
        }

    def _generate_expansion_recommendations(
        self,
        usage_analysis: Dict[str, Any],
        overage_prediction: Dict[str, Any],
        expansion_roi: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific expansion recommendations.

        Args:
            usage_analysis: Usage analysis
            overage_prediction: Overage predictions
            expansion_roi: ROI analysis
            contract_data: Contract data

        Returns:
            List of expansion recommendations
        """
        recommendations = []
        risk_level = overage_prediction["risk_level"]

        # Main tier upgrade recommendation
        if expansion_roi["recommendation"] in ["strongly_recommended", "recommended"]:
            tier_config = self.TIER_RECOMMENDATIONS.get(
                f"overage_risk_{risk_level}",
                self.TIER_RECOMMENDATIONS["overage_risk_low"]
            )

            recommendations.append({
                "recommendation_type": "tier_upgrade",
                "priority": "critical" if risk_level == "high" else "high",
                "action": tier_config["action"],
                "timeline": tier_config["timeline"],
                "estimated_cost": expansion_roi["expansion_cost"],
                "annual_savings": expansion_roi["net_savings"],
                "roi_percentage": expansion_roi["roi_percentage"],
                "rationale": f"Avoid ${expansion_roi['annual_overage_cost']:,} in annual overage charges"
            })

        # Specific metric expansions
        for metric_data in usage_analysis["metrics_at_risk"][:3]:
            if metric_data["status"] == "critical":
                recommendations.append({
                    "recommendation_type": "metric_expansion",
                    "metric": metric_data["metric"],
                    "priority": "high",
                    "current_limit": metric_data["limit"],
                    "recommended_limit": int(metric_data["limit"] * 1.5),
                    "expansion_percentage": 50,
                    "rationale": f"Currently at {metric_data['usage_pct']:.0f}% of {metric_data['metric']} limit"
                })

        # Usage optimization recommendation
        if usage_analysis["average_usage_pct"] > 80:
            recommendations.append({
                "recommendation_type": "usage_optimization",
                "priority": "medium",
                "areas": ["Review API call efficiency", "Implement caching", "Archive old data"],
                "potential_savings": "10-20% usage reduction",
                "rationale": "High usage across multiple metrics - optimization can defer expansion"
            })

        # Commitment discount opportunity
        if expansion_roi["net_savings"] > 0:
            recommendations.append({
                "recommendation_type": "annual_commitment",
                "priority": "low",
                "discount_percentage": 15,
                "additional_savings": int(expansion_roi["expansion_cost"] * 0.15),
                "rationale": "Lock in lower rate with annual prepay"
            })

        return recommendations

    def _create_action_plan(
        self,
        usage_analysis: Dict[str, Any],
        overage_prediction: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Create action plan based on recommendations."""
        actions = []
        status = usage_analysis["overall_status"]
        risk = overage_prediction["risk_level"]

        # Critical actions
        if status == "critical" or risk == "high":
            actions.append({
                "action": "Alert customer of imminent overage charges",
                "owner": "CSM",
                "timeline": "Immediate",
                "priority": "critical"
            })

            actions.append({
                "action": "Present expansion proposal with ROI analysis",
                "owner": "CSM + Account Executive",
                "timeline": "Within 48 hours",
                "priority": "critical"
            })

        # Standard actions
        if recommendations:
            actions.append({
                "action": f"Schedule expansion discussion: {recommendations[0]['recommendation_type']}",
                "owner": "CSM",
                "timeline": recommendations[0].get("timeline", "within_7_days"),
                "priority": recommendations[0].get("priority", "high")
            })

        # Monitoring actions
        actions.append({
            "action": "Set up usage alerts for approaching limits",
            "owner": "System",
            "timeline": "Immediate",
            "priority": "medium"
        })

        if usage_analysis["usage_velocity"]["trend"] == "accelerating":
            actions.append({
                "action": "Weekly usage monitoring and reporting",
                "owner": "CSM",
                "timeline": "Ongoing",
                "priority": "medium"
            })

        return actions[:6]

    def _format_expansion_report(
        self,
        usage_analysis: Dict[str, Any],
        overage_prediction: Dict[str, Any],
        expansion_roi: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format usage-based expansion report."""
        status = usage_analysis["overall_status"]
        risk = overage_prediction["risk_level"]

        status_emoji = {
            "critical": "????",
            "warning": "????",
            "caution": "????",
            "healthy": "????"
        }

        risk_emoji = {
            "high": "????",
            "medium": "??????",
            "low": "???"
        }

        report = f"""**???? Usage-Based Expansion Analysis**

**Overall Usage Status:** {status.upper()} {status_emoji.get(status, '???')}
**Overage Risk:** {risk.upper()} {risk_emoji.get(risk, '???')}
**Average Usage:** {usage_analysis['average_usage_pct']:.1f}% of limits
**Usage Trend:** {usage_analysis['usage_velocity']['trend'].title()} ({usage_analysis['usage_velocity']['average_velocity']:+.1f}%)

**Usage Metrics at Risk ({usage_analysis['metrics_at_risk_count']}):**
"""

        for metric in usage_analysis["metrics_at_risk"][:5]:
            status_icon = status_emoji.get(metric["status"], "???")
            report += f"- **{metric['metric'].replace('_', ' ').title()}** {status_icon}\n"
            report += f"  {metric['used']:,} / {metric['limit']:,} {metric['unit']} ({metric['usage_pct']:.1f}%)\n"
            report += f"  Headroom: {metric['headroom']:,} {metric['unit']}\n"

        # Overage predictions
        if overage_prediction["overage_predictions"]:
            report += f"\n**???? Overage Predictions:**\n"
            report += f"**This Month:** ${overage_prediction['total_projected_overage']:,}\n"
            report += f"**Annual Projection:** ${overage_prediction['annual_overage_projection']:,}\n"
            report += f"**Days Remaining in Period:** {overage_prediction['days_remaining_in_period']}\n\n"

            report += "**Detailed Predictions:**\n"
            for pred in overage_prediction["overage_predictions"][:3]:
                report += f"- **{pred['metric'].replace('_', ' ').title()}**\n"
                report += f"  Projected: {pred['projected_total']:,} (Overage: {pred['projected_overage']:,})\n"
                report += f"  Est. Cost: ${pred['estimated_overage_cost']:,}\n"
                report += f"  Days to Limit: {pred['days_to_limit']}\n"

        # ROI Analysis
        report += f"\n**???? Expansion ROI Analysis:**\n"
        report += f"**Recommendation:** {expansion_roi['recommendation'].replace('_', ' ').title()}\n"
        report += f"- Current Annual Cost: ${expansion_roi['current_annual_cost']:,}\n"
        report += f"- Expansion Cost (+{expansion_roi['expansion_percentage']}%): ${expansion_roi['expansion_cost']:,}\n"
        report += f"- Annual Overage (if no expansion): ${expansion_roi['annual_overage_cost']:,}\n"
        report += f"- Net Savings: ${expansion_roi['net_savings']:,}\n"
        report += f"- ROI: {expansion_roi['roi_percentage']:.1f}%\n"
        report += f"- Payback Period: {expansion_roi['break_even_point']}\n"

        # Recommendations
        if recommendations:
            report += f"\n**???? Expansion Recommendations:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                priority_icon = "????" if rec["priority"] == "critical" else "????" if rec["priority"] == "high" else "????"
                report += f"\n{i}. **{rec['recommendation_type'].replace('_', ' ').title()}** {priority_icon}\n"
                if "estimated_cost" in rec:
                    report += f"   Cost: ${rec['estimated_cost']:,} | Savings: ${rec.get('annual_savings', 0):,} | ROI: {rec.get('roi_percentage', 0):.1f}%\n"
                report += f"   {rec['rationale']}\n"

        # Action plan
        if action_plan:
            report += f"\n**???? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   Owner: {action['owner']} | Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Usage-Based Expansion Agent (TASK-2052)")
        print("=" * 70)

        agent = UsageBasedExpansionAgent()

        # Test 1: High overage risk
        print("\n\nTest 1: High Overage Risk")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze usage-based expansion",
            context={
                "customer_id": "cust_high_usage",
                "customer_metadata": {
                    "plan": "professional"
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "current_usage": {
                    "api_calls": 950000,
                    "storage": 480,
                    "compute_hours": 1900,
                    "users": 48
                },
                "previous_month_usage": {
                    "api_calls": 800000,
                    "storage": 400,
                    "compute_hours": 1600,
                    "users": 45
                },
                "days_in_current_period": 20
            },
            "contract_data": {
                "tier": "professional",
                "contract_value": 60000,
                "usage_limits": {
                    "api_calls": 1000000,
                    "storage": 500,
                    "compute_hours": 2000,
                    "users": 50
                },
                "overage_rates": {
                    "api_calls": 0.05,
                    "storage": 50,
                    "compute_hours": 15,
                    "users": 100
                }
            }
        }

        result1 = await agent.process(state1)

        print(f"Usage Status: {result1['usage_status']}")
        print(f"Overage Risk: {result1['overage_risk']}")
        print(f"Predicted Monthly Overage: ${result1['predicted_overage_cost']:,}")
        print(f"Expansion Savings: ${result1['expansion_savings']:,}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Healthy usage
        print("\n\n" + "=" * 70)
        print("Test 2: Healthy Usage Levels")
        print("-" * 70)

        state2 = create_initial_state(
            "Check usage levels",
            context={
                "customer_id": "cust_healthy",
                "customer_metadata": {"plan": "enterprise"}
            }
        )
        state2["entities"] = {
            "usage_data": {
                "current_usage": {
                    "api_calls": 500000,
                    "storage": 300,
                    "users": 60
                },
                "previous_month_usage": {
                    "api_calls": 480000,
                    "storage": 290,
                    "users": 58
                },
                "days_in_current_period": 15
            },
            "contract_data": {
                "tier": "enterprise",
                "contract_value": 100000,
                "usage_limits": {
                    "api_calls": 2000000,
                    "storage": 1000,
                    "users": 100
                },
                "overage_rates": {
                    "api_calls": 0.04,
                    "storage": 40,
                    "users": 80
                }
            }
        }

        result2 = await agent.process(state2)

        print(f"Usage Status: {result2['usage_status']}")
        print(f"Overage Risk: {result2['overage_risk']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
