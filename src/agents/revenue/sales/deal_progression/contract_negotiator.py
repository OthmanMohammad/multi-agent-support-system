"""
Contract Negotiator Agent - TASK-1044

Negotiates contract terms, approves within limits, escalates beyond limits,
and tracks concessions to optimize deal closure while protecting margins.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("contract_negotiator", tier="revenue", category="sales")
class ContractNegotiator(BaseAgent):
    """
    Contract Negotiator Agent - Specialist in contract term negotiations.

    Handles:
    - Contract term negotiations
    - Approval within authority limits
    - Escalation beyond limits
    - Concession tracking and optimization
    - Win-win deal structuring
    """

    # Approval authority limits by deal size
    APPROVAL_LIMITS = {
        "sales_rep": {
            "max_discount": 0.10,  # 10% max discount
            "max_deal_value": 50000,
            "payment_terms": ["net_30", "quarterly"],
            "contract_length": [1],
            "can_modify_terms": False
        },
        "sales_manager": {
            "max_discount": 0.20,  # 20% max discount
            "max_deal_value": 250000,
            "payment_terms": ["net_30", "net_60", "quarterly", "annual"],
            "contract_length": [1, 2],
            "can_modify_terms": True
        },
        "sales_director": {
            "max_discount": 0.30,  # 30% max discount
            "max_deal_value": 1000000,
            "payment_terms": ["net_30", "net_60", "net_90", "quarterly", "annual"],
            "contract_length": [1, 2, 3],
            "can_modify_terms": True
        },
        "vp_sales": {
            "max_discount": 0.40,  # 40% max discount
            "max_deal_value": float('inf'),
            "payment_terms": ["any"],
            "contract_length": [1, 2, 3, 4, 5],
            "can_modify_terms": True
        }
    }

    # Common negotiation requests
    NEGOTIATION_TYPES = {
        "pricing_discount": {
            "common_requests": ["lower price", "discount", "budget constraint"],
            "negotiable": True,
            "requires_tradeoff": True
        },
        "payment_terms": {
            "common_requests": ["extended payment", "installments", "net 60", "net 90"],
            "negotiable": True,
            "requires_tradeoff": False
        },
        "contract_length": {
            "common_requests": ["shorter commitment", "month to month", "flexible term"],
            "negotiable": True,
            "requires_tradeoff": True
        },
        "additional_features": {
            "common_requests": ["extra features", "more users", "premium support"],
            "negotiable": True,
            "requires_tradeoff": True
        },
        "early_termination": {
            "common_requests": ["cancellation clause", "exit clause", "out clause"],
            "negotiable": True,
            "requires_tradeoff": True
        },
        "custom_terms": {
            "common_requests": ["custom clause", "special provision", "specific requirement"],
            "negotiable": True,
            "requires_tradeoff": True
        }
    }

    # Concession strategies (give-and-take)
    CONCESSION_STRATEGIES = {
        "discount_for_commitment": {
            "give": "pricing_discount",
            "get": "longer_contract",
            "ratio": "5% discount for each year of commitment",
            "max_discount": 0.15
        },
        "discount_for_annual": {
            "give": "pricing_discount",
            "get": "annual_payment",
            "ratio": "10% discount for annual prepayment",
            "max_discount": 0.10
        },
        "discount_for_case_study": {
            "give": "pricing_discount",
            "get": "case_study_rights",
            "ratio": "5% discount for public case study",
            "max_discount": 0.05
        },
        "discount_for_reference": {
            "give": "pricing_discount",
            "get": "reference_customer",
            "ratio": "3% discount for reference calls",
            "max_discount": 0.03
        },
        "features_for_volume": {
            "give": "additional_features",
            "get": "more_users",
            "ratio": "Upgrade tier for 50+ additional users",
            "max_discount": 0.0
        },
        "terms_for_auto_renewal": {
            "give": "flexible_terms",
            "get": "auto_renewal",
            "ratio": "Extended payment terms for auto-renewal",
            "max_discount": 0.0
        }
    }

    # Non-negotiable items
    NON_NEGOTIABLES = [
        "data_security_standards",
        "compliance_requirements",
        "intellectual_property",
        "liability_caps",
        "governing_law"
    ]

    # Concession tracking limits
    MAX_TOTAL_CONCESSIONS = 0.35  # Maximum 35% total value concession
    MAX_MARGIN_EROSION = 0.50  # Never go below 50% margin

    # Deal scoring factors
    DEAL_QUALITY_FACTORS = {
        "strategic_account": 1.3,  # Strategic accounts worth more
        "expansion_potential": 1.2,  # High expansion potential
        "reference_value": 1.15,  # Good reference customer
        "market_entry": 1.25,  # New market entry
        "competitive_win": 1.2,  # Win from competitor
        "standard_deal": 1.0  # Baseline
    }

    # Escalation triggers
    ESCALATION_TRIGGERS = {
        "discount_exceeded": "Requested discount exceeds approval authority",
        "payment_terms_unusual": "Non-standard payment terms requested",
        "custom_legal_terms": "Custom legal terms require legal review",
        "below_margin_threshold": "Deal would fall below minimum margin",
        "high_risk_customer": "Customer presents credit or compliance risk",
        "strategic_importance": "Strategic deal requiring executive approval"
    }

    def __init__(self):
        config = AgentConfig(
            name="contract_negotiator",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=1500,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process contract negotiation request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with negotiation outcome
        """
        self.logger.info("contract_negotiator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        deal_details = state.get("deal_details", {})
        current_proposal = state.get("current_proposal", {})

        self.logger.debug(
            "negotiation_details",
            deal_value=deal_details.get("deal_value", 0),
            current_discount=current_proposal.get("discount", 0)
        )

        # Identify negotiation request type
        negotiation_request = self._identify_negotiation_request(message)

        # Get current authority level
        authority_level = self._determine_authority_level(deal_details)

        # Extract requested concessions
        requested_concessions = self._extract_requested_concessions(
            message,
            negotiation_request,
            current_proposal
        )

        # Check if within approval limits
        approval_check = self._check_approval_authority(
            requested_concessions,
            authority_level,
            deal_details
        )

        # Identify counter-offer opportunities
        counter_offers = self._identify_counter_offers(
            requested_concessions,
            deal_details,
            current_proposal
        )

        # Calculate deal impact
        deal_impact = self._calculate_deal_impact(
            requested_concessions,
            counter_offers,
            deal_details,
            current_proposal
        )

        # Track concessions
        concession_tracking = self._track_concessions(
            requested_concessions,
            counter_offers,
            deal_details
        )

        # Make negotiation decision
        negotiation_decision = self._make_negotiation_decision(
            approval_check,
            deal_impact,
            concession_tracking,
            deal_details
        )

        # Generate negotiation strategy
        strategy = self._generate_negotiation_strategy(
            negotiation_request,
            negotiation_decision,
            counter_offers,
            deal_details
        )

        # Search KB for negotiation best practices
        kb_results = await self.search_knowledge_base(
            f"contract negotiation {negotiation_request['type']}",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_negotiation_response(
            message,
            negotiation_decision,
            counter_offers,
            strategy,
            concession_tracking,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.87
        state["negotiation_request"] = negotiation_request
        state["authority_level"] = authority_level
        state["requested_concessions"] = requested_concessions
        state["approval_check"] = approval_check
        state["counter_offers"] = counter_offers
        state["deal_impact"] = deal_impact
        state["concession_tracking"] = concession_tracking
        state["negotiation_decision"] = negotiation_decision
        state["negotiation_strategy"] = strategy
        state["deal_stage"] = "negotiation"
        state["status"] = "escalated" if negotiation_decision["requires_escalation"] else "resolved"

        self.logger.info(
            "contract_negotiator_completed",
            decision=negotiation_decision["action"],
            escalated=negotiation_decision["requires_escalation"],
            concession_value=concession_tracking["total_concession_value"]
        )

        return state

    def _identify_negotiation_request(self, message: str) -> Dict[str, Any]:
        """Identify the type of negotiation request"""
        message_lower = message.lower()

        for neg_type, details in self.NEGOTIATION_TYPES.items():
            if any(request in message_lower for request in details["common_requests"]):
                return {
                    "type": neg_type,
                    "negotiable": details["negotiable"],
                    "requires_tradeoff": details["requires_tradeoff"]
                }

        return {
            "type": "general",
            "negotiable": True,
            "requires_tradeoff": False
        }

    def _determine_authority_level(self, deal_details: Dict) -> str:
        """Determine appropriate authority level based on deal size"""
        deal_value = deal_details.get("deal_value", 0)

        if deal_value <= self.APPROVAL_LIMITS["sales_rep"]["max_deal_value"]:
            return "sales_rep"
        elif deal_value <= self.APPROVAL_LIMITS["sales_manager"]["max_deal_value"]:
            return "sales_manager"
        elif deal_value <= self.APPROVAL_LIMITS["sales_director"]["max_deal_value"]:
            return "sales_director"
        else:
            return "vp_sales"

    def _extract_requested_concessions(
        self,
        message: str,
        negotiation_request: Dict,
        current_proposal: Dict
    ) -> Dict[str, Any]:
        """Extract specific concessions being requested"""
        message_lower = message.lower()
        concessions = {}

        # Extract discount request
        if "discount" in message_lower or "%" in message:
            import re
            percentages = re.findall(r'(\d+)%', message)
            if percentages:
                concessions["discount"] = float(percentages[0]) / 100
            else:
                concessions["discount"] = 0.15  # Default 15% request

        # Extract payment terms
        if "net 60" in message_lower:
            concessions["payment_terms"] = "net_60"
        elif "net 90" in message_lower:
            concessions["payment_terms"] = "net_90"
        elif "quarterly" in message_lower:
            concessions["payment_terms"] = "quarterly"

        # Extract contract length changes
        if "month to month" in message_lower or "monthly" in message_lower:
            concessions["contract_length"] = 0  # Month-to-month
        elif "shorter" in message_lower:
            concessions["contract_length"] = 1  # 1 year

        # Additional features
        if "more users" in message_lower or "additional users" in message_lower:
            concessions["additional_users"] = True

        return concessions

    def _check_approval_authority(
        self,
        concessions: Dict,
        authority_level: str,
        deal_details: Dict
    ) -> Dict[str, Any]:
        """Check if concessions are within approval authority"""
        limits = self.APPROVAL_LIMITS[authority_level]
        within_authority = True
        blockers = []

        # Check discount
        requested_discount = concessions.get("discount", 0)
        if requested_discount > limits["max_discount"]:
            within_authority = False
            blockers.append(f"Discount {requested_discount:.0%} exceeds {limits['max_discount']:.0%} limit")

        # Check deal value
        deal_value = deal_details.get("deal_value", 0)
        if deal_value > limits["max_deal_value"]:
            within_authority = False
            blockers.append(f"Deal value ${deal_value:,} exceeds ${limits['max_deal_value']:,} limit")

        # Check payment terms
        payment_terms = concessions.get("payment_terms")
        if payment_terms and payment_terms not in limits["payment_terms"] and "any" not in limits["payment_terms"]:
            within_authority = False
            blockers.append(f"Payment terms {payment_terms} not approved for this level")

        return {
            "within_authority": within_authority,
            "authority_level": authority_level,
            "blockers": blockers,
            "limits": limits
        }

    def _identify_counter_offers(
        self,
        concessions: Dict,
        deal_details: Dict,
        current_proposal: Dict
    ) -> List[Dict[str, Any]]:
        """Identify potential counter-offers (give-and-take)"""
        counter_offers = []

        # If they want discount, offer strategies
        if concessions.get("discount", 0) > 0:
            # Discount for longer commitment
            counter_offers.append({
                "strategy": "discount_for_commitment",
                "offer": "Provide requested discount for 3-year commitment",
                "give": f"{concessions['discount']:.0%} discount",
                "get": "3-year contract",
                "value_impact": concessions["discount"] * 0.5  # Net 50% of discount due to longer term
            })

            # Discount for annual payment
            counter_offers.append({
                "strategy": "discount_for_annual",
                "offer": "Provide discount for annual prepayment",
                "give": "10% discount",
                "get": "Annual payment upfront",
                "value_impact": 0.05  # Net 5% cost due to time value
            })

            # Discount for case study
            if deal_details.get("company_profile", {}).get("public_company", False):
                counter_offers.append({
                    "strategy": "discount_for_case_study",
                    "offer": "Provide 5% discount for public case study rights",
                    "give": "5% discount",
                    "get": "Case study and marketing rights",
                    "value_impact": 0.03  # Marketing value offsets
                })

        # If they want more users, upgrade tier
        if concessions.get("additional_users"):
            counter_offers.append({
                "strategy": "features_for_volume",
                "offer": "Upgrade to next tier for additional users",
                "give": "Premium features",
                "get": "50+ additional users",
                "value_impact": 0.0  # Revenue positive
            })

        return counter_offers

    def _calculate_deal_impact(
        self,
        concessions: Dict,
        counter_offers: List[Dict],
        deal_details: Dict,
        current_proposal: Dict
    ) -> Dict[str, Any]:
        """Calculate financial impact of negotiation"""
        deal_value = deal_details.get("deal_value", 100000)
        current_margin = deal_details.get("margin", 0.70)

        # Calculate impact of straight concessions
        discount = concessions.get("discount", 0)
        direct_impact = deal_value * discount

        # Calculate impact with counter-offers
        best_counter_impact = 0
        if counter_offers:
            best_counter_impact = min(co["value_impact"] for co in counter_offers) * deal_value

        # Calculate new margin
        new_margin_straight = current_margin - discount
        new_margin_counter = current_margin - (best_counter_impact / deal_value if deal_value > 0 else 0)

        return {
            "deal_value": deal_value,
            "current_margin": current_margin,
            "direct_impact": direct_impact,
            "direct_impact_percentage": discount,
            "counter_offer_impact": best_counter_impact,
            "counter_offer_impact_percentage": best_counter_impact / deal_value if deal_value > 0 else 0,
            "new_margin_straight": new_margin_straight,
            "new_margin_counter": new_margin_counter,
            "margin_erosion": current_margin - new_margin_counter
        }

    def _track_concessions(
        self,
        concessions: Dict,
        counter_offers: List[Dict],
        deal_details: Dict
    ) -> Dict[str, Any]:
        """Track all concessions made in negotiation"""
        total_concession_pct = 0
        concession_list = []

        # Track requested concessions
        if "discount" in concessions:
            total_concession_pct += concessions["discount"]
            concession_list.append({
                "type": "discount",
                "value_percentage": concessions["discount"],
                "status": "requested"
            })

        # Calculate if within limits
        within_limits = total_concession_pct <= self.MAX_TOTAL_CONCESSIONS

        # Check margin
        current_margin = deal_details.get("margin", 0.70)
        new_margin = current_margin - total_concession_pct
        margin_acceptable = new_margin >= self.MAX_MARGIN_EROSION

        return {
            "concessions": concession_list,
            "total_concession_percentage": total_concession_pct,
            "total_concession_value": deal_details.get("deal_value", 0) * total_concession_pct,
            "within_limits": within_limits,
            "margin_acceptable": margin_acceptable,
            "new_margin": new_margin
        }

    def _make_negotiation_decision(
        self,
        approval_check: Dict,
        deal_impact: Dict,
        concession_tracking: Dict,
        deal_details: Dict
    ) -> Dict[str, Any]:
        """Make final negotiation decision"""
        # Check all approval criteria
        within_authority = approval_check["within_authority"]
        within_concession_limits = concession_tracking["within_limits"]
        margin_acceptable = concession_tracking["margin_acceptable"]

        # Determine action
        if within_authority and within_concession_limits and margin_acceptable:
            action = "approve"
            requires_escalation = False
            rationale = "Concessions within approval authority and margin thresholds"
        elif not margin_acceptable:
            action = "reject"
            requires_escalation = True
            rationale = "Deal would fall below minimum margin threshold"
        elif not within_authority:
            action = "escalate"
            requires_escalation = True
            rationale = "Concessions exceed current authority level"
        else:
            action = "counter_offer"
            requires_escalation = False
            rationale = "Propose alternative structure within authority"

        return {
            "action": action,
            "requires_escalation": requires_escalation,
            "rationale": rationale,
            "escalation_reasons": approval_check.get("blockers", []),
            "recommendation": self._generate_recommendation(action, deal_impact)
        }

    def _generate_recommendation(self, action: str, deal_impact: Dict) -> str:
        """Generate recommendation based on decision"""
        recommendations = {
            "approve": "Approve concessions and move forward with modified terms",
            "reject": "Decline request - deal economics not viable",
            "escalate": "Escalate to higher authority for approval",
            "counter_offer": "Present counter-offer with trade-offs"
        }
        return recommendations.get(action, "Review with management")

    def _generate_negotiation_strategy(
        self,
        negotiation_request: Dict,
        decision: Dict,
        counter_offers: List[Dict],
        deal_details: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive negotiation strategy"""
        return {
            "approach": decision["action"],
            "primary_message": decision["rationale"],
            "counter_offers": counter_offers[:2] if counter_offers else [],  # Top 2 counter-offers
            "anchoring_points": [
                "Emphasize value delivered",
                "Reference similar customer success",
                "Highlight competitive advantages"
            ],
            "negotiation_sequence": [
                "Acknowledge their request",
                "Reaffirm value proposition",
                "Present counter-offer if applicable",
                "Seek commitment on modified terms"
            ],
            "walk_away_threshold": deal_details.get("margin", 0.70) * 0.5  # Don't go below 50% of target margin
        }

    async def _generate_negotiation_response(
        self,
        message: str,
        decision: Dict,
        counter_offers: List[Dict],
        strategy: Dict,
        concession_tracking: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate negotiation response"""

        # Build counter-offers context
        counter_offers_text = ""
        if counter_offers:
            counter_offers_text = "\n\nCounter-Offer Options:\n"
            for co in counter_offers[:2]:
                counter_offers_text += f"- {co['offer']}: Give {co['give']}, Get {co['get']}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nNegotiation Best Practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Contract Negotiator specialist handling deal negotiations.

Negotiation Decision: {decision['action'].upper()}
Rationale: {decision['rationale']}
Escalation Required: {decision['requires_escalation']}

Concession Status:
- Total Requested: {concession_tracking['total_concession_percentage']:.0%}
- New Margin: {concession_tracking['new_margin']:.0%}
- Within Limits: {concession_tracking['within_limits']}

Company: {customer_metadata.get('company', 'Customer')}

Your response should:
1. Acknowledge their negotiation request professionally
2. {'Present counter-offer options with clear trade-offs' if decision['action'] == 'counter_offer' else 'Explain the decision clearly'}
3. Emphasize mutual value and win-win outcomes
4. Be firm but collaborative
5. Keep the deal momentum going
6. {'Mention escalation timeline' if decision['requires_escalation'] else 'Move toward next steps'}
7. Maintain positive relationship
8. Use confident business language"""

        user_prompt = f"""Customer message: {message}

Strategy: {strategy['approach']}

{counter_offers_text}

Negotiation Sequence:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(strategy['negotiation_sequence']))}

{kb_context}

Generate a professional negotiation response."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing ContractNegotiator Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Reasonable discount request
        state1 = create_initial_state(
            "Can you offer us a 15% discount if we commit to a 3-year contract?",
            context={
                "customer_metadata": {
                    "company": "GoodFit Corp",
                    "title": "VP Operations",
                    "company_size": 200,
                    "industry": "technology"
                },
                "deal_details": {
                    "deal_value": 120000,
                    "margin": 0.70
                },
                "current_proposal": {
                    "discount": 0.0,
                    "term": 1
                }
            }
        )

        agent = ContractNegotiator()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Reasonable Discount Request")
        print(f"Negotiation Type: {result1['negotiation_request']['type']}")
        print(f"Authority Level: {result1['authority_level']}")
        print(f"Decision: {result1['negotiation_decision']['action']}")
        print(f"Requires Escalation: {result1['negotiation_decision']['requires_escalation']}")
        print(f"Counter Offers: {len(result1['counter_offers'])}")
        print(f"New Margin: {result1['concession_tracking']['new_margin']:.0%}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Request exceeding authority
        state2 = create_initial_state(
            "We need a 35% discount and net 90 payment terms",
            context={
                "customer_metadata": {
                    "company": "BigDeal Inc",
                    "title": "CFO",
                    "company_size": 1000,
                    "industry": "finance"
                },
                "deal_details": {
                    "deal_value": 500000,
                    "margin": 0.70
                },
                "current_proposal": {
                    "discount": 0.0,
                    "payment_terms": "net_30"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Request Exceeding Authority")
        print(f"Decision: {result2['negotiation_decision']['action']}")
        print(f"Requires Escalation: {result2['negotiation_decision']['requires_escalation']}")
        print(f"Escalation Reasons: {len(result2['approval_check']['blockers'])}")
        print(f"Within Authority: {result2['approval_check']['within_authority']}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Trade-off negotiation
        state3 = create_initial_state(
            "Can we get a 10% discount? We're happy to do annual payment and provide a case study",
            context={
                "customer_metadata": {
                    "company": "Perfect Customer",
                    "title": "Director",
                    "company_size": 150,
                    "industry": "retail"
                },
                "deal_details": {
                    "deal_value": 80000,
                    "margin": 0.70,
                    "company_profile": {"public_company": True}
                },
                "current_proposal": {
                    "discount": 0.0
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Trade-off Negotiation")
        print(f"Decision: {result3['negotiation_decision']['action']}")
        print(f"Counter Offers Available: {len(result3['counter_offers'])}")
        print(f"Deal Impact: ${result3['deal_impact']['direct_impact']:,.2f}")
        print(f"Margin After Concession: {result3['deal_impact']['new_margin_counter']:.0%}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
