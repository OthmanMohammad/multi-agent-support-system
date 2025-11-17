"""
Positioning Advisor Agent - TASK-1056

Advises on positioning against specific competitors, generates talking points,
recommends differentiation strategies, and provides win strategies.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("positioning_advisor", tier="revenue", category="sales")
class PositioningAdvisor(BaseAgent):
    """
    Positioning Advisor Agent - Strategic positioning guidance for competitive situations.

    Handles:
    - Advise on positioning against specific competitors
    - Generate competitive talking points
    - Recommend differentiation strategies
    - Provide win strategies based on scenario
    - Suggest messaging and positioning frameworks
    """

    # Competitor-specific positioning strategies
    POSITIONING_STRATEGIES = {
        "salesforce": {
            "competitor": "Salesforce",
            "their_position": "Market leader, enterprise CRM standard",
            "our_position": "Modern, user-friendly alternative without the complexity and cost",
            "key_differentiators": [
                "10x faster implementation (days vs months)",
                "60% lower total cost of ownership",
                "No expensive consultants required",
                "AI included, not a paid add-on",
                "Better user adoption rates"
            ],
            "when_to_position": {
                "smb": "They're overbuilt for your needs - you'll pay for complexity you don't need",
                "mid_market": "Get enterprise features without enterprise complexity and cost",
                "enterprise": "Modern platform that your team will actually use - not just admins"
            },
            "talking_points": [
                "Salesforce is powerful but requires significant investment in setup and training",
                "Our platform delivers similar outcomes in a fraction of the time",
                "AI features that Salesforce charges $50/user/month for are included in our base price",
                "Your team can be productive in days, not months"
            ],
            "objection_responses": {
                "market_leader": "Yes, they're the incumbent. We're the modern alternative that learns from what customers actually want.",
                "integration_ecosystem": "We integrate with all the same systems, but with simpler setup and better APIs.",
                "proven_solution": "Proven for Fortune 500 companies who can afford consultants. We deliver results without the overhead."
            },
            "win_strategy": "Position as the 'easy button' - same outcomes, 10x less hassle"
        },
        "hubspot": {
            "competitor": "HubSpot",
            "their_position": "User-friendly inbound marketing and sales platform",
            "our_position": "Enterprise-grade features with HubSpot's ease of use, better pricing at scale",
            "key_differentiators": [
                "50% lower cost as you scale",
                "No contact-based pricing surprises",
                "Better enterprise features (SSO, audit logs, etc.)",
                "More flexible automation",
                "Superior API capabilities"
            ],
            "when_to_position": {
                "smb": "Similar ease of use, better pricing as you grow",
                "mid_market": "HubSpot pricing becomes prohibitive at your scale - we grow with you",
                "enterprise": "Enterprise features HubSpot lacks, like advanced security and compliance"
            },
            "talking_points": [
                "HubSpot is great until you scale - then pricing explodes",
                "Contact-based pricing means growth hurts your wallet",
                "We offer the same ease of use with enterprise capabilities",
                "Unlimited API calls on all plans (HubSpot limits by tier)"
            ],
            "objection_responses": {
                "ease_of_use": "We match their ease of use - we've studied what makes them great and improved on it.",
                "free_tier": "Their free tier is limited. Our entry tier gives you everything to grow your business.",
                "marketing_features": "We have the same core features plus better automation and enterprise capabilities."
            },
            "win_strategy": "Position as 'HubSpot for companies that have outgrown HubSpot pricing'"
        },
        "zendesk": {
            "competitor": "Zendesk",
            "their_position": "Established support platform",
            "our_position": "All-in-one platform vs their fragmented product suite",
            "key_differentiators": [
                "One product vs buying multiple Zendesk products",
                "Better automation and AI capabilities",
                "Modern, intuitive interface",
                "Unified analytics across all channels",
                "40% cost savings on average"
            ],
            "when_to_position": {
                "smb": "Everything you need in one product, not multiple expensive add-ons",
                "mid_market": "Unified platform eliminates data silos from separate products",
                "enterprise": "Better AI and automation at a lower total cost"
            },
            "talking_points": [
                "Zendesk requires buying multiple products (Support, Chat, Explore, etc.)",
                "Our single platform does everything with better data flow",
                "Their UI feels dated - ours is modern and intuitive",
                "Better automation means your team can do more with less"
            ],
            "objection_responses": {
                "established_player": "Established doesn't mean best. They've fragmented into too many products.",
                "support_focused": "Support is just one part of customer experience - we do it all.",
                "marketplace": "We have the integrations that matter, without the complexity."
            },
            "win_strategy": "Position as the 'unified platform' vs their product maze"
        },
        "intercom": {
            "competitor": "Intercom",
            "their_position": "Modern customer messaging platform",
            "our_position": "All Intercom's strengths without the pricing pain",
            "key_differentiators": [
                "70% lower cost at scale",
                "No conversation limits or surprise charges",
                "Better support/ticketing features",
                "Transparent, predictable pricing",
                "Same modern UX"
            ],
            "when_to_position": {
                "smb": "Modern platform that won't bankrupt you as you grow",
                "mid_market": "Intercom becomes impossibly expensive at scale - we don't",
                "enterprise": "Better features for actual support teams, not just messaging"
            },
            "talking_points": [
                "Intercom's pricing is a notorious pain point - ours is transparent",
                "Conversation-based pricing penalizes success - we don't",
                "We have messaging PLUS real support features",
                "Same beautiful UX without the pricing shock"
            ],
            "objection_responses": {
                "modern_ui": "We match their modern UX - we're not sacrificing design for affordability.",
                "product_led": "Perfect for product-led companies, but with better support capabilities too.",
                "messaging_first": "Messaging is great, but most companies need traditional support too. We do both."
            },
            "win_strategy": "Position as 'Intercom pricing relief' - same experience, sane pricing"
        },
        "freshdesk": {
            "competitor": "Freshdesk",
            "their_position": "Affordable support platform for SMBs",
            "our_position": "Better features and scalability for similar price",
            "key_differentiators": [
                "More advanced automation",
                "Better AI capabilities included",
                "Superior integration ecosystem",
                "Scales better to enterprise",
                "Better analytics and reporting"
            ],
            "when_to_position": {
                "smb": "Similar pricing but with features you won't outgrow",
                "mid_market": "Freshdesk hits limitations at your scale - we don't",
                "enterprise": "Enterprise features they simply don't have"
            },
            "talking_points": [
                "Freshdesk is budget-friendly but limited in capabilities",
                "We offer enterprise features at SMB-friendly prices",
                "Better automation means better productivity",
                "Won't need to switch as you grow"
            ],
            "objection_responses": {
                "price": "Our pricing is competitive, and you get far more capability.",
                "simplicity": "Simple doesn't mean limited. We're powerful AND easy to use.",
                "good_enough": "'Good enough' costs you in the long run. We're the better long-term choice."
            },
            "win_strategy": "Position as the 'platform you won't outgrow' vs budget option"
        }
    }

    # Positioning frameworks
    FRAMEWORKS = {
        "feature_parity_plus": {
            "name": "Feature Parity Plus",
            "description": "Show we match their core features plus unique capabilities",
            "steps": [
                "Acknowledge their strengths",
                "Show we match those features",
                "Highlight our additional capabilities",
                "Demonstrate cost or ease advantages"
            ]
        },
        "tco_winner": {
            "name": "Total Cost of Ownership",
            "description": "Win on total cost, not just sticker price",
            "steps": [
                "Show comparable or lower base price",
                "Add their hidden costs (implementation, add-ons, training)",
                "Calculate true 3-year TCO",
                "Demonstrate savings"
            ]
        },
        "ease_champion": {
            "name": "Ease of Use Champion",
            "description": "Win on faster time to value and user adoption",
            "steps": [
                "Highlight setup complexity issues",
                "Show our faster implementation timeline",
                "Demonstrate higher user adoption rates",
                "Calculate time to value"
            ]
        },
        "unified_platform": {
            "name": "Unified Platform",
            "description": "Win against point solutions or fragmented suites",
            "steps": [
                "Show pain of managing multiple tools",
                "Demonstrate data flow benefits of unified platform",
                "Highlight administrative overhead savings",
                "Show better analytics from unified data"
            ]
        }
    }

    # Differentiation themes
    DIFFERENTIATION_THEMES = {
        "pricing": {
            "theme": "Transparent, Predictable Pricing",
            "messages": [
                "No hidden fees or surprise charges",
                "All features included in base price",
                "Scales predictably with your business"
            ]
        },
        "ease_of_use": {
            "theme": "Easy to Use, Easy to Love",
            "messages": [
                "Setup in hours, not months",
                "Your team will actually use it",
                "High user adoption out of the box"
            ]
        },
        "completeness": {
            "theme": "Complete Platform",
            "messages": [
                "Everything you need in one place",
                "No need for multiple tools or add-ons",
                "Unified data and analytics"
            ]
        },
        "innovation": {
            "theme": "Modern, AI-First Platform",
            "messages": [
                "AI built in, not bolted on",
                "Modern architecture and UX",
                "Continuous innovation"
            ]
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="positioning_advisor",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.3,
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
        """Process positioning advice"""
        self.logger.info("positioning_advisor_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify competitors to position against
        competitors = self._identify_competitors(message, state)

        # Generate positioning strategies
        positioning_strategies = self._generate_strategies(competitors, customer_metadata)

        # Generate talking points
        talking_points = self._generate_talking_points(competitors, customer_metadata)

        # Recommend differentiation themes
        differentiation_themes = self._recommend_themes(competitors, customer_metadata)

        # Select positioning framework
        recommended_framework = self._select_framework(competitors, customer_metadata)

        # Generate win strategy
        win_strategy = self._generate_win_strategy(
            competitors,
            customer_metadata,
            positioning_strategies
        )

        # Generate messaging guidance
        messaging = self._generate_messaging(
            competitors,
            differentiation_themes,
            customer_metadata
        )

        # Calculate confidence
        confidence = 0.89

        # Update state
        state["positioning_strategies"] = positioning_strategies
        state["competitive_talking_points"] = talking_points
        state["differentiation_themes"] = differentiation_themes
        state["recommended_framework"] = recommended_framework
        state["win_strategy"] = win_strategy
        state["positioning_messaging"] = messaging
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "positioning_advisor_completed",
            competitors_addressed=len(competitors),
            strategies_generated=len(positioning_strategies)
        )

        return state

    def _identify_competitors(self, message: str, state: AgentState) -> List[str]:
        """Identify which competitors to position against"""
        message_lower = message.lower()
        competitors = []

        # Check for specific mentions
        for competitor in self.POSITIONING_STRATEGIES.keys():
            if competitor in message_lower:
                competitors.append(competitor)

        # Use from state if available
        if not competitors:
            competitors = state.get("mentioned_competitors", [])

        # Default to top 2 competitors
        if not competitors:
            competitors = ["salesforce", "hubspot"]

        return competitors

    def _generate_strategies(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Generate positioning strategies for each competitor"""
        strategies = []
        company_size = customer_metadata.get("company_size", 50)

        # Determine market segment
        if company_size < 50:
            segment = "smb"
        elif company_size < 500:
            segment = "mid_market"
        else:
            segment = "enterprise"

        for competitor in competitors:
            if competitor in self.POSITIONING_STRATEGIES:
                strategy_data = self.POSITIONING_STRATEGIES[competitor]

                strategy = {
                    "competitor": strategy_data["competitor"],
                    "their_position": strategy_data["their_position"],
                    "our_position": strategy_data["our_position"],
                    "key_differentiators": strategy_data["key_differentiators"],
                    "segment_positioning": strategy_data["when_to_position"].get(segment, ""),
                    "talking_points": strategy_data["talking_points"],
                    "win_strategy": strategy_data["win_strategy"]
                }

                strategies.append(strategy)

        return strategies

    def _generate_talking_points(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Generate competitive talking points"""
        talking_points = []

        for competitor in competitors:
            if competitor in self.POSITIONING_STRATEGIES:
                strategy = self.POSITIONING_STRATEGIES[competitor]

                for point in strategy["talking_points"]:
                    talking_points.append({
                        "competitor": strategy["competitor"],
                        "talking_point": point,
                        "when_to_use": "When discussing features and capabilities",
                        "tone": "confident_not_arrogant"
                    })

                # Add objection responses as talking points
                for objection, response in strategy["objection_responses"].items():
                    talking_points.append({
                        "competitor": strategy["competitor"],
                        "talking_point": response,
                        "when_to_use": f"When they raise: '{objection.replace('_', ' ')}'",
                        "tone": "respectful_but_firm",
                        "objection_handler": True
                    })

        return talking_points

    def _recommend_themes(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Recommend differentiation themes"""
        themes = []

        # Always include pricing if we're competitive
        themes.append({
            "theme": self.DIFFERENTIATION_THEMES["pricing"]["theme"],
            "messages": self.DIFFERENTIATION_THEMES["pricing"]["messages"],
            "priority": "high",
            "relevance": "Universal advantage"
        })

        # Check for complexity competitors
        complex_competitors = ["salesforce"]
        if any(c in competitors for c in complex_competitors):
            themes.append({
                "theme": self.DIFFERENTIATION_THEMES["ease_of_use"]["theme"],
                "messages": self.DIFFERENTIATION_THEMES["ease_of_use"]["messages"],
                "priority": "high",
                "relevance": "Against complex enterprise solutions"
            })

        # Check for fragmented competitors
        fragmented_competitors = ["zendesk"]
        if any(c in competitors for c in fragmented_competitors):
            themes.append({
                "theme": self.DIFFERENTIATION_THEMES["completeness"]["theme"],
                "messages": self.DIFFERENTIATION_THEMES["completeness"]["messages"],
                "priority": "high",
                "relevance": "Against fragmented product suites"
            })

        # Always include innovation
        themes.append({
            "theme": self.DIFFERENTIATION_THEMES["innovation"]["theme"],
            "messages": self.DIFFERENTIATION_THEMES["innovation"]["messages"],
            "priority": "medium",
            "relevance": "Modern vs legacy solutions"
        })

        return themes

    def _select_framework(
        self,
        competitors: List[str],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Select best positioning framework for situation"""

        # Default to feature parity plus
        framework_key = "feature_parity_plus"

        # If competing on price-sensitive deal
        if customer_metadata.get("budget_constrained"):
            framework_key = "tco_winner"

        # If competing against complex solution
        if any(c in ["salesforce"] for c in competitors):
            framework_key = "ease_champion"

        # If competing against fragmented solutions
        if any(c in ["zendesk"] for c in competitors):
            framework_key = "unified_platform"

        framework = self.FRAMEWORKS[framework_key].copy()
        framework["framework_key"] = framework_key

        return framework

    def _generate_win_strategy(
        self,
        competitors: List[str],
        customer_metadata: Dict,
        positioning_strategies: List[Dict]
    ) -> Dict[str, Any]:
        """Generate overall win strategy"""

        company_size = customer_metadata.get("company_size", 50)
        industry = customer_metadata.get("industry", "")

        strategy = {
            "primary_approach": "",
            "key_messages": [],
            "proof_points": [],
            "next_steps": []
        }

        # Determine primary approach
        if len(competitors) == 1 and competitors[0] in self.POSITIONING_STRATEGIES:
            comp_strategy = self.POSITIONING_STRATEGIES[competitors[0]]
            strategy["primary_approach"] = comp_strategy["win_strategy"]
        else:
            strategy["primary_approach"] = "Position as best-of-breed: enterprise capabilities with SMB ease and pricing"

        # Key messages
        for pos_strat in positioning_strategies[:2]:  # Top 2
            strategy["key_messages"].extend(pos_strat["key_differentiators"][:3])

        # Proof points
        strategy["proof_points"] = [
            "Customer success stories from similar companies",
            "Third-party review scores and testimonials",
            "Head-to-head feature comparison",
            "Total cost of ownership calculation"
        ]

        # Next steps
        strategy["next_steps"] = [
            "Share competitive comparison guide",
            "Offer head-to-head demo",
            "Provide customer references in their industry",
            "Calculate personalized ROI and TCO"
        ]

        return strategy

    def _generate_messaging(
        self,
        competitors: List[str],
        differentiation_themes: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate messaging guidance"""

        messaging = {
            "elevator_pitch": "",
            "value_proposition": "",
            "key_messages": [],
            "dos": [],
            "donts": []
        }

        # Elevator pitch
        if competitors:
            comp_names = ", ".join([self.POSITIONING_STRATEGIES.get(c, {}).get("competitor", c.title()) for c in competitors[:2]])
            messaging["elevator_pitch"] = f"We deliver the capabilities of {comp_names} with better ease of use, transparent pricing, and faster time to value."
        else:
            messaging["elevator_pitch"] = "Modern, all-in-one platform that's powerful enough for enterprises yet easy enough for anyone to use."

        # Value proposition
        messaging["value_proposition"] = "Get enterprise-grade capabilities without enterprise complexity or cost. Our customers are productive in days, not months."

        # Key messages from themes
        for theme in differentiation_themes:
            messaging["key_messages"].extend(theme["messages"])

        # Dos
        messaging["dos"] = [
            "Acknowledge competitor strengths respectfully",
            "Focus on customer outcomes, not just features",
            "Use third-party validation (reviews, analyst reports)",
            "Quantify the difference (time, cost, adoption)",
            "Tell customer success stories",
            "Offer proof (demo, trial, references)"
        ]

        # Don'ts
        messaging["donts"] = [
            "Don't badmouth competitors",
            "Don't make claims you can't back up",
            "Don't ignore their valid strengths",
            "Don't get defensive",
            "Don't overwhelm with features - focus on value",
            "Don't forget to ask for the business"
        ]

        return messaging


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing PositioningAdvisor Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Positioning against Salesforce
        state1 = create_initial_state(
            "How should we position against Salesforce for a mid-market company?",
            context={
                "customer_metadata": {
                    "company": "MidMarket Corp",
                    "company_size": 150,
                    "industry": "technology"
                }
            }
        )

        agent = PositioningAdvisor()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Positioning vs Salesforce (Mid-Market)")
        for strategy in result1['positioning_strategies']:
            print(f"\nCompetitor: {strategy['competitor']}")
            print(f"Their Position: {strategy['their_position']}")
            print(f"Our Position: {strategy['our_position']}")
            print(f"\nSegment Positioning: {strategy['segment_positioning']}")
            print(f"\nKey Differentiators:")
            for diff in strategy['key_differentiators'][:3]:
                print(f"  • {diff}")
            print(f"\nWin Strategy: {strategy['win_strategy']}")

        print(f"\nRecommended Framework: {result1['recommended_framework']['name']}")
        print(f"Description: {result1['recommended_framework']['description']}")

        # Test case 2: Multi-competitor positioning
        state2 = create_initial_state(
            "We're competing against both HubSpot and Intercom. What's our positioning?",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "company_size": 75,
                    "industry": "saas"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - Multi-Competitor Positioning")
        print(f"Competitors: {len(result2['positioning_strategies'])}")

        print(f"\nDifferentiation Themes:")
        for theme in result2['differentiation_themes']:
            print(f"\n  {theme['theme']} (Priority: {theme['priority']})")
            print(f"  Relevance: {theme['relevance']}")
            for msg in theme['messages']:
                print(f"    • {msg}")

        print(f"\nWin Strategy:")
        win = result2['win_strategy']
        print(f"  Primary Approach: {win['primary_approach']}")
        print(f"  Key Messages ({len(win['key_messages'])}):")
        for msg in win['key_messages'][:3]:
            print(f"    • {msg}")

        # Test case 3: Messaging guidance
        state3 = create_initial_state(
            "What should our messaging be against Zendesk?",
            context={
                "customer_metadata": {
                    "company": "SupportCo",
                    "company_size": 100
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - Messaging Guidance")
        messaging = result3['positioning_messaging']
        print(f"\nElevator Pitch:")
        print(f"  {messaging['elevator_pitch']}")
        print(f"\nValue Proposition:")
        print(f"  {messaging['value_proposition']}")
        print(f"\nDOs:")
        for do in messaging['dos'][:3]:
            print(f"  ✓ {do}")
        print(f"\nDON'Ts:")
        for dont in messaging['donts'][:3]:
            print(f"  ✗ {dont}")

        print(f"\nTalking Points: {len(result3['competitive_talking_points'])}")
        for tp in result3['competitive_talking_points'][:3]:
            print(f"\n  • {tp['talking_point']}")
            print(f"    When: {tp['when_to_use']}")

        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
