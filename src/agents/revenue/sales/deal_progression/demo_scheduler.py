"""
Demo Scheduler Agent - TASK-1041

Schedules demos automatically, finds available time slots, sends calendar invites,
and prepares demo environment for optimal product presentations.
"""

from datetime import datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("demo_scheduler", tier="revenue", category="sales")
class DemoScheduler(BaseAgent):
    """
    Demo Scheduler Agent - Specialist in scheduling and preparing product demos.

    Handles:
    - Automatic demo scheduling
    - Available time slot identification
    - Calendar invite generation
    - Demo environment preparation
    - Pre-demo briefing materials
    """

    # Demo types and durations
    DEMO_TYPES = {
        "discovery": {
            "duration_minutes": 30,
            "description": "Initial discovery demo to understand needs",
            "preparation_time": 15,
            "follow_up_required": True,
        },
        "standard": {
            "duration_minutes": 45,
            "description": "Standard product demonstration",
            "preparation_time": 30,
            "follow_up_required": True,
        },
        "deep_dive": {
            "duration_minutes": 90,
            "description": "Technical deep dive with engineering team",
            "preparation_time": 60,
            "follow_up_required": True,
        },
        "executive": {
            "duration_minutes": 30,
            "description": "Executive overview and business value",
            "preparation_time": 45,
            "follow_up_required": True,
        },
        "custom": {
            "duration_minutes": 60,
            "description": "Custom demo tailored to specific use case",
            "preparation_time": 120,
            "follow_up_required": True,
        },
    }

    # Available time slots (business hours)
    BUSINESS_HOURS = {
        "start": 9,  # 9 AM
        "end": 17,  # 5 PM
        "timezone": "America/New_York",
    }

    # Demo preparation checklist
    PREPARATION_CHECKLIST = {
        "environment": [
            "Set up demo environment",
            "Prepare sample data",
            "Test all features to be shown",
            "Configure for prospect's use case",
        ],
        "materials": [
            "Create custom demo script",
            "Prepare slide deck",
            "Ready case studies",
            "Have pricing information available",
        ],
        "logistics": [
            "Send calendar invite",
            "Send pre-demo questionnaire",
            "Confirm technical requirements",
            "Send connection details",
        ],
        "research": [
            "Review prospect's website",
            "Research their industry",
            "Identify pain points",
            "Prepare relevant examples",
        ],
    }

    # Demo environment templates by industry
    ENVIRONMENT_TEMPLATES = {
        "technology": "saas_tech_template",
        "healthcare": "hipaa_compliant_template",
        "finance": "fintech_secure_template",
        "retail": "ecommerce_template",
        "manufacturing": "supply_chain_template",
        "default": "standard_demo_template",
    }

    # Scheduling preferences by seniority
    SCHEDULING_PREFERENCES = {
        "executive": {
            "preferred_times": ["early_morning", "late_afternoon"],
            "buffer_before": 15,
            "buffer_after": 15,
            "flexibility": "low",
        },
        "manager": {
            "preferred_times": ["mid_morning", "mid_afternoon"],
            "buffer_before": 10,
            "buffer_after": 10,
            "flexibility": "medium",
        },
        "individual": {
            "preferred_times": ["morning", "afternoon"],
            "buffer_before": 5,
            "buffer_after": 5,
            "flexibility": "high",
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="demo_scheduler",
            type=AgentType.SPECIALIST,
            # Simple scheduling logic
            temperature=0.3,
            max_tokens=1000,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN,
            ],
            kb_category="sales",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process demo scheduling request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with scheduling details
        """
        self.logger.info("demo_scheduler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        deal_stage = state.get("deal_stage", "discovery")

        self.logger.debug(
            "demo_scheduling_details", message_preview=message[:100], deal_stage=deal_stage
        )

        # Determine demo type based on deal stage and message
        demo_type = self._determine_demo_type(message, deal_stage, customer_metadata)

        # Find available time slots
        available_slots = self._find_available_slots(customer_metadata, demo_type)

        # Generate demo preparation plan
        preparation_plan = self._generate_preparation_plan(demo_type, customer_metadata)

        # Select appropriate environment template
        environment_template = self._select_environment_template(customer_metadata)

        # Generate calendar invite details
        calendar_details = self._generate_calendar_details(
            demo_type, customer_metadata, available_slots[0] if available_slots else None
        )

        # Create pre-demo briefing
        pre_demo_briefing = self._create_pre_demo_briefing(demo_type, customer_metadata)

        # Search KB for demo best practices
        kb_results = await self.search_knowledge_base(
            f"demo best practices {customer_metadata.get('industry', '')}",
            category="sales",
            limit=3,
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_scheduling_response(
            message,
            demo_type,
            available_slots,
            preparation_plan,
            calendar_details,
            kb_results,
            customer_metadata,
            state,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["demo_type"] = demo_type
        state["demo_details"] = self.DEMO_TYPES[demo_type]
        state["available_slots"] = available_slots
        state["preparation_plan"] = preparation_plan
        state["environment_template"] = environment_template
        state["calendar_details"] = calendar_details
        state["pre_demo_briefing"] = pre_demo_briefing
        state["deal_stage"] = "demo_scheduled"
        state["status"] = "resolved"

        self.logger.info(
            "demo_scheduler_completed",
            demo_type=demo_type,
            slots_available=len(available_slots),
            preparation_time=self.DEMO_TYPES[demo_type]["preparation_time"],
        )

        return state

    def _determine_demo_type(self, message: str, deal_stage: str, customer_metadata: dict) -> str:
        """Determine the appropriate demo type"""
        message_lower = message.lower()

        # Check for explicit demo type mentions
        if "executive" in message_lower or customer_metadata.get("title", "").lower() in [
            "ceo",
            "cto",
            "cfo",
        ]:
            return "executive"
        elif "technical" in message_lower or "deep dive" in message_lower:
            return "deep_dive"
        elif "discovery" in message_lower or deal_stage == "discovery":
            return "discovery"
        elif "custom" in message_lower or "specific" in message_lower:
            return "custom"
        else:
            return "standard"

    def _find_available_slots(
        self, customer_metadata: dict, demo_type: str
    ) -> list[dict[str, Any]]:
        """Find available time slots for the demo"""
        slots = []
        now = datetime.now()

        # Get scheduling preferences based on seniority
        title = customer_metadata.get("title", "").lower()
        if any(exec_title in title for exec_title in ["ceo", "cto", "cfo", "vp", "president"]):
            preferences = self.SCHEDULING_PREFERENCES["executive"]
        elif any(mgr_title in title for mgr_title in ["director", "manager", "head"]):
            preferences = self.SCHEDULING_PREFERENCES["manager"]
        else:
            preferences = self.SCHEDULING_PREFERENCES["individual"]

        # Generate slots for next 14 days
        for day_offset in range(1, 15):
            check_date = now + timedelta(days=day_offset)

            # Skip weekends
            if check_date.weekday() >= 5:
                continue

            # Generate time slots based on preferences
            if "early_morning" in preferences["preferred_times"]:
                slots.append(
                    {
                        "datetime": check_date.replace(hour=9, minute=0, second=0),
                        "preference": "high",
                    }
                )
            if (
                "mid_morning" in preferences["preferred_times"]
                or "morning" in preferences["preferred_times"]
            ):
                slots.append(
                    {
                        "datetime": check_date.replace(hour=10, minute=30, second=0),
                        "preference": "high",
                    }
                )
            if (
                "mid_afternoon" in preferences["preferred_times"]
                or "afternoon" in preferences["preferred_times"]
            ):
                slots.append(
                    {
                        "datetime": check_date.replace(hour=14, minute=0, second=0),
                        "preference": "medium",
                    }
                )
            if "late_afternoon" in preferences["preferred_times"]:
                slots.append(
                    {
                        "datetime": check_date.replace(hour=16, minute=0, second=0),
                        "preference": "high",
                    }
                )

        # Return top 5 slots
        return sorted(
            slots, key=lambda x: (x["preference"] == "high", x["datetime"]), reverse=True
        )[:5]

    def _generate_preparation_plan(self, demo_type: str, customer_metadata: dict) -> dict[str, Any]:
        """Generate comprehensive demo preparation plan"""
        demo_info = self.DEMO_TYPES[demo_type]

        return {
            "preparation_time_minutes": demo_info["preparation_time"],
            "checklist": self.PREPARATION_CHECKLIST,
            "priority_items": [
                f"Set up {demo_type} demo environment ({demo_info['preparation_time']} min prep time)",
                f"Customize for {customer_metadata.get('industry', 'their')} industry",
                f"Prepare {demo_info['duration_minutes']}-minute presentation",
                "Test all demo scenarios",
                "Review prospect research",
            ],
            "demo_duration": demo_info["duration_minutes"],
            "follow_up_required": demo_info["follow_up_required"],
        }

    def _select_environment_template(self, customer_metadata: dict) -> str:
        """Select appropriate demo environment template"""
        industry = customer_metadata.get("industry", "").lower()
        return self.ENVIRONMENT_TEMPLATES.get(industry, self.ENVIRONMENT_TEMPLATES["default"])

    def _generate_calendar_details(
        self, demo_type: str, customer_metadata: dict, preferred_slot: dict | None
    ) -> dict[str, Any]:
        """Generate calendar invite details"""
        demo_info = self.DEMO_TYPES[demo_type]

        details = {
            "subject": f"{demo_type.title()} Product Demo - {customer_metadata.get('company', 'Prospect')}",
            "duration_minutes": demo_info["duration_minutes"],
            "description": demo_info["description"],
            "attendees": [
                customer_metadata.get("email", "prospect@company.com"),
                "sales@company.com",
            ],
            "location": "Video Conference (link to be sent)",
            "agenda": self._create_demo_agenda(demo_type),
            "pre_demo_prep": "We'll send a brief questionnaire to customize the demo to your needs",
        }

        if preferred_slot:
            details["proposed_datetime"] = preferred_slot["datetime"].isoformat()
            details["timezone"] = self.BUSINESS_HOURS["timezone"]

        return details

    def _create_demo_agenda(self, demo_type: str) -> list[str]:
        """Create demo agenda based on type"""
        agendas = {
            "discovery": [
                "Introductions (5 min)",
                "Understanding your needs (10 min)",
                "Product overview (10 min)",
                "Q&A and next steps (5 min)",
            ],
            "standard": [
                "Introductions (5 min)",
                "Key features walkthrough (25 min)",
                "Use case demonstrations (10 min)",
                "Q&A and next steps (5 min)",
            ],
            "deep_dive": [
                "Technical overview (20 min)",
                "Architecture and integrations (20 min)",
                "Advanced features (30 min)",
                "Security and compliance (10 min)",
                "Q&A (10 min)",
            ],
            "executive": [
                "Business value overview (10 min)",
                "ROI and key benefits (10 min)",
                "Customer success stories (5 min)",
                "Next steps (5 min)",
            ],
            "custom": [
                "Custom agenda based on requirements",
                "Tailored demonstrations",
                "Specific use cases",
                "Q&A and planning",
            ],
        }
        return agendas.get(demo_type, agendas["standard"])

    def _create_pre_demo_briefing(self, demo_type: str, customer_metadata: dict) -> dict[str, Any]:
        """Create pre-demo briefing for sales team"""
        return {
            "prospect_profile": {
                "company": customer_metadata.get("company", "Unknown"),
                "industry": customer_metadata.get("industry", "Unknown"),
                "size": customer_metadata.get("company_size", "Unknown"),
                "contact": customer_metadata.get("title", "Unknown"),
            },
            "demo_focus": self._determine_demo_focus(customer_metadata),
            "talking_points": self._generate_talking_points(demo_type, customer_metadata),
            "potential_objections": self._identify_potential_objections(customer_metadata),
            "success_criteria": [
                "Clearly demonstrate value proposition",
                "Address specific pain points",
                "Get commitment for next steps",
                "Identify decision-making process",
            ],
        }

    def _determine_demo_focus(self, customer_metadata: dict) -> list[str]:
        """Determine what to focus on during demo"""
        industry = customer_metadata.get("industry", "").lower()

        focus_areas = {
            "technology": ["Integration capabilities", "Developer-friendly APIs", "Scalability"],
            "healthcare": ["HIPAA compliance", "Data security", "Patient privacy"],
            "finance": ["Security features", "Compliance tools", "Audit trails"],
            "retail": ["Customer experience", "Analytics", "Omnichannel capabilities"],
            "default": ["Core features", "Ease of use", "ROI potential"],
        }

        return focus_areas.get(industry, focus_areas["default"])

    def _generate_talking_points(self, demo_type: str, customer_metadata: dict) -> list[str]:
        """Generate key talking points for the demo"""
        return [
            f"How our solution addresses {customer_metadata.get('industry', 'industry')} challenges",
            "Unique value propositions vs competitors",
            "Implementation timeline and ease",
            "Customer success stories from similar companies",
            "Pricing and ROI discussion",
        ]

    def _identify_potential_objections(self, customer_metadata: dict) -> list[str]:
        """Identify potential objections to prepare for"""
        return [
            "Integration complexity",
            "Implementation timeline",
            "Pricing concerns",
            "Change management",
            "Technical requirements",
        ]

    async def _generate_scheduling_response(
        self,
        message: str,
        demo_type: str,
        available_slots: list[dict],
        preparation_plan: dict,
        calendar_details: dict,
        kb_results: list[dict],
        customer_metadata: dict,
        state: AgentState,
    ) -> str:
        """Generate demo scheduling response"""
        # Extract conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        # Build slots context
        slots_context = "\n\nAvailable Time Slots:\n"
        for i, slot in enumerate(available_slots[:3], 1):
            dt = slot["datetime"]
            slots_context += (
                f"{i}. {dt.strftime('%A, %B %d at %I:%M %p')} (Preference: {slot['preference']})\n"
            )

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nDemo Best Practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Demo Scheduler specialist helping schedule product demonstrations.

Demo Details:
- Type: {demo_type.title()}
- Duration: {self.DEMO_TYPES[demo_type]["duration_minutes"]} minutes
- Preparation Required: {preparation_plan["preparation_time_minutes"]} minutes
- Agenda: {len(calendar_details["agenda"])} items

Customer Profile:
- Company: {customer_metadata.get("company", "Unknown")}
- Industry: {customer_metadata.get("industry", "Unknown")}
- Title: {customer_metadata.get("title", "Unknown")}

Your response should:
1. Confirm the demo type and explain what it will cover
2. Present available time slots clearly
3. Explain what preparation will be done
4. Set expectations for the demo
5. Mention any pre-demo materials or questionnaires
6. Be enthusiastic and professional
7. Make scheduling easy with clear next steps"""

        user_prompt = f"""Customer message: {message}

{slots_context}

Demo Agenda:
{chr(10).join(f"- {item}" for item in calendar_details["agenda"])}

{kb_context}

Generate an engaging demo scheduling response."""

        response = await self.call_llm(
            system_prompt, user_prompt, conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing DemoScheduler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Standard demo request
        state1 = create_initial_state(
            "I'd like to schedule a demo to see how your product works",
            context={
                "customer_metadata": {
                    "company": "TechStartup Inc",
                    "title": "Product Manager",
                    "company_size": 50,
                    "industry": "technology",
                    "email": "pm@techstartup.com",
                },
                "deal_stage": "discovery",
            },
        )

        agent = DemoScheduler()
        result1 = await agent.process(state1)

        print("\nTest 1 - Standard Demo Request")
        print(f"Demo Type: {result1['demo_type']}")
        print(f"Duration: {result1['demo_details']['duration_minutes']} minutes")
        print(f"Available Slots: {len(result1['available_slots'])}")
        print(
            f"Preparation Time: {result1['preparation_plan']['preparation_time_minutes']} minutes"
        )
        print(f"Environment Template: {result1['environment_template']}")
        print(f"Deal Stage: {result1['deal_stage']}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Executive demo request
        state2 = create_initial_state(
            "Our CEO wants to see a quick executive overview of the platform",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "title": "Chief Technology Officer",
                    "company_size": 500,
                    "industry": "finance",
                    "email": "cto@enterprise.com",
                },
                "deal_stage": "qualification",
            },
        )

        result2 = await agent.process(state2)

        print("\nTest 2 - Executive Demo Request")
        print(f"Demo Type: {result2['demo_type']}")
        print(f"Duration: {result2['demo_details']['duration_minutes']} minutes")
        print(f"Calendar Subject: {result2['calendar_details']['subject']}")
        print(f"Agenda Items: {len(result2['calendar_details']['agenda'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Technical deep dive
        state3 = create_initial_state(
            "We need a technical deep dive to understand the architecture and integration capabilities",
            context={
                "customer_metadata": {
                    "company": "Healthcare Systems",
                    "title": "Director of Engineering",
                    "company_size": 300,
                    "industry": "healthcare",
                    "email": "eng@healthcare.com",
                },
                "deal_stage": "evaluation",
            },
        )

        result3 = await agent.process(state3)

        print("\nTest 3 - Technical Deep Dive")
        print(f"Demo Type: {result3['demo_type']}")
        print(f"Duration: {result3['demo_details']['duration_minutes']} minutes")
        print(
            f"Preparation Time: {result3['preparation_plan']['preparation_time_minutes']} minutes"
        )
        print(f"Demo Focus Areas: {', '.join(result3['pre_demo_briefing']['demo_focus'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
