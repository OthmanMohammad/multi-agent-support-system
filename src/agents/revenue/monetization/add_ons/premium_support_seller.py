"""
Premium Support Seller Agent - TASK-3022

Sells premium support packages by identifying high-touch support needs.
Converts support-intensive customers into premium support subscribers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("premium_support_seller", tier="revenue", category="monetization")
class PremiumSupportSeller(BaseAgent):
    """
    Premium Support Seller Agent - Identifies and converts premium support opportunities.

    Handles:
    - Identify customers with high support needs
    - Analyze support ticket patterns and volume
    - Calculate time savings with premium support
    - Present premium support value proposition
    - Compare standard vs premium support benefits
    - Calculate ROI for premium support
    - Close premium support sales
    - Track conversion success rates
    """

    # Premium support tiers
    PREMIUM_SUPPORT_TIERS = {
        "business": {
            "name": "Business Support",
            "price_monthly": 500,
            "price_annual": 5000,
            "features": [
                "24/7 email and chat support",
                "4-hour response SLA",
                "Unlimited tickets",
                "Phone support during business hours",
                "Monthly support reviews"
            ],
            "ideal_for": ["mid_market", "growing_teams"],
            "min_tickets_per_month": 15
        },
        "enterprise": {
            "name": "Enterprise Support",
            "price_monthly": 1500,
            "price_annual": 15000,
            "features": [
                "24/7 phone, email, chat support",
                "1-hour critical response SLA",
                "Dedicated support engineer",
                "Quarterly business reviews",
                "Architecture guidance",
                "Priority bug fixes",
                "Named support contacts"
            ],
            "ideal_for": ["enterprise", "mission_critical"],
            "min_tickets_per_month": 25
        },
        "premium_plus": {
            "name": "Premium Plus Support",
            "price_monthly": 3000,
            "price_annual": 30000,
            "features": [
                "All Enterprise features",
                "30-minute critical response SLA",
                "Dedicated support team (3 engineers)",
                "Weekly sync meetings",
                "Custom SLA agreements",
                "On-call support engineer",
                "Proactive monitoring"
            ],
            "ideal_for": ["enterprise", "high_value"],
            "min_tickets_per_month": 40
        }
    }

    # Qualification criteria
    QUALIFICATION_CRITERIA = {
        "high_ticket_volume": {
            "metric": "tickets_per_month",
            "threshold": 15,
            "weight": 0.30
        },
        "critical_issues": {
            "metric": "critical_tickets_per_month",
            "threshold": 3,
            "weight": 0.25
        },
        "slow_response_frustration": {
            "metric": "avg_response_time_hours",
            "threshold": 6,
            "weight": 0.20
        },
        "escalations": {
            "metric": "escalated_tickets",
            "threshold": 5,
            "weight": 0.15
        },
        "weekend_tickets": {
            "metric": "weekend_tickets",
            "threshold": 5,
            "weight": 0.10
        }
    }

    # Value calculation factors
    VALUE_FACTORS = {
        "time_saved_per_ticket_hours": 2,  # Hours saved with faster response
        "engineer_hourly_cost": 75,  # Average engineer cost
        "downtime_cost_per_hour": 5000,  # Cost of critical downtime
        "productivity_boost": 0.25  # 25% productivity improvement
    }

    def __init__(self):
        config = AgentConfig(
            name="premium_support_seller",
            type=AgentType.SPECIALIST,
             # Sonnet for sales conversations
            temperature=0.3,
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
        Identify and sell premium support packages.

        Args:
            state: Current agent state with support usage data

        Returns:
            Updated state with premium support recommendation
        """
        self.logger.info("premium_support_seller_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Qualify customer for premium support
        qualification = self._qualify_customer(customer_metadata)

        # Determine recommended tier
        recommended_tier = self._recommend_tier(
            qualification,
            customer_metadata
        )

        # Calculate ROI and value
        roi_analysis = self._calculate_roi(
            recommended_tier,
            customer_metadata
        )

        # Build value proposition
        value_proposition = self._build_value_proposition(
            recommended_tier,
            roi_analysis,
            customer_metadata
        )

        # Compare current vs premium support
        comparison = self._compare_support_tiers(
            recommended_tier,
            customer_metadata
        )

        # Generate objection handling
        objections = self._prepare_objection_handling(recommended_tier)

        # Search KB for premium support resources
        kb_results = await self.search_knowledge_base(
            "premium support enterprise SLA",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_sales_response(
            message,
            qualification,
            recommended_tier,
            value_proposition,
            roi_analysis,
            comparison,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.87
        state["premium_support_qualification"] = qualification
        state["recommended_tier"] = recommended_tier
        state["roi_analysis"] = roi_analysis
        state["value_proposition"] = value_proposition
        state["support_comparison"] = comparison
        state["status"] = "resolved"

        self.logger.info(
            "premium_support_seller_completed",
            qualified=qualification["is_qualified"],
            recommended_tier=recommended_tier,
            roi_percentage=roi_analysis.get("roi_percentage", 0)
        )

        return state

    def _qualify_customer(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Qualify customer for premium support based on criteria"""
        qualification = {
            "is_qualified": False,
            "qualification_score": 0.0,
            "qualifying_factors": [],
            "signals": {}
        }

        total_weight = 0
        weighted_score = 0

        for factor, config in self.QUALIFICATION_CRITERIA.items():
            metric = config["metric"]
            threshold = config["threshold"]
            weight = config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)
            qualification["signals"][factor] = {
                "metric": metric,
                "actual": actual_value,
                "threshold": threshold,
                "meets_threshold": actual_value >= threshold
            }

            if actual_value >= threshold:
                weighted_score += weight
                qualification["qualifying_factors"].append(factor)

        qualification["qualification_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0,
            2
        )
        qualification["is_qualified"] = qualification["qualification_score"] >= 50

        return qualification

    def _recommend_tier(
        self,
        qualification: Dict,
        customer_metadata: Dict
    ) -> str:
        """Recommend appropriate premium support tier"""
        tickets_per_month = customer_metadata.get("tickets_per_month", 0)
        company_size = customer_metadata.get("company_size", 0)
        current_mrr = customer_metadata.get("current_mrr", 0)

        # Recommend based on volume and company profile
        if tickets_per_month >= 40 or company_size >= 500 or current_mrr >= 10000:
            return "premium_plus"
        elif tickets_per_month >= 25 or company_size >= 100 or current_mrr >= 5000:
            return "enterprise"
        else:
            return "business"

    def _calculate_roi(
        self,
        tier: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate ROI for premium support investment"""
        tier_info = self.PREMIUM_SUPPORT_TIERS[tier]
        annual_cost = tier_info["price_annual"]

        tickets_per_month = customer_metadata.get("tickets_per_month", 0)
        critical_tickets = customer_metadata.get("critical_tickets_per_month", 0)

        # Calculate time savings
        annual_tickets = tickets_per_month * 12
        time_saved_hours = annual_tickets * self.VALUE_FACTORS["time_saved_per_ticket_hours"]
        time_saved_value = time_saved_hours * self.VALUE_FACTORS["engineer_hourly_cost"]

        # Calculate downtime reduction
        downtime_reduction_hours = critical_tickets * 12 * 4  # 4 hours saved per critical issue
        downtime_value = downtime_reduction_hours * self.VALUE_FACTORS["downtime_cost_per_hour"]

        # Calculate productivity gains
        productivity_value = time_saved_value * self.VALUE_FACTORS["productivity_boost"]

        # Total annual value
        total_annual_value = time_saved_value + downtime_value + productivity_value

        # Calculate ROI
        roi_percentage = ((total_annual_value - annual_cost) / annual_cost) * 100 if annual_cost > 0 else 0
        payback_months = (annual_cost / (total_annual_value / 12)) if total_annual_value > 0 else 0

        return {
            "annual_cost": annual_cost,
            "monthly_cost": tier_info["price_monthly"],
            "time_saved_hours": round(time_saved_hours, 0),
            "time_saved_value": round(time_saved_value, 2),
            "downtime_reduction_value": round(downtime_value, 2),
            "productivity_value": round(productivity_value, 2),
            "total_annual_value": round(total_annual_value, 2),
            "roi_percentage": round(roi_percentage, 2),
            "payback_months": round(payback_months, 1),
            "monthly_savings": round((total_annual_value - annual_cost) / 12, 2)
        }

    def _build_value_proposition(
        self,
        tier: str,
        roi_analysis: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Build personalized value proposition"""
        tier_info = self.PREMIUM_SUPPORT_TIERS[tier]
        company = customer_metadata.get("company", "your team")

        return {
            "headline": f"{tier_info['name']} - Save {roi_analysis['time_saved_hours']:.0f} hours annually",
            "key_benefits": [
                f"Reduce response time from 6+ hours to {tier_info.get('sla', '1 hour')}",
                f"Save ${roi_analysis['time_saved_value']:,.0f} in engineering time annually",
                f"Prevent ${roi_analysis['downtime_reduction_value']:,.0f} in downtime costs",
                f"ROI: {roi_analysis['roi_percentage']:.0f}% annual return"
            ],
            "use_case": f"With {customer_metadata.get('tickets_per_month', 0)} tickets/month, {company} needs faster, dedicated support",
            "urgency": "Critical issues are costing you time and money every day"
        }

    def _compare_support_tiers(
        self,
        recommended_tier: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Compare current support with recommended premium tier"""
        recommended = self.PREMIUM_SUPPORT_TIERS[recommended_tier]

        return {
            "current": {
                "name": "Standard Support",
                "response_time": "24-48 hours",
                "channels": "Email only",
                "availability": "Business hours",
                "cost": "$0/month"
            },
            "recommended": {
                "name": recommended["name"],
                "response_time": "1-4 hours SLA",
                "channels": "Phone, Email, Chat",
                "availability": "24/7",
                "cost": f"${recommended['price_monthly']}/month",
                "features": recommended["features"]
            },
            "upgrade_value": "Faster resolutions, less downtime, dedicated support"
        }

    def _prepare_objection_handling(self, tier: str) -> Dict[str, str]:
        """Prepare responses to common objections"""
        tier_info = self.PREMIUM_SUPPORT_TIERS[tier]

        return {
            "too_expensive": f"The ROI shows you'll save more than the ${tier_info['price_monthly']}/mo cost in reduced downtime and engineer time",
            "dont_need_it": "Your support volume and critical issues show this would save significant time and money",
            "try_later": "Every month without premium support is costing you thousands in productivity losses",
            "works_fine_now": "Standard support works, but critical issues taking 24+ hours cost you real money and team frustration"
        }

    async def _generate_sales_response(
        self,
        message: str,
        qualification: Dict,
        recommended_tier: str,
        value_proposition: Dict,
        roi_analysis: Dict,
        comparison: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate premium support sales response"""

        tier_info = self.PREMIUM_SUPPORT_TIERS[recommended_tier]

        # Build qualification context
        qual_context = f"""
Qualification Score: {qualification['qualification_score']}/100
Qualifying Factors: {', '.join(qualification['qualifying_factors'])}
Recommended Tier: {tier_info['name']}
"""

        # Build ROI context
        roi_context = f"""
ROI Analysis:
- Monthly Cost: ${roi_analysis['monthly_cost']}
- Annual Value: ${roi_analysis['total_annual_value']:,.0f}
- ROI: {roi_analysis['roi_percentage']:.0f}%
- Payback Period: {roi_analysis['payback_months']} months
- Time Saved: {roi_analysis['time_saved_hours']:.0f} hours/year
"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nPremium Support Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Premium Support Seller helping customers get better support outcomes.

Customer: {customer_metadata.get('company', 'Customer')}
Current Support Tickets: {customer_metadata.get('tickets_per_month', 0)}/month
{qual_context}
{roi_context}

Your response should:
1. Acknowledge their support challenges empathetically
2. Identify specific pain points from their support usage
3. Present the value of {tier_info['name']}
4. Quantify ROI and time savings
5. Compare current vs premium support clearly
6. Address concerns about cost with value
7. Create urgency around support improvements
8. Make it easy to upgrade
9. Be consultative, not pushy
10. Focus on solving their support pain

Tone: Helpful, data-driven, solution-focused"""

        user_prompt = f"""Customer message: {message}

Value Proposition:
{value_proposition['headline']}

Key Benefits:
{chr(10).join(f'- {benefit}' for benefit in value_proposition['key_benefits'])}

{kb_context}

Generate a compelling premium support recommendation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
