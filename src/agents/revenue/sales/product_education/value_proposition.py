"""
Value Proposition Agent - TASK-1025

Crafts tailored value propositions for prospects.
Explains "why us" vs competitors, highlights differentiators, and matches benefits to goals.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("value_proposition", tier="revenue", category="sales")
class ValueProposition(BaseAgent):
    """
    Value Proposition Agent - Specialist in crafting compelling value propositions.

    Handles:
    - Tailored value proposition creation
    - Competitive differentiation ("why us")
    - Unique differentiator highlighting
    - Benefit-to-goal mapping
    - Objection handling through value messaging
    """

    # Core value pillars
    VALUE_PILLARS = {
        "ease_of_use": {
            "headline": "Easiest to implement and use",
            "description": "Up and running in days, not months",
            "proof_points": [
                "Average setup time: 3 days vs 4-6 weeks for competitors",
                "93% of users proficient within first week",
                "No-code configuration for 80% of use cases"
            ],
            "best_for": ["small", "medium"]
        },
        "enterprise_grade": {
            "headline": "Enterprise-grade security and compliance",
            "description": "Built for the most demanding requirements",
            "proof_points": [
                "SOC 2 Type II, HIPAA, and GDPR compliant",
                "99.99% uptime SLA",
                "Enterprise SSO and advanced access controls"
            ],
            "best_for": ["large", "enterprise"]
        },
        "innovation": {
            "headline": "Most innovative AI-powered platform",
            "description": "Cutting-edge technology that's always ahead",
            "proof_points": [
                "AI-powered automation saves 10x more time",
                "Predictive analytics built-in",
                "Continuous innovation with monthly releases"
            ],
            "best_for": ["technology", "finance"]
        },
        "integration": {
            "headline": "Connects to everything you use",
            "description": "200+ pre-built integrations and robust API",
            "proof_points": [
                "200+ native integrations vs avg 50 for competitors",
                "Full REST API with 99.9% reliability",
                "Real-time bidirectional sync"
            ],
            "best_for": ["all"]
        },
        "support": {
            "headline": "White-glove support that cares",
            "description": "24/7 human support, not chatbots",
            "proof_points": [
                "Average response time: 2 minutes",
                "98% customer satisfaction score",
                "Dedicated success manager for every account"
            ],
            "best_for": ["all"]
        },
        "roi": {
            "headline": "Proven ROI in under 6 months",
            "description": "Fast payback with measurable results",
            "proof_points": [
                "Average ROI: 312% in first year",
                "Payback period: 4.2 months average",
                "Customer success rate: 96%"
            ],
            "best_for": ["all"]
        }
    }

    # Competitive differentiators by competitor
    COMPETITIVE_ADVANTAGES = {
        "competitor_a": {
            "name": "Legacy Leader",
            "our_advantages": [
                "Modern UI that users love (vs their 90s-era interface)",
                "50% lower pricing with transparent per-user model",
                "No long-term contracts required",
                "Setup in days vs their 3-month implementation"
            ]
        },
        "competitor_b": {
            "name": "Fast-Growing Startup",
            "our_advantages": [
                "Enterprise-grade reliability (99.99% vs their 98%)",
                "Proven at scale (5000+ enterprise customers)",
                "24/7 support vs business hours only",
                "SOC 2 Type II certified (they're still working on it)"
            ]
        },
        "competitor_c": {
            "name": "Budget Option",
            "our_advantages": [
                "Full feature set (not limited 'lite' version)",
                "Scales with you (no painful migrations later)",
                "Real support team vs community forums",
                "Better long-term value despite higher initial price"
            ]
        }
    }

    # Goal-to-benefit mapping
    GOAL_BENEFIT_MAPPING = {
        "reduce_costs": [
            "60% reduction in manual labor costs",
            "Eliminate redundant tools (average 3-5 tools replaced)",
            "Reduce errors that cost money"
        ],
        "save_time": [
            "5-10 hours saved per user per week",
            "Automated workflows handle routine tasks",
            "Faster decision-making with real-time data"
        ],
        "improve_quality": [
            "95% reduction in errors",
            "Consistent processes across teams",
            "Audit trail for accountability"
        ],
        "scale_operations": [
            "Handle 10x volume without adding headcount",
            "Proven at enterprise scale (Fortune 500 customers)",
            "Infrastructure that grows with you"
        ],
        "ensure_compliance": [
            "Automated compliance workflows",
            "Always audit-ready",
            "Reduce compliance risk by 80%"
        ],
        "improve_customer_satisfaction": [
            "Faster response times to customers",
            "Better data for personalization",
            "Consistent customer experience"
        ],
        "increase_revenue": [
            "Sell more with better insights",
            "Faster time-to-market for new products",
            "Higher conversion rates"
        ]
    }

    # Industry-specific value props
    INDUSTRY_VALUE_PROPS = {
        "technology": "Built by engineers, for engineers. API-first design with the flexibility you need.",
        "healthcare": "HIPAA-compliant, secure, and purpose-built for healthcare workflows.",
        "finance": "Bank-grade security with SOX compliance built-in. Trusted by top financial institutions.",
        "retail": "Omnichannel ready. Integrate POS, inventory, and customer data seamlessly.",
        "manufacturing": "IoT-ready platform. Real-time visibility from shop floor to top floor."
    }

    def __init__(self):
        config = AgentConfig(
            name="value_proposition",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.4,
            max_tokens=1200,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process value proposition creation"""
        self.logger.info("value_proposition_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        conversation_history = state.get("messages", [])

        # Identify prospect's goals
        identified_goals = self._identify_goals(message, conversation_history)

        # Select relevant value pillars
        selected_pillars = self._select_value_pillars(customer_metadata, identified_goals)

        # Map benefits to goals
        benefit_mapping = self._map_benefits_to_goals(identified_goals)

        # Generate competitive positioning
        competitive_positioning = self._generate_competitive_positioning(
            message,
            customer_metadata
        )

        # Create industry-specific angle
        industry_angle = self._get_industry_value_prop(customer_metadata)

        # Build unique differentiators list
        differentiators = self._build_differentiators(selected_pillars)

        # Search KB for customer testimonials
        kb_results = await self.search_knowledge_base(
            f"customer testimonial success story {customer_metadata.get('industry', '')}",
            category="sales",
            limit=5
        )
        state["kb_results"] = kb_results

        # Generate tailored value proposition
        response = await self._generate_value_prop_response(
            message,
            identified_goals,
            selected_pillars,
            benefit_mapping,
            competitive_positioning,
            industry_angle,
            differentiators,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.86
        state["identified_goals"] = identified_goals
        state["selected_value_pillars"] = selected_pillars
        state["benefit_mapping"] = benefit_mapping
        state["competitive_positioning"] = competitive_positioning
        state["differentiators"] = differentiators
        state["status"] = "resolved"

        self.logger.info(
            "value_proposition_completed",
            goals_count=len(identified_goals),
            pillars_count=len(selected_pillars)
        )

        return state

    def _identify_goals(
        self,
        message: str,
        conversation_history: List[Dict]
    ) -> List[str]:
        """Identify prospect's business goals"""
        goals = []

        # Combine all conversation text
        all_text = message.lower()
        for msg in conversation_history:
            if msg.get("content"):
                all_text += " " + msg["content"].lower()

        # Goal keywords
        goal_keywords = {
            "reduce_costs": ["save money", "reduce cost", "cut costs", "budget", "expensive"],
            "save_time": ["save time", "faster", "efficiency", "automate", "manual"],
            "improve_quality": ["quality", "errors", "mistakes", "accuracy", "consistency"],
            "scale_operations": ["scale", "growth", "growing", "expand", "capacity"],
            "ensure_compliance": ["compliance", "audit", "regulatory", "hipaa", "sox", "gdpr"],
            "improve_customer_satisfaction": ["customer", "satisfaction", "experience", "service"],
            "increase_revenue": ["revenue", "sales", "grow business", "profits", "conversion"]
        }

        for goal, keywords in goal_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                goals.append(goal)

        # Default goal if none detected
        if not goals:
            goals.append("improve_efficiency")

        return goals

    def _select_value_pillars(
        self,
        customer_metadata: Dict,
        goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Select most relevant value pillars"""
        company_size = customer_metadata.get("company_size", 0)
        industry = customer_metadata.get("industry", "other").lower()

        # Determine size category
        if company_size < 50:
            size_category = "small"
        elif company_size < 500:
            size_category = "medium"
        elif company_size < 1000:
            size_category = "large"
        else:
            size_category = "enterprise"

        selected = []

        # Always include ROI and support
        selected.append(self.VALUE_PILLARS["roi"])
        selected.append(self.VALUE_PILLARS["support"])

        # Add pillars based on company size
        for pillar_name, pillar in self.VALUE_PILLARS.items():
            if pillar_name in ["roi", "support"]:
                continue  # Already added

            best_for = pillar.get("best_for", [])
            if "all" in best_for or size_category in best_for or industry in best_for:
                selected.append(pillar)

        # Limit to top 4 pillars
        return selected[:4]

    def _map_benefits_to_goals(self, goals: List[str]) -> Dict[str, List[str]]:
        """Map specific benefits to identified goals"""
        mapping = {}

        for goal in goals:
            if goal in self.GOAL_BENEFIT_MAPPING:
                mapping[goal] = self.GOAL_BENEFIT_MAPPING[goal]

        return mapping

    def _generate_competitive_positioning(
        self,
        message: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate competitive positioning"""
        message_lower = message.lower()

        # Try to detect competitor mentions
        mentioned_competitor = None
        for comp_key, comp_data in self.COMPETITIVE_ADVANTAGES.items():
            if comp_data["name"].lower() in message_lower:
                mentioned_competitor = comp_key
                break

        if mentioned_competitor:
            positioning = self.COMPETITIVE_ADVANTAGES[mentioned_competitor]
        else:
            # Generic positioning against all competitors
            positioning = {
                "name": "Other Solutions",
                "our_advantages": [
                    "Faster time to value (days vs months)",
                    "Better price-to-performance ratio",
                    "Superior customer support and satisfaction",
                    "More flexible and easier to use"
                ]
            }

        return positioning

    def _get_industry_value_prop(self, customer_metadata: Dict) -> str:
        """Get industry-specific value proposition"""
        industry = customer_metadata.get("industry", "technology").lower()
        return self.INDUSTRY_VALUE_PROPS.get(
            industry,
            "Purpose-built for your industry with proven results."
        )

    def _build_differentiators(self, selected_pillars: List[Dict]) -> List[str]:
        """Build list of unique differentiators"""
        differentiators = []

        for pillar in selected_pillars:
            # Take the headline as a differentiator
            differentiators.append(pillar["headline"])

        return differentiators

    async def _generate_value_prop_response(
        self,
        message: str,
        goals: List[str],
        pillars: List[Dict],
        benefit_mapping: Dict,
        competitive_positioning: Dict,
        industry_angle: str,
        differentiators: List[str],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate tailored value proposition response"""

        # Build pillars context
        pillars_context = "\n\nKey Value Pillars:\n"
        for pillar in pillars:
            pillars_context += f"- {pillar['headline']}: {pillar['description']}\n"
            pillars_context += f"  Proof: {pillar['proof_points'][0]}\n"

        # Build benefits context
        benefits_context = "\n\nBenefits Matched to Goals:\n"
        for goal, benefits in benefit_mapping.items():
            benefits_context += f"- {goal.replace('_', ' ').title()}:\n"
            for benefit in benefits:
                benefits_context += f"  • {benefit}\n"

        # Build competitive context
        competitive_context = f"\n\nWhy Choose Us vs {competitive_positioning['name']}:\n"
        for advantage in competitive_positioning["our_advantages"]:
            competitive_context += f"- {advantage}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nCustomer Success Stories:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Success Story')}\n"

        system_prompt = f"""You are a Value Proposition specialist crafting compelling "why us" messaging.

Prospect Profile:
- Industry: {customer_metadata.get('industry', 'Unknown').title()}
- Company Size: {customer_metadata.get('company_size', 'Unknown')}
- Title: {customer_metadata.get('title', 'Unknown')}
- Goals: {', '.join([g.replace('_', ' ').title() for g in goals])}

Industry Positioning: {industry_angle}

Unique Differentiators: {', '.join(differentiators)}

Your response should:
1. Lead with the most compelling value pillar for their situation
2. Connect benefits directly to their stated goals
3. Use specific proof points and numbers
4. Address competitive concerns if mentioned
5. Include industry-specific language
6. Make it personal and relevant, not generic
7. Build confidence through proof (customer stories, metrics)
8. End with a clear reason to choose us"""

        user_prompt = f"""Customer message: {message}

{pillars_context}
{benefits_context}
{competitive_context}
{kb_context}

Generate a compelling, tailored value proposition response."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    """Test harness for ValueProposition"""
    import asyncio
    from src.workflow.state import AgentState

    async def test_value_proposition():
        agent = ValueProposition()

        # Test case 1: Cost-focused prospect
        state1 = AgentState(
            current_message="Why should we choose you? We're looking to reduce costs and improve efficiency.",
            customer_metadata={
                "title": "VP Operations",
                "industry": "manufacturing",
                "company_size": 500
            },
            messages=[],
            status="pending"
        )

        result1 = await agent.process(state1)
        print("Test 1 - Cost Reduction Value Prop:")
        print(f"Identified Goals: {result1['identified_goals']}")
        print(f"Value Pillars: {[p['headline'] for p in result1['selected_value_pillars']]}")
        print(f"Differentiators: {result1['differentiators']}")
        print()

        # Test case 2: Competitive situation
        state2 = AgentState(
            current_message="We're currently evaluating you against Legacy Leader. What makes you different?",
            customer_metadata={
                "title": "CTO",
                "industry": "technology",
                "company_size": 1200
            },
            messages=[],
            status="pending"
        )

        result2 = await agent.process(state2)
        print("Test 2 - Competitive Differentiation:")
        print(f"Competitor: {result2['competitive_positioning']['name']}")
        print(f"Our Advantages: {len(result2['competitive_positioning']['our_advantages'])}")
        print()

    asyncio.run(test_value_proposition())
