"""
Customer Insights Agent - TASK-2068

Generates actionable insights about customer accounts from data analysis,
identifying patterns, trends, and opportunities for improved customer success.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("customer_insights", tier="revenue", category="customer_success")
class CustomerInsightsAgent(BaseAgent):
    """
    Customer Insights Agent.

    Generates actionable insights by:
    - Analyzing usage patterns and trends
    - Identifying customer behavior patterns
    - Detecting anomalies and risks early
    - Uncovering expansion opportunities
    - Benchmarking against similar customers
    - Predicting customer needs and challenges
    """

    # Insight categories
    INSIGHT_CATEGORIES = {
        "usage_pattern": "Patterns in product usage and adoption",
        "risk_indicator": "Early warning signs of potential issues",
        "opportunity": "Expansion and growth opportunities",
        "behavior_trend": "Changes in customer behavior over time",
        "performance_gap": "Areas where customer is underperforming",
        "success_factor": "Key drivers of customer success"
    }

    # Insight priority levels
    PRIORITY_LEVELS = {
        "critical": {"action_required": "immediate", "impact": "high"},
        "high": {"action_required": "this_week", "impact": "medium_high"},
        "medium": {"action_required": "this_month", "impact": "medium"},
        "low": {"action_required": "monitor", "impact": "low"}
    }

    # Analysis dimensions
    ANALYSIS_DIMENSIONS = [
        "usage_trends",
        "engagement_patterns",
        "health_indicators",
        "value_realization",
        "relationship_strength",
        "expansion_signals"
    ]

    def __init__(self):
        config = AgentConfig(
            name="customer_insights",
            type=AgentType.SPECIALIST,
            temperature=0.4,
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
        Generate customer insights from data.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with actionable insights
        """
        self.logger.info("customer_insights_generation_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("entities", {}).get("usage_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        business_data = state.get("entities", {}).get("business_data", {})
        health_data = state.get("entities", {}).get("health_data", {})
        historical_data = state.get("entities", {}).get("historical_data", {})

        self.logger.debug(
            "customer_insights_details",
            customer_id=customer_id,
            tier=customer_metadata.get("tier", "standard")
        )

        # Generate insights across dimensions
        insights = self._generate_comprehensive_insights(
            usage_data,
            engagement_data,
            business_data,
            health_data,
            historical_data,
            customer_metadata
        )

        # Analyze trends
        trend_analysis = self._analyze_trends(
            usage_data,
            engagement_data,
            historical_data
        )

        # Identify anomalies
        anomalies = self._detect_anomalies(
            usage_data,
            engagement_data,
            historical_data
        )

        # Generate predictions
        predictions = self._generate_predictions(
            insights,
            trend_analysis,
            customer_metadata
        )

        # Create benchmarking comparison
        benchmarking = self._create_benchmarking_analysis(
            usage_data,
            engagement_data,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_insight_recommendations(
            insights,
            anomalies,
            predictions
        )

        # Create action plan
        action_plan = self._create_insights_action_plan(
            insights,
            predictions,
            anomalies
        )

        # Format response
        response = self._format_insights_report(
            insights,
            trend_analysis,
            anomalies,
            predictions,
            benchmarking,
            recommendations,
            action_plan
        )

        state["agent_response"] = response
        state["total_insights"] = len(insights)
        state["critical_insights"] = len([i for i in insights if i["priority"] == "critical"])
        state["anomalies_detected"] = len(anomalies)
        state["trend_direction"] = trend_analysis.get("overall_trend", "stable")
        state["insights"] = insights
        state["response_confidence"] = 0.89
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "customer_insights_generation_completed",
            customer_id=customer_id,
            total_insights=len(insights),
            critical_insights=len([i for i in insights if i["priority"] == "critical"])
        )

        return state

    def _generate_comprehensive_insights(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        business_data: Dict[str, Any],
        health_data: Dict[str, Any],
        historical_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate comprehensive insights across all dimensions.

        Args:
            usage_data: Product usage metrics
            engagement_data: Customer engagement metrics
            business_data: Business and contract data
            health_data: Customer health metrics
            historical_data: Historical trend data
            customer_metadata: Customer profile data

        Returns:
            List of actionable insights
        """
        insights = []

        # Usage pattern insights
        insights.extend(self._analyze_usage_patterns(usage_data, historical_data))

        # Engagement insights
        insights.extend(self._analyze_engagement_patterns(engagement_data, historical_data))

        # Risk insights
        insights.extend(self._analyze_risk_indicators(health_data, usage_data, engagement_data))

        # Opportunity insights
        insights.extend(self._analyze_opportunities(usage_data, business_data, customer_metadata))

        # Value realization insights
        insights.extend(self._analyze_value_realization(usage_data, business_data))

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return insights[:10]  # Top 10 insights

    def _analyze_usage_patterns(
        self,
        usage_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze usage patterns for insights."""
        insights = []

        # Check adoption rate
        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        adoption_rate = (active_users / total_users * 100) if total_users > 0 else 0

        if adoption_rate < 50:
            insights.append({
                "category": "usage_pattern",
                "insight": f"Low user adoption at {int(adoption_rate)}% - significant unused capacity",
                "priority": "high",
                "impact": "Underutilization reduces perceived value and retention risk",
                "recommendation": "Launch user activation campaign targeting inactive licenses"
            })
        elif adoption_rate > 90:
            insights.append({
                "category": "opportunity",
                "insight": f"Very high adoption at {int(adoption_rate)}% - approaching capacity",
                "priority": "medium",
                "impact": "Limited headroom for growth, potential expansion opportunity",
                "recommendation": "Proactively discuss license expansion to support growth"
            })

        # Check feature usage
        features_used = len(usage_data.get("features_used", []))
        total_features = usage_data.get("total_features_available", 10)
        feature_adoption = (features_used / total_features * 100) if total_features > 0 else 0

        if feature_adoption < 40:
            insights.append({
                "category": "usage_pattern",
                "insight": f"Limited feature adoption ({int(feature_adoption)}%) - only using basic capabilities",
                "priority": "medium",
                "impact": "Not realizing full platform value, higher churn risk",
                "recommendation": "Create feature adoption roadmap and training plan"
            })

        # Check automation usage
        automation_rules = usage_data.get("automation_rules_active", 0)
        if automation_rules == 0 and features_used >= 5:
            insights.append({
                "category": "opportunity",
                "insight": "No automation workflows configured despite active platform use",
                "priority": "medium",
                "impact": "Missing efficiency gains and time savings opportunities",
                "recommendation": "Demonstrate automation capabilities and quick-win use cases"
            })

        return insights

    def _analyze_engagement_patterns(
        self,
        engagement_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze engagement patterns for insights."""
        insights = []

        # NPS analysis
        nps = engagement_data.get("nps_score", 5)
        if nps <= 6:
            insights.append({
                "category": "risk_indicator",
                "insight": f"Low NPS score of {nps}/10 indicates dissatisfaction",
                "priority": "critical",
                "impact": "High churn risk and potential negative word-of-mouth",
                "recommendation": "Schedule urgent feedback session to understand concerns"
            })
        elif nps >= 9:
            insights.append({
                "category": "success_factor",
                "insight": f"Excellent NPS score of {nps}/10 - strong satisfaction",
                "priority": "low",
                "impact": "Advocacy opportunity and low churn risk",
                "recommendation": "Request testimonial, case study, or referral"
            })

        # Support ticket analysis
        tickets = engagement_data.get("support_tickets_last_30d", 0)
        if tickets > 10:
            insights.append({
                "category": "risk_indicator",
                "insight": f"High support volume ({tickets} tickets in 30 days) suggests product issues",
                "priority": "high",
                "impact": "User frustration, productivity impact, satisfaction decline",
                "recommendation": "Analyze ticket patterns and provide proactive resolution"
            })

        # Engagement trend
        touchpoints = engagement_data.get("touchpoints_last_30d", 0)
        previous_touchpoints = historical_data.get("touchpoints_previous_30d", touchpoints)

        if touchpoints < previous_touchpoints * 0.5 and previous_touchpoints > 5:
            insights.append({
                "category": "behavior_trend",
                "insight": f"Significant drop in engagement ({touchpoints} vs {previous_touchpoints} touchpoints)",
                "priority": "high",
                "impact": "Declining relationship strength and potential disengagement",
                "recommendation": "Proactively reach out to re-engage and understand status"
            })

        return insights

    def _analyze_risk_indicators(
        self,
        health_data: Dict[str, Any],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze risk indicators for insights."""
        insights = []

        # Overall health score
        health_score = health_data.get("health_score", 50)
        if health_score < 40:
            insights.append({
                "category": "risk_indicator",
                "insight": f"Critical health score of {health_score}/100 - account at severe risk",
                "priority": "critical",
                "impact": "Imminent churn risk requiring immediate intervention",
                "recommendation": "Escalate to executive team for save plan"
            })

        # Login recency
        last_login = engagement_data.get("last_login_date")
        if last_login:
            try:
                last_login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                days_since_login = (datetime.now(UTC) - last_login_date).days
                if days_since_login > 14:
                    insights.append({
                        "category": "risk_indicator",
                        "insight": f"No login activity for {days_since_login} days - potential abandonment",
                        "priority": "critical" if days_since_login > 30 else "high",
                        "impact": "Product not being used, value not realized",
                        "recommendation": "Urgent outreach to understand situation and re-engage"
                    })
            except:
                pass

        return insights

    def _analyze_opportunities(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze expansion and growth opportunities."""
        insights = []

        # License expansion opportunity
        active_users = usage_data.get("active_users", 0)
        contracted_users = business_data.get("contracted_users", 10)

        if active_users > contracted_users * 0.9:
            insights.append({
                "category": "opportunity",
                "insight": f"Using {active_users}/{contracted_users} licenses (90%+) - expansion opportunity",
                "priority": "high",
                "impact": "Revenue expansion, remove adoption blocker",
                "recommendation": "Propose 25-50% license expansion in renewal discussion"
            })

        # Feature tier upgrade opportunity
        tier = customer_metadata.get("tier", "standard")
        features_used = len(usage_data.get("features_used", []))

        if tier in ["standard", "growth"] and features_used >= 6:
            insights.append({
                "category": "opportunity",
                "insight": f"Heavy feature usage on {tier} tier - potential upgrade candidate",
                "priority": "medium",
                "impact": "Revenue expansion, unlock advanced capabilities",
                "recommendation": "Demonstrate premium features and upgrade value proposition"
            })

        return insights

    def _analyze_value_realization(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze value realization insights."""
        insights = []

        # ROI analysis
        automation_rules = usage_data.get("automation_rules_active", 0)
        time_saved_hours = automation_rules * 40  # Estimate
        contract_value = business_data.get("contract_value", 50000)
        estimated_value = time_saved_hours * 50

        if estimated_value < contract_value * 0.5:
            insights.append({
                "category": "performance_gap",
                "insight": f"Value realization below 50% of contract value - ROI gap",
                "priority": "high",
                "impact": "Renewal risk due to unclear value proposition",
                "recommendation": "Conduct value assessment and create ROI improvement plan"
            })
        elif estimated_value > contract_value * 2:
            insights.append({
                "category": "success_factor",
                "insight": f"Strong value realization at 2x+ ROI - success story candidate",
                "priority": "low",
                "impact": "High retention likelihood, advocacy opportunity",
                "recommendation": "Document success metrics for case study and renewal"
            })

        return insights

    def _analyze_trends(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze trends over time."""
        # Usage trend
        current_users = usage_data.get("active_users", 0)
        previous_users = historical_data.get("previous_month_active_users", current_users)

        usage_change = ((current_users - previous_users) / previous_users * 100) if previous_users > 0 else 0
        usage_trend = "increasing" if usage_change > 10 else "stable" if usage_change >= -5 else "declining"

        # Engagement trend
        current_nps = engagement_data.get("nps_score", 5)
        previous_nps = historical_data.get("previous_quarter_nps", current_nps)

        nps_change = current_nps - previous_nps
        engagement_trend = "improving" if nps_change > 1 else "stable" if nps_change >= -1 else "declining"

        # Overall trend
        if usage_trend == "increasing" and engagement_trend == "improving":
            overall_trend = "positive"
        elif usage_trend == "declining" or engagement_trend == "declining":
            overall_trend = "negative"
        else:
            overall_trend = "stable"

        return {
            "overall_trend": overall_trend,
            "usage_trend": usage_trend,
            "usage_change_pct": round(usage_change, 1),
            "engagement_trend": engagement_trend,
            "nps_change": nps_change
        }

    def _detect_anomalies(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detect anomalies in customer data."""
        anomalies = []

        # Sudden drop in usage
        current_users = usage_data.get("active_users", 0)
        previous_users = historical_data.get("previous_month_active_users", current_users)

        if previous_users > 0 and current_users < previous_users * 0.5:
            anomalies.append({
                "type": "usage_drop",
                "description": f"Sudden 50%+ drop in active users ({previous_users} ??? {current_users})",
                "severity": "critical",
                "possible_cause": "Organizational change, product issue, or migration away"
            })

        # Spike in support tickets
        current_tickets = engagement_data.get("support_tickets_last_30d", 0)
        previous_tickets = historical_data.get("support_tickets_previous_30d", current_tickets)

        if previous_tickets < 5 and current_tickets > previous_tickets * 3:
            anomalies.append({
                "type": "support_spike",
                "description": f"Unusual spike in support tickets ({previous_tickets} ??? {current_tickets})",
                "severity": "high",
                "possible_cause": "Product bug, feature confusion, or new rollout issues"
            })

        return anomalies

    def _generate_predictions(
        self,
        insights: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate predictions based on insights and trends."""
        predictions = []

        # Churn prediction
        critical_insights = [i for i in insights if i["priority"] == "critical"]
        if critical_insights:
            predictions.append({
                "prediction": "High churn risk in next 90 days",
                "confidence": "high",
                "basis": f"{len(critical_insights)} critical risk indicators detected",
                "mitigation": "Immediate executive intervention and save plan required"
            })

        # Growth prediction
        overall_trend = trend_analysis["overall_trend"]
        if overall_trend == "positive":
            predictions.append({
                "prediction": "Likely expansion opportunity within 6 months",
                "confidence": "medium",
                "basis": "Positive usage and engagement trends",
                "mitigation": "Proactively present expansion options"
            })

        # Advocacy prediction
        advocacy_insights = [i for i in insights if i["category"] == "success_factor"]
        if advocacy_insights:
            predictions.append({
                "prediction": "Strong advocacy candidate",
                "confidence": "medium",
                "basis": "Multiple success factors present",
                "mitigation": "Request testimonial or case study"
            })

        return predictions[:4]

    def _create_benchmarking_analysis(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create benchmarking comparison."""
        tier = customer_metadata.get("tier", "standard")

        # Simplified benchmarks - would come from analytics in production
        benchmarks = {
            "enterprise": {"adoption": 85, "features": 9, "nps": 8, "health": 82},
            "premium": {"adoption": 75, "features": 7, "nps": 7, "health": 75},
            "growth": {"adoption": 65, "features": 5, "nps": 7, "health": 68},
            "standard": {"adoption": 55, "features": 4, "nps": 6, "health": 60}
        }

        benchmark = benchmarks.get(tier, benchmarks["standard"])

        # Calculate actual metrics
        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        actual_adoption = int((active_users / total_users * 100)) if total_users > 0 else 0

        actual_features = len(usage_data.get("features_used", []))
        actual_nps = engagement_data.get("nps_score", 0)

        return {
            "tier": tier,
            "adoption": {"actual": actual_adoption, "benchmark": benchmark["adoption"]},
            "features": {"actual": actual_features, "benchmark": benchmark["features"]},
            "nps": {"actual": actual_nps, "benchmark": benchmark["nps"]},
            "performance_vs_benchmark": "above" if actual_adoption > benchmark["adoption"] else "below"
        }

    def _generate_insight_recommendations(
        self,
        insights: List[Dict[str, Any]],
        anomalies: List[Dict[str, str]],
        predictions: List[Dict[str, str]]
    ) -> List[str]:
        """Generate recommendations based on insights."""
        recommendations = []

        # Address critical insights
        critical = [i for i in insights if i["priority"] == "critical"]
        if critical:
            recommendations.append("Address critical risk indicators immediately - account requires urgent attention")

        # Address anomalies
        if anomalies:
            recommendations.append(f"Investigate {len(anomalies)} detected anomalies to understand root causes")

        # Opportunity insights
        opportunities = [i for i in insights if i["category"] == "opportunity"]
        if opportunities:
            recommendations.append(f"Pursue {len(opportunities)} identified expansion opportunities")

        # General
        recommendations.append("Review insights with customer in next touchpoint")

        return recommendations[:5]

    def _create_insights_action_plan(
        self,
        insights: List[Dict[str, Any]],
        predictions: List[Dict[str, str]],
        anomalies: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Create action plan based on insights."""
        actions = []

        # Critical insights
        for insight in insights:
            if insight["priority"] == "critical":
                actions.append({
                    "action": insight["recommendation"],
                    "owner": "CSM + CS Manager",
                    "timeline": "Immediate",
                    "priority": "critical"
                })
                break  # One critical action at a time

        # High priority insights
        high_priority = [i for i in insights if i["priority"] == "high"]
        if high_priority and len(actions) < 3:
            actions.append({
                "action": high_priority[0]["recommendation"],
                "owner": "CSM",
                "timeline": "This week",
                "priority": "high"
            })

        # Anomaly investigation
        if anomalies:
            actions.append({
                "action": f"Investigate anomaly: {anomalies[0]['description']}",
                "owner": "CSM + Support",
                "timeline": "Within 48 hours",
                "priority": "high"
            })

        return actions[:5]

    def _format_insights_report(
        self,
        insights: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any],
        anomalies: List[Dict[str, str]],
        predictions: List[Dict[str, str]],
        benchmarking: Dict[str, Any],
        recommendations: List[str],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format customer insights report."""
        trend = trend_analysis["overall_trend"]

        trend_emoji = {
            "positive": "????",
            "stable": "??????",
            "negative": "????"
        }

        report = f"""**???? Customer Insights Analysis**

**Overall Trend:** {trend.title()} {trend_emoji.get(trend, '???')}
**Total Insights:** {len(insights)}
**Critical Issues:** {len([i for i in insights if i['priority'] == 'critical'])}
**Anomalies Detected:** {len(anomalies)}

**???? Trend Analysis:**
- Usage: {trend_analysis['usage_trend'].title()} ({trend_analysis['usage_change_pct']:+.1f}%)
- Engagement: {trend_analysis['engagement_trend'].title()} (NPS {trend_analysis['nps_change']:+d})
"""

        # Key insights
        report += "\n**???? Key Insights:**\n"
        for i, insight in enumerate(insights[:5], 1):
            priority_icon = "????" if insight["priority"] == "critical" else "????" if insight["priority"] == "high" else "????"
            category_icon = "??????" if insight["category"] == "risk_indicator" else "????" if insight["category"] == "opportunity" else "????"
            report += f"{i}. **{insight['insight']}** {priority_icon} {category_icon}\n"
            report += f"   - Impact: {insight['impact']}\n"
            report += f"   - Recommendation: {insight['recommendation']}\n"

        # Anomalies
        if anomalies:
            report += "\n**???? Anomalies Detected:**\n"
            for i, anomaly in enumerate(anomalies[:3], 1):
                severity_icon = "????" if anomaly["severity"] == "critical" else "????"
                report += f"{i}. **{anomaly['description']}** {severity_icon}\n"
                report += f"   - Possible Cause: {anomaly['possible_cause']}\n"

        # Predictions
        if predictions:
            report += "\n**???? Predictions:**\n"
            for i, pred in enumerate(predictions[:3], 1):
                report += f"{i}. {pred['prediction']} (Confidence: {pred['confidence']})\n"
                report += f"   - Basis: {pred['basis']}\n"

        # Benchmarking
        report += "\n**???? vs. Benchmark:**\n"
        report += f"- Adoption: {benchmarking['adoption']['actual']}% vs {benchmarking['adoption']['benchmark']}% benchmark\n"
        report += f"- Features: {benchmarking['features']['actual']} vs {benchmarking['features']['benchmark']} benchmark\n"
        report += f"- NPS: {benchmarking['nps']['actual']}/10 vs {benchmarking['nps']['benchmark']}/10 benchmark\n"
        report += f"- Performance: {benchmarking['performance_vs_benchmark'].title()} average for {benchmarking['tier']} tier\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommendations:**\n"
            for i, rec in enumerate(recommendations[:4], 1):
                report += f"{i}. {rec}\n"

        # Action plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Customer Insights Agent (TASK-2068)")
        print("=" * 70)

        agent = CustomerInsightsAgent()

        # Test 1: Healthy customer with opportunities
        print("\n\nTest 1: Healthy Customer with Opportunities")
        print("-" * 70)

        state1 = create_initial_state(
            "Generate customer insights",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "industry": "technology"
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "active_users": 95,
                "total_users": 100,
                "features_used": ["reporting", "analytics", "automation", "api", "dashboards", "integrations", "workflows"],
                "total_features_available": 10,
                "automation_rules_active": 8
            },
            "engagement_data": {
                "nps_score": 9,
                "support_tickets_last_30d": 3,
                "touchpoints_last_30d": 12,
                "last_login_date": (datetime.now(UTC) - timedelta(days=1)).isoformat()
            },
            "business_data": {
                "contract_value": 120000,
                "contracted_users": 100
            },
            "health_data": {
                "health_score": 92
            },
            "historical_data": {
                "previous_month_active_users": 85,
                "previous_quarter_nps": 8,
                "touchpoints_previous_30d": 10,
                "support_tickets_previous_30d": 2
            }
        }

        result1 = await agent.process(state1)

        print(f"Total Insights: {result1['total_insights']}")
        print(f"Critical Insights: {result1['critical_insights']}")
        print(f"Anomalies: {result1['anomalies_detected']}")
        print(f"Trend: {result1['trend_direction']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: At-risk customer
        print("\n\n" + "=" * 70)
        print("Test 2: At-Risk Customer")
        print("-" * 70)

        state2 = create_initial_state(
            "Analyze customer risks",
            context={
                "customer_id": "cust_growth_002",
                "customer_metadata": {
                    "tier": "growth"
                }
            }
        )
        state2["entities"] = {
            "usage_data": {
                "active_users": 10,
                "total_users": 50,
                "features_used": ["reporting"],
                "total_features_available": 8,
                "automation_rules_active": 0
            },
            "engagement_data": {
                "nps_score": 4,
                "support_tickets_last_30d": 15,
                "touchpoints_last_30d": 2,
                "last_login_date": (datetime.now(UTC) - timedelta(days=25)).isoformat()
            },
            "business_data": {
                "contract_value": 35000,
                "contracted_users": 50
            },
            "health_data": {
                "health_score": 35
            },
            "historical_data": {
                "previous_month_active_users": 25,
                "previous_quarter_nps": 6,
                "touchpoints_previous_30d": 8,
                "support_tickets_previous_30d": 3
            }
        }

        result2 = await agent.process(state2)

        print(f"Total Insights: {result2['total_insights']}")
        print(f"Critical Insights: {result2['critical_insights']}")
        print(f"Trend: {result2['trend_direction']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:700]}...")

    asyncio.run(test())
