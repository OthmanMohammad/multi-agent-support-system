"""
Add-On Recommender Agent - TASK-3021

Recommends relevant add-ons based on usage patterns, needs, and customer profile.
Identifies upsell opportunities for premium features and services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("add_on_recommender", tier="revenue", category="monetization")
class AddOnRecommender(BaseAgent):
    """
    Add-On Recommender Agent - Identifies and recommends add-on products.

    Handles:
    - Identify add-on opportunities from usage patterns
    - Recommend relevant add-ons by customer profile
    - Calculate ROI for add-on purchases
    - Explain value proposition of each add-on
    - Personalize recommendations
    - Track recommendation acceptance
    - Optimize recommendation strategy
    - Close add-on sales
    """

    # Available add-on products
    ADD_ON_CATALOG = {
        "premium_support": {
            "name": "Premium Support",
            "price_monthly": 500,
            "price_annual": 5000,
            "description": "24/7 support, 1-hour response SLA, dedicated support engineer",
            "ideal_for": ["high_ticket_volume", "enterprise", "mission_critical"],
            "roi_metric": "support_response_time_reduction"
        },
        "api_access_plus": {
            "name": "API Access Plus",
            "price_monthly": 200,
            "price_annual": 2000,
            "description": "Higher rate limits, advanced endpoints, webhooks",
            "ideal_for": ["high_api_usage", "integration_heavy", "developers"],
            "roi_metric": "development_efficiency"
        },
        "training_package": {
            "name": "Team Training Package",
            "price_one_time": 2000,
            "description": "8-hour live training, certification, best practices workshop",
            "ideal_for": ["new_teams", "low_adoption", "enterprise"],
            "roi_metric": "user_productivity"
        },
        "professional_services": {
            "name": "Professional Services",
            "price_hourly": 250,
            "description": "Custom development, integrations, migrations, consulting",
            "ideal_for": ["custom_needs", "complex_integration", "enterprise"],
            "roi_metric": "time_to_value"
        },
        "advanced_analytics": {
            "name": "Advanced Analytics",
            "price_monthly": 300,
            "price_annual": 3000,
            "description": "Custom reports, dashboards, data export, API analytics",
            "ideal_for": ["data_driven", "reporting_needs", "enterprise"],
            "roi_metric": "decision_quality"
        },
        "dedicated_account_manager": {
            "name": "Dedicated Account Manager",
            "price_monthly": 1000,
            "price_annual": 10000,
            "description": "Personal account manager, quarterly business reviews, strategic planning",
            "ideal_for": ["enterprise", "high_value", "strategic"],
            "roi_metric": "partnership_value"
        }
    }

    # Trigger signals for recommendations
    RECOMMENDATION_TRIGGERS = {
        "premium_support": {
            "signals": [
                {"metric": "support_tickets_per_month", "threshold": 20, "operator": ">="},
                {"metric": "avg_response_time_hours", "threshold": 4, "operator": ">="},
                {"metric": "critical_tickets", "threshold": 3, "operator": ">="}
            ],
            "confidence_boost": 0.20
        },
        "api_access_plus": {
            "signals": [
                {"metric": "api_calls", "threshold": 500000, "operator": ">="},
                {"metric": "rate_limit_hits", "threshold": 10, "operator": ">="},
                {"metric": "webhook_requests", "threshold": 5, "operator": ">="}
            ],
            "confidence_boost": 0.25
        },
        "training_package": {
            "signals": [
                {"metric": "team_size", "threshold": 10, "operator": ">="},
                {"metric": "feature_adoption_rate", "threshold": 0.30, "operator": "<="},
                {"metric": "support_tickets_how_to", "threshold": 15, "operator": ">="}
            ],
            "confidence_boost": 0.30
        },
        "professional_services": {
            "signals": [
                {"metric": "custom_integration_requests", "threshold": 3, "operator": ">="},
                {"metric": "advanced_feature_requests", "threshold": 5, "operator": ">="},
                {"metric": "migration_mentioned", "threshold": 1, "operator": ">="}
            ],
            "confidence_boost": 0.25
        },
        "advanced_analytics": {
            "signals": [
                {"metric": "report_exports", "threshold": 50, "operator": ">="},
                {"metric": "dashboard_views", "threshold": 100, "operator": ">="},
                {"metric": "data_api_calls", "threshold": 1000, "operator": ">="}
            ],
            "confidence_boost": 0.20
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="add_on_recommender",
            type=AgentType.SPECIALIST,
             # Sonnet for nuanced recommendations
            temperature=0.4,
            max_tokens=600,
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
        Recommend relevant add-ons based on customer profile and usage.

        Args:
            state: Current agent state

        Returns:
            Updated state with add-on recommendations
        """
        self.logger.info("add_on_recommender_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Analyze customer profile
        customer_profile = self._analyze_customer_profile(customer_metadata)

        # Identify add-on opportunities
        opportunities = self._identify_opportunities(
            customer_metadata,
            customer_profile
        )

        # Calculate ROI for each recommendation
        recommendations_with_roi = self._calculate_roi(
            opportunities,
            customer_metadata
        )

        # Rank recommendations
        ranked_recommendations = self._rank_recommendations(
            recommendations_with_roi,
            customer_profile
        )

        # Generate value propositions
        value_props = self._generate_value_propositions(
            ranked_recommendations,
            customer_metadata
        )

        # Search KB for add-on information
        kb_results = await self.search_knowledge_base(
            "add-on products premium support training",
            category="monetization",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_recommendation_response(
            message,
            customer_profile,
            ranked_recommendations,
            value_props,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["customer_profile"] = customer_profile
        state["add_on_opportunities"] = opportunities
        state["add_on_recommendations"] = ranked_recommendations
        state["value_propositions"] = value_props
        state["status"] = "resolved"

        self.logger.info(
            "add_on_recommender_completed",
            recommendations_count=len(ranked_recommendations),
            top_recommendation=ranked_recommendations[0]["add_on_id"] if ranked_recommendations else None
        )

        return state

    def _analyze_customer_profile(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Analyze customer to build profile for recommendations"""
        profile = {
            "tier": "unknown",
            "maturity": "unknown",
            "needs": [],
            "budget_capacity": "unknown"
        }

        # Determine tier
        company_size = customer_metadata.get("company_size", 0)
        if company_size >= 500:
            profile["tier"] = "enterprise"
        elif company_size >= 50:
            profile["tier"] = "mid_market"
        else:
            profile["tier"] = "smb"

        # Determine maturity
        account_age_days = customer_metadata.get("account_age_days", 0)
        feature_adoption = customer_metadata.get("feature_adoption_rate", 0)

        if account_age_days >= 180 and feature_adoption >= 0.70:
            profile["maturity"] = "advanced"
        elif account_age_days >= 90 and feature_adoption >= 0.40:
            profile["maturity"] = "growing"
        else:
            profile["maturity"] = "new"

        # Identify needs based on usage patterns
        if customer_metadata.get("support_tickets_per_month", 0) >= 15:
            profile["needs"].append("high_support")

        if customer_metadata.get("api_calls", 0) >= 100000:
            profile["needs"].append("api_heavy")

        if customer_metadata.get("team_size", 0) >= 10:
            profile["needs"].append("large_team")

        if customer_metadata.get("custom_requests", 0) >= 3:
            profile["needs"].append("customization")

        # Estimate budget capacity
        current_spend = customer_metadata.get("current_mrr", 0)
        if current_spend >= 10000:
            profile["budget_capacity"] = "high"
        elif current_spend >= 2000:
            profile["budget_capacity"] = "medium"
        else:
            profile["budget_capacity"] = "low"

        return profile

    def _identify_opportunities(
        self,
        customer_metadata: Dict,
        profile: Dict
    ) -> List[Dict[str, Any]]:
        """Identify add-on opportunities from signals"""
        opportunities = []

        for add_on_id, trigger_config in self.RECOMMENDATION_TRIGGERS.items():
            signals_met = 0
            total_signals = len(trigger_config["signals"])

            for signal in trigger_config["signals"]:
                metric = signal["metric"]
                threshold = signal["threshold"]
                operator = signal["operator"]
                actual_value = customer_metadata.get(metric, 0)

                if operator == ">=":
                    if actual_value >= threshold:
                        signals_met += 1
                elif operator == "<=":
                    if actual_value <= threshold:
                        signals_met += 1
                elif operator == "==":
                    if actual_value == threshold:
                        signals_met += 1

            # Calculate confidence
            signal_confidence = signals_met / total_signals if total_signals > 0 else 0
            base_confidence = 0.50
            confidence = min(base_confidence + signal_confidence * trigger_config["confidence_boost"], 1.0)

            if confidence >= 0.60:  # Only recommend if 60%+ confidence
                add_on_info = self.ADD_ON_CATALOG[add_on_id]
                opportunities.append({
                    "add_on_id": add_on_id,
                    "add_on_name": add_on_info["name"],
                    "confidence": round(confidence, 2),
                    "signals_met": signals_met,
                    "total_signals": total_signals,
                    "trigger_reason": f"{signals_met}/{total_signals} signals met"
                })

        return opportunities

    def _calculate_roi(
        self,
        opportunities: List[Dict],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Calculate ROI for each add-on recommendation"""
        recommendations = []

        for opp in opportunities:
            add_on_id = opp["add_on_id"]
            add_on_info = self.ADD_ON_CATALOG[add_on_id]

            # Calculate cost
            if "price_monthly" in add_on_info:
                monthly_cost = add_on_info["price_monthly"]
                annual_cost = add_on_info.get("price_annual", monthly_cost * 12)
            elif "price_one_time" in add_on_info:
                monthly_cost = 0
                annual_cost = add_on_info["price_one_time"]
            else:
                monthly_cost = 0
                annual_cost = 0

            # Estimate value (simplified - would use real metrics in production)
            estimated_value = self._estimate_value(add_on_id, customer_metadata)

            # Calculate ROI
            if annual_cost > 0:
                roi_percentage = ((estimated_value - annual_cost) / annual_cost) * 100
            else:
                roi_percentage = 0

            recommendations.append({
                **opp,
                "monthly_cost": monthly_cost,
                "annual_cost": annual_cost,
                "estimated_annual_value": estimated_value,
                "roi_percentage": round(roi_percentage, 2),
                "payback_months": round(annual_cost / (estimated_value / 12), 1) if estimated_value > 0 else 0
            })

        return recommendations

    def _estimate_value(self, add_on_id: str, customer_metadata: Dict) -> float:
        """Estimate annual value of add-on (simplified)"""
        # These are simplified estimates - real implementation would use actual data
        value_estimates = {
            "premium_support": 15000,  # Time savings, reduced downtime
            "api_access_plus": 10000,  # Developer efficiency
            "training_package": 8000,   # User productivity
            "professional_services": 20000,  # Custom development value
            "advanced_analytics": 12000,  # Better decisions
            "dedicated_account_manager": 25000  # Strategic value
        }

        base_value = value_estimates.get(add_on_id, 5000)

        # Adjust by company size
        company_size = customer_metadata.get("company_size", 50)
        size_multiplier = min(company_size / 100, 3.0)  # Max 3x

        return round(base_value * size_multiplier, 2)

    def _rank_recommendations(
        self,
        recommendations: List[Dict],
        profile: Dict
    ) -> List[Dict[str, Any]]:
        """Rank recommendations by priority"""
        # Score each recommendation
        for rec in recommendations:
            score = 0

            # Weight by confidence
            score += rec["confidence"] * 40

            # Weight by ROI
            roi_score = min(rec["roi_percentage"] / 100, 2.0) * 30  # Cap at 200% ROI
            score += roi_score

            # Weight by fit with profile
            add_on_id = rec["add_on_id"]
            add_on_info = self.ADD_ON_CATALOG[add_on_id]

            if profile["tier"] in add_on_info.get("ideal_for", []):
                score += 20

            if any(need in add_on_info.get("ideal_for", []) for need in profile["needs"]):
                score += 10

            rec["priority_score"] = round(score, 2)

        # Sort by priority score
        return sorted(recommendations, key=lambda x: x["priority_score"], reverse=True)

    def _generate_value_propositions(
        self,
        recommendations: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, str]:
        """Generate personalized value propositions"""
        value_props = {}

        for rec in recommendations[:5]:  # Top 5
            add_on_id = rec["add_on_id"]
            add_on_info = self.ADD_ON_CATALOG[add_on_id]

            company = customer_metadata.get("company", "your team")

            if add_on_id == "premium_support":
                value_prop = f"With {rec['signals_met']} support tickets this month, Premium Support would give {company} 1-hour response SLAs and a dedicated engineer, saving ~20 hours/month."
            elif add_on_id == "api_access_plus":
                value_prop = f"Your API usage shows you're hitting rate limits. API Access Plus unlocks higher limits and webhooks, improving developer productivity by 40%."
            elif add_on_id == "training_package":
                value_prop = f"Our data shows {company} is using only 30% of available features. Our Training Package typically boosts adoption to 75% and productivity by 50%."
            elif add_on_id == "professional_services":
                value_prop = f"Based on your custom integration needs, our Professional Services team can build what you need in 2-3 weeks vs 3-6 months DIY."
            else:
                value_prop = add_on_info["description"]

            value_props[add_on_id] = value_prop

        return value_props

    async def _generate_recommendation_response(
        self,
        message: str,
        profile: Dict,
        recommendations: List[Dict],
        value_props: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate add-on recommendation response"""

        # Build recommendations context
        rec_context = ""
        if recommendations:
            rec_context = "\n\nTop Add-On Recommendations:\n"
            for rec in recommendations[:3]:  # Top 3
                rec_context += f"- {rec['add_on_name']}: ROI {rec['roi_percentage']:.0f}%, Confidence {rec['confidence']*100:.0f}%\n"

        # Build profile context
        profile_context = f"""
Customer Profile:
- Tier: {profile['tier']}
- Maturity: {profile['maturity']}
- Needs: {', '.join(profile['needs']) if profile['needs'] else 'Standard'}
- Budget Capacity: {profile['budget_capacity']}
"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nAdd-On Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are an Add-On Recommender specialist identifying upsell opportunities.

Customer: {customer_metadata.get('company', 'Customer')}
{profile_context}
{rec_context}

Your response should:
1. Show understanding of their usage and needs
2. Recommend 1-3 most relevant add-ons
3. Explain specific value for their situation
4. Quantify ROI and benefits
5. Address "what's in it for me"
6. Make it easy to say yes
7. Provide next steps to purchase
8. Be consultative, not pushy
9. Focus on solving their problems"""

        user_prompt = f"""Customer message: {message}

Value Propositions:
{chr(10).join(f'- {add_on}: {prop}' for add_on, prop in list(value_props.items())[:3])}

{kb_context}

Generate a personalized add-on recommendation."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Recommendation context is built from customer data
        )
        return response
