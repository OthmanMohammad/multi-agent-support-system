"""
Cohort Analyzer Agent - TASK-2015

Analyzes customer cohorts, retention curves, and lifetime value (LTV).
Provides insights into customer behavior patterns by cohort.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("cohort_analyzer", tier="operational", category="analytics")
class CohortAnalyzerAgent(BaseAgent):
    """
    Cohort Analyzer Agent.

    Analyzes customer cohorts and their behavior over time:
    - Cohort definition and segmentation
    - Retention curve analysis
    - Lifetime Value (LTV) by cohort
    - Churn rate analysis by cohort
    - Cohort comparison and trends
    - Revenue and engagement patterns
    """

    # Cohort types
    COHORT_TYPES = {
        "acquisition": "Grouped by signup date",
        "product": "Grouped by product/plan tier",
        "geographic": "Grouped by location",
        "industry": "Grouped by industry vertical",
        "size": "Grouped by company size"
    }

    # Retention periods
    RETENTION_PERIODS = [7, 30, 60, 90, 180, 365]  # Days

    def __init__(self):
        config = AgentConfig(
            name="cohort_analyzer",
            type=AgentType.ANALYZER,
            temperature=0.2,
            max_tokens=1500,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze customer cohorts.

        Args:
            state: Current agent state with cohort parameters

        Returns:
            Updated state with cohort analysis
        """
        self.logger.info("cohort_analysis_started")

        state = self.update_state(state)

        # Extract parameters
        cohort_type = state.get("entities", {}).get("cohort_type", "acquisition")
        cohort_period = state.get("entities", {}).get("cohort_period", "monthly")
        include_ltv = state.get("entities", {}).get("include_ltv", True)
        include_retention = state.get("entities", {}).get("include_retention", True)

        self.logger.debug(
            "cohort_analysis_details",
            cohort_type=cohort_type,
            cohort_period=cohort_period,
            include_ltv=include_ltv
        )

        # Define cohorts
        cohorts = self._define_cohorts(cohort_type, cohort_period)

        # Analyze retention for each cohort
        retention_analysis = None
        if include_retention:
            retention_analysis = self._analyze_retention(cohorts)

        # Calculate LTV for each cohort
        ltv_analysis = None
        if include_ltv:
            ltv_analysis = self._calculate_cohort_ltv(cohorts)

        # Analyze churn patterns
        churn_analysis = self._analyze_churn_patterns(cohorts)

        # Compare cohorts
        cohort_comparison = self._compare_cohorts(cohorts, retention_analysis, ltv_analysis)

        # Generate insights
        insights = self._generate_cohort_insights(
            cohorts,
            retention_analysis,
            ltv_analysis,
            churn_analysis
        )

        # Format response
        response = self._format_cohort_report(
            cohort_type,
            cohorts,
            retention_analysis,
            ltv_analysis,
            churn_analysis,
            cohort_comparison,
            insights
        )

        state["agent_response"] = response
        state["cohorts"] = cohorts
        state["retention_analysis"] = retention_analysis
        state["ltv_analysis"] = ltv_analysis
        state["churn_analysis"] = churn_analysis
        state["cohort_insights"] = insights
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "cohort_analysis_completed",
            cohort_type=cohort_type,
            cohorts_analyzed=len(cohorts),
            insights_generated=len(insights)
        )

        return state

    def _define_cohorts(
        self,
        cohort_type: str,
        cohort_period: str
    ) -> List[Dict[str, Any]]:
        """
        Define cohorts based on type and period.

        Args:
            cohort_type: Type of cohort
            cohort_period: Period for cohort grouping

        Returns:
            List of defined cohorts
        """
        # Mock cohort data - in production, query database
        current_date = datetime.now(UTC)

        if cohort_type == "acquisition":
            # Monthly acquisition cohorts for last 6 months
            cohorts = []
            for i in range(6):
                cohort_date = current_date - timedelta(days=30 * i)
                cohort_name = cohort_date.strftime("%Y-%m")

                cohorts.append({
                    "cohort_id": f"acq_{cohort_name}",
                    "cohort_name": cohort_name,
                    "cohort_type": cohort_type,
                    "customer_count": 450 - (i * 50),  # Mock declining acquisition
                    "signup_date": cohort_date.strftime("%Y-%m-%d"),
                    "age_days": 30 * i
                })

            return cohorts

        elif cohort_type == "product":
            # Product tier cohorts
            return [
                {
                    "cohort_id": "product_basic",
                    "cohort_name": "Basic Plan",
                    "cohort_type": cohort_type,
                    "customer_count": 1250,
                    "avg_revenue": 29
                },
                {
                    "cohort_id": "product_pro",
                    "cohort_name": "Professional Plan",
                    "cohort_type": cohort_type,
                    "customer_count": 820,
                    "avg_revenue": 99
                },
                {
                    "cohort_id": "product_enterprise",
                    "cohort_name": "Enterprise Plan",
                    "cohort_type": cohort_type,
                    "customer_count": 145,
                    "avg_revenue": 499
                }
            ]

        else:
            # Default generic cohorts
            return [
                {
                    "cohort_id": "cohort_1",
                    "cohort_name": "Cohort 1",
                    "cohort_type": cohort_type,
                    "customer_count": 500
                }
            ]

    def _analyze_retention(
        self,
        cohorts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze retention curves for cohorts.

        Args:
            cohorts: List of cohorts

        Returns:
            Retention analysis
        """
        retention_data = {
            "periods": self.RETENTION_PERIODS,
            "cohorts": {}
        }

        for cohort in cohorts:
            cohort_id = cohort["cohort_id"]
            customer_count = cohort["customer_count"]

            # Mock retention rates - in production, calculate from actual data
            retention_rates = {}
            for period in self.RETENTION_PERIODS:
                # Simulate decreasing retention over time
                base_retention = 0.85
                decay_rate = 0.002
                retention_rate = base_retention * (1 - decay_rate) ** period
                retention_rates[period] = {
                    "retention_rate": round(retention_rate * 100, 2),
                    "retained_customers": int(customer_count * retention_rate),
                    "churned_customers": int(customer_count * (1 - retention_rate))
                }

            retention_data["cohorts"][cohort_id] = {
                "cohort_name": cohort["cohort_name"],
                "initial_size": customer_count,
                "retention_by_period": retention_rates
            }

        # Calculate average retention curve
        avg_retention = {}
        for period in self.RETENTION_PERIODS:
            rates = [
                cohort_data["retention_by_period"][period]["retention_rate"]
                for cohort_data in retention_data["cohorts"].values()
            ]
            avg_retention[period] = round(sum(rates) / len(rates), 2) if rates else 0

        retention_data["average_retention_curve"] = avg_retention

        return retention_data

    def _calculate_cohort_ltv(
        self,
        cohorts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate lifetime value for each cohort.

        Args:
            cohorts: List of cohorts

        Returns:
            LTV analysis
        """
        ltv_data = {"cohorts": {}}

        for cohort in cohorts:
            cohort_id = cohort["cohort_id"]
            customer_count = cohort["customer_count"]

            # Mock LTV calculation - in production, calculate from actual revenue
            avg_revenue_per_month = cohort.get("avg_revenue", 50)
            avg_customer_lifetime_months = 24  # 2 years
            ltv = avg_revenue_per_month * avg_customer_lifetime_months

            # Calculate components
            total_revenue = customer_count * ltv
            avg_acquisition_cost = 150  # Mock CAC
            ltv_cac_ratio = ltv / avg_acquisition_cost if avg_acquisition_cost > 0 else 0

            ltv_data["cohorts"][cohort_id] = {
                "cohort_name": cohort["cohort_name"],
                "customer_count": customer_count,
                "ltv": round(ltv, 2),
                "total_cohort_value": round(total_revenue, 2),
                "avg_monthly_revenue": avg_revenue_per_month,
                "avg_lifetime_months": avg_customer_lifetime_months,
                "cac": avg_acquisition_cost,
                "ltv_cac_ratio": round(ltv_cac_ratio, 2),
                "payback_period_months": round(avg_acquisition_cost / avg_revenue_per_month, 1) if avg_revenue_per_month > 0 else 0
            }

        return ltv_data

    def _analyze_churn_patterns(
        self,
        cohorts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze churn patterns by cohort.

        Args:
            cohorts: List of cohorts

        Returns:
            Churn analysis
        """
        churn_data = {"cohorts": {}}

        for cohort in cohorts:
            cohort_id = cohort["cohort_id"]
            customer_count = cohort["customer_count"]

            # Mock churn data
            import random
            monthly_churn_rate = random.uniform(2, 8)  # 2-8% monthly churn
            churned_customers = int(customer_count * (monthly_churn_rate / 100))

            churn_data["cohorts"][cohort_id] = {
                "cohort_name": cohort["cohort_name"],
                "monthly_churn_rate": round(monthly_churn_rate, 2),
                "churned_customers_month": churned_customers,
                "at_risk_customers": int(customer_count * 0.15),  # 15% at risk
                "churn_reasons": {
                    "price": 35,
                    "lack_of_use": 25,
                    "competitor": 20,
                    "product_fit": 15,
                    "other": 5
                }
            }

        return churn_data

    def _compare_cohorts(
        self,
        cohorts: List[Dict[str, Any]],
        retention_analysis: Optional[Dict[str, Any]],
        ltv_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare cohorts across key metrics.

        Args:
            cohorts: List of cohorts
            retention_analysis: Retention data
            ltv_analysis: LTV data

        Returns:
            Cohort comparison
        """
        comparison = {
            "best_performing": {},
            "worst_performing": {},
            "insights": []
        }

        if ltv_analysis:
            # Find highest and lowest LTV cohorts
            ltv_cohorts = ltv_analysis.get("cohorts", {})
            if ltv_cohorts:
                sorted_by_ltv = sorted(
                    ltv_cohorts.items(),
                    key=lambda x: x[1].get("ltv", 0),
                    reverse=True
                )

                comparison["best_performing"]["ltv"] = sorted_by_ltv[0][1]["cohort_name"]
                comparison["worst_performing"]["ltv"] = sorted_by_ltv[-1][1]["cohort_name"]

        if retention_analysis:
            # Find highest and lowest retention cohorts (90-day retention)
            retention_cohorts = retention_analysis.get("cohorts", {})
            if retention_cohorts:
                sorted_by_retention = sorted(
                    retention_cohorts.items(),
                    key=lambda x: x[1]["retention_by_period"].get(90, {}).get("retention_rate", 0),
                    reverse=True
                )

                comparison["best_performing"]["retention"] = sorted_by_retention[0][1]["cohort_name"]
                comparison["worst_performing"]["retention"] = sorted_by_retention[-1][1]["cohort_name"]

        return comparison

    def _generate_cohort_insights(
        self,
        cohorts: List[Dict[str, Any]],
        retention_analysis: Optional[Dict[str, Any]],
        ltv_analysis: Optional[Dict[str, Any]],
        churn_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from cohort analysis.

        Args:
            cohorts: Cohort data
            retention_analysis: Retention data
            ltv_analysis: LTV data
            churn_analysis: Churn data

        Returns:
            List of insights
        """
        insights = []

        # LTV insights
        if ltv_analysis:
            ltv_cohorts = ltv_analysis.get("cohorts", {})
            high_ltv_cohorts = [
                c for c in ltv_cohorts.values()
                if c.get("ltv_cac_ratio", 0) > 3
            ]

            if high_ltv_cohorts:
                insights.append({
                    "type": "positive",
                    "category": "ltv",
                    "message": f"{len(high_ltv_cohorts)} cohorts have LTV:CAC ratio >3:1 (healthy)",
                    "priority": "high"
                })

        # Retention insights
        if retention_analysis:
            avg_curve = retention_analysis.get("average_retention_curve", {})
            retention_90d = avg_curve.get(90, 0)

            if retention_90d > 75:
                insights.append({
                    "type": "positive",
                    "category": "retention",
                    "message": f"Strong 90-day retention: {retention_90d}%",
                    "priority": "high"
                })
            elif retention_90d < 50:
                insights.append({
                    "type": "alert",
                    "category": "retention",
                    "message": f"Low 90-day retention: {retention_90d}% - needs improvement",
                    "priority": "critical"
                })

        # Churn insights
        churn_cohorts = churn_analysis.get("cohorts", {})
        if churn_cohorts:
            avg_churn = sum(c.get("monthly_churn_rate", 0) for c in churn_cohorts.values()) / len(churn_cohorts)

            if avg_churn > 5:
                insights.append({
                    "type": "alert",
                    "category": "churn",
                    "message": f"High average monthly churn: {avg_churn:.1f}%",
                    "priority": "high"
                })

        return insights

    def _format_cohort_report(
        self,
        cohort_type: str,
        cohorts: List[Dict[str, Any]],
        retention_analysis: Optional[Dict[str, Any]],
        ltv_analysis: Optional[Dict[str, Any]],
        churn_analysis: Dict[str, Any],
        cohort_comparison: Dict[str, Any],
        insights: List[Dict[str, Any]]
    ) -> str:
        """Format cohort analysis report."""
        report = f"""**Cohort Analysis Report**

**Cohort Type:** {cohort_type.title()}
**Total Cohorts Analyzed:** {len(cohorts)}

"""

        # Cohort summary
        report += "**Cohort Overview:**\n"
        for cohort in cohorts[:5]:  # Top 5 cohorts
            report += f"- {cohort['cohort_name']}: {cohort['customer_count']} customers\n"

        # LTV Analysis
        if ltv_analysis:
            report += "\n**Lifetime Value by Cohort:**\n"
            for cohort_id, ltv_data in list(ltv_analysis.get("cohorts", {}).items())[:5]:
                report += f"- {ltv_data['cohort_name']}: ${ltv_data['ltv']:,.2f} LTV (LTV:CAC {ltv_data['ltv_cac_ratio']:.1f}:1)\n"

        # Retention Analysis
        if retention_analysis:
            report += "\n**Retention Curves:**\n"
            avg_curve = retention_analysis.get("average_retention_curve", {})
            report += "Average Retention:\n"
            for period in [7, 30, 90, 180, 365]:
                if period in avg_curve:
                    report += f"  - Day {period}: {avg_curve[period]:.1f}%\n"

        # Churn Analysis
        report += "\n**Churn Analysis:**\n"
        for cohort_id, churn_data in list(churn_analysis.get("cohorts", {}).items())[:3]:
            report += f"- {churn_data['cohort_name']}: {churn_data['monthly_churn_rate']:.2f}% monthly churn\n"

        # Comparison
        if cohort_comparison.get("best_performing"):
            report += "\n**Top Performing Cohorts:**\n"
            for metric, cohort_name in cohort_comparison["best_performing"].items():
                report += f"- Best {metric.upper()}: {cohort_name}\n"

        # Insights
        if insights:
            report += "\n**Key Insights:**\n"
            for insight in insights:
                icon = "🔴" if insight.get("type") == "alert" else "✅" if insight.get("type") == "positive" else "ℹ️"
                report += f"{icon} {insight['message']}\n"

        report += f"\n*Analysis completed at {datetime.now(UTC).isoformat()}*"

        return report
