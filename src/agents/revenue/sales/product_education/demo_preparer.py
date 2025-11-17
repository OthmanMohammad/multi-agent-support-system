"""
Demo Preparer Agent - TASK-1023

Creates personalized demo environments and generates custom demo scripts.
Prepares talking points for sales reps and handles demo logistics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("demo_preparer", tier="revenue", category="sales")
class DemoPreparer(BaseAgent):
    """
    Demo Preparer Agent - Specialist in demo preparation and logistics.

    Handles:
    - Creating personalized demo environments
    - Generating custom demo scripts
    - Preparing talking points for sales reps
    - Scheduling and logistics coordination
    - Demo follow-up planning
    """

    # Demo types
    DEMO_TYPES = {
        "quick_overview": {
            "duration": 15,
            "depth": "surface",
            "features_count": 3,
            "best_for": ["initial_interest", "executive"]
        },
        "standard_demo": {
            "duration": 30,
            "depth": "balanced",
            "features_count": 5,
            "best_for": ["qualified_lead", "manager"]
        },
        "deep_dive": {
            "duration": 60,
            "depth": "detailed",
            "features_count": 8,
            "best_for": ["technical_evaluation", "technical"]
        },
        "proof_of_concept": {
            "duration": 90,
            "depth": "comprehensive",
            "features_count": 10,
            "best_for": ["final_stage", "enterprise"]
        }
    }

    # Demo environment templates
    ENVIRONMENT_TEMPLATES = {
        "technology": "tech_startup_saas_template",
        "healthcare": "healthcare_clinic_template",
        "finance": "financial_services_template",
        "retail": "ecommerce_retail_template",
        "manufacturing": "manufacturing_ops_template"
    }

    # Key talking points by feature
    FEATURE_TALKING_POINTS = {
        "automation": [
            "Show how 5-minute task becomes 30-second automation",
            "Highlight no-code workflow builder",
            "Demo error handling and notifications"
        ],
        "integration": [
            "Live connect to their existing tools",
            "Show bi-directional data sync",
            "Demonstrate real-time updates"
        ],
        "analytics": [
            "Start with executive dashboard view",
            "Drill down into specific metrics",
            "Show custom report builder"
        ],
        "collaboration": [
            "Demo team workspace setup",
            "Show real-time collaboration features",
            "Highlight permission controls"
        ]
    }

    # Demo scheduling preferences
    BEST_DEMO_TIMES = {
        "monday": ["10:00", "14:00"],
        "tuesday": ["10:00", "11:00", "14:00", "15:00"],
        "wednesday": ["10:00", "11:00", "14:00", "15:00"],
        "thursday": ["10:00", "11:00", "14:00", "15:00"],
        "friday": ["10:00", "11:00"]
    }

    def __init__(self):
        config = AgentConfig(
            name="demo_preparer",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.3,
            max_tokens=1200,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process demo preparation request"""
        self.logger.info("demo_preparer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Determine appropriate demo type
        demo_type = self._determine_demo_type(customer_metadata, message)

        # Select demo environment template
        environment = self._select_environment(customer_metadata)

        # Generate demo script
        demo_script = self._generate_demo_script(
            demo_type,
            customer_metadata,
            environment
        )

        # Prepare talking points
        talking_points = self._prepare_talking_points(
            demo_script["features_to_demo"],
            customer_metadata
        )

        # Generate scheduling options
        scheduling_options = self._generate_scheduling_options()

        # Create follow-up plan
        follow_up_plan = self._create_follow_up_plan(demo_type)

        # Search KB for demo best practices
        kb_results = await self.search_knowledge_base(
            f"demo best practices {customer_metadata.get('industry', '')}",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_demo_prep_response(
            message,
            demo_type,
            demo_script,
            talking_points,
            scheduling_options,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.87
        state["demo_type"] = demo_type
        state["demo_environment"] = environment
        state["demo_script"] = demo_script
        state["talking_points"] = talking_points
        state["scheduling_options"] = scheduling_options
        state["follow_up_plan"] = follow_up_plan
        state["status"] = "resolved"

        self.logger.info(
            "demo_preparer_completed",
            demo_type=demo_type,
            duration=self.DEMO_TYPES[demo_type]["duration"]
        )

        return state

    def _determine_demo_type(
        self,
        customer_metadata: Dict,
        message: str
    ) -> str:
        """Determine the most appropriate demo type"""
        message_lower = message.lower()
        title = customer_metadata.get("title", "").lower()
        company_size = customer_metadata.get("company_size", 0)

        # Quick overview for executives or initial contact
        if any(exec_title in title for exec_title in ["ceo", "cfo", "president"]):
            return "quick_overview"

        # Deep dive for technical evaluation
        if any(tech_word in message_lower for tech_word in ["technical", "integration", "api", "evaluate"]):
            return "deep_dive"

        # POC for enterprise/late stage
        if company_size > 1000 or "proof of concept" in message_lower or "poc" in message_lower:
            return "proof_of_concept"

        # Default to standard demo
        return "standard_demo"

    def _select_environment(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Select appropriate demo environment template"""
        industry = customer_metadata.get("industry", "technology").lower()
        template_name = self.ENVIRONMENT_TEMPLATES.get(industry, "tech_startup_saas_template")

        return {
            "template_name": template_name,
            "industry": industry,
            "sample_data": f"sample_data_{industry}.json",
            "branding": {
                "company_name": customer_metadata.get("company", "Demo Company"),
                "industry": industry
            }
        }

    def _generate_demo_script(
        self,
        demo_type: str,
        customer_metadata: Dict,
        environment: Dict
    ) -> Dict[str, Any]:
        """Generate structured demo script"""
        demo_config = self.DEMO_TYPES[demo_type]

        # Select features to demo based on industry and type
        industry = customer_metadata.get("industry", "technology").lower()
        features_to_demo = self._select_features_for_demo(
            industry,
            demo_config["features_count"]
        )

        # Create timeline
        duration = demo_config["duration"]
        timeline = self._create_demo_timeline(duration, features_to_demo)

        return {
            "demo_type": demo_type,
            "duration_minutes": duration,
            "features_to_demo": features_to_demo,
            "timeline": timeline,
            "environment": environment["template_name"],
            "opening": f"Welcome to {customer_metadata.get('company', 'your')} personalized demo",
            "closing": "Next steps and Q&A"
        }

    def _select_features_for_demo(self, industry: str, count: int) -> List[str]:
        """Select most relevant features for demo"""
        # Industry-specific feature priority
        industry_features = {
            "technology": ["api_integration", "automation", "webhooks", "analytics", "collaboration"],
            "healthcare": ["hipaa_compliance", "security", "audit_logs", "patient_management", "reporting"],
            "finance": ["sox_compliance", "security", "audit_trails", "analytics", "data_governance"],
            "retail": ["inventory", "analytics", "customer_insights", "integration", "reporting"],
            "manufacturing": ["iot_integration", "quality_control", "supply_chain", "analytics", "automation"]
        }

        features = industry_features.get(industry, ["automation", "integration", "analytics", "reporting", "collaboration"])
        return features[:count]

    def _create_demo_timeline(self, duration: int, features: List[str]) -> List[Dict[str, Any]]:
        """Create minute-by-minute demo timeline"""
        timeline = []

        # Opening (5-10% of time)
        opening_time = max(2, int(duration * 0.1))
        timeline.append({
            "segment": "Opening & Introductions",
            "duration_minutes": opening_time,
            "activities": ["Welcome", "Agenda overview", "Understand their goals"]
        })

        # Feature demos (70-80% of time)
        demo_time = int(duration * 0.75)
        time_per_feature = demo_time // len(features)

        for feature in features:
            timeline.append({
                "segment": f"Demo: {feature.replace('_', ' ').title()}",
                "duration_minutes": time_per_feature,
                "activities": self.FEATURE_TALKING_POINTS.get(feature, ["Show feature", "Explain benefits", "Answer questions"])[:3]
            })

        # Q&A and Closing (15-20% of time)
        closing_time = duration - opening_time - (time_per_feature * len(features))
        timeline.append({
            "segment": "Q&A and Next Steps",
            "duration_minutes": max(3, closing_time),
            "activities": ["Answer questions", "Discuss next steps", "Schedule follow-up"]
        })

        return timeline

    def _prepare_talking_points(
        self,
        features: List[str],
        customer_metadata: Dict
    ) -> Dict[str, List[str]]:
        """Prepare talking points for sales rep"""
        talking_points = {}

        # General talking points
        talking_points["opening"] = [
            f"Acknowledge their industry: {customer_metadata.get('industry', 'your industry')}",
            "Reference their specific challenges",
            "Set expectations for demo format"
        ]

        # Feature-specific talking points
        for feature in features:
            talking_points[feature] = self.FEATURE_TALKING_POINTS.get(
                feature,
                ["Explain the feature", "Show practical application", "Highlight benefits"]
            )

        # Closing talking points
        talking_points["closing"] = [
            "Summarize how solution addresses their needs",
            "Discuss implementation timeline",
            "Propose clear next steps",
            "Schedule follow-up meeting"
        ]

        return talking_points

    def _generate_scheduling_options(self) -> List[Dict[str, str]]:
        """Generate optimal scheduling time slots"""
        options = []
        today = datetime.now()

        # Generate next 5 business days
        days_added = 0
        current_date = today

        while days_added < 5:
            current_date += timedelta(days=1)
            weekday = current_date.strftime("%A").lower()

            # Skip weekends
            if weekday in ["saturday", "sunday"]:
                continue

            # Get best times for this day
            times = self.BEST_DEMO_TIMES.get(weekday, ["10:00", "14:00"])

            for time in times:
                options.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": time,
                    "datetime": f"{current_date.strftime('%Y-%m-%d')} {time}"
                })

            days_added += 1

        return options[:10]  # Return top 10 slots

    def _create_follow_up_plan(self, demo_type: str) -> Dict[str, Any]:
        """Create follow-up plan after demo"""
        if demo_type == "quick_overview":
            return {
                "immediate": "Send thank you email with recording",
                "24_hours": "Share detailed feature documentation",
                "48_hours": "Schedule standard demo if interested",
                "1_week": "Check-in call"
            }
        elif demo_type == "standard_demo":
            return {
                "immediate": "Send demo recording and relevant case studies",
                "24_hours": "Provide trial access if applicable",
                "3_days": "Schedule technical deep-dive if needed",
                "1_week": "Proposal or next steps discussion"
            }
        elif demo_type == "deep_dive":
            return {
                "immediate": "Send technical documentation and API docs",
                "24_hours": "Provide sandbox environment",
                "3_days": "Technical Q&A session",
                "1_week": "POC or pilot discussion"
            }
        else:  # proof_of_concept
            return {
                "immediate": "Send POC proposal",
                "48_hours": "Share success criteria document",
                "1_week": "POC kickoff meeting",
                "ongoing": "Weekly POC check-ins"
            }

    async def _generate_demo_prep_response(
        self,
        message: str,
        demo_type: str,
        demo_script: Dict,
        talking_points: Dict,
        scheduling_options: List[Dict],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate demo preparation response"""

        # Build demo script summary
        script_context = f"\n\nDemo Script ({demo_script['duration_minutes']} minutes):\n"
        for segment in demo_script["timeline"]:
            script_context += f"- {segment['segment']} ({segment['duration_minutes']} min)\n"

        # Build scheduling context
        schedule_context = "\n\nAvailable Demo Slots (next few days):\n"
        for option in scheduling_options[:5]:
            schedule_context += f"- {option['datetime']}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nDemo best practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Demo Preparer specialist helping schedule and prepare product demonstrations.

Prospect Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown').title()}
- Title: {customer_metadata.get('title', 'Unknown')}

Demo Configuration:
- Type: {demo_type.replace('_', ' ').title()}
- Duration: {demo_script['duration_minutes']} minutes
- Features to showcase: {', '.join(demo_script['features_to_demo'])}

Your response should:
1. Confirm demo format and duration
2. Highlight key features that will be covered
3. Provide scheduling options
4. Set clear expectations
5. Ask about any specific areas they want to focus on
6. Be professional and organized"""

        user_prompt = f"""Customer message: {message}

{script_context}
{schedule_context}
{kb_context}

Generate a professional demo preparation response."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    """Test harness for DemoPreparer"""
    import asyncio
    from src.workflow.state import AgentState

    async def test_demo_preparer():
        agent = DemoPreparer()

        # Test case 1: Executive quick demo
        state1 = AgentState(
            current_message="I'd like to see a quick overview of your platform",
            customer_metadata={
                "title": "CEO",
                "company": "TechStartup Inc",
                "industry": "technology",
                "company_size": 150
            },
            messages=[],
            status="pending"
        )

        result1 = await agent.process(state1)
        print("Test 1 - Executive Quick Demo:")
        print(f"Demo Type: {result1['demo_type']}")
        print(f"Duration: {result1['demo_script']['duration_minutes']} minutes")
        print(f"Features: {result1['demo_script']['features_to_demo']}")
        print()

        # Test case 2: Technical deep dive
        state2 = AgentState(
            current_message="We need a technical demo to evaluate your API integration capabilities",
            customer_metadata={
                "title": "Engineering Manager",
                "company": "FinanceCorp",
                "industry": "finance",
                "company_size": 800
            },
            messages=[],
            status="pending"
        )

        result2 = await agent.process(state2)
        print("Test 2 - Technical Deep Dive:")
        print(f"Demo Type: {result2['demo_type']}")
        print(f"Timeline segments: {len(result2['demo_script']['timeline'])}")
        print(f"Scheduling options: {len(result2['scheduling_options'])}")
        print()

    asyncio.run(test_demo_preparer())
