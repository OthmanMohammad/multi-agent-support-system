"""
Multi-Year Deal Agent - TASK-3033

Identifies and closes multi-year contracts for predictable revenue and customer commitment.
Converts annual customers into multi-year commitments with appropriate incentives.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("multi_year_deal", tier="revenue", category="monetization")
class MultiYearDeal(BaseAgent):
    """
    Multi-Year Deal Agent - Closes multi-year commitments.

    Handles:
    - Identify customers ready for multi-year commitment
    - Analyze customer stability and satisfaction
    - Calculate multi-year pricing and discounts
    - Present long-term value proposition
    - Structure payment terms
    - Negotiate multi-year contracts
    - Close multi-year deals
    - Track contract value and bookings
    """

    # Multi-year deal structures
    DEAL_STRUCTURES = {
        "two_year": {
            "term_months": 24,
            "discount": 0.15,  # 15% discount
            "payment_options": ["annual", "upfront"],
            "min_arr": 10000,
            "ideal_customer_profile": ["stable", "satisfied", "growing"]
        },
        "three_year": {
            "term_months": 36,
            "discount": 0.20,  # 20% discount
            "payment_options": ["annual", "upfront"],
            "min_arr": 25000,
            "ideal_customer_profile": ["enterprise", "strategic", "committed"]
        },
        "five_year": {
            "term_months": 60,
            "discount": 0.25,  # 25% discount
            "payment_options": ["annual", "upfront", "quarterly"],
            "min_arr": 100000,
            "ideal_customer_profile": ["enterprise", "mission_critical", "partner"]
        }
    }

    # Qualification criteria for multi-year deals
    QUALIFICATION_CRITERIA = {
        "customer_health": {
            "metrics": [
                {"metric": "nps_score", "threshold": 8, "weight": 0.25},
                {"metric": "feature_adoption_rate", "threshold": 0.70, "weight": 0.20},
                {"metric": "support_satisfaction", "threshold": 4.0, "weight": 0.15}
            ]
        },
        "financial_stability": {
            "metrics": [
                {"metric": "account_age_days", "threshold": 180, "weight": 0.20},
                {"metric": "payment_history_score", "threshold": 95, "weight": 0.10},
                {"metric": "current_arr", "threshold": 10000, "weight": 0.10}
            ]
        }
    }

    # Value drivers for multi-year commitment
    VALUE_DRIVERS = {
        "price_lock": "Lock in current pricing for entire term",
        "discount": "Significant discount vs year-by-year",
        "predictability": "Budget certainty for multi-year planning",
        "priority_roadmap": "Influence on product roadmap",
        "dedicated_csm": "Dedicated customer success manager",
        "priority_support": "Priority support and SLAs"
    }

    def __init__(self):
        config = AgentConfig(
            name="multi_year_deal",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20241022",  # Sonnet for complex deal structuring
            temperature=0.4,
            max_tokens=700,
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
        Identify and close multi-year deal opportunities.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with multi-year deal proposal
        """
        self.logger.info("multi_year_deal_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Qualify for multi-year deal
        qualification = self._qualify_for_multi_year(customer_metadata)

        # Determine optimal deal structure
        recommended_structure = self._recommend_deal_structure(
            qualification,
            customer_metadata
        )

        # Calculate multi-year pricing
        pricing_proposal = self._calculate_multi_year_pricing(
            recommended_structure,
            customer_metadata
        )

        # Build value proposition
        value_proposition = self._build_value_proposition(
            recommended_structure,
            pricing_proposal,
            customer_metadata
        )

        # Structure payment terms
        payment_options = self._structure_payment_terms(
            pricing_proposal,
            recommended_structure
        )

        # Calculate metrics (TCV, ACV, etc.)
        deal_metrics = self._calculate_deal_metrics(
            pricing_proposal,
            recommended_structure
        )

        # Generate negotiation framework
        negotiation_framework = self._generate_negotiation_framework(
            pricing_proposal,
            customer_metadata
        )

        # Search KB for multi-year deal resources
        kb_results = await self.search_knowledge_base(
            "multi-year contract enterprise commitment",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_deal_response(
            message,
            qualification,
            recommended_structure,
            pricing_proposal,
            value_proposition,
            payment_options,
            deal_metrics,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.86
        state["multi_year_qualification"] = qualification
        state["recommended_structure"] = recommended_structure
        state["pricing_proposal"] = pricing_proposal
        state["value_proposition"] = value_proposition
        state["payment_options"] = payment_options
        state["deal_metrics"] = deal_metrics
        state["status"] = "resolved"

        # Escalate large deals
        if deal_metrics.get("tcv", 0) >= 100000:
            state["should_escalate"] = True
            state["escalation_reason"] = f"Large multi-year deal: ${deal_metrics['tcv']:,.0f} TCV"

        self.logger.info(
            "multi_year_deal_completed",
            qualified=qualification["is_qualified"],
            recommended_term=recommended_structure,
            tcv=deal_metrics.get("tcv", 0)
        )

        return state

    def _qualify_for_multi_year(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Qualify customer for multi-year commitment"""
        qualification = {
            "is_qualified": False,
            "qualification_score": 0.0,
            "strengths": [],
            "concerns": []
        }

        total_weight = 0
        weighted_score = 0

        # Check customer health metrics
        for metric_config in self.QUALIFICATION_CRITERIA["customer_health"]["metrics"]:
            metric = metric_config["metric"]
            threshold = metric_config["threshold"]
            weight = metric_config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            if actual_value >= threshold:
                weighted_score += weight
                qualification["strengths"].append(f"Strong {metric}")
            else:
                qualification["concerns"].append(f"Low {metric}")

        # Check financial stability
        for metric_config in self.QUALIFICATION_CRITERIA["financial_stability"]["metrics"]:
            metric = metric_config["metric"]
            threshold = metric_config["threshold"]
            weight = metric_config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            if actual_value >= threshold:
                weighted_score += weight
                qualification["strengths"].append(f"Good {metric}")
            else:
                qualification["concerns"].append(f"Concern: {metric}")

        qualification["qualification_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0,
            2
        )
        qualification["is_qualified"] = qualification["qualification_score"] >= 70

        return qualification

    def _recommend_deal_structure(
        self,
        qualification: Dict,
        customer_metadata: Dict
    ) -> str:
        """Recommend optimal multi-year deal structure"""
        current_arr = customer_metadata.get("current_arr", 0)
        company_size = customer_metadata.get("company_size", 0)
        qualification_score = qualification["qualification_score"]

        # Enterprise 5-year deals
        if current_arr >= 100000 and company_size >= 500 and qualification_score >= 85:
            return "five_year"
        # Strategic 3-year deals
        elif current_arr >= 25000 and company_size >= 100 and qualification_score >= 75:
            return "three_year"
        # Standard 2-year deals
        elif current_arr >= 10000 and qualification_score >= 70:
            return "two_year"
        else:
            return "two_year"  # Default

    def _calculate_multi_year_pricing(
        self,
        structure: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate multi-year deal pricing"""
        deal_config = self.DEAL_STRUCTURES[structure]
        current_arr = customer_metadata.get("current_arr", 0)

        # Base multi-year value (current ARR * years)
        years = deal_config["term_months"] / 12
        base_multi_year_value = current_arr * years

        # Apply discount
        discount_percentage = deal_config["discount"]
        discount_amount = base_multi_year_value * discount_percentage
        discounted_total = base_multi_year_value - discount_amount

        # Annual pricing
        discounted_arr = discounted_total / years

        return {
            "structure": structure,
            "term_years": years,
            "term_months": deal_config["term_months"],
            "base_arr": current_arr,
            "discounted_arr": round(discounted_arr, 2),
            "base_multi_year_value": round(base_multi_year_value, 2),
            "discount_percentage": discount_percentage * 100,
            "discount_amount": round(discount_amount, 2),
            "total_contract_value": round(discounted_total, 2),
            "annual_savings": round(current_arr - discounted_arr, 2),
            "total_savings": round(discount_amount, 2)
        }

    def _build_value_proposition(
        self,
        structure: str,
        pricing: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Build multi-year value proposition"""
        deal_config = self.DEAL_STRUCTURES[structure]

        benefits = []
        for key, description in self.VALUE_DRIVERS.items():
            if key == "discount":
                benefits.append(f"Save ${pricing['total_savings']:,.0f} over {pricing['term_years']:.0f} years")
            elif key == "price_lock":
                benefits.append("Lock in pricing - avoid future rate increases")
            elif key == "dedicated_csm" and structure in ["three_year", "five_year"]:
                benefits.append("Dedicated customer success manager included")
            elif key == "priority_roadmap" and structure == "five_year":
                benefits.append("Strategic input on product roadmap")
            else:
                benefits.append(description)

        return {
            "headline": f"{pricing['term_years']:.0f}-Year Partnership - Save ${pricing['total_savings']:,.0f}",
            "key_benefits": benefits[:5],
            "risk_mitigation": "Flexible terms and performance guarantees",
            "strategic_value": "Long-term partnership with dedicated support"
        }

    def _structure_payment_terms(
        self,
        pricing: Dict,
        structure: str
    ) -> List[Dict[str, Any]]:
        """Structure payment term options"""
        deal_config = self.DEAL_STRUCTURES[structure]
        tcv = pricing["total_contract_value"]
        arr = pricing["discounted_arr"]

        options = []

        # Annual payments
        if "annual" in deal_config["payment_options"]:
            options.append({
                "option": "Annual Payments",
                "frequency": "Annual",
                "amount_per_payment": round(arr, 2),
                "total_payments": int(pricing["term_years"]),
                "total_cost": round(tcv, 2),
                "discount": f"{pricing['discount_percentage']:.0f}%",
                "recommended": True
            })

        # Upfront payment (additional discount)
        if "upfront" in deal_config["payment_options"]:
            upfront_discount = 0.05  # Additional 5% for upfront
            upfront_total = tcv * (1 - upfront_discount)
            options.append({
                "option": "Upfront Payment",
                "frequency": "One-time",
                "amount_per_payment": round(upfront_total, 2),
                "total_payments": 1,
                "total_cost": round(upfront_total, 2),
                "discount": f"{(pricing['discount_percentage'] + upfront_discount * 100):.0f}%",
                "additional_savings": round(tcv - upfront_total, 2),
                "recommended": False
            })

        # Quarterly payments (if available)
        if "quarterly" in deal_config["payment_options"]:
            quarterly_amount = arr / 4
            options.append({
                "option": "Quarterly Payments",
                "frequency": "Quarterly",
                "amount_per_payment": round(quarterly_amount, 2),
                "total_payments": int(pricing["term_years"] * 4),
                "total_cost": round(tcv, 2),
                "discount": f"{pricing['discount_percentage']:.0f}%",
                "recommended": False
            })

        return options

    def _calculate_deal_metrics(
        self,
        pricing: Dict,
        structure: str
    ) -> Dict[str, Any]:
        """Calculate key deal metrics"""
        return {
            "tcv": pricing["total_contract_value"],  # Total Contract Value
            "acv": pricing["discounted_arr"],  # Annual Contract Value
            "term_months": pricing["term_months"],
            "term_years": pricing["term_years"],
            "discount_percentage": pricing["discount_percentage"],
            "total_savings": pricing["total_savings"],
            "bookings": pricing["total_contract_value"],  # Full TCV booked
            "deal_size_category": self._categorize_deal_size(pricing["total_contract_value"])
        }

    def _categorize_deal_size(self, tcv: float) -> str:
        """Categorize deal by size"""
        if tcv >= 500000:
            return "mega_deal"
        elif tcv >= 250000:
            return "enterprise"
        elif tcv >= 100000:
            return "mid_market"
        else:
            return "standard"

    def _generate_negotiation_framework(
        self,
        pricing: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate framework for deal negotiation"""
        return {
            "anchor_price": pricing["total_contract_value"],
            "walk_away_price": pricing["total_contract_value"] * 0.85,  # 15% max negotiation room
            "concessions_available": [
                "Additional training sessions",
                "Extended support hours",
                "Quarterly business reviews",
                "Priority feature requests"
            ],
            "non_negotiables": [
                "Minimum term length",
                "Payment terms"
            ],
            "escalation_threshold": pricing["total_contract_value"] * 0.90
        }

    async def _generate_deal_response(
        self,
        message: str,
        qualification: Dict,
        structure: str,
        pricing: Dict,
        value_proposition: Dict,
        payment_options: List[Dict],
        deal_metrics: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate multi-year deal response"""

        # Build qualification context
        qual_context = f"""
Qualification Score: {qualification['qualification_score']}/100
Strengths: {', '.join(qualification['strengths'][:3])}
Recommended Term: {pricing['term_years']:.0f} years
"""

        # Build deal context
        deal_context = f"""
Multi-Year Deal Proposal:
- Term: {pricing['term_years']:.0f} years ({pricing['term_months']} months)
- Total Contract Value: ${deal_metrics['tcv']:,.0f}
- Annual Value: ${deal_metrics['acv']:,.0f}/year
- Discount: {pricing['discount_percentage']:.0f}%
- Total Savings: ${pricing['total_savings']:,.0f}
- Deal Category: {deal_metrics['deal_size_category']}
"""

        # Build payment options context
        payment_context = "\n\nPayment Options:\n"
        for option in payment_options:
            payment_context += f"- {option['option']}: {option['frequency']} payments of ${option['amount_per_payment']:,.0f}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nMulti-Year Contract Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Multi-Year Deal specialist structuring long-term partnerships.

Customer: {customer_metadata.get('company', 'Customer')}
Current ARR: ${customer_metadata.get('current_arr', 0):,.0f}
{qual_context}
{deal_context}

Your response should:
1. Position multi-year as a strategic partnership
2. Emphasize mutual long-term commitment
3. Highlight significant cost savings
4. Present pricing protection against future increases
5. Explain enhanced benefits and priority
6. Show flexible payment options
7. Address concerns about long-term commitment
8. Create urgency around current pricing
9. Make decision easy with clear value
10. Provide path to signature

Tone: Strategic, partnership-focused, value-driven"""

        user_prompt = f"""Customer message: {message}

Value Proposition:
{value_proposition['headline']}

Key Benefits:
{chr(10).join(f'- {benefit}' for benefit in value_proposition['key_benefits'])}

{payment_context}

{kb_context}

Generate a compelling multi-year deal proposal."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
