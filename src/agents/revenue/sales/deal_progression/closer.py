"""
Closer Agent - TASK-1045

Drives deals to signature, creates urgency with incentives, executive alignment strategies,
and final objection handling to successfully close deals.
"""

from datetime import datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("closer", tier="revenue", category="sales")
class Closer(BaseAgent):
    """
    Closer Agent - Specialist in closing deals and driving to signature.

    Handles:
    - Deal closing strategies
    - Urgency creation with time-bound incentives
    - Executive alignment and sponsorship
    - Final objection handling
    - Signature facilitation
    """

    # Closing strategies by deal stage
    CLOSING_STRATEGIES = {
        "trial_conversion": {
            "primary_tactic": "value_reinforcement",
            "urgency_method": "trial_ending",
            "key_messages": [
                "You've seen the value",
                "Don't lose progress",
                "Team is already using it",
            ],
            "incentive": "trial_extension_or_discount",
        },
        "proposal_acceptance": {
            "primary_tactic": "roi_focus",
            "urgency_method": "limited_time_offer",
            "key_messages": [
                "Clear ROI demonstrated",
                "Solution addresses needs",
                "Time to move forward",
            ],
            "incentive": "early_adopter_pricing",
        },
        "negotiation_complete": {
            "primary_tactic": "commitment_seeking",
            "urgency_method": "quarter_end",
            "key_messages": ["All concerns addressed", "Terms agreed", "Ready to start"],
            "incentive": "implementation_priority",
        },
        "verbal_agreement": {
            "primary_tactic": "contract_facilitation",
            "urgency_method": "business_impact",
            "key_messages": [
                "Let's make it official",
                "Start delivering value",
                "Lock in these terms",
            ],
            "incentive": "accelerated_onboarding",
        },
    }

    # Urgency creation tactics
    URGENCY_TACTICS = {
        "time_limited_discount": {
            "type": "pricing",
            "duration_days": 7,
            "message": "Special pricing available until [DATE]",
            "discount_range": (0.05, 0.15),
            "effectiveness": 0.85,
        },
        "quarter_end_incentive": {
            "type": "pricing",
            "duration_days": 14,
            "message": "Quarter-end special - additional savings this month",
            "discount_range": (0.10, 0.20),
            "effectiveness": 0.80,
        },
        "implementation_priority": {
            "type": "service",
            "duration_days": 10,
            "message": "Sign by [DATE] for priority implementation slot",
            "value": "accelerated_timeline",
            "effectiveness": 0.75,
        },
        "feature_early_access": {
            "type": "value_add",
            "duration_days": 14,
            "message": "Early access to upcoming features for early adopters",
            "value": "beta_features",
            "effectiveness": 0.70,
        },
        "price_increase_pending": {
            "type": "pricing",
            "duration_days": 30,
            "message": "Lock in current pricing before upcoming increase",
            "impact": "price_protection",
            "effectiveness": 0.75,
        },
        "competitive_window": {
            "type": "strategic",
            "duration_days": 5,
            "message": "Limited availability in your market segment",
            "value": "exclusivity",
            "effectiveness": 0.65,
        },
    }

    # Executive alignment strategies
    EXECUTIVE_ALIGNMENT = {
        "champion_enablement": {
            "objective": "Arm internal champion with materials",
            "deliverables": [
                "Executive summary",
                "ROI deck",
                "Business case",
                "Competitor comparison",
            ],
            "timeline_days": 3,
        },
        "executive_briefing": {
            "objective": "Present to economic buyer",
            "format": "30-minute executive overview",
            "focus": ["Strategic value", "ROI metrics", "Risk mitigation", "Success timeline"],
            "timeline_days": 7,
        },
        "peer_reference": {
            "objective": "Connect with similar customer",
            "approach": "Reference call with peer executive",
            "value": "Social proof and best practices",
            "timeline_days": 5,
        },
        "executive_sponsor": {
            "objective": "Engage vendor executive",
            "approach": "VP-level relationship building",
            "value": "Strategic partnership discussion",
            "timeline_days": 10,
        },
    }

    # Final objection patterns
    FINAL_OBJECTIONS = {
        "need_more_time": {
            "type": "stalling",
            "response_strategy": "create_urgency",
            "tactics": [
                "Highlight cost of delay",
                "Offer pilot program",
                "Set specific decision date",
            ],
            "success_rate": 0.60,
        },
        "budget_approval_pending": {
            "type": "process",
            "response_strategy": "facilitate_approval",
            "tactics": [
                "Provide budget justification",
                "Offer phased approach",
                "Executive briefing",
            ],
            "success_rate": 0.70,
        },
        "need_executive_approval": {
            "type": "decision_maker",
            "response_strategy": "executive_alignment",
            "tactics": ["Executive summary", "ROI presentation", "Reference call"],
            "success_rate": 0.75,
        },
        "comparing_alternatives": {
            "type": "competitive",
            "response_strategy": "differentiation",
            "tactics": ["Feature comparison", "TCO analysis", "Customer success stories"],
            "success_rate": 0.65,
        },
        "internal_resistance": {
            "type": "political",
            "response_strategy": "stakeholder_management",
            "tactics": ["Identify blockers", "Address concerns", "Build coalition"],
            "success_rate": 0.55,
        },
        "timing_not_right": {
            "type": "priority",
            "response_strategy": "value_reframing",
            "tactics": ["Cost of inaction", "Competitive risk", "Quick wins"],
            "success_rate": 0.50,
        },
    }

    # Closing signals (buying indicators)
    CLOSING_SIGNALS = {
        "strong": [
            "asked_about_implementation_timeline",
            "requested_contract_review",
            "introduced_procurement_team",
            "discussing_specific_start_dates",
            "asking_detailed_technical_questions",
            "requested_reference_calls",
        ],
        "moderate": [
            "positive_trial_feedback",
            "multiple_stakeholder_engagement",
            "detailed_pricing_questions",
            "asking_about_support_options",
            "discussing_integration_details",
        ],
        "weak": [
            "general_interest",
            "exploring_options",
            "early_stage_questions",
            "broad_research",
        ],
    }

    # Deal momentum indicators
    MOMENTUM_LEVELS = {
        "high": {
            "indicators": ["frequent_communication", "rapid_responses", "expanding_stakeholders"],
            "action": "accelerate_to_close",
            "timeline": "1-2 weeks",
        },
        "medium": {
            "indicators": ["regular_communication", "steady_progress", "stable_engagement"],
            "action": "maintain_pressure",
            "timeline": "3-4 weeks",
        },
        "low": {
            "indicators": ["slow_responses", "delayed_meetings", "single_contact"],
            "action": "create_urgency",
            "timeline": "4-6 weeks",
        },
        "stalled": {
            "indicators": ["no_response", "cancelled_meetings", "radio_silence"],
            "action": "re_engage_or_disqualify",
            "timeline": "indefinite",
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="closer",
            type=AgentType.SPECIALIST,
            temperature=0.3,  # Lower for more consistent, professional responses
            max_tokens=400,  # Concise responses
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
        Process deal closing request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with closing strategy
        """
        self.logger.info("closer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        deal_details = state.get("deal_details", {})
        deal_stage = state.get("deal_stage", "proposal_acceptance")

        self.logger.debug(
            "closing_details", stage=deal_stage, deal_value=deal_details.get("deal_value", 0)
        )

        # Assess deal readiness
        deal_readiness = self._assess_deal_readiness(message, deal_details, deal_stage)

        # Identify closing signals
        closing_signals = self._identify_closing_signals(message, deal_details)

        # Detect any final objections
        final_objections = self._detect_final_objections(message)

        # Assess deal momentum
        momentum = self._assess_deal_momentum(deal_details)

        # Select closing strategy
        closing_strategy = self._select_closing_strategy(deal_stage, deal_readiness, momentum)

        # Create urgency tactics
        urgency_tactics = self._create_urgency_tactics(deal_details, closing_strategy, momentum)

        # Determine executive alignment needs
        executive_alignment = self._determine_executive_alignment(deal_details, customer_metadata)

        # Generate closing plan
        closing_plan = self._generate_closing_plan(
            closing_strategy, urgency_tactics, executive_alignment, final_objections, deal_details
        )

        # Calculate close probability
        close_probability = self._calculate_close_probability(
            deal_readiness, closing_signals, momentum, final_objections
        )

        # Search KB for closing techniques
        kb_results = await self.search_knowledge_base(
            f"closing techniques {deal_stage}", category="sales", limit=3
        )
        state["kb_results"] = kb_results

        # Generate response with conversation context
        response = await self._generate_closing_response(
            message,
            closing_strategy,
            closing_plan,
            urgency_tactics,
            close_probability,
            final_objections,
            kb_results,
            customer_metadata,
            state,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["deal_readiness"] = deal_readiness
        state["closing_signals"] = closing_signals
        state["final_objections"] = final_objections
        state["momentum"] = momentum
        state["closing_strategy"] = closing_strategy
        state["urgency_tactics"] = urgency_tactics
        state["executive_alignment"] = executive_alignment
        state["closing_plan"] = closing_plan
        state["close_probability"] = close_probability
        state["deal_stage"] = "closing"
        state["status"] = "resolved"

        self.logger.info(
            "closer_completed",
            strategy=closing_strategy["primary_tactic"],
            close_probability=close_probability,
            momentum=momentum["level"],
        )

        return state

    def _assess_deal_readiness(
        self, message: str, deal_details: dict, deal_stage: str
    ) -> dict[str, Any]:
        """Assess if deal is ready to close"""
        readiness_score = 0
        max_score = 10
        checklist = {}

        # Check if proposal sent
        if deal_details.get("proposal_sent", False):
            readiness_score += 2
            checklist["proposal_sent"] = True
        else:
            checklist["proposal_sent"] = False

        # Check if demo completed
        if deal_details.get("demo_completed", False):
            readiness_score += 2
            checklist["demo_completed"] = True
        else:
            checklist["demo_completed"] = False

        # Check if decision maker engaged
        if deal_details.get("decision_maker_engaged", False):
            readiness_score += 2
            checklist["decision_maker_engaged"] = True
        else:
            checklist["decision_maker_engaged"] = False

        # Check if objections addressed
        if deal_details.get("objections_resolved", True):
            readiness_score += 2
            checklist["objections_resolved"] = True
        else:
            checklist["objections_resolved"] = False

        # Check if budget confirmed
        if deal_details.get("budget_confirmed", False):
            readiness_score += 2
            checklist["budget_confirmed"] = True
        else:
            checklist["budget_confirmed"] = False

        readiness_percentage = readiness_score / max_score

        return {
            "score": readiness_score,
            "max_score": max_score,
            "percentage": readiness_percentage,
            "checklist": checklist,
            "ready_to_close": readiness_percentage >= 0.7,
        }

    def _identify_closing_signals(self, message: str, deal_details: dict) -> dict[str, list[str]]:
        """Identify buying signals in communication"""
        signals = {"strong": [], "moderate": [], "weak": []}

        message_lower = message.lower()

        # Check for strong signals
        if any(
            sig in message_lower
            for sig in ["implementation", "start date", "contract", "procurement"]
        ):
            signals["strong"].append("asking_about_implementation")
        if "reference" in message_lower:
            signals["strong"].append("requested_references")

        # Check for moderate signals
        if "pricing" in message_lower or "cost" in message_lower:
            signals["moderate"].append("detailed_pricing_questions")
        if "support" in message_lower or "training" in message_lower:
            signals["moderate"].append("asking_about_support")

        # From deal details
        if deal_details.get("trial_active", False):
            signals["moderate"].append("active_trial_usage")

        return signals

    def _detect_final_objections(self, message: str) -> list[dict[str, Any]]:
        """Detect any final objections before closing"""
        objections = []
        message_lower = message.lower()

        for obj_type, obj_details in self.FINAL_OBJECTIONS.items():
            # Simple pattern matching
            if (
                (
                    obj_type == "need_more_time"
                    and any(
                        phrase in message_lower
                        for phrase in ["need time", "think about it", "not ready"]
                    )
                )
                or (
                    obj_type == "budget_approval_pending"
                    and "budget" in message_lower
                    and "approval" in message_lower
                )
                or (
                    obj_type == "need_executive_approval"
                    and (
                        "executive" in message_lower
                        or "ceo" in message_lower
                        or "approval" in message_lower
                    )
                )
            ):
                objections.append({"type": obj_type, "details": obj_details})

        return objections

    def _assess_deal_momentum(self, deal_details: dict) -> dict[str, Any]:
        """Assess current deal momentum"""
        # Analyze engagement patterns
        days_since_last_contact = deal_details.get("days_since_last_contact", 0)
        response_time_hours = deal_details.get("avg_response_time_hours", 24)
        stakeholder_count = deal_details.get("stakeholder_count", 1)

        # Determine momentum level
        if days_since_last_contact <= 2 and response_time_hours <= 24 and stakeholder_count >= 3:
            level = "high"
        elif days_since_last_contact <= 5 and response_time_hours <= 48:
            level = "medium"
        elif days_since_last_contact <= 10:
            level = "low"
        else:
            level = "stalled"

        momentum_info = self.MOMENTUM_LEVELS[level]

        return {
            "level": level,
            "action": momentum_info["action"],
            "timeline": momentum_info["timeline"],
            "days_since_contact": days_since_last_contact,
            "response_time": response_time_hours,
        }

    def _select_closing_strategy(
        self, deal_stage: str, readiness: dict, momentum: dict
    ) -> dict[str, Any]:
        """Select appropriate closing strategy"""
        # Get base strategy for stage
        if deal_stage in self.CLOSING_STRATEGIES:
            strategy = self.CLOSING_STRATEGIES[deal_stage].copy()
        else:
            strategy = self.CLOSING_STRATEGIES["proposal_acceptance"].copy()

        # Adjust based on readiness
        if readiness["percentage"] < 0.5:
            strategy["approach"] = "build_readiness"
        elif momentum["level"] == "high":
            strategy["approach"] = "aggressive_close"
        elif momentum["level"] == "stalled":
            strategy["approach"] = "re_engagement"
        else:
            strategy["approach"] = "standard_close"

        return strategy

    def _create_urgency_tactics(
        self, deal_details: dict, strategy: dict, momentum: dict
    ) -> list[dict[str, Any]]:
        """Create urgency tactics appropriate for the deal"""
        tactics = []

        deal_details.get("deal_value", 0)

        # Select tactics based on momentum
        if momentum["level"] == "high":
            # Use aggressive urgency
            tactics.append(
                {
                    "tactic": "implementation_priority",
                    "details": self.URGENCY_TACTICS["implementation_priority"],
                    "deadline": (datetime.now() + timedelta(days=7)).strftime("%B %d, %Y"),
                }
            )
        elif momentum["level"] == "medium":
            # Use moderate urgency
            tactics.append(
                {
                    "tactic": "time_limited_discount",
                    "details": self.URGENCY_TACTICS["time_limited_discount"],
                    "deadline": (datetime.now() + timedelta(days=10)).strftime("%B %d, %Y"),
                    "discount": "10%",
                }
            )
        else:
            # Use value-focused urgency
            tactics.append(
                {
                    "tactic": "competitive_window",
                    "details": self.URGENCY_TACTICS["competitive_window"],
                    "deadline": (datetime.now() + timedelta(days=14)).strftime("%B %d, %Y"),
                }
            )

        # Add quarter-end if applicable
        now = datetime.now()
        days_to_quarter_end = 90 - (now.day % 90)
        if days_to_quarter_end <= 21:
            tactics.append(
                {
                    "tactic": "quarter_end_incentive",
                    "details": self.URGENCY_TACTICS["quarter_end_incentive"],
                    "deadline": (now + timedelta(days=days_to_quarter_end)).strftime("%B %d, %Y"),
                }
            )

        return tactics[:2]  # Return top 2 tactics

    def _determine_executive_alignment(
        self, deal_details: dict, customer_metadata: dict
    ) -> dict[str, Any]:
        """Determine executive alignment strategy"""
        deal_value = deal_details.get("deal_value", 0)
        decision_maker_title = customer_metadata.get("title", "").lower()

        # Determine if executive alignment needed
        needs_executive = deal_value > 100000 or not any(
            exec_title in decision_maker_title
            for exec_title in ["ceo", "cto", "cfo", "vp", "president"]
        )

        if needs_executive:
            # Select alignment strategies
            strategies = []

            # Always enable champion
            strategies.append(self.EXECUTIVE_ALIGNMENT["champion_enablement"])

            # Add executive briefing for large deals
            if deal_value > 200000:
                strategies.append(self.EXECUTIVE_ALIGNMENT["executive_briefing"])
                strategies.append(self.EXECUTIVE_ALIGNMENT["peer_reference"])

            return {
                "needed": True,
                "strategies": strategies,
                "priority": "high" if deal_value > 200000 else "medium",
            }
        else:
            return {"needed": False, "strategies": [], "priority": "low"}

    def _generate_closing_plan(
        self,
        strategy: dict,
        urgency_tactics: list[dict],
        executive_alignment: dict,
        objections: list[dict],
        deal_details: dict,
    ) -> dict[str, Any]:
        """Generate comprehensive closing plan"""
        plan_steps = []

        # Step 1: Address any final objections
        if objections:
            for obj in objections:
                plan_steps.append(
                    {
                        "step": f"Address {obj['type'].replace('_', ' ')}",
                        "tactics": obj["details"]["tactics"],
                        "timeline": "Immediate",
                    }
                )

        # Step 2: Executive alignment if needed
        if executive_alignment["needed"]:
            for strat in executive_alignment["strategies"]:
                plan_steps.append(
                    {
                        "step": strat["objective"],
                        "deliverables": strat.get("deliverables", []),
                        "timeline": f"{strat['timeline_days']} days",
                    }
                )

        # Step 3: Create urgency
        if urgency_tactics:
            plan_steps.append(
                {
                    "step": "Present time-limited incentive",
                    "tactics": [t["tactic"] for t in urgency_tactics],
                    "timeline": "This week",
                }
            )

        # Step 4: Request commitment
        plan_steps.append(
            {
                "step": "Request signature",
                "approach": strategy["primary_tactic"],
                "timeline": "Next 7-14 days",
            }
        )

        return {
            "steps": plan_steps,
            "total_timeline_days": 14,
            "success_probability": self._estimate_success_probability(strategy, objections),
        }

    def _estimate_success_probability(self, strategy: dict, objections: list[dict]) -> float:
        """Estimate probability of successful close"""
        base_probability = 0.60

        # Reduce for objections
        for obj in objections:
            base_probability *= obj["details"]["success_rate"]

        return min(max(base_probability, 0.0), 1.0)

    def _calculate_close_probability(
        self, readiness: dict, signals: dict, momentum: dict, objections: list[dict]
    ) -> float:
        """Calculate overall close probability"""
        # Start with readiness
        probability = readiness["percentage"]

        # Boost for signals
        strong_signals = len(signals["strong"])
        moderate_signals = len(signals["moderate"])
        probability += (strong_signals * 0.10) + (moderate_signals * 0.05)

        # Adjust for momentum
        momentum_adjustments = {"high": 0.15, "medium": 0.05, "low": -0.05, "stalled": -0.20}
        probability += momentum_adjustments.get(momentum["level"], 0)

        # Reduce for objections
        probability -= len(objections) * 0.10

        return max(0.0, min(1.0, probability))

    async def _generate_closing_response(
        self,
        message: str,
        strategy: dict,
        plan: dict,
        urgency_tactics: list[dict],
        close_probability: float,
        objections: list[dict],
        kb_results: list[dict],
        customer_metadata: dict,
        state: AgentState,
    ) -> str:
        """Generate closing response"""

        # Get conversation history for multi-turn context
        conversation_history = self.get_conversation_context(state)

        # Build urgency context
        urgency_context = ""
        if urgency_tactics:
            urgency_context = "\n\nTime-Limited Opportunities:\n"
            for tactic in urgency_tactics:
                urgency_context += (
                    f"- {tactic['details']['message'].replace('[DATE]', tactic['deadline'])}\n"
                )

        # Build objection context
        objection_context = ""
        if objections:
            objection_context = "\n\nFinal Concerns to Address:\n"
            for obj in objections:
                objection_context += f"- {obj['type'].replace('_', ' ').title()}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nClosing Best Practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a helpful sales assistant.

Customer: {customer_metadata.get("company", "Customer")}

CRITICAL RULES:
1. NEVER use placeholder text like "[Agent Name]", "[Your Name]", or similar. Just speak naturally without introducing yourself by name.
2. ALWAYS answer direct questions first. If the customer asks about pricing, give them pricing information immediately.
3. Keep responses SHORT and DIRECT - 2-4 sentences max for simple questions.
4. Be helpful and professional, NOT pushy or aggressive.
5. Use the customer's name if known from conversation history.
6. Reference previous conversation context naturally - don't repeat introductions.
7. Only mention promotions or deadlines if directly relevant to what they asked.

DO NOT:
- Give long sales pitches
- Ask multiple questions in one response
- Use aggressive urgency tactics
- Repeat information already discussed
- Introduce yourself or use placeholder names"""

        user_prompt = f"""Customer message: {message}

Respond helpfully and directly to what the customer is asking. If they're ready to proceed, help them with the next steps simply and clearly."""

        # Call LLM with conversation history for multi-turn context
        response = await self.call_llm(
            system_prompt, user_prompt, conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing Closer Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: High-momentum deal ready to close
        state1 = create_initial_state(
            "Everything looks good. What are the next steps to get started?",
            context={
                "customer_metadata": {
                    "company": "ReadyBuyer Inc",
                    "title": "VP Operations",
                    "company_size": 200,
                    "industry": "technology",
                },
                "deal_details": {
                    "deal_value": 150000,
                    "proposal_sent": True,
                    "demo_completed": True,
                    "decision_maker_engaged": True,
                    "objections_resolved": True,
                    "budget_confirmed": True,
                    "days_since_last_contact": 1,
                    "avg_response_time_hours": 12,
                    "stakeholder_count": 4,
                    "trial_active": True,
                },
                "deal_stage": "verbal_agreement",
            },
        )

        agent = Closer()
        result1 = await agent.process(state1)

        print("\nTest 1 - High-Momentum Ready to Close")
        print(f"Deal Readiness: {result1['deal_readiness']['percentage']:.0%}")
        print(f"Momentum Level: {result1['momentum']['level']}")
        print(f"Close Probability: {result1['close_probability']:.0%}")
        print(f"Closing Strategy: {result1['closing_strategy']['approach']}")
        print(f"Urgency Tactics: {len(result1['urgency_tactics'])}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Deal with final objections
        state2 = create_initial_state(
            "We like the solution but need more time to get executive approval and budget sign-off",
            context={
                "customer_metadata": {
                    "company": "SlowDecision Corp",
                    "title": "Director",
                    "company_size": 500,
                    "industry": "finance",
                },
                "deal_details": {
                    "deal_value": 300000,
                    "proposal_sent": True,
                    "demo_completed": True,
                    "decision_maker_engaged": False,
                    "objections_resolved": True,
                    "budget_confirmed": False,
                    "days_since_last_contact": 5,
                    "avg_response_time_hours": 48,
                    "stakeholder_count": 2,
                },
                "deal_stage": "negotiation_complete",
            },
        )

        result2 = await agent.process(state2)

        print("\nTest 2 - Deal with Final Objections")
        print(f"Final Objections: {len(result2['final_objections'])}")
        print(f"Momentum Level: {result2['momentum']['level']}")
        print(f"Close Probability: {result2['close_probability']:.0%}")
        print(f"Executive Alignment Needed: {result2['executive_alignment']['needed']}")
        print(f"Closing Plan Steps: {len(result2['closing_plan']['steps'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Stalled deal needing re-engagement
        state3 = create_initial_state(
            "Just following up on our proposal",
            context={
                "customer_metadata": {
                    "company": "Stalled Inc",
                    "title": "Manager",
                    "company_size": 75,
                    "industry": "retail",
                },
                "deal_details": {
                    "deal_value": 50000,
                    "proposal_sent": True,
                    "demo_completed": True,
                    "decision_maker_engaged": False,
                    "objections_resolved": True,
                    "budget_confirmed": False,
                    "days_since_last_contact": 15,
                    "avg_response_time_hours": 120,
                    "stakeholder_count": 1,
                },
                "deal_stage": "proposal_acceptance",
            },
        )

        result3 = await agent.process(state3)

        print("\nTest 3 - Stalled Deal Re-engagement")
        print(f"Momentum Level: {result3['momentum']['level']}")
        print(f"Momentum Action: {result3['momentum']['action']}")
        print(f"Close Probability: {result3['close_probability']:.0%}")
        print(f"Closing Strategy: {result3['closing_strategy']['approach']}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
