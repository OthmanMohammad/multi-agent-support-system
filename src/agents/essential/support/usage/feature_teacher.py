"""
Feature Teacher Agent - Teaches specific features in-depth.

Specialist for feature learning with step-by-step guides, examples, and tutorials.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("feature_teacher", tier="essential", category="usage")
class FeatureTeacher(BaseAgent):
    """
    Feature Teacher Agent - Specialist for in-depth feature education.

    Handles:
    - Step-by-step feature tutorials
    - Personalized lessons by skill level
    - Video tutorial links
    - Practice exercises
    - KB article references
    """

    FEATURES = {
        "reports": {
            "description": "Create custom reports and dashboards",
            "steps": [
                "Navigate to Reports section",
                "Click 'New Report' button",
                "Select your data source",
                "Choose visualization type",
                "Configure report parameters",
                "Preview your report",
                "Save and share",
            ],
            "video_url": "/tutorials/reports",
            "kb_articles": ["kb_reports_101", "kb_custom_dashboards", "kb_advanced_analytics"],
            "difficulty": "intermediate",
            "time_to_learn": "15 minutes",
        },
        "api": {
            "description": "Use API to integrate with other tools",
            "steps": [
                "Generate API key in Settings",
                "Read API documentation",
                "Make your first GET request",
                "Authenticate requests",
                "Handle API responses",
                "Implement error handling",
                "Monitor API usage",
            ],
            "video_url": "/tutorials/api",
            "kb_articles": ["kb_api_quickstart", "kb_api_auth", "kb_api_best_practices"],
            "difficulty": "advanced",
            "time_to_learn": "30 minutes",
        },
        "automation": {
            "description": "Automate repetitive tasks",
            "steps": [
                "Open Automation settings",
                "Click 'Create Automation'",
                "Define trigger condition",
                "Select actions to perform",
                "Configure action parameters",
                "Test automation",
                "Activate and monitor",
            ],
            "video_url": "/tutorials/automation",
            "kb_articles": ["kb_automation_basics", "kb_automation_examples"],
            "difficulty": "intermediate",
            "time_to_learn": "20 minutes",
        },
        "dashboards": {
            "description": "Build interactive dashboards",
            "steps": [
                "Create new dashboard",
                "Add widgets and charts",
                "Connect data sources",
                "Configure refresh intervals",
                "Set up filters",
                "Share with team",
                "Enable real-time updates",
            ],
            "video_url": "/tutorials/dashboards",
            "kb_articles": ["kb_dashboard_guide", "kb_widget_library"],
            "difficulty": "beginner",
            "time_to_learn": "10 minutes",
        },
        "workflows": {
            "description": "Design custom workflows",
            "steps": [
                "Map out your process",
                "Create workflow template",
                "Define stages and transitions",
                "Add automation rules",
                "Assign team members",
                "Test workflow",
                "Deploy and track",
            ],
            "video_url": "/tutorials/workflows",
            "kb_articles": ["kb_workflow_design", "kb_workflow_templates"],
            "difficulty": "intermediate",
            "time_to_learn": "25 minutes",
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="feature_teacher",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN,
            ],
            kb_category="usage",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process feature learning requests"""
        self.logger.info("feature_teacher_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "feature_learning_processing_started",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Extract feature to learn and user skill level
        feature_name = self._extract_feature_name(message)
        user_skill_level = customer_context.get("skill_level", "beginner")

        self.logger.info("feature_detected", feature=feature_name, skill_level=user_skill_level)

        # Generate lesson
        if feature_name and feature_name in self.FEATURES:
            lesson = self._create_lesson(feature_name, user_skill_level)

            # Search KB for additional resources
            kb_results = await self.search_knowledge_base(message, category="usage", limit=2)
            state["kb_results"] = kb_results

            response = lesson["content"]
            state["feature_taught"] = feature_name
            state["tutorial_provided"] = True

            if kb_results:
                self.logger.info("feature_kb_articles_found", count=len(kb_results))
        else:
            # List available features
            response = self._list_available_features()
            state["tutorial_provided"] = False

        state["agent_response"] = response
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "feature_teaching_completed",
            feature=feature_name,
            tutorial_provided=state["tutorial_provided"],
            status="resolved",
        )

        return state

    def _extract_feature_name(self, message: str) -> str | None:
        """Extract feature name from user message"""
        message_lower = message.lower()

        for feature in self.FEATURES:
            if feature in message_lower:
                return feature

        # Check for common aliases
        if any(word in message_lower for word in ["report", "reporting", "analytics"]):
            return "reports"
        elif any(word in message_lower for word in ["api", "integration", "rest"]):
            return "api"
        elif any(word in message_lower for word in ["automate", "automation", "trigger"]):
            return "automation"
        elif any(word in message_lower for word in ["dashboard", "widget", "chart"]):
            return "dashboards"
        elif any(word in message_lower for word in ["workflow", "process", "pipeline"]):
            return "workflows"

        return None

    def _create_lesson(self, feature: str, skill_level: str) -> dict[str, Any]:
        """Create personalized lesson for feature"""
        feature_info = self.FEATURES[feature]

        # Adjust complexity based on skill level
        if skill_level == "beginner":
            content = f"""
# Learning: {feature_info["description"]}

**What you'll learn:** {feature_info["description"]}

**Difficulty:** {feature_info["difficulty"].title()}
**Time needed:** {feature_info["time_to_learn"]}

**Step-by-step guide:**
{self._format_steps(feature_info["steps"], detailed=True)}

**📹 Watch video tutorial:** {feature_info["video_url"]} ({feature_info["time_to_learn"]})

**🎯 Practice exercise:**
Try creating your first {feature} following the steps above. Take your time and don't worry about making mistakes - that's how you learn!

**💡 Tips for beginners:**
- Follow each step in order
- Don't skip the video tutorial
- Practice multiple times
- Ask for help if you get stuck

**📚 Helpful resources:**
{self._format_kb_links(feature_info["kb_articles"])}

**Need help?** Let me know if you need clarification on any step!
"""
        elif skill_level == "intermediate":
            content = f"""
# {feature.title()} - Intermediate Guide

**Overview:** {feature_info["description"]}

**Steps:**
{self._format_steps(feature_info["steps"], detailed=False)}

**⏱️ Time to master:** {feature_info["time_to_learn"]}
**📹 Video:** {feature_info["video_url"]}

**🔥 Pro tips:**
- Use keyboard shortcuts to speed up your workflow (see Shortcuts guide)
- Set up templates to save time on repetitive tasks
- Automate common patterns with rules
- Bookmark your most-used configurations

**📚 Advanced resources:**
{self._format_kb_links(feature_info["kb_articles"])}

**Next level:** Once you master this, explore advanced {feature} features!
"""
        else:  # advanced
            content = f"""
# {feature.title()} - Advanced Deep Dive

**{feature_info["description"]}**

**Quick reference:**
{self._format_steps(feature_info["steps"], detailed=False)}

**🚀 Advanced techniques:**
- API integration for programmatic control
- Custom scripting and extensions
- Performance optimization strategies
- Enterprise-scale best practices

**📹 Tutorial:** {feature_info["video_url"]}
**📚 Documentation:** {self._format_kb_links(feature_info["kb_articles"])}

**Architecture considerations:**
- Scalability patterns
- Security best practices
- Monitoring and observability
- Disaster recovery planning

**Looking for specific advanced topics?** Let me know what you want to deep-dive into!
"""

        return {"content": content, "feature": feature, "skill_level": skill_level}

    def _format_steps(self, steps: list[str], detailed: bool) -> str:
        """Format steps with optional details"""
        if detailed:
            return "\n".join(
                [
                    f"{i + 1}. **{step}**\n   Take your time with this step. Make sure you understand it before moving on."
                    for i, step in enumerate(steps)
                ]
            )
        else:
            return "\n".join([f"{i + 1}. {step}" for i, step in enumerate(steps)])

    def _format_kb_links(self, articles: list[str]) -> str:
        """Format KB article links"""
        return "\n".join(
            [f"- [{a.replace('kb_', '').replace('_', ' ').title()}](/kb/{a})" for a in articles]
        )

    def _list_available_features(self) -> str:
        """List all available features to learn"""
        features = "\n".join(
            [
                f"**{name.title()}** - {info['description']}\n"
                f"   Difficulty: {info['difficulty'].title()} | Time: {info['time_to_learn']}"
                for name, info in self.FEATURES.items()
            ]
        )

        return f"""
I can teach you these features:

{features}

**Which would you like to learn?**

Just tell me which feature interests you, and I'll create a personalized tutorial based on your skill level!
"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Beginner learning reports
        print("=" * 60)
        print("Test 1: Beginner learning reports")
        print("=" * 60)

        state = create_initial_state("I want to learn about reports")
        state["customer_metadata"] = {"skill_level": "beginner"}

        agent = FeatureTeacher()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Feature taught: {result.get('feature_taught')}")
        print(f"Tutorial provided: {result.get('tutorial_provided')}")

        # Test 2: Advanced user learning API
        print("\n" + "=" * 60)
        print("Test 2: Advanced user learning API")
        print("=" * 60)

        state2 = create_initial_state("How do I use the API?")
        state2["customer_metadata"] = {"skill_level": "advanced"}

        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Feature taught: {result2.get('feature_taught')}")

        # Test 3: Unknown feature
        print("\n" + "=" * 60)
        print("Test 3: Unknown feature - list all")
        print("=" * 60)

        state3 = create_initial_state("What can you teach me?")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")

    asyncio.run(test())
