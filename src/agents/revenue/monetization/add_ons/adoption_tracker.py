"""
Adoption Tracker Agent - TASK-3025

Tracks add-on adoption rates and identifies upsell opportunities.
Monitors which add-ons are being used and optimizes add-on strategy.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("adoption_tracker", tier="revenue", category="monetization")
class AdoptionTracker(BaseAgent):
    """
    Adoption Tracker Agent - Monitors add-on adoption and usage.

    Handles:
    - Track add-on purchase rates
    - Monitor add-on usage and engagement
    - Identify underutilized add-ons
    - Calculate add-on ROI for customers
    - Detect upsell opportunities
    - Analyze adoption patterns
    - Recommend optimization strategies
    - Track expansion revenue from add-ons
    """

    # Add-on adoption metrics
    ADOPTION_METRICS = {
        "premium_support": {
            "usage_indicators": [
                "support_tickets_opened",
                "phone_calls_made",
                "dedicated_engineer_contacts",
                "business_review_attendance",
            ],
            "healthy_usage_threshold": {
                "support_tickets_opened": 5,  # Per month
                "phone_calls_made": 2,
                "dedicated_engineer_contacts": 4,
            },
            "roi_metric": "response_time_improvement",
        },
        "api_access_plus": {
            "usage_indicators": [
                "api_calls_advanced_endpoints",
                "webhook_deliveries",
                "rate_limit_headroom_used",
            ],
            "healthy_usage_threshold": {
                "api_calls_advanced_endpoints": 1000,
                "webhook_deliveries": 100,
            },
            "roi_metric": "api_efficiency",
        },
        "training_package": {
            "usage_indicators": [
                "training_sessions_attended",
                "certification_completed",
                "feature_adoption_post_training",
            ],
            "healthy_usage_threshold": {
                "training_sessions_attended": 1,
                "feature_adoption_post_training": 0.70,
            },
            "roi_metric": "productivity_increase",
        },
        "professional_services": {
            "usage_indicators": [
                "project_milestones_completed",
                "deliverables_received",
                "project_satisfaction_score",
            ],
            "healthy_usage_threshold": {
                "project_milestones_completed": 1,
                "project_satisfaction_score": 4.0,
            },
            "roi_metric": "implementation_success",
        },
        "advanced_analytics": {
            "usage_indicators": ["custom_reports_created", "dashboard_views", "data_exports"],
            "healthy_usage_threshold": {"custom_reports_created": 3, "dashboard_views": 50},
            "roi_metric": "data_driven_decisions",
        },
    }

    # Adoption health scoring
    HEALTH_SCORE_WEIGHTS = {
        "usage_frequency": 0.40,
        "feature_utilization": 0.30,
        "value_realization": 0.20,
        "customer_satisfaction": 0.10,
    }

    # Upsell triggers based on adoption
    UPSELL_TRIGGERS = {
        "high_adoption_of_basic": {
            "condition": "Using basic add-on at >80% capacity",
            "recommendation": "Upgrade to next tier",
            "confidence_boost": 0.25,
        },
        "multiple_add_ons": {
            "condition": "Using 3+ add-ons separately",
            "recommendation": "Bundle package or enterprise plan",
            "confidence_boost": 0.30,
        },
        "underutilized_add_on": {
            "condition": "Add-on usage <40% of potential",
            "recommendation": "Training or optimization session",
            "confidence_boost": 0.20,
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="adoption_tracker",
            type=AgentType.SPECIALIST,
            # Haiku for efficient tracking
            temperature=0.3,
            max_tokens=500,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="monetization",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Track add-on adoption and identify opportunities.

        Args:
            state: Current agent state with add-on usage data

        Returns:
            Updated state with adoption analysis
        """
        self.logger.info("adoption_tracker_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Get customer's current add-ons
        current_add_ons = customer_metadata.get("active_add_ons", [])

        # Track adoption for each add-on
        adoption_analysis = self._analyze_add_on_adoption(current_add_ons, customer_metadata)

        # Calculate health scores
        health_scores = self._calculate_health_scores(adoption_analysis, customer_metadata)

        # Identify underutilized add-ons
        underutilized = self._identify_underutilized_add_ons(adoption_analysis, health_scores)

        # Detect upsell opportunities
        upsell_opportunities = self._detect_upsell_opportunities(
            adoption_analysis, health_scores, customer_metadata
        )

        # Generate optimization recommendations
        optimization_recs = self._generate_optimization_recommendations(
            underutilized, adoption_analysis
        )

        # Calculate add-on revenue metrics
        revenue_metrics = self._calculate_addon_revenue_metrics(current_add_ons, customer_metadata)

        # Search KB for adoption best practices
        kb_results = await self.search_knowledge_base(
            "add-on adoption feature utilization", category="monetization", limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_adoption_response(
            message,
            adoption_analysis,
            health_scores,
            underutilized,
            upsell_opportunities,
            optimization_recs,
            revenue_metrics,
            kb_results,
            customer_metadata,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.84
        state["adoption_analysis"] = adoption_analysis
        state["health_scores"] = health_scores
        state["underutilized_add_ons"] = underutilized
        state["upsell_opportunities"] = upsell_opportunities
        state["optimization_recommendations"] = optimization_recs
        state["addon_revenue_metrics"] = revenue_metrics
        state["status"] = "resolved"

        self.logger.info(
            "adoption_tracker_completed",
            add_ons_tracked=len(adoption_analysis),
            underutilized_count=len(underutilized),
            upsell_opportunities=len(upsell_opportunities),
        )

        return state

    def _analyze_add_on_adoption(
        self, add_ons: list[str], customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Analyze adoption for each active add-on"""
        analysis = []

        for add_on_id in add_ons:
            if add_on_id not in self.ADOPTION_METRICS:
                continue

            metrics_config = self.ADOPTION_METRICS[add_on_id]
            usage_data = {}
            threshold_met_count = 0
            total_thresholds = len(metrics_config["healthy_usage_threshold"])

            # Check each usage indicator
            for indicator in metrics_config["usage_indicators"]:
                actual_value = customer_metadata.get(indicator, 0)
                usage_data[indicator] = actual_value

                # Check against threshold
                threshold = metrics_config["healthy_usage_threshold"].get(indicator)
                if threshold is not None and actual_value >= threshold:
                    threshold_met_count += 1

            # Calculate adoption percentage
            adoption_percentage = (
                (threshold_met_count / total_thresholds * 100) if total_thresholds > 0 else 0
            )

            analysis.append(
                {
                    "add_on_id": add_on_id,
                    "usage_data": usage_data,
                    "thresholds_met": threshold_met_count,
                    "total_thresholds": total_thresholds,
                    "adoption_percentage": round(adoption_percentage, 2),
                    "status": self._determine_adoption_status(adoption_percentage),
                }
            )

        return analysis

    def _determine_adoption_status(self, adoption_percentage: float) -> str:
        """Determine adoption status from percentage"""
        if adoption_percentage >= 80:
            return "excellent"
        elif adoption_percentage >= 60:
            return "good"
        elif adoption_percentage >= 40:
            return "moderate"
        else:
            return "poor"

    def _calculate_health_scores(
        self, adoption_analysis: list[dict], customer_metadata: dict
    ) -> dict[str, dict[str, Any]]:
        """Calculate health scores for each add-on"""
        health_scores = {}

        for addon in adoption_analysis:
            add_on_id = addon["add_on_id"]

            # Calculate component scores (simplified)
            usage_score = addon["adoption_percentage"]
            feature_utilization = addon["adoption_percentage"]  # Simplified
            value_realization = customer_metadata.get(f"{add_on_id}_satisfaction", 75)
            satisfaction = customer_metadata.get(f"{add_on_id}_nps", 70)

            # Weighted health score
            health_score = (
                usage_score * self.HEALTH_SCORE_WEIGHTS["usage_frequency"]
                + feature_utilization * self.HEALTH_SCORE_WEIGHTS["feature_utilization"]
                + value_realization * self.HEALTH_SCORE_WEIGHTS["value_realization"]
                + satisfaction * self.HEALTH_SCORE_WEIGHTS["customer_satisfaction"]
            )

            health_scores[add_on_id] = {
                "overall_health": round(health_score, 2),
                "usage_score": round(usage_score, 2),
                "satisfaction_score": round(satisfaction, 2),
                "status": self._determine_health_status(health_score),
            }

        return health_scores

    def _determine_health_status(self, health_score: float) -> str:
        """Determine health status from score"""
        if health_score >= 80:
            return "healthy"
        elif health_score >= 60:
            return "at_risk"
        else:
            return "unhealthy"

    def _identify_underutilized_add_ons(
        self, adoption_analysis: list[dict], health_scores: dict
    ) -> list[dict[str, Any]]:
        """Identify add-ons not being fully utilized"""
        underutilized = []

        for addon in adoption_analysis:
            add_on_id = addon["add_on_id"]
            health = health_scores.get(add_on_id, {})

            if addon["adoption_percentage"] < 40 or health.get("status") == "unhealthy":
                underutilized.append(
                    {
                        "add_on_id": add_on_id,
                        "adoption_percentage": addon["adoption_percentage"],
                        "health_score": health.get("overall_health", 0),
                        "reason": "Low usage and engagement",
                        "risk": "Potential churn or non-renewal",
                    }
                )

        return underutilized

    def _detect_upsell_opportunities(
        self, adoption_analysis: list[dict], health_scores: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Detect upsell opportunities from adoption patterns"""
        opportunities = []

        # High adoption of basic add-ons
        for addon in adoption_analysis:
            if addon["adoption_percentage"] >= 80:
                opportunities.append(
                    {
                        "type": "upgrade_tier",
                        "add_on_id": addon["add_on_id"],
                        "reason": "High utilization of current tier",
                        "recommendation": f"Upgrade {addon['add_on_id']} to next tier",
                        "confidence": 0.80,
                    }
                )

        # Multiple add-ons = bundle opportunity
        if len(adoption_analysis) >= 3:
            total_addon_cost = customer_metadata.get("total_addon_spend", 0)
            if total_addon_cost >= 1000:
                opportunities.append(
                    {
                        "type": "bundle_package",
                        "reason": "Using multiple add-ons",
                        "recommendation": "Enterprise bundle package",
                        "potential_savings": total_addon_cost * 0.20,
                        "confidence": 0.75,
                    }
                )

        return opportunities

    def _generate_optimization_recommendations(
        self, underutilized: list[dict], adoption_analysis: list[dict]
    ) -> list[dict[str, Any]]:
        """Generate recommendations to improve add-on adoption"""
        recommendations = []

        for addon in underutilized:
            add_on_id = addon["add_on_id"]

            if add_on_id == "premium_support":
                recommendations.append(
                    {
                        "add_on_id": add_on_id,
                        "action": "Training session on support features",
                        "expected_impact": "Increase usage by 50%",
                        "timeline": "1 week",
                    }
                )
            elif add_on_id == "api_access_plus":
                recommendations.append(
                    {
                        "add_on_id": add_on_id,
                        "action": "Developer onboarding for advanced endpoints",
                        "expected_impact": "Unlock 60% more API value",
                        "timeline": "2 weeks",
                    }
                )
            elif add_on_id == "advanced_analytics":
                recommendations.append(
                    {
                        "add_on_id": add_on_id,
                        "action": "Custom report setup session",
                        "expected_impact": "Create 5+ valuable reports",
                        "timeline": "1 week",
                    }
                )
            else:
                recommendations.append(
                    {
                        "add_on_id": add_on_id,
                        "action": "Feature adoption review",
                        "expected_impact": "Improve utilization",
                        "timeline": "Immediate",
                    }
                )

        return recommendations

    def _calculate_addon_revenue_metrics(
        self, add_ons: list[str], customer_metadata: dict
    ) -> dict[str, Any]:
        """Calculate revenue metrics from add-ons"""
        total_addon_mrr = customer_metadata.get("total_addon_spend", 0)
        base_mrr = customer_metadata.get("base_plan_cost", 0)

        addon_percentage = (total_addon_mrr / base_mrr * 100) if base_mrr > 0 else 0

        return {
            "total_addon_mrr": total_addon_mrr,
            "base_mrr": base_mrr,
            "addon_percentage_of_revenue": round(addon_percentage, 2),
            "active_addons_count": len(add_ons),
            "expansion_potential": "High" if addon_percentage < 30 else "Medium",
        }

    async def _generate_adoption_response(
        self,
        message: str,
        adoption_analysis: list[dict],
        health_scores: dict,
        underutilized: list[dict],
        upsell_opportunities: list[dict],
        optimization_recs: list[dict],
        revenue_metrics: dict,
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate adoption tracking response"""

        # Build adoption summary
        adoption_summary = f"""
Active Add-Ons: {len(adoption_analysis)}
Underutilized: {len(underutilized)}
Upsell Opportunities: {len(upsell_opportunities)}
Add-On Revenue: ${revenue_metrics["total_addon_mrr"]}/month ({revenue_metrics["addon_percentage_of_revenue"]:.0f}% of total)
"""

        # Build health context
        health_context = ""
        if health_scores:
            health_context = "\n\nAdd-On Health Scores:\n"
            for add_on_id, health in health_scores.items():
                health_context += (
                    f"- {add_on_id}: {health['overall_health']:.0f}/100 ({health['status']})\n"
                )

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nAdoption Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are an Adoption Tracker analyzing add-on utilization and expansion opportunities.

Customer: {customer_metadata.get("company", "Customer")}
{adoption_summary}
{health_context}

Your response should:
1. Summarize add-on adoption status
2. Highlight well-utilized add-ons
3. Identify underutilized add-ons
4. Provide specific optimization recommendations
5. Present upsell opportunities
6. Quantify potential value improvements
7. Be data-driven and actionable
8. Focus on maximizing customer value
9. Help customer get ROI from add-ons

Tone: Analytical, helpful, value-focused"""

        user_prompt = f"""Customer message: {message}

Optimization Recommendations:
{chr(10).join(f"- {rec['add_on_id']}: {rec['action']}" for rec in optimization_recs[:3])}

Upsell Opportunities:
{chr(10).join(f"- {opp['recommendation']}" for opp in upsell_opportunities[:2])}

{kb_context}

Generate an insightful adoption analysis."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Adoption tracking uses customer usage data
        )
        return response
