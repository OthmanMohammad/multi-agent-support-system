"""
Funnel Analyzer Agent - TASK-2016

Analyzes conversion funnels and identifies bottlenecks in user journeys.
Provides step-by-step conversion metrics and optimization recommendations.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("funnel_analyzer", tier="operational", category="analytics")
class FunnelAnalyzerAgent(BaseAgent):
    """
    Funnel Analyzer Agent.

    Analyzes conversion funnels to optimize user journeys:
    - Step-by-step conversion rates
    - Drop-off identification and quantification
    - Bottleneck detection
    - Funnel comparison (time periods, segments)
    - Conversion optimization recommendations
    - Time-to-convert analysis
    """

    # Common funnel types
    FUNNEL_TYPES = {
        "onboarding": [
            "signup",
            "email_verification",
            "profile_setup",
            "first_project",
            "first_action",
        ],
        "sales": ["lead", "qualified", "demo", "proposal", "negotiation", "closed_won"],
        "product": [
            "trial_signup",
            "first_login",
            "feature_activation",
            "regular_usage",
            "paid_conversion",
        ],
        "support": ["ticket_created", "assigned", "first_response", "in_progress", "resolved"],
    }

    # Conversion rate benchmarks
    BENCHMARKS = {"excellent": 80, "good": 60, "average": 40, "poor": 20}

    def __init__(self):
        config = AgentConfig(
            name="funnel_analyzer",
            type=AgentType.ANALYZER,
            temperature=0.2,
            max_tokens=1500,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze conversion funnel.

        Args:
            state: Current agent state with funnel data

        Returns:
            Updated state with funnel analysis
        """
        self.logger.info("funnel_analysis_started")

        state = self.update_state(state)

        # Extract parameters
        funnel_type = state.get("entities", {}).get("funnel_type", "product")
        funnel_steps = state.get("entities", {}).get("funnel_steps", None)
        time_period = state.get("entities", {}).get("time_period", "30d")
        segment_by = state.get("entities", {}).get("segment_by", None)

        self.logger.debug(
            "funnel_analysis_details",
            funnel_type=funnel_type,
            custom_steps=funnel_steps is not None,
            time_period=time_period,
        )

        # Get funnel definition
        funnel_definition = self._get_funnel_definition(funnel_type, funnel_steps)

        # Fetch funnel data
        funnel_data = self._fetch_funnel_data(funnel_definition, time_period)

        # Calculate conversion rates
        conversion_metrics = self._calculate_conversion_rates(funnel_data)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(conversion_metrics)

        # Calculate time-to-convert
        time_analysis = self._analyze_time_to_convert(funnel_data)

        # Segment analysis if requested
        segment_analysis = None
        if segment_by:
            segment_analysis = self._analyze_by_segment(funnel_data, segment_by)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            conversion_metrics, bottlenecks, time_analysis
        )

        # Format response
        response = self._format_funnel_report(
            funnel_type,
            funnel_definition,
            conversion_metrics,
            bottlenecks,
            time_analysis,
            segment_analysis,
            recommendations,
        )

        state["agent_response"] = response
        state["funnel_data"] = funnel_data
        state["conversion_metrics"] = conversion_metrics
        state["bottlenecks"] = bottlenecks
        state["time_analysis"] = time_analysis
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "funnel_analysis_completed",
            funnel_type=funnel_type,
            steps=len(funnel_definition),
            bottlenecks_found=len(bottlenecks),
        )

        return state

    def _get_funnel_definition(self, funnel_type: str, custom_steps: list[str] | None) -> list[str]:
        """
        Get funnel step definitions.

        Args:
            funnel_type: Type of funnel
            custom_steps: Custom step definitions

        Returns:
            List of funnel steps
        """
        if custom_steps:
            return custom_steps
        elif funnel_type in self.FUNNEL_TYPES:
            return self.FUNNEL_TYPES[funnel_type]
        else:
            return self.FUNNEL_TYPES["product"]  # Default

    def _fetch_funnel_data(self, funnel_definition: list[str], time_period: str) -> dict[str, Any]:
        """
        Fetch funnel data from data sources.

        Args:
            funnel_definition: Funnel steps
            time_period: Time period

        Returns:
            Funnel data
        """
        # Mock funnel data - in production, query actual data
        funnel_data = {"time_period": time_period, "steps": [], "total_entered": 10000}

        # Generate decreasing user counts through funnel
        current_users = funnel_data["total_entered"]

        for i, step in enumerate(funnel_definition):
            # Simulate drop-off (10-30% per step)
            import random

            drop_rate = random.uniform(0.10, 0.30)
            users_at_step = int(current_users * (1 - drop_rate))

            funnel_data["steps"].append(
                {
                    "step_number": i + 1,
                    "step_name": step,
                    "users_entered": current_users,
                    "users_completed": users_at_step,
                    "users_dropped": current_users - users_at_step,
                    "avg_time_to_complete_hours": random.uniform(0.5, 48),
                }
            )

            current_users = users_at_step

        return funnel_data

    def _calculate_conversion_rates(self, funnel_data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate conversion metrics for funnel.

        Args:
            funnel_data: Raw funnel data

        Returns:
            Conversion metrics
        """
        steps = funnel_data.get("steps", [])
        total_entered = funnel_data.get("total_entered", 0)

        metrics = {"overall_conversion_rate": 0, "step_metrics": []}

        if not steps or total_entered == 0:
            return metrics

        # Calculate overall conversion (first step to last step)
        final_users = steps[-1]["users_completed"] if steps else 0
        metrics["overall_conversion_rate"] = round((final_users / total_entered) * 100, 2)

        # Calculate per-step metrics
        for _i, step in enumerate(steps):
            users_entered = step["users_entered"]
            users_completed = step["users_completed"]
            users_dropped = step["users_dropped"]

            # Step conversion rate
            step_conversion = (users_completed / users_entered * 100) if users_entered > 0 else 0

            # Cumulative conversion from start
            cumulative_conversion = (
                (users_completed / total_entered * 100) if total_entered > 0 else 0
            )

            # Drop-off rate
            drop_off_rate = (users_dropped / users_entered * 100) if users_entered > 0 else 0

            step_metric = {
                "step_number": step["step_number"],
                "step_name": step["step_name"],
                "users_entered": users_entered,
                "users_completed": users_completed,
                "users_dropped": users_dropped,
                "step_conversion_rate": round(step_conversion, 2),
                "cumulative_conversion_rate": round(cumulative_conversion, 2),
                "drop_off_rate": round(drop_off_rate, 2),
                "performance": self._classify_conversion_rate(step_conversion),
            }

            metrics["step_metrics"].append(step_metric)

        return metrics

    def _classify_conversion_rate(self, rate: float) -> str:
        """Classify conversion rate performance."""
        if rate >= self.BENCHMARKS["excellent"]:
            return "excellent"
        elif rate >= self.BENCHMARKS["good"]:
            return "good"
        elif rate >= self.BENCHMARKS["average"]:
            return "average"
        else:
            return "poor"

    def _identify_bottlenecks(self, conversion_metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Identify funnel bottlenecks.

        Args:
            conversion_metrics: Conversion metrics

        Returns:
            List of bottlenecks
        """
        bottlenecks = []
        step_metrics = conversion_metrics.get("step_metrics", [])

        for metric in step_metrics:
            # Identify bottleneck if drop-off rate > 30% or poor performance
            drop_off_rate = metric.get("drop_off_rate", 0)
            performance = metric.get("performance", "average")

            if drop_off_rate > 30 or performance == "poor":
                severity = (
                    "critical" if drop_off_rate > 50 else "high" if drop_off_rate > 40 else "medium"
                )

                bottlenecks.append(
                    {
                        "step_number": metric["step_number"],
                        "step_name": metric["step_name"],
                        "drop_off_rate": drop_off_rate,
                        "users_lost": metric["users_dropped"],
                        "severity": severity,
                        "impact": self._calculate_bottleneck_impact(metric, conversion_metrics),
                    }
                )

        # Sort by severity and impact
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        bottlenecks.sort(key=lambda x: (severity_order.get(x["severity"], 3), -x["users_lost"]))

        return bottlenecks

    def _calculate_bottleneck_impact(
        self, step_metric: dict[str, Any], conversion_metrics: dict[str, Any]
    ) -> str:
        """Calculate impact of bottleneck."""
        users_lost = step_metric.get("users_dropped", 0)
        total_users = conversion_metrics.get("step_metrics", [{}])[0].get("users_entered", 1)

        impact_pct = (users_lost / total_users) * 100 if total_users > 0 else 0

        if impact_pct > 20:
            return f"High impact - {impact_pct:.1f}% of total users lost"
        elif impact_pct > 10:
            return f"Medium impact - {impact_pct:.1f}% of total users lost"
        else:
            return f"Low impact - {impact_pct:.1f}% of total users lost"

    def _analyze_time_to_convert(self, funnel_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze time taken at each funnel step.

        Args:
            funnel_data: Funnel data

        Returns:
            Time analysis
        """
        steps = funnel_data.get("steps", [])

        time_metrics = {"total_time_hours": 0, "step_times": []}

        for step in steps:
            avg_time = step.get("avg_time_to_complete_hours", 0)
            time_metrics["total_time_hours"] += avg_time

            time_metrics["step_times"].append(
                {
                    "step_name": step["step_name"],
                    "avg_time_hours": round(avg_time, 2),
                    "time_classification": "fast"
                    if avg_time < 1
                    else "normal"
                    if avg_time < 24
                    else "slow",
                }
            )

        time_metrics["total_time_hours"] = round(time_metrics["total_time_hours"], 2)

        return time_metrics

    def _analyze_by_segment(self, funnel_data: dict[str, Any], segment_by: str) -> dict[str, Any]:
        """
        Analyze funnel by segment.

        Args:
            funnel_data: Funnel data
            segment_by: Segmentation criterion

        Returns:
            Segment analysis
        """
        # Mock segment analysis
        return {
            "segment_type": segment_by,
            "segments": [
                {"segment_name": "Segment A", "overall_conversion": 45.2, "user_count": 6000},
                {"segment_name": "Segment B", "overall_conversion": 38.7, "user_count": 4000},
            ],
        }

    def _generate_recommendations(
        self,
        conversion_metrics: dict[str, Any],
        bottlenecks: list[dict[str, Any]],
        time_analysis: dict[str, Any],
    ) -> list[str]:
        """
        Generate optimization recommendations.

        Args:
            conversion_metrics: Conversion metrics
            bottlenecks: Identified bottlenecks
            time_analysis: Time analysis

        Returns:
            List of recommendations
        """
        recommendations = []

        # Overall conversion
        overall_rate = conversion_metrics.get("overall_conversion_rate", 0)
        if overall_rate < 20:
            recommendations.append(
                f"CRITICAL: Overall conversion rate is {overall_rate}% - major funnel optimization needed"
            )
        elif overall_rate < 40:
            recommendations.append(
                f"Overall conversion rate is {overall_rate}% - improvement opportunities exist"
            )

        # Bottleneck recommendations
        for bottleneck in bottlenecks[:3]:  # Top 3 bottlenecks
            recommendations.append(
                f"Focus on {bottleneck['step_name']}: {bottleneck['drop_off_rate']:.1f}% drop-off ({bottleneck['severity']} severity)"
            )

        # Time-based recommendations
        slow_steps = [
            s for s in time_analysis.get("step_times", []) if s["time_classification"] == "slow"
        ]
        if slow_steps:
            recommendations.append(
                f"Optimize slow steps: {', '.join(s['step_name'] for s in slow_steps)}"
            )

        if not bottlenecks:
            recommendations.append("Funnel performing well - focus on incremental optimizations")

        return recommendations

    def _format_funnel_report(
        self,
        funnel_type: str,
        funnel_definition: list[str],
        conversion_metrics: dict[str, Any],
        bottlenecks: list[dict[str, Any]],
        time_analysis: dict[str, Any],
        segment_analysis: dict[str, Any] | None,
        recommendations: list[str],
    ) -> str:
        """Format funnel analysis report."""
        report = f"""**Funnel Analysis Report**

**Funnel Type:** {funnel_type.title()}
**Total Steps:** {len(funnel_definition)}
**Overall Conversion Rate:** {conversion_metrics.get("overall_conversion_rate", 0)}%

**Funnel Steps:**
"""

        # Step-by-step breakdown
        for metric in conversion_metrics.get("step_metrics", []):
            perf_icon = (
                "✅"
                if metric["performance"] == "excellent"
                else "⚠️"
                if metric["performance"] == "poor"
                else "➡️"
            )
            report += f"\n{metric['step_number']}. **{metric['step_name']}** {perf_icon}\n"
            report += f"   - Users Entered: {metric['users_entered']:,}\n"
            report += f"   - Users Completed: {metric['users_completed']:,}\n"
            report += f"   - Step Conversion: {metric['step_conversion_rate']}%\n"
            report += (
                f"   - Drop-off: {metric['drop_off_rate']}% ({metric['users_dropped']:,} users)\n"
            )

        # Bottlenecks
        if bottlenecks:
            report += "\n**Identified Bottlenecks:**\n"
            for bottleneck in bottlenecks:
                severity_icon = "🔴" if bottleneck["severity"] == "critical" else "⚠️"
                report += f"{severity_icon} **{bottleneck['step_name']}**\n"
                report += f"   - Drop-off Rate: {bottleneck['drop_off_rate']:.1f}%\n"
                report += f"   - Users Lost: {bottleneck['users_lost']:,}\n"
                report += f"   - {bottleneck['impact']}\n"

        # Time analysis
        report += "\n**Time to Convert:**\n"
        report += f"- Total Average Time: {time_analysis['total_time_hours']:.1f} hours\n"
        for step_time in time_analysis.get("step_times", [])[:3]:
            report += f"- {step_time['step_name']}: {step_time['avg_time_hours']:.1f}h ({step_time['time_classification']})\n"

        # Recommendations
        report += "\n**Recommendations:**\n"
        for rec in recommendations:
            report += f"- {rec}\n"

        report += f"\n*Analysis completed at {datetime.now(UTC).isoformat()}*"

        return report
