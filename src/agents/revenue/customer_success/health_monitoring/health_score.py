"""
Customer Health Score Agent - TASK-2011

Calculates comprehensive customer health scores (0-100) to predict churn and
identify at-risk customers. Analyzes usage, engagement, support, and financial metrics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("health_score", tier="revenue", category="customer_success")
class HealthScoreAgent(BaseAgent):
    """
    Customer Health Score Agent.

    Calculates 0-100 health score from multiple dimensions:
    - Product Usage (0-30 points): DAU/MAU, feature adoption, session frequency
    - User Engagement (0-25 points): NPS, QBR attendance, community participation
    - Financial Health (0-20 points): Payment status, plan level
    - Support Health (0-15 points): Ticket volume, CSAT, escalations
    - Relationship Health (0-10 points): CSM touchpoints, executive engagement
    """

    # Health score thresholds
    HEALTH_TIERS = {
        "thriving": (85, 100),
        "healthy": (70, 84),
        "needs_attention": (55, 69),
        "at_risk": (40, 54),
        "critical": (0, 39)
    }

    # Scoring weights
    WEIGHTS = {
        "usage": 30,
        "engagement": 25,
        "financial": 20,
        "support": 15,
        "relationship": 10
    }

    def __init__(self):
        config = AgentConfig(
            name="health_score",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            max_tokens=700,
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
        Calculate customer health score.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with health score and analysis
        """
        self.logger.info("health_score_processing_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})

        # Extract data from state or entities
        usage_data = state.get("entities", {}).get("usage_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        business_data = state.get("entities", {}).get("business_data", {})

        self.logger.debug(
            "health_score_calculation_details",
            customer_id=customer_id,
            has_usage_data=bool(usage_data),
            has_engagement_data=bool(engagement_data)
        )

        # Calculate health score
        health_analysis = self._calculate_health_score(
            usage_data,
            engagement_data,
            business_data,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(health_analysis)

        # Build response
        response = self._format_health_report(health_analysis, recommendations)

        state["agent_response"] = response
        state["health_score"] = health_analysis["total_score"]
        state["health_status"] = health_analysis["health_status"]
        state["health_trend"] = health_analysis.get("trend", "stable")
        state["health_analysis"] = health_analysis
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "health_score_calculated",
            customer_id=customer_id,
            health_score=health_analysis["total_score"],
            health_status=health_analysis["health_status"]
        )

        return state

    def _calculate_health_score(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        business_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive health score.

        Args:
            usage_data: Product usage metrics
            engagement_data: Customer engagement metrics
            business_data: Financial and contract data
            customer_metadata: Customer profile data

        Returns:
            Health analysis with scores and breakdown
        """
        breakdown = {}

        # 1. Product Usage Score (0-30 points)
        usage_score = self._calculate_usage_score(usage_data)
        breakdown["product_usage"] = usage_score

        # 2. User Engagement Score (0-25 points)
        engagement_score = self._calculate_engagement_score(engagement_data)
        breakdown["user_engagement"] = engagement_score

        # 3. Financial Health Score (0-20 points)
        financial_score = self._calculate_financial_score(business_data, customer_metadata)
        breakdown["financial_health"] = financial_score

        # 4. Support Health Score (0-15 points)
        support_score = self._calculate_support_score(engagement_data)
        breakdown["support_health"] = support_score

        # 5. Relationship Health Score (0-10 points)
        relationship_score = self._calculate_relationship_score(engagement_data)
        breakdown["relationship_health"] = relationship_score

        # Calculate total
        total_score = sum(breakdown.values())
        total_score = min(max(total_score, 0), 100)  # Clamp to 0-100

        # Determine health status
        health_status = self._determine_health_status(total_score)

        # Determine trend (if previous score available)
        previous_score = customer_metadata.get("previous_health_score")
        trend = self._calculate_trend(total_score, previous_score)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(breakdown, usage_data, engagement_data)

        # Identify positive signals
        positive_signals = self._identify_positive_signals(breakdown, usage_data, engagement_data)

        return {
            "total_score": int(total_score),
            "health_status": health_status,
            "score_breakdown": {k: int(v) for k, v in breakdown.items()},
            "trend": trend,
            "score_change": int(total_score - previous_score) if previous_score else 0,
            "risk_factors": risk_factors,
            "positive_signals": positive_signals,
            "calculated_at": datetime.now(UTC).isoformat()
        }

    def _calculate_usage_score(self, usage_data: Dict[str, Any]) -> float:
        """Calculate product usage score (0-30)."""
        score = 0.0

        # DAU/MAU ratio (0-15 points)
        dau = usage_data.get("daily_active_users", 0)
        total_users = usage_data.get("total_users", 1)
        dau_ratio = dau / total_users if total_users > 0 else 0
        score += dau_ratio * 15

        # Feature adoption (0-10 points)
        features_used = usage_data.get("features_used", 0)
        total_features = 10  # Assuming 10 key features
        adoption_ratio = min(features_used / total_features, 1.0)
        score += adoption_ratio * 10

        # Active automation rules (0-5 points)
        automation_rules = usage_data.get("automation_rules_active", 0)
        score += min(automation_rules, 5)

        return min(score, 30)

    def _calculate_engagement_score(self, engagement_data: Dict[str, Any]) -> float:
        """Calculate user engagement score (0-25)."""
        score = 0.0

        # NPS score (0-15 points)
        nps = engagement_data.get("nps_score", 5)
        nps_normalized = (nps / 10) * 15
        score += nps_normalized

        # Feature requests (0-5 points) - shows engagement
        feature_requests = engagement_data.get("feature_requests", 0)
        score += min(feature_requests * 1.5, 5)

        # Login recency (0-5 points)
        last_login = engagement_data.get("last_login")
        if last_login:
            if isinstance(last_login, str):
                try:
                    last_login = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                except:
                    last_login = datetime.now(UTC)
            days_since_login = (datetime.now(UTC) - last_login).days
            if days_since_login < 1:
                score += 5
            elif days_since_login < 3:
                score += 3
            elif days_since_login < 7:
                score += 1

        return min(score, 25)

    def _calculate_financial_score(
        self,
        business_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> float:
        """Calculate financial health score (0-20)."""
        score = 0.0

        # Payment status (0-15 points)
        payment_status = business_data.get("payment_status", "current")
        if payment_status == "current":
            score += 15
        elif payment_status == "past_due_7":
            score += 10
        elif payment_status == "past_due_30":
            score += 5

        # Plan level (0-5 points)
        plan = customer_metadata.get("plan", "free")
        plan_scores = {"free": 1, "basic": 2, "premium": 4, "enterprise": 5}
        score += plan_scores.get(plan, 1)

        return min(score, 20)

    def _calculate_support_score(self, engagement_data: Dict[str, Any]) -> float:
        """Calculate support health score (0-15)."""
        score = 15.0  # Start at max, deduct for issues

        # Support tickets (deduct points)
        tickets = engagement_data.get("support_tickets_last_30d", 0)
        if tickets == 0:
            score = 15
        elif tickets <= 2:
            score = 12
        elif tickets <= 5:
            score = 8
        elif tickets <= 10:
            score = 4
        else:
            score = 0

        return max(score, 0)

    def _calculate_relationship_score(self, engagement_data: Dict[str, Any]) -> float:
        """Calculate relationship health score (0-10)."""
        # This would be based on QBR completion, CSM touchpoints, etc.
        # For now, use a baseline
        score = 7.0

        # Adjust based on QBR attendance
        qbr_attended = engagement_data.get("qbr_attended_last_quarter", False)
        if qbr_attended:
            score += 3

        return min(score, 10)

    def _determine_health_status(self, score: float) -> str:
        """Determine health status from score."""
        for status, (min_score, max_score) in self.HEALTH_TIERS.items():
            if min_score <= score <= max_score:
                return status
        return "needs_attention"

    def _calculate_trend(self, current_score: float, previous_score: Optional[float]) -> str:
        """Calculate health score trend."""
        if not previous_score:
            return "new"

        change = current_score - previous_score

        if change > 5:
            return "improving"
        elif change < -5:
            return "declining"
        else:
            return "stable"

    def _identify_risk_factors(
        self,
        breakdown: Dict[str, float],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify risk factors affecting health."""
        risk_factors = []

        if breakdown.get("product_usage", 0) < 15:
            risk_factors.append({
                "factor": "Low product usage",
                "severity": "high",
                "impact": -10,
                "description": f"Usage score only {int(breakdown['product_usage'])}/30 - low DAU or feature adoption"
            })

        if breakdown.get("support_health", 0) < 8:
            risk_factors.append({
                "factor": "High support ticket volume",
                "severity": "medium",
                "impact": -7,
                "description": f"Support score {int(breakdown['support_health'])}/15 - indicates product issues"
            })

        if breakdown.get("user_engagement", 0) < 12:
            nps = engagement_data.get("nps_score", 5)
            if nps < 7:
                risk_factors.append({
                    "factor": "Low NPS score",
                    "severity": "high",
                    "impact": -10,
                    "description": f"NPS score {nps}/10 - customer dissatisfaction"
                })

        if breakdown.get("relationship_health", 0) < 5:
            risk_factors.append({
                "factor": "Weak CSM relationship",
                "severity": "medium",
                "impact": -5,
                "description": "Low engagement with CSM - schedule check-in"
            })

        return risk_factors

    def _identify_positive_signals(
        self,
        breakdown: Dict[str, float],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[str]:
        """Identify positive signals in customer health."""
        signals = []

        dau = usage_data.get("daily_active_users", 0)
        total_users = usage_data.get("total_users", 1)
        dau_ratio = dau / total_users if total_users > 0 else 0

        if dau_ratio > 0.7:
            signals.append(f"High DAU ratio ({int(dau_ratio * 100)}%) - strong daily engagement")

        automation_rules = usage_data.get("automation_rules_active", 0)
        if automation_rules >= 3:
            signals.append(f"Using automation ({automation_rules} rules) - power user behavior")

        nps = engagement_data.get("nps_score", 5)
        if nps >= 9:
            signals.append(f"NPS score {nps}/10 - promoter, high satisfaction")

        if breakdown.get("financial_health", 0) >= 18:
            signals.append("Excellent payment history and plan level")

        if breakdown.get("support_health", 0) >= 12:
            signals.append("Low support ticket volume - product working well")

        return signals

    def _generate_recommendations(self, health_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate action recommendations based on health score."""
        recommendations = []

        score = health_analysis["total_score"]
        status = health_analysis["health_status"]
        risk_factors = health_analysis.get("risk_factors", [])

        if status == "critical":
            recommendations.append({
                "action": "Immediate executive intervention required",
                "priority": "critical",
                "owner": "VP Customer Success",
                "timeline": "Within 24 hours"
            })
            recommendations.append({
                "action": "Schedule emergency call to understand issues",
                "priority": "critical",
                "owner": "CSM",
                "timeline": "Within 24 hours"
            })

        elif status == "at_risk":
            recommendations.append({
                "action": "CSM to conduct urgent check-in call",
                "priority": "high",
                "owner": "CSM",
                "timeline": "Within 48 hours"
            })
            recommendations.append({
                "action": "Review support ticket history for systemic issues",
                "priority": "high",
                "owner": "CSM + Support",
                "timeline": "Within 1 week"
            })

        elif status == "needs_attention":
            recommendations.append({
                "action": "Schedule quarterly business review (QBR)",
                "priority": "medium",
                "owner": "CSM",
                "timeline": "Within 2 weeks"
            })

        # Specific recommendations based on risk factors
        for risk in risk_factors:
            if "Low product usage" in risk["factor"]:
                recommendations.append({
                    "action": "Launch feature adoption campaign",
                    "priority": "high",
                    "owner": "CSM",
                    "timeline": "This week"
                })

            if "High support ticket" in risk["factor"]:
                recommendations.append({
                    "action": "Analyze support tickets for patterns",
                    "priority": "high",
                    "owner": "Support + Product",
                    "timeline": "Within 3 days"
                })

        return recommendations

    def _format_health_report(
        self,
        health_analysis: Dict[str, Any],
        recommendations: List[Dict[str, str]]
    ) -> str:
        """Format health score report."""
        score = health_analysis["total_score"]
        status = health_analysis["health_status"]
        breakdown = health_analysis["score_breakdown"]
        trend = health_analysis["trend"]

        # Status emoji
        status_emoji = {
            "thriving": "????",
            "healthy": "???",
            "needs_attention": "??????",
            "at_risk": "????",
            "critical": "????"
        }

        report = f"""**{status_emoji.get(status, '????')} Customer Health Score: {score}/100**

**Status:** {status.replace('_', ' ').title()}
**Trend:** {trend.capitalize()} {self._trend_arrow(trend)}

**Score Breakdown:**
"""

        for component, component_score in breakdown.items():
            max_score = self.WEIGHTS.get(component.split('_')[0], 10)
            percentage = int((component_score / max_score) * 100)
            bar = self._generate_bar(percentage)
            report += f"- {component.replace('_', ' ').title()}: {component_score}/{max_score} {bar}\n"

        # Risk factors
        if health_analysis.get("risk_factors"):
            report += "\n**?????? Risk Factors:**\n"
            for risk in health_analysis["risk_factors"][:3]:
                report += f"- **{risk['factor']}** ({risk['severity']} severity)\n"
                report += f"  {risk['description']}\n"

        # Positive signals
        if health_analysis.get("positive_signals"):
            report += "\n**??? Positive Signals:**\n"
            for signal in health_analysis["positive_signals"][:3]:
                report += f"- {signal}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommended Actions:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"{i}. **{rec['action']}**\n"
                report += f"   - Priority: {rec['priority'].upper()}\n"
                report += f"   - Owner: {rec['owner']}\n"
                report += f"   - Timeline: {rec['timeline']}\n"

        return report

    def _trend_arrow(self, trend: str) -> str:
        """Get arrow for trend."""
        arrows = {
            "improving": "????",
            "stable": "??????",
            "declining": "????",
            "new": "????"
        }
        return arrows.get(trend, "")

    def _generate_bar(self, percentage: int) -> str:
        """Generate visual progress bar."""
        filled = int(percentage / 10)
        empty = 10 - filled
        return "???" * filled + "???" * empty + f" {percentage}%"


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Customer Health Score Agent (TASK-2011)")
        print("=" * 70)

        agent = HealthScoreAgent()

        # Test 1: Healthy customer
        print("\n\nTest 1: Healthy Customer")
        print("-" * 70)

        state1 = create_initial_state(
            "Calculate health score for this customer",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {
                    "plan": "premium",
                    "previous_health_score": 80
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "daily_active_users": 12,
                "total_users": 15,
                "features_used": 8,
                "automation_rules_active": 5
            },
            "engagement_data": {
                "nps_score": 9,
                "support_tickets_last_30d": 1,
                "feature_requests": 3,
                "last_login": datetime.now(UTC).isoformat(),
                "qbr_attended_last_quarter": True
            },
            "business_data": {
                "payment_status": "current",
                "contract_value": 45000
            }
        }

        result1 = await agent.process(state1)

        print(f"Health Score: {result1['health_score']}")
        print(f"Health Status: {result1['health_status']}")
        print(f"Trend: {result1['health_trend']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: At-risk customer
        print("\n\n" + "=" * 70)
        print("Test 2: At-Risk Customer")
        print("-" * 70)

        state2 = create_initial_state(
            "Calculate health score",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {
                    "plan": "basic",
                    "previous_health_score": 70
                }
            }
        )
        state2["entities"] = {
            "usage_data": {
                "daily_active_users": 2,
                "total_users": 10,
                "features_used": 2,
                "automation_rules_active": 0
            },
            "engagement_data": {
                "nps_score": 4,
                "support_tickets_last_30d": 12,
                "feature_requests": 0,
                "last_login": (datetime.now(UTC) - timedelta(days=10)).isoformat(),
                "qbr_attended_last_quarter": False
            },
            "business_data": {
                "payment_status": "past_due_7"
            }
        }

        result2 = await agent.process(state2)

        print(f"Health Score: {result2['health_score']}")
        print(f"Health Status: {result2['health_status']}")
        print(f"Trend: {result2['health_trend']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
