"""
Pricing Analyzer Agent - TASK-1055

Tracks competitor pricing changes, analyzes packaging strategies,
monitors discount patterns, and provides pricing recommendations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("pricing_analyzer", tier="revenue", category="sales")
class PricingAnalyzer(BaseAgent):
    """
    Pricing Analyzer Agent - Analyzes competitive pricing and packaging strategies.

    Handles:
    - Track competitor pricing changes
    - Analyze packaging strategies
    - Monitor discount patterns
    - Provide pricing recommendations
    - Calculate total cost of ownership comparisons
    """

    # Competitor pricing structures
    COMPETITOR_PRICING = {
        "salesforce": {
            "name": "Salesforce",
            "tiers": [
                {
                    "tier": "Essentials",
                    "price_per_user_monthly": 25,
                    "min_users": 1,
                    "max_users": 10,
                    "features_included": ["basic_crm", "mobile_app"],
                    "limitations": ["Limited to 10 users", "Basic support only"]
                },
                {
                    "tier": "Professional",
                    "price_per_user_monthly": 75,
                    "min_users": 1,
                    "features_included": ["full_crm", "automation", "reports"],
                    "limitations": ["Limited API calls", "Standard support"]
                },
                {
                    "tier": "Enterprise",
                    "price_per_user_monthly": 150,
                    "min_users": 1,
                    "features_included": ["everything", "advanced_automation", "unlimited_api"],
                    "limitations": []
                },
                {
                    "tier": "Unlimited",
                    "price_per_user_monthly": 300,
                    "min_users": 1,
                    "features_included": ["everything", "premier_support", "sandboxes"],
                    "limitations": []
                }
            ],
            "addons": [
                {"name": "Einstein AI", "price_per_user_monthly": 50},
                {"name": "Advanced Analytics", "price_per_user_monthly": 75},
                {"name": "Marketing Cloud", "price_monthly": 1250}
            ],
            "typical_discount": 0.15,
            "implementation_cost": 50000,
            "typical_contract_length": 12,
            "pricing_model": "per_user"
        },
        "hubspot": {
            "name": "HubSpot",
            "tiers": [
                {
                    "tier": "Free",
                    "price_per_user_monthly": 0,
                    "features_included": ["basic_crm", "forms", "limited_contacts"],
                    "limitations": ["Limited contacts", "Basic features only", "HubSpot branding"]
                },
                {
                    "tier": "Starter",
                    "price_monthly": 50,
                    "min_users": 2,
                    "features_included": ["crm", "email", "forms"],
                    "limitations": ["1,000 marketing contacts", "Email support"]
                },
                {
                    "tier": "Professional",
                    "price_monthly": 890,
                    "min_users": 5,
                    "features_included": ["automation", "custom_reports", "workflows"],
                    "limitations": ["2,000 marketing contacts", "Additional contacts cost extra"]
                },
                {
                    "tier": "Enterprise",
                    "price_monthly": 3600,
                    "min_users": 10,
                    "features_included": ["everything", "predictive_lead_scoring", "custom_objects"],
                    "limitations": ["10,000 marketing contacts included"]
                }
            ],
            "addons": [
                {"name": "Additional Contacts (1K)", "price_monthly": 50},
                {"name": "Additional User", "price_per_user_monthly": 45},
                {"name": "Reporting Add-on", "price_monthly": 200}
            ],
            "typical_discount": 0.10,
            "implementation_cost": 5000,
            "typical_contract_length": 12,
            "pricing_model": "contact_based",
            "price_increases": "Significant increases at scale"
        },
        "zendesk": {
            "name": "Zendesk",
            "tiers": [
                {
                    "tier": "Suite Team",
                    "price_per_user_monthly": 49,
                    "min_users": 1,
                    "features_included": ["ticketing", "messaging", "help_center"],
                    "limitations": ["Basic features", "Email support"]
                },
                {
                    "tier": "Suite Growth",
                    "price_per_user_monthly": 79,
                    "min_users": 1,
                    "features_included": ["automation", "sla", "multilingual"],
                    "limitations": ["Standard support"]
                },
                {
                    "tier": "Suite Professional",
                    "price_per_user_monthly": 99,
                    "min_users": 1,
                    "features_included": ["advanced_ai", "custom_roles", "sandbox"],
                    "limitations": []
                },
                {
                    "tier": "Suite Enterprise",
                    "price_per_user_monthly": 150,
                    "min_users": 1,
                    "features_included": ["everything", "premium_support"],
                    "limitations": []
                }
            ],
            "addons": [
                {"name": "Advanced AI", "price_per_user_monthly": 50},
                {"name": "Zendesk Explore", "price_per_user_monthly": 15}
            ],
            "typical_discount": 0.20,
            "implementation_cost": 10000,
            "typical_contract_length": 12,
            "pricing_model": "per_user",
            "notes": "Need multiple products for complete solution"
        },
        "intercom": {
            "name": "Intercom",
            "tiers": [
                {
                    "tier": "Essential",
                    "price_monthly": 39,
                    "features_included": ["basic_messaging", "help_center"],
                    "limitations": ["Very limited features", "Email support only"]
                },
                {
                    "tier": "Advanced",
                    "price_monthly": 99,
                    "features_included": ["product_tours", "custom_bots", "reports"],
                    "limitations": ["Conversation limits apply"]
                },
                {
                    "tier": "Expert",
                    "price_monthly": 499,
                    "features_included": ["advanced_automation", "series", "multiple_workspaces"],
                    "limitations": ["Still has conversation limits"]
                }
            ],
            "addons": [
                {"name": "Additional Seats", "price_per_user_monthly": 19},
                {"name": "Fin AI Agent", "price_per_resolution": 0.99},
                {"name": "Additional Conversations", "varies": True}
            ],
            "typical_discount": 0.05,
            "implementation_cost": 3000,
            "typical_contract_length": 12,
            "pricing_model": "conversation_based",
            "price_increases": "Extreme increases at scale - major pain point",
            "notes": "Pricing becomes very expensive with volume"
        },
        "freshdesk": {
            "name": "Freshdesk",
            "tiers": [
                {
                    "tier": "Free",
                    "price_per_user_monthly": 0,
                    "max_users": 10,
                    "features_included": ["ticketing", "basic_reports"],
                    "limitations": ["Limited to 10 agents", "Email support only"]
                },
                {
                    "tier": "Growth",
                    "price_per_user_monthly": 15,
                    "features_included": ["automation", "sla", "custom_reports"],
                    "limitations": ["Email/chat support"]
                },
                {
                    "tier": "Pro",
                    "price_per_user_monthly": 49,
                    "features_included": ["custom_roles", "workflows", "multiple_products"],
                    "limitations": []
                },
                {
                    "tier": "Enterprise",
                    "price_per_user_monthly": 79,
                    "features_included": ["everything", "audit_log", "sandbox"],
                    "limitations": []
                }
            ],
            "addons": [
                {"name": "Freddy AI", "price_per_user_monthly": 29}
            ],
            "typical_discount": 0.15,
            "implementation_cost": 2000,
            "typical_contract_length": 12,
            "pricing_model": "per_user"
        }
    }

    # Our pricing (for comparison)
    OUR_PRICING = {
        "tiers": [
            {
                "tier": "Startup",
                "price_per_user_monthly": 29,
                "min_users": 1,
                "features_included": ["full_crm", "automation", "ai_included", "unlimited_api", "all_features"],
                "limitations": []
            },
            {
                "tier": "Growth",
                "price_per_user_monthly": 59,
                "min_users": 5,
                "features_included": ["everything", "advanced_analytics", "priority_support", "custom_integrations"],
                "limitations": []
            },
            {
                "tier": "Enterprise",
                "price_per_user_monthly": 99,
                "min_users": 20,
                "features_included": ["everything", "dedicated_support", "sla", "audit_logs", "sso", "custom_training"],
                "limitations": []
            }
        ],
        "addons": [],  # All features included in base price
        "typical_discount": 0.10,
        "implementation_cost": 0,  # Free implementation
        "pricing_model": "per_user",
        "advantages": [
            "No hidden fees or required add-ons",
            "All features included in base price (especially AI)",
            "Free implementation and onboarding",
            "Volume discounts available",
            "Flexible contract terms"
        ]
    }

    # Recent pricing changes
    RECENT_PRICE_CHANGES = {
        "salesforce": [
            {
                "date": "2024-01-01",
                "change": "Einstein AI pricing increased from $40 to $50/user/month",
                "impact": "high",
                "percentage_increase": 0.25
            }
        ],
        "hubspot": [
            {
                "date": "2023-11-15",
                "change": "Professional tier increased from $800 to $890/month",
                "impact": "medium",
                "percentage_increase": 0.11
            }
        ],
        "intercom": [
            {
                "date": "2023-12-01",
                "change": "Fin AI pricing model changed to per-resolution",
                "impact": "high",
                "notes": "Caused significant customer complaints"
            }
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="pricing_analyzer",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20240620",
            temperature=0.2,
            max_tokens=1500,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process pricing analysis"""
        self.logger.info("pricing_analyzer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify competitors to analyze
        competitors_to_analyze = self._identify_competitors(message, state)

        # Generate pricing comparison
        pricing_comparison = self._generate_pricing_comparison(
            competitors_to_analyze,
            customer_metadata
        )

        # Calculate TCO (Total Cost of Ownership)
        tco_analysis = self._calculate_tco(
            competitors_to_analyze,
            customer_metadata
        )

        # Identify pricing advantages
        pricing_advantages = self._identify_pricing_advantages(
            competitors_to_analyze,
            customer_metadata
        )

        # Analyze discount patterns
        discount_analysis = self._analyze_discounts(competitors_to_analyze)

        # Get recent price changes
        price_changes = self._get_price_changes(competitors_to_analyze)

        # Generate pricing recommendations
        recommendations = self._generate_recommendations(
            pricing_comparison,
            tco_analysis,
            pricing_advantages,
            customer_metadata
        )

        # Calculate confidence
        confidence = 0.90  # High confidence - based on known pricing data

        # Update state
        state["pricing_comparison"] = pricing_comparison
        state["tco_analysis"] = tco_analysis
        state["pricing_advantages"] = pricing_advantages
        state["discount_analysis"] = discount_analysis
        state["recent_price_changes"] = price_changes
        state["pricing_recommendations"] = recommendations
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "pricing_analyzer_completed",
            competitors_analyzed=len(competitors_to_analyze),
            advantages_found=len(pricing_advantages)
        )

        return state

    def _identify_competitors(self, message: str, state: AgentState) -> List[str]:
        """Identify which competitors to analyze"""
        message_lower = message.lower()
        competitors = []

        # Check for specific mentions
        for competitor in self.COMPETITOR_PRICING.keys():
            if competitor in message_lower:
                competitors.append(competitor)

        # Use from state if available
        if not competitors:
            competitors = state.get("mentioned_competitors", [])

        # Default to top 3 competitors
        if not competitors:
            competitors = ["salesforce", "hubspot", "intercom"]

        return competitors

    def _generate_pricing_comparison(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive pricing comparison"""
        company_size = customer_metadata.get("company_size", 50)

        comparison = {
            "scenario": f"{company_size} users",
            "our_pricing": [],
            "competitor_pricing": []
        }

        # Calculate our pricing
        our_tier = self._determine_best_tier(company_size, self.OUR_PRICING)
        our_monthly = our_tier["price_per_user_monthly"] * company_size
        our_annual = our_monthly * 12

        comparison["our_pricing"] = {
            "tier": our_tier["tier"],
            "price_per_user": our_tier["price_per_user_monthly"],
            "monthly_cost": our_monthly,
            "annual_cost": our_annual,
            "implementation_cost": self.OUR_PRICING["implementation_cost"],
            "total_year_1": our_annual + self.OUR_PRICING["implementation_cost"],
            "features_included": our_tier["features_included"]
        }

        # Calculate competitor pricing
        for competitor in competitors:
            comp_data = self.COMPETITOR_PRICING.get(competitor, {})
            comp_tier = self._determine_best_tier(company_size, comp_data)

            if "price_per_user_monthly" in comp_tier:
                monthly = comp_tier["price_per_user_monthly"] * company_size
            else:
                monthly = comp_tier.get("price_monthly", 0)

            annual = monthly * 12
            implementation = comp_data.get("implementation_cost", 0)

            comparison["competitor_pricing"].append({
                "competitor": comp_data.get("name", competitor.title()),
                "tier": comp_tier["tier"],
                "price_per_user": comp_tier.get("price_per_user_monthly"),
                "monthly_cost": monthly,
                "annual_cost": annual,
                "implementation_cost": implementation,
                "total_year_1": annual + implementation,
                "features_included": comp_tier["features_included"],
                "limitations": comp_tier.get("limitations", []),
                "typical_addons": len(comp_data.get("addons", []))
            })

        return comparison

    def _determine_best_tier(self, company_size: int, pricing_data: Dict) -> Dict:
        """Determine best pricing tier for company size"""
        tiers = pricing_data.get("tiers", [])

        # Find appropriate tier based on min_users
        appropriate_tiers = [
            t for t in tiers
            if t.get("min_users", 0) <= company_size and t.get("max_users", 999999) >= company_size
        ]

        if appropriate_tiers:
            # Return middle tier if multiple options
            return appropriate_tiers[len(appropriate_tiers) // 2]

        # Default to highest tier if no appropriate tier found
        return tiers[-1] if tiers else {}

    def _calculate_tco(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate total cost of ownership comparison"""
        company_size = customer_metadata.get("company_size", 50)
        years = 3  # 3-year TCO

        tco = {
            "analysis_period": f"{years} years",
            "company_size": company_size,
            "our_tco": {},
            "competitor_tco": []
        }

        # Calculate our TCO
        our_tier = self._determine_best_tier(company_size, self.OUR_PRICING)
        our_annual = our_tier["price_per_user_monthly"] * company_size * 12

        tco["our_tco"] = {
            "year_1": our_annual + self.OUR_PRICING["implementation_cost"],
            "year_2": our_annual,
            "year_3": our_annual,
            "total_3_year": (our_annual * years) + self.OUR_PRICING["implementation_cost"],
            "average_annual": ((our_annual * years) + self.OUR_PRICING["implementation_cost"]) / years
        }

        # Calculate competitor TCO
        for competitor in competitors:
            comp_data = self.COMPETITOR_PRICING.get(competitor, {})
            comp_tier = self._determine_best_tier(company_size, comp_data)

            if "price_per_user_monthly" in comp_tier:
                comp_annual = comp_tier["price_per_user_monthly"] * company_size * 12
            else:
                comp_annual = comp_tier.get("price_monthly", 0) * 12

            implementation = comp_data.get("implementation_cost", 0)

            # Add typical addon costs (estimate 30% additional)
            addon_multiplier = 1.3 if comp_data.get("addons") else 1.0
            comp_annual_with_addons = comp_annual * addon_multiplier

            tco["competitor_tco"].append({
                "competitor": comp_data.get("name", competitor.title()),
                "year_1": comp_annual_with_addons + implementation,
                "year_2": comp_annual_with_addons,
                "year_3": comp_annual_with_addons,
                "total_3_year": (comp_annual_with_addons * years) + implementation,
                "average_annual": ((comp_annual_with_addons * years) + implementation) / years,
                "includes_typical_addons": comp_data.get("addons") is not None
            })

        # Calculate savings
        for comp_tco in tco["competitor_tco"]:
            savings = comp_tco["total_3_year"] - tco["our_tco"]["total_3_year"]
            savings_percentage = (savings / comp_tco["total_3_year"]) * 100 if comp_tco["total_3_year"] > 0 else 0
            comp_tco["savings_vs_us"] = savings
            comp_tco["savings_percentage"] = savings_percentage

        return tco

    def _identify_pricing_advantages(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Identify our pricing advantages"""
        advantages = []

        # Transparent pricing (no hidden fees)
        advantages.append({
            "advantage": "No Hidden Fees or Required Add-ons",
            "description": "All features included in base price, unlike competitors who charge extra for AI, analytics, etc.",
            "impact": "high",
            "competitors_affected": [c for c in competitors if self.COMPETITOR_PRICING.get(c, {}).get("addons")]
        })

        # Free implementation
        implementation_costs = [
            self.COMPETITOR_PRICING.get(c, {}).get("implementation_cost", 0)
            for c in competitors
        ]
        if any(cost > 0 for cost in implementation_costs):
            advantages.append({
                "advantage": "Free Implementation & Onboarding",
                "description": "Save $2K-$50K+ on implementation costs",
                "impact": "high",
                "competitors_affected": competitors
            })

        # Better pricing model
        conversation_based = [c for c in competitors if self.COMPETITOR_PRICING.get(c, {}).get("pricing_model") == "conversation_based"]
        if conversation_based:
            advantages.append({
                "advantage": "Predictable Per-User Pricing",
                "description": "No surprise bills from conversation limits or contact-based pricing",
                "impact": "high",
                "competitors_affected": conversation_based
            })

        # Lower cost at scale
        advantages.append({
            "advantage": "Better Value at Scale",
            "description": "Our pricing scales linearly while competitors have expensive add-ons and limits",
            "impact": "medium",
            "competitors_affected": competitors
        })

        return advantages

    def _analyze_discounts(self, competitors: List[str]) -> Dict[str, Any]:
        """Analyze competitor discount patterns"""
        analysis = {
            "our_typical_discount": self.OUR_PRICING["typical_discount"],
            "competitor_discounts": []
        }

        for competitor in competitors:
            comp_data = self.COMPETITOR_PRICING.get(competitor, {})
            analysis["competitor_discounts"].append({
                "competitor": comp_data.get("name", competitor.title()),
                "typical_discount": comp_data.get("typical_discount", 0),
                "contract_length": comp_data.get("typical_contract_length", 12),
                "negotiation_leverage": "high" if comp_data.get("typical_discount", 0) >= 0.15 else "medium"
            })

        return analysis

    def _get_price_changes(self, competitors: List[str]) -> List[Dict[str, Any]]:
        """Get recent competitor price changes"""
        changes = []

        for competitor in competitors:
            comp_changes = self.RECENT_PRICE_CHANGES.get(competitor, [])
            for change in comp_changes:
                changes.append({
                    "competitor": competitor.title(),
                    "date": change["date"],
                    "change": change["change"],
                    "impact": change["impact"],
                    "percentage_increase": change.get("percentage_increase", 0),
                    "notes": change.get("notes", "")
                })

        # Sort by date (most recent first)
        changes.sort(key=lambda x: x["date"], reverse=True)

        return changes

    def _generate_recommendations(
        self,
        pricing_comparison: Dict,
        tco_analysis: Dict,
        pricing_advantages: List[Dict],
        customer_metadata: Dict
    ) -> List[str]:
        """Generate pricing-based recommendations"""
        recommendations = []

        # TCO savings
        if tco_analysis.get("competitor_tco"):
            max_savings = max(
                c["savings_vs_us"] for c in tco_analysis["competitor_tco"]
                if c["savings_vs_us"] > 0
            )
            if max_savings > 0:
                recommendations.append(
                    f"Emphasize ${max_savings:,.0f} in 3-year TCO savings"
                )

        # Implementation cost savings
        if self.OUR_PRICING["implementation_cost"] == 0:
            recommendations.append(
                "Highlight free implementation (competitors charge $2K-$50K+)"
            )

        # Transparent pricing
        recommendations.append(
            "Lead with transparent pricing - no hidden fees or expensive add-ons"
        )

        # Pricing model advantages
        recommendations.append(
            "Emphasize predictable per-user pricing vs conversation/contact-based models"
        )

        # Volume discounts
        company_size = customer_metadata.get("company_size", 0)
        if company_size >= 100:
            recommendations.append(
                "Offer volume discount for large team size"
            )

        return recommendations


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing PricingAnalyzer Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Small team pricing comparison
        state1 = create_initial_state(
            "How does our pricing compare to Salesforce for a team of 25?",
            context={
                "customer_metadata": {
                    "company": "StartupCo",
                    "company_size": 25,
                    "industry": "technology"
                }
            }
        )

        agent = PricingAnalyzer()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Pricing Comparison (25 users)")
        comparison = result1['pricing_comparison']
        print(f"Scenario: {comparison['scenario']}")
        print(f"\nOur Pricing:")
        our = comparison['our_pricing']
        print(f"  Tier: {our['tier']}")
        print(f"  Monthly: ${our['monthly_cost']:,.0f}")
        print(f"  Annual: ${our['annual_cost']:,.0f}")
        print(f"  Year 1 Total: ${our['total_year_1']:,.0f}")

        print(f"\nCompetitor Pricing:")
        for comp in comparison['competitor_pricing']:
            print(f"\n  {comp['competitor']}:")
            print(f"    Tier: {comp['tier']}")
            print(f"    Monthly: ${comp['monthly_cost']:,.0f}")
            print(f"    Annual: ${comp['annual_cost']:,.0f}")
            print(f"    Year 1 Total: ${comp['total_year_1']:,.0f}")
            print(f"    Typical Add-ons: {comp['typical_addons']}")

        # Test case 2: TCO analysis for larger team
        state2 = create_initial_state(
            "What's the 3-year total cost of ownership vs HubSpot and Intercom for 100 users?",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "company_size": 100,
                    "industry": "saas"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - TCO Analysis (100 users, 3 years)")
        tco = result2['tco_analysis']
        print(f"Analysis Period: {tco['analysis_period']}")
        print(f"\nOur TCO:")
        print(f"  Year 1: ${tco['our_tco']['year_1']:,.0f}")
        print(f"  Year 2: ${tco['our_tco']['year_2']:,.0f}")
        print(f"  Year 3: ${tco['our_tco']['year_3']:,.0f}")
        print(f"  3-Year Total: ${tco['our_tco']['total_3_year']:,.0f}")

        print(f"\nCompetitor TCO:")
        for comp in tco['competitor_tco']:
            print(f"\n  {comp['competitor']}:")
            print(f"    3-Year Total: ${comp['total_3_year']:,.0f}")
            print(f"    Savings vs Us: ${comp['savings_vs_us']:,.0f} ({comp['savings_percentage']:.1f}%)")
            print(f"    Includes Add-ons: {comp['includes_typical_addons']}")

        # Test case 3: Pricing advantages
        state3 = create_initial_state(
            "What are our pricing advantages over competitors?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "company_size": 200
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - Pricing Advantages")
        print(f"Advantages Identified: {len(result3['pricing_advantages'])}")
        for adv in result3['pricing_advantages']:
            print(f"\n  • {adv['advantage']}")
            print(f"    {adv['description']}")
            print(f"    Impact: {adv['impact'].upper()}")
            print(f"    Affects: {', '.join([c.title() for c in adv['competitors_affected']])}")

        print(f"\nRecommendations:")
        for rec in result3['pricing_recommendations']:
            print(f"  • {rec}")

        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
