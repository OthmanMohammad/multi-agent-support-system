"""
Price Objection Handler Agent - TASK-1031

Handles "too expensive" objections by providing ROI justification,
payment terms, discounts, and competitor pricing comparisons.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("price_objection_handler", tier="revenue", category="sales")
class PriceObjectionHandler(BaseAgent):
    """
    Price Objection Handler Agent - Specialist in handling pricing concerns.

    Handles:
    - "Too expensive" objections
    - ROI justification and cost-benefit analysis
    - Payment terms and discounts
    - Competitor pricing comparisons
    - Value-based pricing explanations
    """

    # Response strategies for different price objection types
    RESPONSE_STRATEGIES = {
        "too_expensive": {
            "approach": "roi_justification",
            "tactics": ["show_cost_savings", "calculate_roi", "compare_alternatives"],
            "supporting_materials": ["roi_calculator", "case_studies", "cost_comparison"]
        },
        "budget_constraints": {
            "approach": "flexible_payment",
            "tactics": ["payment_plans", "phased_rollout", "starter_package"],
            "supporting_materials": ["payment_options", "pricing_tiers", "starter_guide"]
        },
        "competitor_cheaper": {
            "approach": "value_differentiation",
            "tactics": ["feature_comparison", "tco_analysis", "quality_difference"],
            "supporting_materials": ["competitive_analysis", "feature_matrix", "customer_reviews"]
        },
        "no_budget": {
            "approach": "value_demonstration",
            "tactics": ["free_trial", "pilot_program", "budget_justification_template"],
            "supporting_materials": ["trial_guide", "business_case_template", "success_stories"]
        },
        "unclear_value": {
            "approach": "value_clarification",
            "tactics": ["use_case_mapping", "roi_examples", "customer_testimonials"],
            "supporting_materials": ["value_proposition", "industry_benchmarks", "testimonials"]
        }
    }

    # Objection severity levels
    SEVERITY_INDICATORS = {
        "blocker": ["can't afford", "no budget", "way too expensive", "not in budget"],
        "major": ["too expensive", "too pricey", "costs too much", "overpriced"],
        "minor": ["a bit expensive", "seems high", "concerned about cost", "price point"]
    }

    # ROI templates by industry
    ROI_TEMPLATES = {
        "technology": {
            "time_savings": "30% reduction in development time",
            "cost_savings": "40% lower operational costs",
            "revenue_impact": "25% faster time-to-market",
            "payback_period": "6-9 months"
        },
        "healthcare": {
            "time_savings": "20 hours/week saved per clinician",
            "cost_savings": "35% reduction in administrative overhead",
            "revenue_impact": "15% increase in patient throughput",
            "payback_period": "8-12 months"
        },
        "finance": {
            "time_savings": "50% faster transaction processing",
            "cost_savings": "45% reduction in manual errors",
            "revenue_impact": "20% improvement in compliance",
            "payback_period": "4-8 months"
        },
        "retail": {
            "time_savings": "25% faster inventory management",
            "cost_savings": "30% reduction in stockouts",
            "revenue_impact": "18% increase in sales conversion",
            "payback_period": "6-10 months"
        },
        "default": {
            "time_savings": "25% productivity improvement",
            "cost_savings": "35% operational cost reduction",
            "revenue_impact": "20% faster growth",
            "payback_period": "6-12 months"
        }
    }

    # Payment options and discounts
    PAYMENT_OPTIONS = {
        "annual_discount": "20% discount on annual commitment",
        "quarterly_payment": "Quarterly payment plans available",
        "volume_discount": "Volume discounts for 50+ users",
        "startup_program": "50% off for early-stage startups",
        "nonprofit_discount": "30% discount for nonprofits",
        "pilot_pricing": "Special pilot program pricing"
    }

    # Competitor pricing positioning
    COMPETITOR_COMPARISONS = {
        "total_cost_ownership": "30% lower TCO over 3 years vs competitors",
        "no_hidden_fees": "Transparent pricing - no setup fees, no hidden costs",
        "included_features": "Support and core features included (competitors charge extra)",
        "scalability": "No pricing jumps - linear scaling as you grow",
        "flexibility": "No long-term contracts required (competitors lock you in)"
    }

    def __init__(self):
        config = AgentConfig(
            name="price_objection_handler",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=1000,
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
        Process price objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with objection handling response
        """
        self.logger.info("price_objection_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "price_objection_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Detect objection type and severity
        objection_type = self._detect_objection_type(message)
        objection_severity = self._assess_severity(message)

        # Get response strategy
        strategy = self.RESPONSE_STRATEGIES.get(objection_type, self.RESPONSE_STRATEGIES["unclear_value"])

        # Calculate ROI for prospect's industry
        roi_data = self._calculate_roi(customer_metadata)

        # Get relevant payment options
        payment_options = self._get_payment_options(customer_metadata, objection_severity)

        # Get competitor comparisons
        competitor_comparisons = self._get_competitor_comparisons(objection_type)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=4
        )
        state["kb_results"] = kb_results

        # Generate personalized response
        response = await self._generate_objection_response(
            message,
            objection_type,
            objection_severity,
            strategy,
            roi_data,
            payment_options,
            competitor_comparisons,
            kb_results,
            customer_metadata,
            state
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            objection_type,
            objection_severity,
            customer_metadata
        )

        # Determine if escalation is needed
        needs_escalation = self._check_escalation_needed(
            objection_severity,
            resolution_confidence
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["objection_type"] = objection_type
        state["objection_severity"] = objection_severity
        state["response_strategy"] = strategy
        state["roi_data"] = roi_data
        state["payment_options"] = payment_options
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "price_objection_handler_completed",
            objection_type=objection_type,
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation
        )

        return state

    def _detect_objection_type(self, message: str) -> str:
        """Detect the type of price objection from the message"""
        message_lower = message.lower()

        # Check for specific objection patterns
        if any(phrase in message_lower for phrase in ["no budget", "can't afford", "not budgeted"]):
            return "no_budget"
        elif any(phrase in message_lower for phrase in ["competitor", "cheaper", "less expensive"]):
            return "competitor_cheaper"
        elif any(phrase in message_lower for phrase in ["budget constraint", "limited budget", "tight budget"]):
            return "budget_constraints"
        elif any(phrase in message_lower for phrase in ["don't see value", "worth it", "justify", "why so expensive"]):
            return "unclear_value"
        elif any(phrase in message_lower for phrase in ["too expensive", "too pricey", "costs too much", "price"]):
            return "too_expensive"
        else:
            return "unclear_value"

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the price objection"""
        message_lower = message.lower()

        # Check severity indicators
        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"  # Default to minor if no strong indicators

    def _calculate_roi(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Calculate ROI metrics based on customer's industry and size"""
        industry = customer_metadata.get("industry", "default").lower()
        company_size = customer_metadata.get("company_size", 50)

        # Get ROI template for industry
        roi_template = self.ROI_TEMPLATES.get(industry, self.ROI_TEMPLATES["default"])

        # Calculate estimated annual savings
        estimated_cost = company_size * 50  # $50/user/month average
        estimated_savings = estimated_cost * 2.5  # 2.5x ROI on average

        return {
            "template": roi_template,
            "estimated_monthly_cost": estimated_cost,
            "estimated_annual_savings": estimated_savings,
            "roi_multiplier": "2.5x",
            "industry": industry
        }

    def _get_payment_options(self, customer_metadata: Dict, severity: str) -> List[str]:
        """Get relevant payment options based on customer profile and objection severity"""
        options = []

        company_size = customer_metadata.get("company_size", 0)
        industry = customer_metadata.get("industry", "").lower()

        # Always offer annual discount
        options.append(self.PAYMENT_OPTIONS["annual_discount"])

        # Add severity-specific options
        if severity in ["blocker", "major"]:
            options.append(self.PAYMENT_OPTIONS["quarterly_payment"])
            options.append(self.PAYMENT_OPTIONS["pilot_pricing"])

        # Add size-based options
        if company_size >= 50:
            options.append(self.PAYMENT_OPTIONS["volume_discount"])
        elif company_size < 20:
            options.append(self.PAYMENT_OPTIONS["startup_program"])

        # Add industry-specific options
        if "nonprofit" in industry or "education" in industry:
            options.append(self.PAYMENT_OPTIONS["nonprofit_discount"])

        return options

    def _get_competitor_comparisons(self, objection_type: str) -> Dict[str, str]:
        """Get relevant competitor comparisons based on objection type"""
        if objection_type == "competitor_cheaper":
            # Return all comparisons for competitor objections
            return self.COMPETITOR_COMPARISONS
        else:
            # Return selective comparisons
            return {
                "total_cost_ownership": self.COMPETITOR_COMPARISONS["total_cost_ownership"],
                "no_hidden_fees": self.COMPETITOR_COMPARISONS["no_hidden_fees"],
                "included_features": self.COMPETITOR_COMPARISONS["included_features"]
            }

    def _calculate_resolution_confidence(
        self,
        objection_type: str,
        severity: str,
        customer_metadata: Dict
    ) -> float:
        """Calculate confidence that the objection can be resolved"""
        base_confidence = 0.75

        # Adjust for severity
        severity_adjustments = {
            "minor": 0.15,
            "major": 0.0,
            "blocker": -0.15
        }
        confidence = base_confidence + severity_adjustments.get(severity, 0.0)

        # Adjust for objection type (some are easier to handle)
        type_adjustments = {
            "unclear_value": 0.10,  # Easy to clarify value
            "too_expensive": 0.05,
            "budget_constraints": 0.00,
            "competitor_cheaper": -0.05,
            "no_budget": -0.10  # Hardest to overcome
        }
        confidence += type_adjustments.get(objection_type, 0.0)

        # Adjust for company profile
        company_size = customer_metadata.get("company_size", 0)
        if company_size >= 100:
            confidence += 0.05  # Larger companies have more budget flexibility

        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1

    def _check_escalation_needed(self, severity: str, confidence: float) -> bool:
        """Determine if escalation to sales manager is needed"""
        # Escalate if blocker severity or low confidence
        if severity == "blocker":
            return True
        if confidence < 0.60:
            return True
        return False

    async def _generate_objection_response(
        self,
        message: str,
        objection_type: str,
        severity: str,
        strategy: Dict,
        roi_data: Dict,
        payment_options: List[str],
        competitor_comparisons: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict,
        state: AgentState
    ) -> str:
        """Generate personalized response to price objection"""
        # Extract conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build ROI context
        roi_context = f"""
ROI Data for {roi_data['industry'].title()} Industry:
- Time Savings: {roi_data['template']['time_savings']}
- Cost Savings: {roi_data['template']['cost_savings']}
- Revenue Impact: {roi_data['template']['revenue_impact']}
- Typical Payback: {roi_data['template']['payback_period']}
- Estimated Annual Savings: ${roi_data['estimated_annual_savings']:,.0f}
- ROI Multiplier: {roi_data['roi_multiplier']}
"""

        # Build payment options context
        payment_context = "\n\nAvailable Payment Options:\n"
        for option in payment_options:
            payment_context += f"- {option}\n"

        # Build competitor comparison context
        competitor_context = ""
        if competitor_comparisons:
            competitor_context = "\n\nCompetitive Advantages:\n"
            for key, value in competitor_comparisons.items():
                competitor_context += f"- {value}\n"

        system_prompt = f"""You are a Price Objection Handler specialist helping overcome pricing concerns.

Objection Analysis:
- Type: {objection_type.replace('_', ' ').title()}
- Severity: {severity.upper()}
- Response Strategy: {strategy['approach'].replace('_', ' ').title()}

Customer Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}
- Company Size: {customer_metadata.get('company_size', 'Unknown')}

Your response should:
1. Acknowledge their pricing concern empathetically
2. Use the {strategy['approach']} approach
3. Highlight relevant ROI metrics and cost savings
4. Present payment options that match their situation
5. Include competitive advantages when relevant
6. Be consultative and focused on value, not just price
7. Offer concrete next steps (ROI calculator, pilot program, etc.)

Key Tactics to Use: {', '.join(strategy['tactics'])}
Supporting Materials: {', '.join(strategy['supporting_materials'])}"""

        user_prompt = f"""Customer message: {message}

{roi_context}
{payment_context}
{competitor_context}
{kb_context}

Generate a empathetic, value-focused response that addresses their pricing concern."""

        response = await self.call_llm(
            system_prompt,
            user_prompt,
            conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing PriceObjectionHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Major price objection from enterprise
        state1 = create_initial_state(
            "Your product seems too expensive compared to what we're currently using",
            context={
                "customer_metadata": {
                    "company": "TechCorp Inc",
                    "title": "VP of Engineering",
                    "company_size": 300,
                    "industry": "technology",
                    "email": "vp@techcorp.com"
                }
            }
        )

        agent = PriceObjectionHandler()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Enterprise 'Too Expensive' Objection")
        print(f"Objection Type: {result1['objection_type']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Needs Escalation: {result1['needs_escalation']}")
        print(f"ROI Multiplier: {result1['roi_data']['roi_multiplier']}")
        print(f"Payment Options: {len(result1['payment_options'])}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Budget blocker from startup
        state2 = create_initial_state(
            "We love the product but we just don't have budget for this right now",
            context={
                "customer_metadata": {
                    "company": "Startup Labs",
                    "title": "Founder",
                    "company_size": 8,
                    "industry": "technology"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Startup Budget Blocker")
        print(f"Objection Type: {result2['objection_type']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Needs Escalation: {result2['needs_escalation']}")
        print(f"Payment Options: {len(result2['payment_options'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Competitor comparison objection
        state3 = create_initial_state(
            "We found a competitor that offers similar features for half the price",
            context={
                "customer_metadata": {
                    "company": "MidMarket Co",
                    "title": "Director of Operations",
                    "company_size": 150,
                    "industry": "retail"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Competitor Pricing Comparison")
        print(f"Objection Type: {result3['objection_type']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"Needs Escalation: {result3['needs_escalation']}")
        print(f"Competitor Comparisons Provided: {len(result3.get('response_strategy', {}).get('supporting_materials', []))}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
