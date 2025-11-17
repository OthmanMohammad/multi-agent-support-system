"""
Proposal Generator Agent - TASK-1043

Generates customized proposals, calculates pricing based on requirements,
creates line items, and includes terms and conditions for professional proposals.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("proposal_generator", tier="revenue", category="sales")
class ProposalGenerator(BaseAgent):
    """
    Proposal Generator Agent - Specialist in creating professional sales proposals.

    Handles:
    - Customized proposal generation
    - Pricing calculations based on requirements
    - Line item creation with detailed breakdowns
    - Terms and conditions inclusion
    - Discount and incentive structuring
    """

    # Pricing tiers and base costs
    PRICING_TIERS = {
        "starter": {
            "base_price_per_user": 50,
            "min_users": 5,
            "max_users": 50,
            "included_features": ["core", "basic_support", "basic_analytics"],
            "description": "Perfect for small teams getting started"
        },
        "professional": {
            "base_price_per_user": 100,
            "min_users": 10,
            "max_users": 500,
            "included_features": ["core", "advanced", "priority_support", "advanced_analytics", "integrations"],
            "description": "For growing teams with advanced needs"
        },
        "enterprise": {
            "base_price_per_user": 200,
            "min_users": 50,
            "max_users": 10000,
            "included_features": ["all_features", "dedicated_support", "custom_integrations", "sla", "training"],
            "description": "Complete solution for large organizations"
        }
    }

    # Add-on services and pricing
    ADD_ON_SERVICES = {
        "implementation": {
            "base_cost": 5000,
            "per_user_cost": 50,
            "description": "Professional implementation and setup",
            "duration_weeks": 4
        },
        "training": {
            "base_cost": 2000,
            "per_session_cost": 500,
            "description": "Customized training sessions",
            "duration_weeks": 2
        },
        "premium_support": {
            "monthly_cost": 1000,
            "description": "24/7 premium support with SLA",
            "response_time": "2 hours"
        },
        "custom_integration": {
            "base_cost": 10000,
            "per_integration_cost": 5000,
            "description": "Custom integration development",
            "duration_weeks": 8
        },
        "data_migration": {
            "base_cost": 3000,
            "per_gb_cost": 100,
            "description": "Data migration from legacy systems",
            "duration_weeks": 3
        },
        "dedicated_csm": {
            "monthly_cost": 2000,
            "description": "Dedicated Customer Success Manager",
            "availability": "business_hours"
        }
    }

    # Volume discounts
    VOLUME_DISCOUNTS = {
        "tier_1": {"min_users": 100, "discount": 0.10, "label": "10% volume discount"},
        "tier_2": {"min_users": 250, "discount": 0.15, "label": "15% volume discount"},
        "tier_3": {"min_users": 500, "discount": 0.20, "label": "20% volume discount"},
        "tier_4": {"min_users": 1000, "discount": 0.25, "label": "25% enterprise discount"}
    }

    # Payment terms
    PAYMENT_TERMS = {
        "monthly": {
            "multiplier": 1.0,
            "discount": 0.0,
            "terms": "Net 30"
        },
        "annual": {
            "multiplier": 10.0,  # 2 months free
            "discount": 0.17,
            "terms": "Net 30",
            "savings_description": "Save 17% with annual commitment"
        },
        "biannual": {
            "multiplier": 5.5,  # 0.5 months free
            "discount": 0.08,
            "terms": "Net 30",
            "savings_description": "Save 8% with 6-month commitment"
        }
    }

    # Contract lengths and incentives
    CONTRACT_INCENTIVES = {
        "1_year": {
            "discount": 0.0,
            "description": "Standard 1-year agreement"
        },
        "2_year": {
            "discount": 0.05,
            "description": "5% discount on 2-year commitment"
        },
        "3_year": {
            "discount": 0.10,
            "description": "10% discount on 3-year commitment"
        }
    }

    # Standard terms and conditions
    TERMS_AND_CONDITIONS = {
        "payment_terms": "Payment due within 30 days of invoice date",
        "contract_length": "Initial term as specified, auto-renewal unless cancelled 30 days prior",
        "cancellation": "30-day written notice required for cancellation",
        "support": "Standard support included during business hours (9 AM - 5 PM ET)",
        "sla": "99.9% uptime SLA for Enterprise tier",
        "data_security": "SOC 2 Type II compliant, encryption at rest and in transit",
        "price_protection": "Price lock for duration of contract term",
        "users": "User licenses can be added anytime, prorated billing applies"
    }

    # Proposal sections template
    PROPOSAL_SECTIONS = [
        "executive_summary",
        "understanding_your_needs",
        "proposed_solution",
        "pricing_breakdown",
        "implementation_plan",
        "timeline",
        "terms_and_conditions",
        "next_steps"
    ]

    def __init__(self):
        config = AgentConfig(
            name="proposal_generator",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.2,  # Low temperature for accuracy
            max_tokens=2000,
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
        Process proposal generation request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with proposal details
        """
        self.logger.info("proposal_generator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        requirements = state.get("requirements", {})

        self.logger.debug(
            "proposal_generation_details",
            company=customer_metadata.get("company", "Unknown"),
            users=requirements.get("num_users", 0)
        )

        # Extract proposal requirements
        proposal_requirements = self._extract_requirements(
            message,
            customer_metadata,
            requirements
        )

        # Determine pricing tier
        pricing_tier = self._determine_pricing_tier(proposal_requirements)

        # Calculate base pricing
        base_pricing = self._calculate_base_pricing(
            pricing_tier,
            proposal_requirements
        )

        # Calculate add-ons
        addon_pricing = self._calculate_addon_pricing(proposal_requirements)

        # Apply discounts
        discounts = self._calculate_discounts(
            base_pricing,
            proposal_requirements
        )

        # Generate line items
        line_items = self._generate_line_items(
            base_pricing,
            addon_pricing,
            discounts,
            proposal_requirements
        )

        # Calculate totals
        totals = self._calculate_totals(line_items)

        # Generate implementation timeline
        timeline = self._generate_timeline(proposal_requirements, addon_pricing)

        # Select terms and conditions
        terms = self._generate_terms(pricing_tier, proposal_requirements)

        # Create proposal summary
        proposal_summary = self._create_proposal_summary(
            proposal_requirements,
            totals,
            timeline
        )

        # Search KB for proposal templates
        kb_results = await self.search_knowledge_base(
            f"proposal template {customer_metadata.get('industry', '')}",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_proposal_response(
            message,
            proposal_summary,
            line_items,
            totals,
            timeline,
            terms,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.92
        state["proposal_requirements"] = proposal_requirements
        state["pricing_tier"] = pricing_tier
        state["base_pricing"] = base_pricing
        state["addon_pricing"] = addon_pricing
        state["discounts"] = discounts
        state["line_items"] = line_items
        state["totals"] = totals
        state["timeline"] = timeline
        state["terms"] = terms
        state["proposal_summary"] = proposal_summary
        state["deal_stage"] = "proposal_sent"
        state["status"] = "resolved"

        self.logger.info(
            "proposal_generator_completed",
            tier=pricing_tier,
            total_annual=totals["annual_total"],
            discount_applied=totals["total_discount"]
        )

        return state

    def _extract_requirements(
        self,
        message: str,
        customer_metadata: Dict,
        requirements: Dict
    ) -> Dict[str, Any]:
        """Extract proposal requirements from message and context"""
        # Get user count
        num_users = requirements.get("num_users", customer_metadata.get("company_size", 50))

        # Detect payment preference
        message_lower = message.lower()
        if "monthly" in message_lower:
            payment_term = "monthly"
        elif "annual" in message_lower or "yearly" in message_lower:
            payment_term = "annual"
        else:
            payment_term = "annual"  # Default to annual

        # Detect contract length
        if "3 year" in message_lower or "three year" in message_lower:
            contract_length = "3_year"
        elif "2 year" in message_lower or "two year" in message_lower:
            contract_length = "2_year"
        else:
            contract_length = "1_year"

        # Detect add-ons needed
        addons = []
        if "implementation" in message_lower or "onboarding" in message_lower:
            addons.append("implementation")
        if "training" in message_lower:
            addons.append("training")
        if "migration" in message_lower or "data transfer" in message_lower:
            addons.append("data_migration")
        if "integration" in message_lower:
            addons.append("custom_integration")
        if "premium support" in message_lower or "24/7" in message_lower:
            addons.append("premium_support")

        return {
            "num_users": num_users,
            "payment_term": payment_term,
            "contract_length": contract_length,
            "addons": addons,
            "industry": customer_metadata.get("industry", "technology"),
            "company": customer_metadata.get("company", "Customer"),
            "urgency": "standard"
        }

    def _determine_pricing_tier(self, requirements: Dict) -> str:
        """Determine appropriate pricing tier"""
        num_users = requirements["num_users"]

        if num_users >= self.PRICING_TIERS["enterprise"]["min_users"]:
            return "enterprise"
        elif num_users >= self.PRICING_TIERS["professional"]["min_users"]:
            return "professional"
        else:
            return "starter"

    def _calculate_base_pricing(
        self,
        tier: str,
        requirements: Dict
    ) -> Dict[str, Any]:
        """Calculate base subscription pricing"""
        tier_info = self.PRICING_TIERS[tier]
        num_users = requirements["num_users"]
        payment_term = requirements["payment_term"]

        # Base monthly per user
        monthly_per_user = tier_info["base_price_per_user"]
        monthly_total = monthly_per_user * num_users

        # Apply payment term multiplier
        payment_info = self.PAYMENT_TERMS[payment_term]
        term_total = monthly_total * payment_info["multiplier"]

        return {
            "tier": tier,
            "num_users": num_users,
            "monthly_per_user": monthly_per_user,
            "monthly_total": monthly_total,
            "annual_total": monthly_total * 12,
            "payment_term": payment_term,
            "term_total": term_total,
            "included_features": tier_info["included_features"]
        }

    def _calculate_addon_pricing(self, requirements: Dict) -> Dict[str, Any]:
        """Calculate add-on service pricing"""
        addons = {}
        total_addon_cost = 0
        total_monthly_recurring = 0

        for addon in requirements.get("addons", []):
            if addon in self.ADD_ON_SERVICES:
                addon_info = self.ADD_ON_SERVICES[addon]

                if "base_cost" in addon_info:
                    # One-time cost
                    cost = addon_info["base_cost"]
                    if "per_user_cost" in addon_info:
                        cost += addon_info["per_user_cost"] * requirements["num_users"]

                    addons[addon] = {
                        "type": "one_time",
                        "cost": cost,
                        "description": addon_info["description"]
                    }
                    total_addon_cost += cost

                elif "monthly_cost" in addon_info:
                    # Recurring monthly cost
                    cost = addon_info["monthly_cost"]

                    addons[addon] = {
                        "type": "recurring",
                        "monthly_cost": cost,
                        "annual_cost": cost * 12,
                        "description": addon_info["description"]
                    }
                    total_monthly_recurring += cost

        return {
            "addons": addons,
            "total_one_time": total_addon_cost,
            "total_monthly_recurring": total_monthly_recurring,
            "total_annual_recurring": total_monthly_recurring * 12
        }

    def _calculate_discounts(
        self,
        base_pricing: Dict,
        requirements: Dict
    ) -> Dict[str, Any]:
        """Calculate applicable discounts"""
        discounts = []
        total_discount_amount = 0
        discount_percentage = 0.0

        num_users = requirements["num_users"]
        payment_term = requirements["payment_term"]
        contract_length = requirements["contract_length"]

        # Volume discount
        for tier_key in sorted(self.VOLUME_DISCOUNTS.keys(), reverse=True):
            tier = self.VOLUME_DISCOUNTS[tier_key]
            if num_users >= tier["min_users"]:
                discount_pct = tier["discount"]
                discount_amt = base_pricing["term_total"] * discount_pct
                discounts.append({
                    "type": "volume",
                    "label": tier["label"],
                    "percentage": discount_pct,
                    "amount": discount_amt
                })
                total_discount_amount += discount_amt
                discount_percentage += discount_pct
                break

        # Payment term discount
        payment_info = self.PAYMENT_TERMS[payment_term]
        if payment_info["discount"] > 0:
            discount_pct = payment_info["discount"]
            discount_amt = base_pricing["annual_total"] * discount_pct
            discounts.append({
                "type": "payment_term",
                "label": payment_info.get("savings_description", "Payment discount"),
                "percentage": discount_pct,
                "amount": discount_amt
            })
            total_discount_amount += discount_amt
            discount_percentage += discount_pct

        # Contract length discount
        contract_info = self.CONTRACT_INCENTIVES[contract_length]
        if contract_info["discount"] > 0:
            discount_pct = contract_info["discount"]
            discount_amt = base_pricing["term_total"] * discount_pct
            discounts.append({
                "type": "contract_length",
                "label": contract_info["description"],
                "percentage": discount_pct,
                "amount": discount_amt
            })
            total_discount_amount += discount_amt
            discount_percentage += discount_pct

        return {
            "discounts": discounts,
            "total_amount": total_discount_amount,
            "total_percentage": discount_percentage
        }

    def _generate_line_items(
        self,
        base_pricing: Dict,
        addon_pricing: Dict,
        discounts: Dict,
        requirements: Dict
    ) -> List[Dict[str, Any]]:
        """Generate detailed line items for proposal"""
        items = []

        # Base subscription
        items.append({
            "category": "subscription",
            "description": f"{base_pricing['tier'].title()} Plan - {requirements['num_users']} users",
            "quantity": requirements['num_users'],
            "unit_price": base_pricing['monthly_per_user'],
            "subtotal": base_pricing['term_total'],
            "term": requirements['payment_term']
        })

        # Add-ons (one-time)
        for addon_name, addon_details in addon_pricing["addons"].items():
            if addon_details["type"] == "one_time":
                items.append({
                    "category": "service",
                    "description": addon_details["description"],
                    "quantity": 1,
                    "unit_price": addon_details["cost"],
                    "subtotal": addon_details["cost"],
                    "term": "one_time"
                })

        # Add-ons (recurring)
        for addon_name, addon_details in addon_pricing["addons"].items():
            if addon_details["type"] == "recurring":
                items.append({
                    "category": "addon",
                    "description": f"{addon_details['description']} (monthly recurring)",
                    "quantity": 1,
                    "unit_price": addon_details["monthly_cost"],
                    "subtotal": addon_details["annual_cost"],
                    "term": "monthly"
                })

        # Discounts
        for discount in discounts["discounts"]:
            items.append({
                "category": "discount",
                "description": discount["label"],
                "quantity": 1,
                "unit_price": -discount["amount"],
                "subtotal": -discount["amount"],
                "term": "applied"
            })

        return items

    def _calculate_totals(self, line_items: List[Dict]) -> Dict[str, Any]:
        """Calculate proposal totals"""
        subtotal = 0
        total_discount = 0
        one_time_total = 0
        recurring_total = 0

        for item in line_items:
            if item["category"] == "discount":
                total_discount += abs(item["subtotal"])
            elif item["term"] == "one_time":
                one_time_total += item["subtotal"]
                subtotal += item["subtotal"]
            else:
                recurring_total += item["subtotal"]
                subtotal += item["subtotal"]

        total = subtotal - total_discount

        return {
            "subtotal": subtotal,
            "total_discount": total_discount,
            "one_time_total": one_time_total,
            "annual_total": recurring_total - total_discount,
            "total": total,
            "monthly_equivalent": total / 12 if total > 0 else 0
        }

    def _generate_timeline(
        self,
        requirements: Dict,
        addon_pricing: Dict
    ) -> Dict[str, Any]:
        """Generate implementation timeline"""
        start_date = datetime.now()
        phases = []

        # Contract signing
        phases.append({
            "phase": "Contract Execution",
            "duration_weeks": 1,
            "start": start_date,
            "end": start_date + timedelta(weeks=1),
            "activities": ["Contract signed", "Payment processed", "Account setup"]
        })

        current_date = start_date + timedelta(weeks=1)

        # Implementation if included
        if any(addon in requirements.get("addons", []) for addon in ["implementation", "data_migration"]):
            impl_weeks = 4
            phases.append({
                "phase": "Implementation",
                "duration_weeks": impl_weeks,
                "start": current_date,
                "end": current_date + timedelta(weeks=impl_weeks),
                "activities": ["Environment setup", "Data migration", "Configuration", "Integration"]
            })
            current_date += timedelta(weeks=impl_weeks)

        # Training if included
        if "training" in requirements.get("addons", []):
            training_weeks = 2
            phases.append({
                "phase": "Training",
                "duration_weeks": training_weeks,
                "start": current_date,
                "end": current_date + timedelta(weeks=training_weeks),
                "activities": ["User training", "Admin training", "Best practices"]
            })
            current_date += timedelta(weeks=training_weeks)

        # Go-live
        phases.append({
            "phase": "Go-Live",
            "duration_weeks": 1,
            "start": current_date,
            "end": current_date + timedelta(weeks=1),
            "activities": ["Production launch", "Monitoring", "Support"]
        })

        total_weeks = sum(p["duration_weeks"] for p in phases)

        return {
            "phases": phases,
            "total_weeks": total_weeks,
            "estimated_completion": current_date + timedelta(weeks=1)
        }

    def _generate_terms(
        self,
        tier: str,
        requirements: Dict
    ) -> Dict[str, str]:
        """Generate terms and conditions"""
        terms = self.TERMS_AND_CONDITIONS.copy()

        # Customize based on tier
        if tier == "enterprise":
            terms["support"] = "24/7 dedicated support with 2-hour response SLA"
            terms["sla"] = "99.9% uptime SLA with financial penalties"

        # Add contract length
        contract_years = int(requirements["contract_length"].split("_")[0])
        terms["contract_length"] = f"{contract_years}-year initial term, auto-renewal unless cancelled 30 days prior"

        return terms

    def _create_proposal_summary(
        self,
        requirements: Dict,
        totals: Dict,
        timeline: Dict
    ) -> Dict[str, Any]:
        """Create executive proposal summary"""
        return {
            "company": requirements["company"],
            "solution": f"{requirements['num_users']}-user {self._determine_pricing_tier(requirements).title()} solution",
            "investment": {
                "year_one_total": totals["annual_total"] + totals["one_time_total"],
                "annual_recurring": totals["annual_total"],
                "monthly_equivalent": totals["monthly_equivalent"],
                "savings": totals["total_discount"]
            },
            "timeline": f"{timeline['total_weeks']} weeks to full deployment",
            "contract_term": requirements["contract_length"].replace("_", " ")
        }

    async def _generate_proposal_response(
        self,
        message: str,
        proposal_summary: Dict,
        line_items: List[Dict],
        totals: Dict,
        timeline: Dict,
        terms: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate proposal presentation response"""

        # Build line items summary
        line_items_text = "\n\nProposal Line Items:\n"
        for item in line_items:
            line_items_text += f"- {item['description']}: ${item['subtotal']:,.2f}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Proposal Generator specialist creating professional sales proposals.

Proposal Summary:
- Solution: {proposal_summary['solution']}
- Year 1 Investment: ${proposal_summary['investment']['year_one_total']:,.2f}
- Annual Recurring: ${proposal_summary['investment']['annual_recurring']:,.2f}
- Total Savings: ${proposal_summary['investment']['savings']:,.2f}
- Implementation Timeline: {proposal_summary['timeline']}
- Contract Term: {proposal_summary['contract_term']}

Company: {customer_metadata.get('company', 'Customer')}
Industry: {customer_metadata.get('industry', 'Unknown')}

Your response should:
1. Present the proposal professionally and enthusiastically
2. Highlight the customized solution for their needs
3. Clearly explain pricing and value
4. Emphasize savings and discounts
5. Outline implementation timeline
6. Mention next steps (review, questions, signature)
7. Be confident but not pushy
8. Use professional business language"""

        user_prompt = f"""Customer message: {message}

{line_items_text}

Total Investment:
- Year 1: ${totals['one_time_total'] + totals['annual_total']:,.2f}
- Annual Recurring: ${totals['annual_total']:,.2f}
- Monthly Equivalent: ${totals['monthly_equivalent']:,.2f}

Timeline: {timeline['total_weeks']} weeks from contract to go-live

{kb_context}

Generate a professional proposal presentation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing ProposalGenerator Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Small business starter proposal
        state1 = create_initial_state(
            "Can you send us a proposal for 25 users with training included?",
            context={
                "customer_metadata": {
                    "company": "SmallBiz Inc",
                    "title": "Owner",
                    "company_size": 25,
                    "industry": "retail"
                },
                "requirements": {
                    "num_users": 25
                }
            }
        )

        agent = ProposalGenerator()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Small Business Starter Proposal")
        print(f"Pricing Tier: {result1['pricing_tier']}")
        print(f"Line Items: {len(result1['line_items'])}")
        print(f"Annual Total: ${result1['totals']['annual_total']:,.2f}")
        print(f"Total Discount: ${result1['totals']['total_discount']:,.2f}")
        print(f"Timeline: {result1['timeline']['total_weeks']} weeks")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Enterprise proposal with full services
        state2 = create_initial_state(
            "We need a comprehensive proposal for 500 users with implementation, training, data migration, and premium support on a 3-year annual contract",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "title": "VP Operations",
                    "company_size": 500,
                    "industry": "finance"
                },
                "requirements": {
                    "num_users": 500
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Enterprise Full Service Proposal")
        print(f"Pricing Tier: {result2['pricing_tier']}")
        print(f"Line Items: {len(result2['line_items'])}")
        print(f"Year 1 Total: ${result2['totals']['one_time_total'] + result2['totals']['annual_total']:,.2f}")
        print(f"Annual Recurring: ${result2['totals']['annual_total']:,.2f}")
        print(f"Total Discount: ${result2['totals']['total_discount']:,.2f}")
        print(f"Add-ons: {len(result2['addon_pricing']['addons'])}")
        print(f"Timeline: {result2['timeline']['total_weeks']} weeks")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Mid-market professional
        state3 = create_initial_state(
            "Please prepare a proposal for our team of 150 users",
            context={
                "customer_metadata": {
                    "company": "MidMarket Co",
                    "title": "Director of IT",
                    "company_size": 150,
                    "industry": "technology"
                },
                "requirements": {
                    "num_users": 150
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Mid-Market Professional Proposal")
        print(f"Pricing Tier: {result3['pricing_tier']}")
        print(f"Monthly Equivalent: ${result3['totals']['monthly_equivalent']:,.2f}")
        print(f"Annual Total: ${result3['totals']['annual_total']:,.2f}")
        print(f"Discounts Applied: {len(result3['discounts']['discounts'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
