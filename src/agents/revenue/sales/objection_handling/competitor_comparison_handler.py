"""
Competitor Comparison Handler Agent - TASK-1033

Handles "we're using competitor Y" objections by providing differentiation points,
competitive advantages, migration support, and case studies.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("competitor_comparison_handler", tier="revenue", category="sales")
class CompetitorComparisonHandler(BaseAgent):
    """
    Competitor Comparison Handler Agent - Specialist in competitive differentiation.

    Handles:
    - "We're using competitor Y" objections
    - Competitive differentiation and advantages
    - Migration support and process
    - Competitive case studies and win stories
    - Head-to-head feature comparisons
    """

    # Response strategies for different competitor scenarios
    RESPONSE_STRATEGIES = {
        "considering_competitor": {
            "approach": "proactive_differentiation",
            "tactics": ["feature_comparison", "customer_testimonials", "unique_value_props"],
            "supporting_materials": ["comparison_matrix", "case_studies", "competitive_battlecard"],
        },
        "using_competitor": {
            "approach": "migration_focused",
            "tactics": ["migration_support", "competitive_advantages", "switching_incentives"],
            "supporting_materials": ["migration_guide", "win_stories", "switching_checklist"],
        },
        "satisfied_with_competitor": {
            "approach": "value_gap_identification",
            "tactics": ["uncover_pain_points", "show_unique_capabilities", "roi_comparison"],
            "supporting_materials": ["capability_comparison", "roi_calculator", "analyst_reports"],
        },
        "multi_vendor": {
            "approach": "partnership_positioning",
            "tactics": ["complementary_positioning", "integration_story", "consolidation_benefits"],
            "supporting_materials": [
                "integration_docs",
                "consolidation_roi",
                "partnership_examples",
            ],
        },
    }

    # Known competitors and their weaknesses/our advantages
    COMPETITOR_ANALYSIS = {
        "salesforce": {
            "name": "Salesforce",
            "category": "CRM/Sales",
            "our_advantages": [
                "3x easier setup and onboarding (days vs months)",
                "60% lower total cost of ownership",
                "No complex customization required",
                "Built-in AI features (Salesforce charges extra)",
                "Better user experience and adoption rates",
            ],
            "their_weaknesses": [
                "Complex setup requiring consultants",
                "High total cost with add-ons",
                "Steep learning curve for users",
                "Over-engineered for most companies",
            ],
            "migration_difficulty": "medium",
            "common_pain_points": ["complexity", "cost", "user adoption", "customization overhead"],
        },
        "hubspot": {
            "name": "HubSpot",
            "category": "Marketing/Sales",
            "our_advantages": [
                "More flexible pricing model",
                "Better enterprise features",
                "Superior API and integrations",
                "Advanced automation capabilities",
                "Better customer support",
            ],
            "their_weaknesses": [
                "Expensive as you scale",
                "Limited enterprise features",
                "Less flexible workflows",
                "Contact-based pricing gets expensive",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": [
                "pricing scaling",
                "enterprise limitations",
                "workflow flexibility",
            ],
        },
        "zendesk": {
            "name": "Zendesk",
            "category": "Support",
            "our_advantages": [
                "All-in-one platform (no multiple products needed)",
                "Better AI-powered automation",
                "More intuitive interface",
                "Better value for money",
                "Unified analytics across teams",
            ],
            "their_weaknesses": [
                "Multiple products to buy separately",
                "Complex pricing structure",
                "Limited customization",
                "Dated user interface",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": [
                "product fragmentation",
                "pricing complexity",
                "limited automation",
            ],
        },
        "intercom": {
            "name": "Intercom",
            "category": "Customer Messaging",
            "our_advantages": [
                "50% lower cost at scale",
                "Better support features",
                "More comprehensive platform",
                "Better reporting and analytics",
                "No conversation-based pricing limits",
            ],
            "their_weaknesses": [
                "Very expensive at scale",
                "Conversation limits frustrating",
                "Limited ticketing features",
                "Missing some support capabilities",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": [
                "cost at scale",
                "conversation limits",
                "limited support features",
            ],
        },
        "freshdesk": {
            "name": "Freshdesk",
            "category": "Support",
            "our_advantages": [
                "More advanced automation",
                "Better AI capabilities",
                "Superior integration ecosystem",
                "More scalable architecture",
                "Better enterprise features",
            ],
            "their_weaknesses": [
                "Basic automation",
                "Limited AI capabilities",
                "Fewer integrations",
                "Performance issues at scale",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": ["limited automation", "scalability", "basic features"],
        },
        "trello": {
            "name": "Trello",
            "category": "Project Management",
            "our_advantages": [
                "More powerful project views (Gantt, Timeline, Calendar)",
                "Advanced reporting and analytics",
                "Better team collaboration features",
                "Stronger automation capabilities",
                "Enterprise-grade security",
                "Scalable for larger teams",
            ],
            "their_weaknesses": [
                "Limited to basic Kanban boards",
                "Gets messy with many cards",
                "No built-in time tracking",
                "Limited reporting",
                "Not suitable for complex projects",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": [
                "gets messy at scale",
                "limited views",
                "basic features only",
                "lack of reporting",
            ],
        },
        "asana": {
            "name": "Asana",
            "category": "Project Management",
            "our_advantages": [
                "More intuitive interface",
                "Better pricing for teams",
                "Stronger integration ecosystem",
                "More flexible workflows",
                "Better mobile experience",
            ],
            "their_weaknesses": [
                "Can be overwhelming with features",
                "Complex permission system",
                "Expensive at scale",
                "Steep learning curve",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": ["complexity", "pricing", "overwhelming features"],
        },
        "monday": {
            "name": "Monday.com",
            "category": "Project Management",
            "our_advantages": [
                "More cost-effective per user",
                "Better out-of-box workflows",
                "Simpler pricing model",
                "Faster implementation",
                "Better customer support",
            ],
            "their_weaknesses": [
                "Very expensive",
                "Complex pricing tiers",
                "Requires significant setup",
                "Too many features for simple needs",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": ["expensive", "complex pricing", "feature bloat"],
        },
        "jira": {
            "name": "Jira",
            "category": "Project Management",
            "our_advantages": [
                "Easier to use for non-technical teams",
                "Faster setup and onboarding",
                "Better user experience",
                "Lower administrative overhead",
                "More flexible for different use cases",
            ],
            "their_weaknesses": [
                "Complex admin and configuration",
                "Steep learning curve",
                "Designed primarily for software teams",
                "Requires dedicated admin",
            ],
            "migration_difficulty": "medium",
            "common_pain_points": ["complexity", "learning curve", "too developer-focused"],
        },
        "basecamp": {
            "name": "Basecamp",
            "category": "Project Management",
            "our_advantages": [
                "More powerful features",
                "Better for scaling teams",
                "Advanced automation",
                "Superior integrations",
                "Better reporting",
            ],
            "their_weaknesses": [
                "Limited feature set",
                "Basic task management",
                "No time tracking",
                "Limited customization",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": ["limited features", "basic functionality"],
        },
        "clickup": {
            "name": "ClickUp",
            "category": "Project Management",
            "our_advantages": [
                "Simpler interface",
                "Better performance",
                "More reliable platform",
                "Better customer support",
                "Clearer pricing",
            ],
            "their_weaknesses": [
                "Feature overload",
                "Performance issues",
                "Steep learning curve",
                "Frequent changes to interface",
            ],
            "migration_difficulty": "easy",
            "common_pain_points": ["performance", "too many features", "constant changes"],
        },
    }

    # Migration support offerings
    MIGRATION_SUPPORT = {
        "data_migration": {
            "service": "Free data migration assistance",
            "description": "We'll help migrate your data with zero downtime",
            "included_in": ["enterprise", "growth"],
            "typical_timeline": "1-2 weeks",
        },
        "onboarding": {
            "service": "Dedicated onboarding specialist",
            "description": "Personal onboarding support for smooth transition",
            "included_in": ["enterprise", "growth", "startup"],
            "typical_timeline": "2-4 weeks",
        },
        "training": {
            "service": "Team training sessions",
            "description": "Live training for your team to get up to speed quickly",
            "included_in": ["enterprise", "growth"],
            "typical_timeline": "1 week",
        },
        "parallel_run": {
            "service": "Parallel environment support",
            "description": "Run both systems in parallel during transition",
            "included_in": ["enterprise"],
            "typical_timeline": "Flexible",
        },
        "success_manager": {
            "service": "Dedicated success manager",
            "description": "Ongoing support post-migration",
            "included_in": ["enterprise", "growth"],
            "typical_timeline": "Ongoing",
        },
    }

    # Case studies of customers who switched from competitors
    COMPETITIVE_WIN_STORIES = {
        "salesforce_to_us": {
            "company": "TechCorp (500 employees)",
            "from_competitor": "salesforce",
            "results": "80% faster onboarding, 60% cost savings, 95% user adoption (vs 40% before)",
            "quote": "We got better results in 2 weeks than we did in 6 months with Salesforce",
            "industry": "technology",
        },
        "hubspot_to_us": {
            "company": "GrowthCo (200 employees)",
            "from_competitor": "hubspot",
            "results": "50% cost reduction, 3x more automation, better enterprise features",
            "quote": "We were paying more and getting less. The switch was a no-brainer",
            "industry": "saas",
        },
        "zendesk_to_us": {
            "company": "SupportFirst (150 employees)",
            "from_competitor": "zendesk",
            "results": "40% improvement in response time, unified platform, 35% cost savings",
            "quote": "One platform instead of three separate products. Game changer",
            "industry": "ecommerce",
        },
        "intercom_to_us": {
            "company": "ScaleUp Inc (300 employees)",
            "from_competitor": "intercom",
            "results": "70% cost reduction, better features, no conversation limits",
            "quote": "Intercom became impossibly expensive. We got more for less",
            "industry": "technology",
        },
        "trello_to_us": {
            "company": "DesignStudio (75 employees)",
            "from_competitor": "trello",
            "results": "3x better project visibility, 50% faster delivery times, proper reporting",
            "quote": "Trello was fine until we grew. Now we actually know what's happening across teams",
            "industry": "creative",
        },
        "asana_to_us": {
            "company": "MarketingPros (120 employees)",
            "from_competitor": "asana",
            "results": "40% cost savings, simpler workflows, 90% team adoption in first week",
            "quote": "Asana was too complex for what we needed. This just works",
            "industry": "marketing",
        },
        "monday_to_us": {
            "company": "ConsultCo (200 employees)",
            "from_competitor": "monday",
            "results": "60% cost reduction, same features, better support",
            "quote": "Monday.com pricing was crushing us. We got everything we needed for less",
            "industry": "consulting",
        },
        "jira_to_us": {
            "company": "AgileTeam (80 employees)",
            "from_competitor": "jira",
            "results": "2x faster onboarding, no admin overhead, happier non-dev teams",
            "quote": "Jira is great for developers but our whole company uses project management. This fits everyone",
            "industry": "technology",
        },
    }

    # Severity indicators
    SEVERITY_INDICATORS = {
        "blocker": ["locked in", "long-term contract", "heavily invested", "fully committed"],
        "major": ["currently using", "been with them for years", "satisfied with"],
        "minor": ["looking at", "considering", "evaluating", "comparing"],
    }

    def __init__(self):
        config = AgentConfig(
            name="competitor_comparison_handler",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=1200,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION,
            ],
            kb_category="sales",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process competitor comparison objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with competitive response
        """
        self.logger.info("competitor_comparison_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "competitor_comparison_details",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Identify mentioned competitors
        competitors = self._identify_competitors(message)

        # Assess objection severity
        objection_severity = self._assess_severity(message)

        # Determine competitor relationship stage
        relationship_stage = self._determine_relationship_stage(message)

        # Get competitive analysis
        competitive_analysis = self._get_competitive_analysis(competitors)

        # Determine response strategy
        strategy = self.RESPONSE_STRATEGIES.get(
            relationship_stage, self.RESPONSE_STRATEGIES["considering_competitor"]
        )

        # Get migration support options
        migration_support = self._get_migration_support(objection_severity, customer_metadata)

        # Get relevant win stories
        win_stories = self._get_win_stories(competitors, customer_metadata)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(message, category="sales", limit=4)
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_competitor_response(
            message,
            competitors,
            objection_severity,
            relationship_stage,
            competitive_analysis,
            strategy,
            migration_support,
            win_stories,
            kb_results,
            customer_metadata,
            state,
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            objection_severity, relationship_stage, competitive_analysis
        )

        # Determine escalation need
        needs_escalation = self._check_escalation_needed(objection_severity, resolution_confidence)

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["competitors_mentioned"] = competitors
        state["objection_severity"] = objection_severity
        state["relationship_stage"] = relationship_stage
        state["competitive_analysis"] = competitive_analysis
        state["response_strategy"] = strategy
        state["migration_support"] = migration_support
        state["win_stories"] = win_stories
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "competitor_comparison_handler_completed",
            competitors_count=len(competitors),
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation,
        )

        return state

    def _identify_competitors(self, message: str) -> list[str]:
        """Identify which competitors are mentioned in the message"""
        message_lower = message.lower()
        mentioned = []

        for competitor_key, competitor_data in self.COMPETITOR_ANALYSIS.items():
            if competitor_key in message_lower or competitor_data["name"].lower() in message_lower:
                mentioned.append(competitor_key)

        return mentioned if mentioned else ["generic_competitor"]

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the competitor objection"""
        message_lower = message.lower()

        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"

    def _determine_relationship_stage(self, message: str) -> str:
        """Determine the prospect's relationship stage with competitor"""
        message_lower = message.lower()

        if any(
            phrase in message_lower
            for phrase in ["currently using", "been using", "migrating from"]
        ):
            return "using_competitor"
        elif any(
            phrase in message_lower for phrase in ["happy with", "satisfied with", "works well"]
        ):
            return "satisfied_with_competitor"
        elif any(
            phrase in message_lower for phrase in ["also using", "in addition to", "alongside"]
        ):
            return "multi_vendor"
        else:
            return "considering_competitor"

    def _get_competitive_analysis(self, competitors: list[str]) -> list[dict[str, Any]]:
        """Get competitive analysis for mentioned competitors"""
        analysis = []

        for competitor in competitors:
            if competitor in self.COMPETITOR_ANALYSIS:
                analysis.append(
                    {"competitor": competitor, "data": self.COMPETITOR_ANALYSIS[competitor]}
                )
            else:
                # Generic competitor analysis
                analysis.append(
                    {
                        "competitor": competitor,
                        "data": {
                            "name": competitor.replace("_", " ").title(),
                            "our_advantages": [
                                "Better user experience and ease of use",
                                "More competitive pricing",
                                "Superior customer support",
                                "Faster innovation and feature releases",
                            ],
                            "migration_difficulty": "medium",
                        },
                    }
                )

        return analysis

    def _get_migration_support(
        self, severity: str, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Get relevant migration support offerings"""
        company_size = customer_metadata.get("company_size", 0)

        # Determine plan tier
        if company_size >= 200:
            tier = "enterprise"
        elif company_size >= 50:
            tier = "growth"
        else:
            tier = "startup"

        # Get applicable migration support
        applicable_support = []
        for _service_key, service_data in self.MIGRATION_SUPPORT.items():
            if tier in service_data["included_in"]:
                applicable_support.append(service_data)

        return applicable_support

    def _get_win_stories(
        self, competitors: list[str], customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Get relevant competitive win stories"""
        industry = customer_metadata.get("industry", "").lower()
        stories = []

        for story_key, story_data in self.COMPETITIVE_WIN_STORIES.items():
            # Match by competitor
            for competitor in competitors:
                if competitor in story_key:
                    # Prefer stories from same industry
                    if industry and story_data.get("industry", "").lower() == industry:
                        stories.insert(0, story_data)  # Add to front
                    else:
                        stories.append(story_data)

        return stories[:3]  # Return top 3 most relevant

    def _calculate_resolution_confidence(
        self, severity: str, relationship_stage: str, competitive_analysis: list[dict]
    ) -> float:
        """Calculate confidence in resolving the competitor objection"""
        base_confidence = 0.75

        # Adjust for severity
        severity_adjustments = {"minor": 0.15, "major": 0.0, "blocker": -0.20}
        confidence = base_confidence + severity_adjustments.get(severity, 0.0)

        # Adjust for relationship stage
        stage_adjustments = {
            "considering_competitor": 0.10,
            "multi_vendor": 0.05,
            "using_competitor": -0.05,
            "satisfied_with_competitor": -0.10,
        }
        confidence += stage_adjustments.get(relationship_stage, 0.0)

        # Boost confidence if we have strong competitive analysis
        if (
            competitive_analysis
            and len(competitive_analysis[0].get("data", {}).get("our_advantages", [])) >= 4
        ):
            confidence += 0.05

        return min(max(confidence, 0.0), 1.0)

    def _check_escalation_needed(self, severity: str, confidence: float) -> bool:
        """Determine if escalation is needed"""
        if severity == "blocker" and confidence < 0.70:
            return True
        return confidence < 0.6

    async def _generate_competitor_response(
        self,
        message: str,
        competitors: list[str],
        severity: str,
        relationship_stage: str,
        competitive_analysis: list[dict],
        strategy: dict,
        migration_support: list[dict],
        win_stories: list[dict],
        kb_results: list[dict],
        customer_metadata: dict,
        state: AgentState,
    ) -> str:
        """Generate personalized competitive response"""

        # Get conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build competitive analysis context
        competitive_context = "\n\nCompetitive Analysis:\n"
        for comp in competitive_analysis:
            comp_name = comp["data"].get("name", comp["competitor"])
            competitive_context += f"\n{comp_name}:\n"
            competitive_context += "Our Advantages:\n"
            for advantage in comp["data"].get("our_advantages", []):
                competitive_context += f"  • {advantage}\n"
            if "their_weaknesses" in comp["data"]:
                competitive_context += "Common Customer Pain Points with them:\n"
                for weakness in comp["data"]["their_weaknesses"]:
                    competitive_context += f"  • {weakness}\n"

        # Build migration support context
        migration_context = ""
        if migration_support:
            migration_context = "\n\nMigration Support Available:\n"
            for support in migration_support:
                migration_context += f"• {support['service']}: {support['description']}\n"
                migration_context += f"  Timeline: {support['typical_timeline']}\n"

        # Build win stories context
        stories_context = ""
        if win_stories:
            stories_context = "\n\nCustomer Success Stories:\n"
            for story in win_stories:
                stories_context += f"\n{story['company']}:\n"
                stories_context += f"  Previously: {story['from_competitor'].title()}\n"
                stories_context += f"  Results: {story['results']}\n"
                stories_context += f'  Quote: "{story["quote"]}"\n'

        system_prompt = f"""You are a Competitor Comparison Handler specialist addressing competitive concerns.

Objection Analysis:
- Competitors Mentioned: {", ".join(c.title() for c in competitors)}
- Severity: {severity.upper()}
- Relationship Stage: {relationship_stage.replace("_", " ").title()}
- Response Strategy: {strategy["approach"].replace("_", " ").title()}

Customer Profile:
- Company: {customer_metadata.get("company", "Unknown")}
- Industry: {customer_metadata.get("industry", "Unknown")}
- Company Size: {customer_metadata.get("company_size", "Unknown")}

Your response should:
1. Acknowledge their current tool/evaluation respectfully (never badmouth competitors)
2. Focus on differentiation and unique value we provide
3. Highlight specific advantages relevant to their situation
4. Share relevant customer success stories of similar companies who switched
5. Offer migration support and make switching easy
6. Be confident but not arrogant - let facts speak
7. Provide clear next steps (comparison guide, demo, trial)

Key Tactics: {", ".join(strategy["tactics"])}
Supporting Materials: {", ".join(strategy["supporting_materials"])}"""

        user_prompt = f"""Customer message: {message}

{competitive_context}
{migration_context}
{stories_context}
{kb_context}

Generate a respectful, fact-based response that differentiates our solution."""

        response = await self.call_llm(
            system_prompt, user_prompt, conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing CompetitorComparisonHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Currently using Salesforce
        state1 = create_initial_state(
            "We're currently using Salesforce and it's working okay. Why should we switch?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "title": "VP of Sales",
                    "company_size": 500,
                    "industry": "technology",
                }
            },
        )

        agent = CompetitorComparisonHandler()
        result1 = await agent.process(state1)

        print("\nTest 1 - Currently Using Salesforce")
        print(f"Competitors: {result1['competitors_mentioned']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Relationship Stage: {result1['relationship_stage']}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Migration Support Items: {len(result1['migration_support'])}")
        print(f"Win Stories: {len(result1['win_stories'])}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Evaluating HubSpot
        state2 = create_initial_state(
            "We're looking at HubSpot as well. How do you compare?",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "title": "Marketing Director",
                    "company_size": 120,
                    "industry": "saas",
                }
            },
        )

        result2 = await agent.process(state2)

        print("\nTest 2 - Evaluating HubSpot")
        print(f"Competitors: {result2['competitors_mentioned']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Relationship Stage: {result2['relationship_stage']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Competitive Advantages: {len(result2['competitive_analysis'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Locked into Intercom contract
        state3 = create_initial_state(
            "We're locked into a 2-year contract with Intercom. Their pricing is killing us as we scale.",
            context={
                "customer_metadata": {
                    "company": "ScaleUp Inc",
                    "title": "CTO",
                    "company_size": 250,
                    "industry": "technology",
                }
            },
        )

        result3 = await agent.process(state3)

        print("\nTest 3 - Locked into Intercom Contract (Blocker)")
        print(f"Competitors: {result3['competitors_mentioned']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Relationship Stage: {result3['relationship_stage']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"Needs Escalation: {result3['needs_escalation']}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
