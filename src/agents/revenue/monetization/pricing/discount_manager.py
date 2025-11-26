"""
Discount Manager Agent - TASK-3042

Manages discount approvals and prevents revenue leakage from excessive discounting.
Enforces discount policies and tracks discount effectiveness.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("discount_manager", tier="revenue", category="monetization")
class DiscountManager(BaseAgent):
    """
    Discount Manager Agent - Controls discounting and prevents revenue leakage.

    Handles:
    - Review discount requests
    - Apply discount approval policies
    - Calculate discount impact
    - Prevent excessive discounting
    - Track discount patterns
    - Recommend strategic discounts
    - Monitor discount effectiveness
    - Enforce discount governance
    """

    # Discount approval tiers
    APPROVAL_TIERS = {
        "automatic": {
            "max_percentage": 5,
            "description": "Auto-approved standard discounts",
            "approver": "system",
            "conditions": ["new_customer", "annual_prepay"],
        },
        "manager": {
            "max_percentage": 15,
            "description": "Manager approval required",
            "approver": "sales_manager",
            "conditions": ["multi_year", "large_deal"],
        },
        "director": {
            "max_percentage": 25,
            "description": "Director approval required",
            "approver": "sales_director",
            "conditions": ["strategic_account", "competitive_threat"],
        },
        "vp": {
            "max_percentage": 35,
            "description": "VP approval required",
            "approver": "vp_sales",
            "conditions": ["enterprise_deal", "exceptional_case"],
        },
    }

    # Discount justification reasons
    VALID_JUSTIFICATIONS = {
        "competitive_match": {
            "weight": 0.80,
            "description": "Matching competitor pricing",
            "requires_evidence": True,
        },
        "multi_year_commitment": {
            "weight": 0.90,
            "description": "3+ year contract commitment",
            "requires_evidence": False,
        },
        "volume_discount": {
            "weight": 0.85,
            "description": "Large seat/volume purchase",
            "requires_evidence": False,
        },
        "strategic_account": {
            "weight": 0.75,
            "description": "Strategic importance to business",
            "requires_evidence": True,
        },
        "budget_constraint": {
            "weight": 0.40,
            "description": "Customer budget limitations",
            "requires_evidence": True,
        },
        "annual_prepay": {
            "weight": 0.95,
            "description": "Annual upfront payment",
            "requires_evidence": False,
        },
    }

    # Red flags for discount requests
    DISCOUNT_RED_FLAGS = [
        "Discount requested before value discussion",
        "Discount >20% with weak justification",
        "Serial discounter (3+ times)",
        "No competitor threat validated",
        "Deal size below minimum for tier",
        "Customer hasn't seen demo yet",
    ]

    def __init__(self):
        config = AgentConfig(
            name="discount_manager",
            type=AgentType.SPECIALIST,
            # Haiku for fast discount decisions
            temperature=0.2,  # Low for policy enforcement
            max_tokens=500,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Review and approve/deny discount request.

        Args:
            state: Current agent state with discount request

        Returns:
            Updated state with discount decision
        """
        self.logger.info("discount_manager_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Extract discount request details
        discount_request = self._extract_discount_request(customer_metadata)

        # Validate discount justification
        justification_analysis = self._validate_justification(discount_request)

        # Check approval tier
        approval_tier = self._determine_approval_tier(discount_request)

        # Identify red flags
        red_flags = self._identify_red_flags(discount_request, customer_metadata)

        # Calculate discount impact
        discount_impact = self._calculate_discount_impact(discount_request, customer_metadata)

        # Make approval decision
        decision = self._make_approval_decision(
            discount_request, justification_analysis, approval_tier, red_flags, discount_impact
        )

        # Generate alternative offers
        alternatives = self._generate_alternatives(discount_request, decision, customer_metadata)

        # Generate response
        response = await self._generate_discount_response(
            message,
            discount_request,
            justification_analysis,
            approval_tier,
            red_flags,
            discount_impact,
            decision,
            alternatives,
            customer_metadata,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.95
        state["discount_request"] = discount_request
        state["justification_analysis"] = justification_analysis
        state["approval_tier"] = approval_tier
        state["discount_red_flags"] = red_flags
        state["discount_impact"] = discount_impact
        state["discount_decision"] = decision
        state["alternative_offers"] = alternatives
        state["status"] = "resolved"

        # Escalate if needs higher approval
        if decision["requires_escalation"]:
            state["should_escalate"] = True
            state["escalation_reason"] = (
                f"Discount approval needed from {approval_tier['approver']}"
            )

        self.logger.info(
            "discount_manager_completed",
            decision=decision["approved"],
            discount_percentage=discount_request.get("discount_percentage", 0),
            approval_tier=approval_tier["approver"],
        )

        return state

    def _extract_discount_request(self, customer_metadata: dict) -> dict[str, Any]:
        """Extract discount request details"""
        return {
            "discount_percentage": customer_metadata.get("requested_discount_percentage", 0),
            "discount_amount": customer_metadata.get("requested_discount_amount", 0),
            "deal_size": customer_metadata.get("deal_size", 0),
            "contract_term_months": customer_metadata.get("contract_term_months", 12),
            "justification": customer_metadata.get("discount_justification", ""),
            "competitor": customer_metadata.get("competitor_name", ""),
            "requested_by": customer_metadata.get("sales_rep", ""),
            "customer_type": customer_metadata.get("customer_type", "new"),
        }

    def _validate_justification(self, request: dict) -> dict[str, Any]:
        """Validate discount justification"""
        justification = request["justification"].lower()

        matched_reasons = []
        total_weight = 0

        for reason_key, reason_config in self.VALID_JUSTIFICATIONS.items():
            # Simple keyword matching
            if reason_key.replace("_", " ") in justification:
                matched_reasons.append(
                    {
                        "reason": reason_key,
                        "description": reason_config["description"],
                        "weight": reason_config["weight"],
                        "requires_evidence": reason_config["requires_evidence"],
                    }
                )
                total_weight += reason_config["weight"]

        # Calculate justification strength
        if matched_reasons:
            avg_weight = total_weight / len(matched_reasons)
            strength = (
                "strong" if avg_weight >= 0.80 else "moderate" if avg_weight >= 0.60 else "weak"
            )
        else:
            strength = "none"
            avg_weight = 0

        return {
            "matched_reasons": matched_reasons,
            "strength": strength,
            "weight_score": round(avg_weight, 2),
            "has_valid_justification": len(matched_reasons) > 0,
        }

    def _determine_approval_tier(self, request: dict) -> dict[str, Any]:
        """Determine required approval tier"""
        discount_pct = request["discount_percentage"]

        for tier_name, tier_config in self.APPROVAL_TIERS.items():
            if discount_pct <= tier_config["max_percentage"]:
                return {
                    "tier": tier_name,
                    "max_percentage": tier_config["max_percentage"],
                    "approver": tier_config["approver"],
                    "description": tier_config["description"],
                }

        # Exceeds all tiers - needs CEO
        return {
            "tier": "ceo",
            "max_percentage": discount_pct,
            "approver": "ceo",
            "description": "Exceptional discount requires CEO approval",
        }

    def _identify_red_flags(self, request: dict, customer_metadata: dict) -> list[str]:
        """Identify red flags in discount request"""
        flags = []

        # High discount with weak justification
        if request["discount_percentage"] > 20 and request["justification"] == "":
            flags.append("Discount >20% with no justification provided")

        # Discount requested too early
        if not customer_metadata.get("demo_completed", True):
            flags.append("Discount requested before product demo")

        # Serial discounter
        if customer_metadata.get("previous_discount_requests", 0) >= 3:
            flags.append("Customer has requested discounts 3+ times")

        # Competitor not validated
        if "competitive" in request["justification"].lower() and not request["competitor"]:
            flags.append("Competitive threat mentioned but competitor not specified")

        # Small deal size
        if request["deal_size"] < 5000 and request["discount_percentage"] > 15:
            flags.append("High discount on small deal (low ROI)")

        return flags

    def _calculate_discount_impact(self, request: dict, customer_metadata: dict) -> dict[str, Any]:
        """Calculate financial impact of discount"""
        deal_size = request["deal_size"]
        discount_pct = request["discount_percentage"] / 100
        term_months = request["contract_term_months"]

        # Calculate discount amount
        discount_amount = deal_size * discount_pct
        discounted_price = deal_size - discount_amount

        # Calculate annual impact
        deal_size * (12 / term_months) if term_months > 0 else deal_size
        annual_discount_cost = (
            discount_amount * (12 / term_months) if term_months > 0 else discount_amount
        )

        # Calculate total contract impact

        return {
            "original_price": deal_size,
            "discount_amount": round(discount_amount, 2),
            "discounted_price": round(discounted_price, 2),
            "annual_revenue_impact": round(annual_discount_cost, 2),
            "total_contract_value": round(discounted_price, 2),
            "revenue_leakage_percentage": round(discount_pct * 100, 2),
        }

    def _make_approval_decision(
        self,
        request: dict,
        justification: dict,
        approval_tier: dict,
        red_flags: list[str],
        impact: dict,
    ) -> dict[str, Any]:
        """Make final approval decision"""
        discount_pct = request["discount_percentage"]

        # Auto-deny conditions
        if len(red_flags) >= 3:
            return {
                "approved": False,
                "reason": "Multiple red flags detected",
                "requires_escalation": False,
                "alternative_action": "Address red flags and resubmit",
            }

        if discount_pct > 35:
            return {
                "approved": False,
                "reason": "Discount exceeds maximum threshold (35%)",
                "requires_escalation": True,
                "alternative_action": "CEO approval required",
            }

        # Auto-approve conditions
        if discount_pct <= 5 and len(red_flags) == 0:
            return {
                "approved": True,
                "reason": "Within auto-approval threshold",
                "requires_escalation": False,
                "conditions": ["Standard discount terms apply"],
            }

        # Conditional approval
        if justification["strength"] in ["strong", "moderate"] and len(red_flags) <= 1:
            return {
                "approved": True,
                "reason": f"Valid justification with {justification['strength']} support",
                "requires_escalation": approval_tier["tier"] not in ["automatic", "manager"],
                "conditions": [
                    f"Requires {approval_tier['approver']} approval",
                    "Justification must be documented",
                    "Competitor evidence required"
                    if "competitive" in request["justification"].lower()
                    else None,
                ],
                "approver": approval_tier["approver"],
            }

        # Default to escalation
        return {
            "approved": False,
            "reason": "Requires additional review",
            "requires_escalation": True,
            "alternative_action": f"Submit to {approval_tier['approver']} for review",
        }

    def _generate_alternatives(
        self, request: dict, decision: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Generate alternative offers if discount denied"""
        if decision["approved"]:
            return []

        alternatives = []

        # Smaller discount
        if request["discount_percentage"] > 10:
            alternatives.append(
                {
                    "option": "Reduce discount to 10%",
                    "benefit": "Within standard approval range",
                    "trade_off": f"${request['deal_size'] * 0.10:,.0f} discount vs ${request['deal_size'] * (request['discount_percentage'] / 100):,.0f} requested",
                }
            )

        # Extended term
        alternatives.append(
            {
                "option": "3-year commitment with 15% discount",
                "benefit": "Larger discount justified by longer commitment",
                "trade_off": "3-year lock-in vs 1-year",
            }
        )

        # Value additions instead
        alternatives.append(
            {
                "option": "Include premium support package",
                "benefit": "$500/month value added at no cost",
                "trade_off": "Value add vs price reduction",
            }
        )

        # Annual prepay
        alternatives.append(
            {
                "option": "Annual prepay for 7% discount",
                "benefit": "Cash flow benefit justifies discount",
                "trade_off": "Upfront payment required",
            }
        )

        return alternatives[:3]  # Top 3

    async def _generate_discount_response(
        self,
        message: str,
        request: dict,
        justification: dict,
        approval_tier: dict,
        red_flags: list[str],
        impact: dict,
        decision: dict,
        alternatives: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate discount decision response"""

        # Build request context
        request_context = f"""
Discount Request:
- Amount: {request["discount_percentage"]}% (${impact["discount_amount"]:,.0f})
- Deal Size: ${request["deal_size"]:,.0f}
- Term: {request["contract_term_months"]} months
- Justification: {request["justification"]}
"""

        # Build justification context
        just_context = f"""
Justification Analysis:
- Strength: {justification["strength"]}
- Valid Reasons: {len(justification["matched_reasons"])}
- Weight Score: {justification["weight_score"]}
"""

        # Build red flags context
        flags_context = ""
        if red_flags:
            flags_context = "\n\nRed Flags Detected:\n"
            flags_context += "\n".join(f"- {flag}" for flag in red_flags)

        # Build decision context
        decision_context = f"""
Decision: {"APPROVED" if decision["approved"] else "DENIED"}
Reason: {decision["reason"]}
"""
        if decision.get("requires_escalation"):
            decision_context += f"Escalation Required: {approval_tier['approver']}\n"

        # Build alternatives context
        alt_context = ""
        if alternatives:
            alt_context = "\n\nAlternative Options:\n"
            for alt in alternatives:
                alt_context += f"- {alt['option']}: {alt['benefit']}\n"

        system_prompt = f"""You are a Discount Manager enforcing pricing discipline.

{request_context}
{just_context}
{decision_context}

Your response should:
1. Clearly state approval decision
2. Explain reasoning behind decision
3. Highlight any red flags
4. Quantify revenue impact
5. Specify approval requirements if needed
6. Suggest alternatives if denied
7. Be firm but professional
8. Protect revenue while enabling sales
9. Provide clear next steps

Tone: Professional, policy-driven, solution-oriented"""

        user_prompt = f"""Discount request: {message}

Impact Analysis:
- Revenue Leakage: ${impact["annual_revenue_impact"]:,.0f}/year
- Discounted Price: ${impact["discounted_price"]:,.0f}

{flags_context}

{alt_context}

Generate a clear discount decision response."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Discount decisions use request context
        )
        return response
