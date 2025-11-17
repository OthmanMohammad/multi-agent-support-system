"""
Seat Expansion Agent - TASK-3031

Identifies opportunities to expand seat count based on team growth and usage patterns.
Converts growing teams into additional seat purchases.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("seat_expansion", tier="revenue", category="monetization")
class SeatExpansion(BaseAgent):
    """
    Seat Expansion Agent - Drives seat count growth.

    Handles:
    - Monitor team growth trends
    - Identify seat expansion opportunities
    - Detect seat sharing patterns
    - Calculate seat utilization rates
    - Recommend optimal seat counts
    - Present seat expansion value proposition
    - Close seat expansion deals
    - Track seat expansion revenue
    """

    # Seat expansion signals
    EXPANSION_SIGNALS = {
        "rapid_team_growth": {
            "metric": "new_users_last_30_days",
            "threshold": 5,
            "weight": 0.30,
            "indicator": "Adding 5+ users/month = growing team"
        },
        "high_seat_utilization": {
            "metric": "seat_utilization_percentage",
            "threshold": 90,
            "weight": 0.25,
            "indicator": ">90% seat usage = need more seats"
        },
        "seat_sharing_detected": {
            "metric": "shared_login_instances",
            "threshold": 3,
            "weight": 0.20,
            "indicator": "Seat sharing = insufficient licenses"
        },
        "waitlist_exists": {
            "metric": "users_on_waitlist",
            "threshold": 1,
            "weight": 0.15,
            "indicator": "Waitlisted users = immediate need"
        },
        "department_expansion": {
            "metric": "new_departments_added",
            "threshold": 1,
            "weight": 0.10,
            "indicator": "New departments need seats"
        }
    }

    # Seat package recommendations
    SEAT_PACKAGES = {
        "small_growth": {
            "name": "Small Growth Pack",
            "seats": 5,
            "discount": 0.05,  # 5% discount
            "ideal_for": "Small teams adding users gradually"
        },
        "medium_growth": {
            "name": "Medium Growth Pack",
            "seats": 10,
            "discount": 0.10,  # 10% discount
            "ideal_for": "Growing teams with steady hiring"
        },
        "large_growth": {
            "name": "Large Growth Pack",
            "seats": 25,
            "discount": 0.15,  # 15% discount
            "ideal_for": "Rapid expansion and department rollouts"
        },
        "enterprise_growth": {
            "name": "Enterprise Growth Pack",
            "seats": 50,
            "discount": 0.20,  # 20% discount
            "ideal_for": "Company-wide deployments"
        }
    }

    # Seat pricing tiers (simplified)
    SEAT_PRICING = {
        "basic": 20,     # $20/seat/month
        "professional": 40,
        "enterprise": 75
    }

    def __init__(self):
        config = AgentConfig(
            name="seat_expansion",
            type=AgentType.SPECIALIST,
             # Sonnet for expansion sales
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
        Identify and drive seat expansion opportunities.

        Args:
            state: Current agent state with team and usage data

        Returns:
            Updated state with seat expansion recommendation
        """
        self.logger.info("seat_expansion_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Analyze current seat usage
        seat_analysis = self._analyze_seat_usage(customer_metadata)

        # Identify expansion signals
        expansion_signals = self._identify_expansion_signals(customer_metadata)

        # Calculate expansion opportunity
        expansion_opportunity = self._calculate_expansion_opportunity(
            seat_analysis,
            expansion_signals,
            customer_metadata
        )

        # Recommend seat package
        recommended_package = self._recommend_seat_package(
            expansion_opportunity,
            customer_metadata
        )

        # Calculate expansion value
        expansion_value = self._calculate_expansion_value(
            recommended_package,
            customer_metadata
        )

        # Build expansion proposal
        proposal = self._build_expansion_proposal(
            recommended_package,
            expansion_value,
            expansion_signals,
            customer_metadata
        )

        # Search KB for seat expansion resources
        kb_results = await self.search_knowledge_base(
            "seat expansion team growth user licenses",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_expansion_response(
            message,
            seat_analysis,
            expansion_signals,
            expansion_opportunity,
            recommended_package,
            proposal,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["seat_analysis"] = seat_analysis
        state["expansion_signals"] = expansion_signals
        state["expansion_opportunity"] = expansion_opportunity
        state["recommended_package"] = recommended_package
        state["expansion_proposal"] = proposal
        state["status"] = "resolved"

        self.logger.info(
            "seat_expansion_completed",
            has_opportunity=expansion_opportunity["has_opportunity"],
            recommended_seats=recommended_package.get("seats", 0),
            expansion_arr=expansion_value.get("annual_expansion_revenue", 0)
        )

        return state

    def _analyze_seat_usage(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Analyze current seat usage patterns"""
        current_seats = customer_metadata.get("seat_count", 0)
        active_users = customer_metadata.get("active_users", 0)
        total_users = customer_metadata.get("total_users", 0)

        utilization = (active_users / current_seats * 100) if current_seats > 0 else 0
        capacity_remaining = current_seats - active_users

        return {
            "current_seats": current_seats,
            "active_users": active_users,
            "total_users": total_users,
            "utilization_percentage": round(utilization, 2),
            "capacity_remaining": max(0, capacity_remaining),
            "status": self._determine_capacity_status(utilization)
        }

    def _determine_capacity_status(self, utilization: float) -> str:
        """Determine seat capacity status"""
        if utilization >= 90:
            return "at_capacity"
        elif utilization >= 75:
            return "high_usage"
        elif utilization >= 50:
            return "moderate_usage"
        else:
            return "low_usage"

    def _identify_expansion_signals(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Identify signals indicating need for more seats"""
        signals = {
            "has_expansion_need": False,
            "expansion_score": 0.0,
            "signals_detected": [],
            "urgency": "low"
        }

        total_weight = 0
        weighted_score = 0

        for signal_name, config in self.EXPANSION_SIGNALS.items():
            metric = config["metric"]
            threshold = config["threshold"]
            weight = config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            if actual_value >= threshold:
                weighted_score += weight
                signals["signals_detected"].append({
                    "signal": signal_name,
                    "indicator": config["indicator"],
                    "value": actual_value
                })

        signals["expansion_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0,
            2
        )
        signals["has_expansion_need"] = signals["expansion_score"] >= 40

        # Determine urgency
        if signals["expansion_score"] >= 70:
            signals["urgency"] = "high"
        elif signals["expansion_score"] >= 50:
            signals["urgency"] = "medium"
        else:
            signals["urgency"] = "low"

        return signals

    def _calculate_expansion_opportunity(
        self,
        seat_analysis: Dict,
        expansion_signals: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate seat expansion opportunity size"""
        # Calculate recommended additional seats
        new_users_monthly = customer_metadata.get("new_users_last_30_days", 0)
        waitlisted_users = customer_metadata.get("users_on_waitlist", 0)
        growth_rate = customer_metadata.get("user_growth_rate_percentage", 10)

        # Project 6-month need
        monthly_avg_growth = max(new_users_monthly, 3)
        projected_6_month_growth = monthly_avg_growth * 6
        buffer_seats = int(projected_6_month_growth * 0.20)  # 20% buffer

        recommended_seats = waitlisted_users + projected_6_month_growth + buffer_seats

        return {
            "has_opportunity": expansion_signals["has_expansion_need"],
            "recommended_additional_seats": recommended_seats,
            "immediate_need": waitlisted_users,
            "projected_6_month_need": projected_6_month_growth,
            "buffer_recommended": buffer_seats,
            "confidence": expansion_signals["expansion_score"]
        }

    def _recommend_seat_package(
        self,
        opportunity: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Recommend appropriate seat package"""
        recommended_seats = opportunity["recommended_additional_seats"]

        # Select package based on seat count
        if recommended_seats >= 50:
            package_key = "enterprise_growth"
        elif recommended_seats >= 25:
            package_key = "large_growth"
        elif recommended_seats >= 10:
            package_key = "medium_growth"
        else:
            package_key = "small_growth"

        package_info = self.SEAT_PACKAGES[package_key]
        plan_tier = customer_metadata.get("plan_tier", "professional")
        seat_price = self.SEAT_PRICING.get(plan_tier, 40)

        # Calculate pricing
        seats_to_purchase = package_info["seats"]
        discount = package_info["discount"]
        discounted_price = seat_price * (1 - discount)

        return {
            "package_key": package_key,
            "package_name": package_info["name"],
            "seats": seats_to_purchase,
            "regular_price_per_seat": seat_price,
            "discounted_price_per_seat": round(discounted_price, 2),
            "discount_percentage": discount * 100,
            "total_monthly": round(seats_to_purchase * discounted_price, 2),
            "total_annual": round(seats_to_purchase * discounted_price * 12, 2)
        }

    def _calculate_expansion_value(
        self,
        package: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate value delivered by seat expansion"""
        seats = package["seats"]
        monthly_cost = package["total_monthly"]
        annual_cost = package["total_annual"]

        # Calculate business value
        avg_employee_productivity = 50000  # Annual productivity value per user
        productivity_value = seats * avg_employee_productivity

        # Calculate saved cost (vs hiring delays)
        hiring_delay_cost = seats * 5000  # Cost per delayed hire

        # Calculate ROI
        total_value = productivity_value
        roi_percentage = ((total_value - annual_cost) / annual_cost) * 100 if annual_cost > 0 else 0

        return {
            "monthly_expansion_revenue": monthly_cost,
            "annual_expansion_revenue": annual_cost,
            "productivity_value_unlocked": productivity_value,
            "hiring_delay_cost_avoided": hiring_delay_cost,
            "roi_percentage": round(roi_percentage, 2),
            "cost_per_productive_user": round(monthly_cost / seats, 2) if seats > 0 else 0
        }

    def _build_expansion_proposal(
        self,
        package: Dict,
        expansion_value: Dict,
        signals: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Build seat expansion proposal"""
        return {
            "customer": customer_metadata.get("company", "Customer"),
            "current_seats": customer_metadata.get("seat_count", 0),
            "recommended_additional_seats": package["seats"],
            "package_name": package["package_name"],
            "pricing": {
                "monthly": package["total_monthly"],
                "annual": package["total_annual"],
                "per_seat_monthly": package["discounted_price_per_seat"],
                "discount": f"{package['discount_percentage']:.0f}%"
            },
            "urgency": signals["urgency"],
            "expansion_signals": len(signals["signals_detected"]),
            "value_proposition": f"Enable {package['seats']} more team members to drive ${expansion_value['productivity_value_unlocked']:,.0f} in productivity"
        }

    async def _generate_expansion_response(
        self,
        message: str,
        seat_analysis: Dict,
        signals: Dict,
        opportunity: Dict,
        package: Dict,
        proposal: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate seat expansion response"""

        # Build seat analysis context
        analysis_context = f"""
Current Seats: {seat_analysis['current_seats']}
Active Users: {seat_analysis['active_users']}
Utilization: {seat_analysis['utilization_percentage']:.0f}%
Capacity Status: {seat_analysis['status']}
"""

        # Build expansion context
        expansion_context = f"""
Expansion Opportunity:
- Additional Seats Recommended: {opportunity['recommended_additional_seats']}
- Immediate Need: {opportunity['immediate_need']} users waiting
- 6-Month Projection: {opportunity['projected_6_month_need']} new users
- Recommended Package: {package['package_name']} ({package['seats']} seats)
- Monthly Cost: ${package['total_monthly']:,.2f}
- Discount: {package['discount_percentage']:.0f}%
"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nSeat Expansion Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Seat Expansion specialist helping growing teams add the seats they need.

Customer: {customer_metadata.get('company', 'Customer')}
{analysis_context}
{expansion_context}

Your response should:
1. Acknowledge their team growth positively
2. Highlight current seat utilization and needs
3. Present specific expansion signals detected
4. Recommend the right seat package
5. Explain volume discount benefits
6. Calculate cost per user vs value per user
7. Create urgency for waiting team members
8. Make expansion easy with clear pricing
9. Be consultative and growth-focused
10. Provide next steps to add seats

Tone: Positive, growth-focused, value-driven"""

        user_prompt = f"""Customer message: {message}

Expansion Signals Detected:
{chr(10).join(f"- {s['indicator']}" for s in signals['signals_detected'][:3])}

Value Proposition:
- Only ${package['discounted_price_per_seat']:.2f}/user/month ({package['discount_percentage']:.0f}% discount)
- Enable {package['seats']} more team members immediately
- Support {opportunity['projected_6_month_need']} users growing over next 6 months

{kb_context}

Generate a compelling seat expansion recommendation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
