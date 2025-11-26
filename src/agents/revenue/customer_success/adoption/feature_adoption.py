"""
Feature Adoption Agent - TASK-2031

Identifies unused features, recommends relevant features, educates users on capabilities,
and tracks ROI from feature adoption to drive product stickiness.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("feature_adoption", tier="revenue", category="customer_success")
class FeatureAdoptionAgent(BaseAgent):
    """
    Feature Adoption Agent.

    Drives feature adoption by:
    - Identifying unused or underutilized features
    - Recommending relevant features based on customer profile
    - Creating personalized feature adoption campaigns
    - Tracking ROI from increased feature usage
    - Educating users on advanced capabilities
    - Measuring feature stickiness and value realization
    """

    # Feature categories and value tiers
    FEATURE_TIERS = {
        "core": {"value_score": 100, "adoption_priority": "critical"},
        "advanced": {"value_score": 75, "adoption_priority": "high"},
        "premium": {"value_score": 50, "adoption_priority": "medium"},
        "specialized": {"value_score": 25, "adoption_priority": "low"},
    }

    # Adoption stages
    ADOPTION_STAGES = {
        "not_adopted": 0,
        "aware": 25,
        "trial": 50,
        "regular_use": 75,
        "power_use": 100,
    }

    def __init__(self):
        config = AgentConfig(
            name="feature_adoption",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=800,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="customer_success",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze feature adoption and generate recommendations.

        Args:
            state: Current agent state with customer usage data

        Returns:
            Updated state with adoption analysis and recommendations
        """
        self.logger.info("feature_adoption_analysis_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        usage_data = state.get("entities", {}).get("usage_data", {})
        customer_metadata = state.get("customer_metadata", {})
        available_features = state.get("entities", {}).get("available_features", [])

        self.logger.debug(
            "feature_adoption_details",
            customer_id=customer_id,
            features_available=len(available_features),
            features_used=len(usage_data.get("features_used", [])),
        )

        # Analyze current adoption
        adoption_analysis = self._analyze_feature_adoption(
            usage_data, customer_metadata, available_features
        )

        # Generate feature recommendations
        recommendations = self._generate_feature_recommendations(
            adoption_analysis, customer_metadata
        )

        # Calculate ROI opportunity
        roi_projection = self._calculate_roi_opportunity(
            adoption_analysis, recommendations, customer_metadata
        )

        # Create adoption campaign
        adoption_campaign = self._create_adoption_campaign(
            adoption_analysis, recommendations, customer_metadata
        )

        # Format response
        response = self._format_adoption_report(
            adoption_analysis, recommendations, roi_projection, adoption_campaign
        )

        state["agent_response"] = response
        state["adoption_score"] = adoption_analysis["overall_adoption_score"]
        state["unused_features_count"] = len(adoption_analysis["unused_features"])
        state["recommended_features"] = [r["feature"] for r in recommendations[:5]]
        state["roi_opportunity"] = roi_projection["total_value_opportunity"]
        state["adoption_analysis"] = adoption_analysis
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "feature_adoption_analysis_completed",
            customer_id=customer_id,
            adoption_score=adoption_analysis["overall_adoption_score"],
            unused_features=len(adoption_analysis["unused_features"]),
            roi_opportunity=roi_projection["total_value_opportunity"],
        )

        return state

    def _analyze_feature_adoption(
        self,
        usage_data: dict[str, Any],
        customer_metadata: dict[str, Any],
        available_features: list[str],
    ) -> dict[str, Any]:
        """
        Analyze current feature adoption patterns.

        Args:
            usage_data: Customer usage metrics
            customer_metadata: Customer profile data
            available_features: List of features available to customer

        Returns:
            Comprehensive adoption analysis
        """
        features_used = usage_data.get("features_used", [])
        feature_usage_frequency = usage_data.get("feature_usage_frequency", {})

        # Identify unused features
        unused_features = [f for f in available_features if f not in features_used]

        # Categorize features by adoption stage
        adoption_by_stage = {
            "not_adopted": [],
            "aware": [],
            "trial": [],
            "regular_use": [],
            "power_use": [],
        }

        for feature in available_features:
            stage = self._determine_adoption_stage(feature, feature_usage_frequency)
            adoption_by_stage[stage].append(feature)

        # Calculate overall adoption score
        total_features = len(available_features)
        if total_features == 0:
            overall_adoption_score = 0
        else:
            weighted_score = sum(
                len(features) * self.ADOPTION_STAGES[stage]
                for stage, features in adoption_by_stage.items()
            )
            overall_adoption_score = int(weighted_score / total_features)

        # Identify high-value unused features
        high_value_unused = self._identify_high_value_unused(unused_features, customer_metadata)

        # Calculate adoption velocity
        adoption_velocity = self._calculate_adoption_velocity(usage_data)

        # Identify adoption patterns
        adoption_patterns = self._identify_adoption_patterns(
            feature_usage_frequency, customer_metadata
        )

        return {
            "overall_adoption_score": overall_adoption_score,
            "total_features_available": total_features,
            "features_adopted": len(features_used),
            "adoption_percentage": int(len(features_used) / total_features * 100)
            if total_features > 0
            else 0,
            "unused_features": unused_features,
            "unused_count": len(unused_features),
            "adoption_by_stage": adoption_by_stage,
            "high_value_unused": high_value_unused,
            "adoption_velocity": adoption_velocity,
            "adoption_patterns": adoption_patterns,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _determine_adoption_stage(self, feature: str, usage_frequency: dict[str, int]) -> str:
        """Determine adoption stage for a feature."""
        frequency = usage_frequency.get(feature, 0)

        if frequency == 0:
            return "not_adopted"
        elif frequency < 5:
            return "aware"
        elif frequency < 15:
            return "trial"
        elif frequency < 50:
            return "regular_use"
        else:
            return "power_use"

    def _identify_high_value_unused(
        self, unused_features: list[str], customer_metadata: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Identify high-value features that are unused."""
        high_value = []

        for feature in unused_features:
            tier = self._get_feature_tier(feature, customer_metadata)
            value_score = self.FEATURE_TIERS.get(tier, {}).get("value_score", 0)

            if value_score >= 50:  # Advanced or Core features
                high_value.append(
                    {
                        "feature": feature,
                        "tier": tier,
                        "value_score": value_score,
                        "potential_impact": self._estimate_feature_impact(
                            feature, customer_metadata
                        ),
                    }
                )

        # Sort by value score
        high_value.sort(key=lambda x: x["value_score"], reverse=True)
        return high_value[:10]

    def _get_feature_tier(self, feature: str, customer_metadata: dict[str, Any]) -> str:
        """Determine feature tier based on feature name and customer profile."""
        # Simplified logic - in production, this would use a feature catalog
        feature_lower = feature.lower()

        if any(word in feature_lower for word in ["basic", "core", "essential"]):
            return "core"
        elif any(word in feature_lower for word in ["advanced", "analytics", "automation"]):
            return "advanced"
        elif any(word in feature_lower for word in ["premium", "enterprise", "api"]):
            return "premium"
        else:
            return "specialized"

    def _estimate_feature_impact(self, feature: str, customer_metadata: dict[str, Any]) -> str:
        """Estimate business impact of adopting a feature."""
        tier = self._get_feature_tier(feature, customer_metadata)

        impact_map = {
            "core": "High - Critical for base value realization",
            "advanced": "High - Significant efficiency gains",
            "premium": "Medium - Enhanced capabilities",
            "specialized": "Low - Niche use cases",
        }

        return impact_map.get(tier, "Medium - Standard value")

    def _calculate_adoption_velocity(self, usage_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate rate of feature adoption."""
        current_month_features = len(usage_data.get("features_used", []))
        previous_month_features = usage_data.get(
            "previous_month_features_count", current_month_features
        )

        if previous_month_features > 0:
            velocity_pct = (
                (current_month_features - previous_month_features) / previous_month_features
            ) * 100
        else:
            velocity_pct = 0

        trend = (
            "accelerating" if velocity_pct > 10 else "steady" if velocity_pct >= -5 else "declining"
        )

        return {
            "velocity_percentage": round(velocity_pct, 1),
            "trend": trend,
            "new_features_adopted": max(0, current_month_features - previous_month_features),
        }

    def _identify_adoption_patterns(
        self, usage_frequency: dict[str, int], customer_metadata: dict[str, Any]
    ) -> list[str]:
        """Identify patterns in feature adoption."""
        patterns = []

        if not usage_frequency:
            patterns.append("No usage data available")
            return patterns

        # Check for shallow adoption (many features tried, few used regularly)
        trial_features = sum(1 for freq in usage_frequency.values() if 5 <= freq < 15)
        if trial_features > 5:
            patterns.append("Shallow adoption - users trying features but not adopting regularly")

        # Check for power user behavior
        power_features = sum(1 for freq in usage_frequency.values() if freq >= 50)
        if power_features >= 3:
            patterns.append("Power user behavior detected - good depth in feature usage")

        # Check for stagnation
        low_usage = sum(1 for freq in usage_frequency.values() if freq < 10)
        if low_usage > len(usage_frequency) * 0.7:
            patterns.append("Adoption stagnation - most features have low usage")

        if not patterns:
            patterns.append("Healthy adoption pattern")

        return patterns

    def _generate_feature_recommendations(
        self, adoption_analysis: dict[str, Any], customer_metadata: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate personalized feature recommendations."""
        recommendations = []

        # Recommend high-value unused features first
        for feature_data in adoption_analysis["high_value_unused"][:5]:
            recommendations.append(
                {
                    "feature": feature_data["feature"],
                    "priority": self.FEATURE_TIERS.get(feature_data["tier"], {}).get(
                        "adoption_priority", "medium"
                    ),
                    "value_score": feature_data["value_score"],
                    "reason": f"{feature_data['potential_impact']}",
                    "suggested_use_case": self._suggest_use_case(
                        feature_data["feature"], customer_metadata
                    ),
                    "adoption_effort": self._estimate_adoption_effort(feature_data["tier"]),
                }
            )

        # Add recommendations for underutilized features
        for feature in adoption_analysis["adoption_by_stage"]["trial"][:3]:
            recommendations.append(
                {
                    "feature": feature,
                    "priority": "medium",
                    "value_score": 40,
                    "reason": "Currently in trial - help transition to regular use",
                    "suggested_use_case": self._suggest_use_case(feature, customer_metadata),
                    "adoption_effort": "low",
                }
            )

        # Sort by priority and value
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda x: (priority_order.get(x["priority"], 3), -x["value_score"])
        )

        return recommendations[:8]

    def _suggest_use_case(self, feature: str, customer_metadata: dict[str, Any]) -> str:
        """Suggest specific use case for a feature."""
        # Simplified - in production, this would use ML/knowledge base
        industry = customer_metadata.get("industry", "general")

        use_cases = {
            "analytics": f"Track key {industry} metrics and generate insights",
            "automation": f"Automate repetitive {industry} workflows",
            "reporting": f"Create custom {industry} reports for stakeholders",
            "collaboration": f"Enable team collaboration on {industry} projects",
            "integration": f"Connect with other {industry} tools",
        }

        feature_lower = feature.lower()
        for key, use_case in use_cases.items():
            if key in feature_lower:
                return use_case

        return f"Streamline your {industry} operations"

    def _estimate_adoption_effort(self, tier: str) -> str:
        """Estimate effort required to adopt a feature."""
        effort_map = {
            "core": "low",
            "advanced": "medium",
            "premium": "medium",
            "specialized": "high",
        }
        return effort_map.get(tier, "medium")

    def _calculate_roi_opportunity(
        self,
        adoption_analysis: dict[str, Any],
        recommendations: list[dict[str, Any]],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate ROI opportunity from feature adoption."""
        # Calculate potential value from recommendations
        total_value_score = sum(rec["value_score"] for rec in recommendations)

        # Estimate efficiency gains
        high_priority_count = sum(
            1 for rec in recommendations if rec["priority"] in ["critical", "high"]
        )
        estimated_time_savings_hours = high_priority_count * 10  # 10 hours per month per feature

        # Calculate retention impact
        adoption_score = adoption_analysis["overall_adoption_score"]
        retention_impact = (
            "high" if adoption_score < 50 else "medium" if adoption_score < 75 else "low"
        )

        return {
            "total_value_opportunity": total_value_score,
            "estimated_time_savings_hours": estimated_time_savings_hours,
            "high_priority_features": high_priority_count,
            "retention_impact": retention_impact,
            "expansion_potential": "high" if len(recommendations) >= 5 else "medium",
        }

    def _create_adoption_campaign(
        self,
        adoption_analysis: dict[str, Any],
        recommendations: list[dict[str, Any]],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a feature adoption campaign."""
        if not recommendations:
            return {
                "campaign_type": "maintenance",
                "tactics": ["Continue monitoring usage"],
                "timeline": "ongoing",
            }

        top_priority = recommendations[0]["priority"]

        campaign = {
            "campaign_type": "feature_adoption",
            "focus": f"{top_priority.title()} priority features",
            "tactics": [],
            "timeline": "30 days",
            "success_metrics": [],
        }

        # Add tactics based on recommendations
        if any(rec["priority"] == "critical" for rec in recommendations):
            campaign["tactics"].extend(
                [
                    "Schedule 1:1 feature demo with CSM",
                    "Provide video tutorials for critical features",
                    "Set up automated in-app prompts",
                ]
            )

        campaign["tactics"].extend(
            [
                "Send feature spotlight email series",
                "Share customer success stories showcasing features",
                "Offer office hours for hands-on training",
            ]
        )

        # Add success metrics
        campaign["success_metrics"] = [
            f"Adopt {min(3, len(recommendations))} recommended features",
            f"Increase adoption score by {20 - (adoption_analysis.get('overall_adoption_score', 0) // 10) * 5}%",
            "Achieve 50%+ usage frequency on new features",
        ]

        return campaign

    def _format_adoption_report(
        self,
        adoption_analysis: dict[str, Any],
        recommendations: list[dict[str, Any]],
        roi_projection: dict[str, Any],
        adoption_campaign: dict[str, Any],
    ) -> str:
        """Format feature adoption report."""
        score = adoption_analysis["overall_adoption_score"]

        score_emoji = (
            "????" if score >= 75 else "???" if score >= 50 else "??????" if score >= 25 else "????"
        )

        report = f"""**{score_emoji} Feature Adoption Analysis**

**Overall Adoption Score:** {score}/100
**Features Adopted:** {adoption_analysis["features_adopted"]}/{adoption_analysis["total_features_available"]} ({adoption_analysis["adoption_percentage"]}%)
**Unused Features:** {adoption_analysis["unused_count"]}

**Adoption Velocity:**
- Trend: {adoption_analysis["adoption_velocity"]["trend"].title()} {("????" if adoption_analysis["adoption_velocity"]["velocity_percentage"] > 0 else "????")}
- Change: {adoption_analysis["adoption_velocity"]["velocity_percentage"]:+.1f}%
- New Features This Month: {adoption_analysis["adoption_velocity"]["new_features_adopted"]}

**Feature Adoption by Stage:**
"""

        for stage, features in adoption_analysis["adoption_by_stage"].items():
            if features:
                count = len(features)
                report += f"- {stage.replace('_', ' ').title()}: {count} features\n"

        # Adoption patterns
        if adoption_analysis.get("adoption_patterns"):
            report += "\n**???? Adoption Patterns:**\n"
            for pattern in adoption_analysis["adoption_patterns"]:
                report += f"- {pattern}\n"

        # Top recommendations
        if recommendations:
            report += "\n**???? Top Feature Recommendations:**\n"
            for i, rec in enumerate(recommendations[:5], 1):
                priority_icon = (
                    "????"
                    if rec["priority"] == "critical"
                    else "????"
                    if rec["priority"] == "high"
                    else "????"
                )
                report += f"\n{i}. **{rec['feature']}** {priority_icon}\n"
                report += f"   - Priority: {rec['priority'].title()}\n"
                report += f"   - Value Score: {rec['value_score']}/100\n"
                report += f"   - Use Case: {rec['suggested_use_case']}\n"
                report += f"   - Effort: {rec['adoption_effort'].title()}\n"

        # ROI opportunity
        report += "\n**???? ROI Opportunity:**\n"
        report += f"- Total Value Score: {roi_projection['total_value_opportunity']}\n"
        report += f"- Estimated Time Savings: {roi_projection['estimated_time_savings_hours']} hours/month\n"
        report += f"- Retention Impact: {roi_projection['retention_impact'].title()}\n"
        report += f"- Expansion Potential: {roi_projection['expansion_potential'].title()}\n"

        # Adoption campaign
        report += "\n**???? Recommended Adoption Campaign:**\n"
        report += f"**Focus:** {adoption_campaign['focus']}\n"
        report += f"**Timeline:** {adoption_campaign['timeline']}\n\n"
        report += "**Tactics:**\n"
        for tactic in adoption_campaign["tactics"][:4]:
            report += f"- {tactic}\n"

        report += "\n**Success Metrics:**\n"
        for metric in adoption_campaign["success_metrics"]:
            report += f"- {metric}\n"

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Feature Adoption Agent (TASK-2031)")
        print("=" * 70)

        agent = FeatureAdoptionAgent()

        # Test 1: Low adoption scenario
        print("\n\nTest 1: Low Feature Adoption")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze feature adoption",
            context={
                "customer_id": "cust_low_adoption",
                "customer_metadata": {"plan": "enterprise", "industry": "healthcare"},
            },
        )
        state1["entities"] = {
            "usage_data": {
                "features_used": ["basic_reporting", "user_management"],
                "feature_usage_frequency": {"basic_reporting": 8, "user_management": 12},
                "previous_month_features_count": 2,
            },
            "available_features": [
                "basic_reporting",
                "user_management",
                "advanced_analytics",
                "automation_builder",
                "api_access",
                "custom_dashboards",
                "collaboration_tools",
                "integration_hub",
            ],
        }

        result1 = await agent.process(state1)

        print(f"Adoption Score: {result1['adoption_score']}/100")
        print(f"Unused Features: {result1['unused_features_count']}")
        print(f"ROI Opportunity: {result1['roi_opportunity']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: High adoption scenario
        print("\n\n" + "=" * 70)
        print("Test 2: High Feature Adoption")
        print("-" * 70)

        state2 = create_initial_state(
            "Check feature usage",
            context={
                "customer_id": "cust_high_adoption",
                "customer_metadata": {"plan": "premium", "industry": "technology"},
            },
        )
        state2["entities"] = {
            "usage_data": {
                "features_used": [
                    "basic_reporting",
                    "advanced_analytics",
                    "automation_builder",
                    "custom_dashboards",
                    "collaboration_tools",
                ],
                "feature_usage_frequency": {
                    "basic_reporting": 45,
                    "advanced_analytics": 60,
                    "automation_builder": 35,
                    "custom_dashboards": 55,
                    "collaboration_tools": 25,
                },
                "previous_month_features_count": 4,
            },
            "available_features": [
                "basic_reporting",
                "advanced_analytics",
                "automation_builder",
                "custom_dashboards",
                "collaboration_tools",
                "api_access",
            ],
        }

        result2 = await agent.process(state2)

        print(f"Adoption Score: {result2['adoption_score']}/100")
        print(f"Unused Features: {result2['unused_features_count']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
