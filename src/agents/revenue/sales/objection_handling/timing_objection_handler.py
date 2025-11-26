"""
Timing Objection Handler Agent - TASK-1036

Handles "not ready yet" objections by offering pilot programs, phased rollouts,
and explaining risks of waiting.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("timing_objection_handler", tier="revenue", category="sales")
class TimingObjectionHandler(BaseAgent):
    """
    Timing Objection Handler Agent - Specialist in handling timing/readiness objections.

    Handles:
    - "Not ready yet" objections
    - Pilot programs and trials
    - Phased rollout approaches
    - Risks of waiting/competitive urgency
    - Future-proof commitments
    """

    # Response strategies for different timing objections
    RESPONSE_STRATEGIES = {
        "not_ready_now": {
            "approach": "pilot_program",
            "tactics": ["pilot_offering", "soft_start", "early_wins"],
            "supporting_materials": ["pilot_guide", "quick_start_checklist", "success_stories"],
        },
        "budget_next_quarter": {
            "approach": "reservation_strategy",
            "tactics": ["lock_pricing", "reserve_spot", "budget_justification"],
            "supporting_materials": ["budget_template", "roi_calculator", "pricing_guarantee"],
        },
        "too_busy_right_now": {
            "approach": "low_touch_onboarding",
            "tactics": ["turnkey_setup", "white_glove_onboarding", "minimal_effort_required"],
            "supporting_materials": [
                "onboarding_timeline",
                "effort_estimate",
                "done_for_you_services",
            ],
        },
        "waiting_for_x": {
            "approach": "phased_rollout",
            "tactics": ["start_partial", "gradual_implementation", "parallel_running"],
            "supporting_materials": [
                "phased_plan",
                "implementation_roadmap",
                "flexibility_options",
            ],
        },
        "exploring_options": {
            "approach": "urgency_creation",
            "tactics": ["competitive_pressure", "opportunity_cost", "limited_time_offers"],
            "supporting_materials": ["market_trends", "competitive_analysis", "special_offers"],
        },
    }

    # Pilot program options
    PILOT_PROGRAMS = {
        "quick_start_pilot": {
            "name": "Quick Start Pilot",
            "duration": "30 days",
            "user_limit": "10 users",
            "features": "Core features only",
            "cost": "Free",
            "support_level": "Email support",
            "conversion_incentive": "20% discount on annual plan if converted",
            "ideal_for": ["not_ready_now", "too_busy_right_now"],
        },
        "department_pilot": {
            "name": "Department Pilot",
            "duration": "60 days",
            "user_limit": "25 users",
            "features": "Full platform access",
            "cost": "50% off regular pricing",
            "support_level": "Dedicated success manager",
            "conversion_incentive": "Grandfather pricing + free onboarding",
            "ideal_for": ["not_ready_now", "waiting_for_x"],
        },
        "enterprise_pilot": {
            "name": "Enterprise Pilot",
            "duration": "90 days",
            "user_limit": "Unlimited",
            "features": "Full enterprise features",
            "cost": "Custom pricing",
            "support_level": "White-glove support + quarterly reviews",
            "conversion_incentive": "Custom contract terms",
            "ideal_for": ["waiting_for_x", "exploring_options"],
        },
    }

    # Phased rollout approaches
    PHASED_ROLLOUT_OPTIONS = {
        "crawl_walk_run": {
            "name": "Crawl, Walk, Run Approach",
            "phase1": {
                "duration": "2-4 weeks",
                "scope": "Single team/department (10-20 users)",
                "goal": "Validate fit and gather feedback",
                "effort": "Low - 2-3 hours setup",
            },
            "phase2": {
                "duration": "4-8 weeks",
                "scope": "Expand to related teams (50-100 users)",
                "goal": "Refine processes and build momentum",
                "effort": "Medium - team training",
            },
            "phase3": {
                "duration": "8-12 weeks",
                "scope": "Full company rollout",
                "goal": "Complete adoption and optimization",
                "effort": "Managed - with support team",
            },
        },
        "parallel_running": {
            "name": "Parallel Running",
            "description": "Run new system alongside existing tools",
            "duration": "4-12 weeks",
            "benefits": ["Zero risk", "Compare results", "Smooth transition"],
            "support": "Migration assistance included",
        },
        "feature_based_rollout": {
            "name": "Feature-Based Rollout",
            "description": "Implement features incrementally",
            "approach": "Start with most valuable features, add more over time",
            "benefits": ["Quick wins", "Manageable change", "Lower risk"],
            "timeline": "Flexible, based on your pace",
        },
    }

    # Risks of waiting / urgency factors
    URGENCY_FACTORS = {
        "opportunity_cost": {
            "factor": "Opportunity Cost",
            "impact": "high",
            "description": "Every month of delay costs potential productivity gains",
            "quantification": "Typical ROI of 2.5x means waiting = losing money",
            "time_impact": "6-month delay = $X in lost productivity",
        },
        "competitive_disadvantage": {
            "factor": "Competitive Disadvantage",
            "impact": "medium",
            "description": "Competitors adopting faster move ahead",
            "quantification": "Companies implementing now gain 6-month advantage",
            "time_impact": "Market share implications",
        },
        "price_increases": {
            "factor": "Pricing Changes",
            "impact": "medium",
            "description": "Current pricing guaranteed only for limited time",
            "quantification": "Next pricing tier is 15-20% higher",
            "time_impact": "Lock in current pricing now",
        },
        "change_management": {
            "factor": "Change Management Complexity",
            "impact": "medium",
            "description": "Delaying makes eventual change harder",
            "quantification": "User adoption drops 25% for each quarter delayed",
            "time_impact": "Organizational resistance increases over time",
        },
        "technical_debt": {
            "factor": "Growing Technical Debt",
            "impact": "high",
            "description": "Current inefficient processes accumulate problems",
            "quantification": "Manual processes double in cost annually",
            "time_impact": "Migration complexity increases with delay",
        },
    }

    # Low-effort onboarding options
    LOW_EFFORT_OPTIONS = {
        "white_glove_onboarding": {
            "service": "White-Glove Onboarding",
            "customer_time": "4-6 hours total",
            "our_team_does": [
                "Data migration",
                "Configuration",
                "Integration setup",
                "Team training",
            ],
            "customer_does": ["Initial requirements call", "Provide access", "User acceptance"],
            "timeline": "2 weeks to full production",
            "availability": "Enterprise and Growth plans",
        },
        "turnkey_setup": {
            "service": "Turnkey Setup Service",
            "customer_time": "2-3 hours total",
            "our_team_does": [
                "Pre-configured templates",
                "Automated setup",
                "Best practices applied",
            ],
            "customer_does": ["Review setup", "Invite users"],
            "timeline": "3-5 days to launch",
            "availability": "All plans",
        },
        "done_for_you_migration": {
            "service": "Done-For-You Migration",
            "customer_time": "1-2 hours (data review only)",
            "our_team_does": [
                "Extract data from old system",
                "Clean and transform",
                "Import and validate",
            ],
            "customer_does": ["Provide credentials", "Final approval"],
            "timeline": "1-2 weeks",
            "availability": "Growth and Enterprise plans",
        },
    }

    # Budget justification resources
    BUDGET_RESOURCES = {
        "business_case_template": {
            "name": "Business Case Template",
            "description": "Pre-built ROI calculator and business case",
            "includes": ["Cost-benefit analysis", "ROI projections", "Competitor comparisons"],
            "typical_roi": "2.5x in first year",
        },
        "executive_summary": {
            "name": "Executive Summary",
            "description": "One-page overview for executive approval",
            "includes": ["Key benefits", "Investment required", "Expected outcomes"],
            "format": "PowerPoint and PDF",
        },
        "procurement_kit": {
            "name": "Procurement Kit",
            "description": "Everything procurement needs",
            "includes": ["Security questionnaire", "Vendor information", "Contract templates"],
            "speeds_approval": "By 50% on average",
        },
    }

    # Severity indicators
    SEVERITY_INDICATORS = {
        "blocker": ["not this year", "on hold indefinitely", "definitely not now"],
        "major": ["not ready", "maybe next quarter", "not the right time", "revisit in"],
        "minor": ["timing concern", "soon", "exploring timeline", "when should we"],
    }

    def __init__(self):
        config = AgentConfig(
            name="timing_objection_handler",
            type=AgentType.SPECIALIST,
            temperature=0.4,  # Slightly higher for more creative urgency arguments
            max_tokens=1000,
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
        Process timing objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with timing response
        """
        self.logger.info("timing_objection_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "timing_objection_details",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Identify timing objection type
        objection_type = self._identify_objection_type(message)

        # Assess objection severity
        objection_severity = self._assess_severity(message)

        # Extract timeline mentioned (if any)
        mentioned_timeline = self._extract_timeline(message)

        # Get appropriate response strategy
        strategy = self.RESPONSE_STRATEGIES.get(
            objection_type, self.RESPONSE_STRATEGIES["not_ready_now"]
        )

        # Get pilot program options
        pilot_options = self._get_pilot_options(objection_type, customer_metadata)

        # Get phased rollout options
        rollout_options = self._get_rollout_options(objection_type)

        # Get urgency factors
        urgency_factors = self._get_urgency_factors(objection_type, objection_severity)

        # Get low-effort options
        low_effort_options = self._get_low_effort_options(customer_metadata)

        # Get budget resources
        budget_resources = self._get_budget_resources(objection_type)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(message, category="sales", limit=4)
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_timing_response(
            message,
            objection_type,
            objection_severity,
            mentioned_timeline,
            strategy,
            pilot_options,
            rollout_options,
            urgency_factors,
            low_effort_options,
            budget_resources,
            kb_results,
            customer_metadata,
            state,
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            objection_type, objection_severity, mentioned_timeline
        )

        # Determine escalation need
        needs_escalation = self._check_escalation_needed(objection_severity, resolution_confidence)

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["objection_type"] = objection_type
        state["objection_severity"] = objection_severity
        state["mentioned_timeline"] = mentioned_timeline
        state["response_strategy"] = strategy
        state["pilot_options"] = pilot_options
        state["rollout_options"] = rollout_options
        state["urgency_factors"] = urgency_factors
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "timing_objection_handler_completed",
            objection_type=objection_type,
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation,
        )

        return state

    def _identify_objection_type(self, message: str) -> str:
        """Identify the type of timing objection"""
        message_lower = message.lower()

        if any(
            phrase in message_lower
            for phrase in ["next quarter", "next year", "budget cycle", "fiscal year"]
        ):
            return "budget_next_quarter"
        elif any(
            phrase in message_lower for phrase in ["too busy", "bandwidth", "resources", "capacity"]
        ):
            return "too_busy_right_now"
        elif any(
            phrase in message_lower for phrase in ["waiting for", "after we", "once we", "until we"]
        ):
            return "waiting_for_x"
        elif any(
            phrase in message_lower
            for phrase in ["exploring", "evaluating", "looking at", "considering"]
        ):
            return "exploring_options"
        else:
            return "not_ready_now"

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the timing objection"""
        message_lower = message.lower()

        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"

    def _extract_timeline(self, message: str) -> str | None:
        """Extract any mentioned timeline from the message"""
        message_lower = message.lower()

        timeline_patterns = {
            "next week": "1 week",
            "next month": "1 month",
            "next quarter": "3 months",
            "q1": "Q1",
            "q2": "Q2",
            "q3": "Q3",
            "q4": "Q4",
            "next year": "12+ months",
            "6 months": "6 months",
            "3 months": "3 months",
        }

        for pattern, timeline in timeline_patterns.items():
            if pattern in message_lower:
                return timeline

        return None

    def _get_pilot_options(
        self, objection_type: str, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Get appropriate pilot program options"""
        company_size = customer_metadata.get("company_size", 0)
        options = []

        # Get pilots ideal for this objection type
        for _pilot_key, pilot_data in self.PILOT_PROGRAMS.items():
            if objection_type in pilot_data.get("ideal_for", []):
                options.append(pilot_data)

        # If no specific match, offer based on company size
        if not options:
            if company_size >= 200:
                options.append(self.PILOT_PROGRAMS["enterprise_pilot"])
            elif company_size >= 50:
                options.append(self.PILOT_PROGRAMS["department_pilot"])
            else:
                options.append(self.PILOT_PROGRAMS["quick_start_pilot"])

        return options[:2]  # Return top 2 options

    def _get_rollout_options(self, objection_type: str) -> list[dict[str, Any]]:
        """Get phased rollout options"""
        # Crawl-walk-run is good for most timing objections
        options = [self.PHASED_ROLLOUT_OPTIONS["crawl_walk_run"]]

        # Add parallel running for "waiting_for_x" objections
        if objection_type == "waiting_for_x":
            options.append(self.PHASED_ROLLOUT_OPTIONS["parallel_running"])

        # Add feature-based for "too_busy" objections
        if objection_type == "too_busy_right_now":
            options.append(self.PHASED_ROLLOUT_OPTIONS["feature_based_rollout"])

        return options

    def _get_urgency_factors(self, objection_type: str, severity: str) -> list[dict[str, Any]]:
        """Get relevant urgency factors"""
        factors = []

        # Always include opportunity cost
        factors.append(self.URGENCY_FACTORS["opportunity_cost"])

        # Add based on objection type
        if objection_type == "budget_next_quarter":
            factors.append(self.URGENCY_FACTORS["price_increases"])
        elif objection_type == "exploring_options":
            factors.append(self.URGENCY_FACTORS["competitive_disadvantage"])
        elif objection_type == "waiting_for_x":
            factors.append(self.URGENCY_FACTORS["change_management"])
            factors.append(self.URGENCY_FACTORS["technical_debt"])

        # Don't push too hard on minor objections
        if severity == "minor":
            factors = factors[:2]

        return factors

    def _get_low_effort_options(self, customer_metadata: dict) -> list[dict[str, Any]]:
        """Get low-effort onboarding options"""
        company_size = customer_metadata.get("company_size", 0)
        options = []

        # Larger companies get white-glove
        if company_size >= 100:
            options.append(self.LOW_EFFORT_OPTIONS["white_glove_onboarding"])
            options.append(self.LOW_EFFORT_OPTIONS["done_for_you_migration"])
        else:
            # Smaller companies get turnkey
            options.append(self.LOW_EFFORT_OPTIONS["turnkey_setup"])

        return options

    def _get_budget_resources(self, objection_type: str) -> list[dict[str, Any]]:
        """Get budget justification resources"""
        if objection_type == "budget_next_quarter":
            return [
                self.BUDGET_RESOURCES["business_case_template"],
                self.BUDGET_RESOURCES["executive_summary"],
                self.BUDGET_RESOURCES["procurement_kit"],
            ]
        return [self.BUDGET_RESOURCES["business_case_template"]]

    def _calculate_resolution_confidence(
        self, objection_type: str, severity: str, mentioned_timeline: str | None
    ) -> float:
        """Calculate confidence in resolving the timing objection"""
        base_confidence = 0.70

        # Adjust for objection type (some are easier to overcome)
        type_adjustments = {
            "too_busy_right_now": 0.15,  # Easy with low-effort options
            "not_ready_now": 0.10,  # Pilot programs help
            "exploring_options": 0.05,
            "waiting_for_x": 0.0,
            "budget_next_quarter": -0.05,  # Harder - real budget constraints
        }
        base_confidence += type_adjustments.get(objection_type, 0.0)

        # Adjust for severity
        severity_adjustments = {"minor": 0.15, "major": 0.0, "blocker": -0.20}
        base_confidence += severity_adjustments.get(severity, 0.0)

        # Adjust based on timeline
        if mentioned_timeline:
            if any(term in mentioned_timeline for term in ["week", "month", "Q1", "Q2"]):
                base_confidence += 0.05  # Short timeline = easier
            elif "year" in mentioned_timeline:
                base_confidence -= 0.10  # Long timeline = harder

        return min(max(base_confidence, 0.0), 1.0)

    def _check_escalation_needed(self, severity: str, confidence: float) -> bool:
        """Determine if escalation is needed"""
        if severity == "blocker" and confidence < 0.60:
            return True
        return confidence < 0.55

    async def _generate_timing_response(
        self,
        message: str,
        objection_type: str,
        severity: str,
        mentioned_timeline: str | None,
        strategy: dict,
        pilot_options: list[dict],
        rollout_options: list[dict],
        urgency_factors: list[dict],
        low_effort_options: list[dict],
        budget_resources: list[dict],
        kb_results: list[dict],
        customer_metadata: dict,
        state: AgentState,
    ) -> str:
        """Generate personalized timing objection response"""

        # Get conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build pilot programs context
        pilot_context = ""
        if pilot_options:
            pilot_context = "\n\nPilot Program Options:\n"
            for pilot in pilot_options:
                pilot_context += f"\n{pilot['name']}:\n"
                pilot_context += f"  - Duration: {pilot['duration']}\n"
                pilot_context += f"  - Users: {pilot['user_limit']}\n"
                pilot_context += f"  - Cost: {pilot['cost']}\n"
                pilot_context += f"  - Support: {pilot['support_level']}\n"
                pilot_context += f"  - Conversion Incentive: {pilot['conversion_incentive']}\n"

        # Build rollout options context
        rollout_context = ""
        if rollout_options:
            rollout_context = "\n\nPhased Rollout Options:\n"
            for rollout in rollout_options:
                rollout_context += f"\n{rollout['name']}:\n"
                if "phase1" in rollout:
                    rollout_context += f"  Phase 1: {rollout['phase1']['scope']} ({rollout['phase1']['duration']})\n"
                    rollout_context += f"  - Goal: {rollout['phase1']['goal']}\n"
                    rollout_context += f"  - Effort: {rollout['phase1']['effort']}\n"
                else:
                    rollout_context += f"  - {rollout.get('description', '')}\n"
                    if "benefits" in rollout:
                        rollout_context += f"  - Benefits: {', '.join(rollout['benefits'])}\n"

        # Build urgency context
        urgency_context = ""
        if urgency_factors and severity in ["major", "blocker"]:
            urgency_context = "\n\nConsiderations for Timing:\n"
            for factor in urgency_factors:
                urgency_context += f"\n{factor['factor']} ({factor['impact'].upper()} impact):\n"
                urgency_context += f"  - {factor['description']}\n"
                urgency_context += f"  - Impact: {factor['quantification']}\n"

        # Build low-effort options context
        effort_context = ""
        if low_effort_options:
            effort_context = "\n\nLow-Effort Onboarding Options:\n"
            for option in low_effort_options:
                effort_context += f"\n{option['service']}:\n"
                effort_context += f"  - Your Time Required: {option['customer_time']}\n"
                effort_context += f"  - We Handle: {', '.join(option['our_team_does'])}\n"
                effort_context += f"  - Timeline: {option['timeline']}\n"

        # Build budget resources context
        budget_context = ""
        if budget_resources:
            budget_context = "\n\nBudget Justification Resources:\n"
            for resource in budget_resources:
                budget_context += f"  - {resource['name']}: {resource['description']}\n"

        timeline_str = f" (Timeline mentioned: {mentioned_timeline})" if mentioned_timeline else ""

        system_prompt = f"""You are a Timing Objection Handler specialist addressing readiness and timing concerns.

Objection Analysis:
- Objection Type: {objection_type.replace("_", " ").title()}
- Severity: {severity.upper()}{timeline_str}
- Response Strategy: {strategy["approach"].replace("_", " ").title()}

Customer Profile:
- Company: {customer_metadata.get("company", "Unknown")}
- Industry: {customer_metadata.get("industry", "Unknown")}
- Company Size: {customer_metadata.get("company_size", "Unknown")}

Your response should:
1. Acknowledge their timing concerns empathetically
2. Offer flexible pilot programs to start small and low-risk
3. Suggest phased rollout approaches that match their pace
4. Present low-effort onboarding options to minimize disruption
5. Gently highlight opportunity costs and urgency factors (without being pushy)
6. Provide budget justification resources if needed
7. Make it easy to say "yes" to starting small now

Key Tactics: {", ".join(strategy["tactics"])}
Supporting Materials: {", ".join(strategy["supporting_materials"])}

Important: Be understanding and flexible. Focus on removing barriers, not pressuring."""

        user_prompt = f"""Customer message: {message}

{pilot_context}
{rollout_context}
{effort_context}
{urgency_context}
{budget_context}
{kb_context}

Generate a helpful, flexible response that addresses their timing concerns."""

        response = await self.call_llm(
            system_prompt, user_prompt, conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing TimingObjectionHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Too busy right now
        state1 = create_initial_state(
            "We're interested but our team is completely swamped right now. No bandwidth for onboarding.",
            context={
                "customer_metadata": {
                    "company": "BusyCo Inc",
                    "title": "Operations Manager",
                    "company_size": 150,
                    "industry": "technology",
                }
            },
        )

        agent = TimingObjectionHandler()
        result1 = await agent.process(state1)

        print("\nTest 1 - Too Busy Right Now")
        print(f"Objection Type: {result1['objection_type']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Pilot Options: {len(result1['pilot_options'])}")
        print(f"Low-Effort Options: {len(result1.get('low_effort_options', []))}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Budget next quarter
        state2 = create_initial_state(
            "This looks great but budget is locked for this quarter. Can we revisit in Q2?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "title": "CFO",
                    "company_size": 500,
                    "industry": "finance",
                }
            },
        )

        result2 = await agent.process(state2)

        print("\nTest 2 - Budget Next Quarter")
        print(f"Objection Type: {result2['objection_type']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Mentioned Timeline: {result2['mentioned_timeline']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Budget Resources: {len(result2.get('budget_resources', []))}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Waiting for something
        state3 = create_initial_state(
            "We need to finish our CRM migration first, then we can look at this. Maybe in 6 months.",
            context={
                "customer_metadata": {
                    "company": "MidMarket Co",
                    "title": "VP of Sales",
                    "company_size": 200,
                    "industry": "retail",
                }
            },
        )

        result3 = await agent.process(state3)

        print("\nTest 3 - Waiting for CRM Migration")
        print(f"Objection Type: {result3['objection_type']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Mentioned Timeline: {result3['mentioned_timeline']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"Rollout Options: {len(result3['rollout_options'])}")
        print(f"Urgency Factors: {len(result3['urgency_factors'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
