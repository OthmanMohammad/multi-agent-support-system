"""
Workflow Optimizer Agent - Analyzes and optimizes customer workflows.

Specialist for workflow analysis, best practices, and time-saving suggestions.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("workflow_optimizer", tier="essential", category="usage")
class WorkflowOptimizer(BaseAgent):
    """
    Workflow Optimizer Agent - Specialist for workflow efficiency analysis.

    Handles:
    - Workflow inefficiency detection
    - Best practice recommendations
    - Time-saving optimization suggestions
    - Automation opportunities
    - Template and shortcut suggestions
    """

    def __init__(self):
        config = AgentConfig(
            name="workflow_optimizer",
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
        """Process workflow optimization requests"""
        self.logger.info("workflow_optimizer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        current_workflow = state.get("current_workflow_description", "")

        self.logger.debug(
            "workflow_analysis_started",
            message_preview=message[:100],
            turn_count=state["turn_count"],
        )

        # Analyze workflow
        analysis = self._analyze_workflow(customer_context, current_workflow, message)

        self.logger.info(
            "workflow_analyzed",
            inefficiencies_found=len(analysis["inefficiencies"]),
            workflow_score=analysis["workflow_score"],
        )

        # Generate optimization suggestions
        optimizations = self._generate_optimizations(analysis)

        # Search KB for best practices
        kb_results = await self.search_knowledge_base(
            "workflow optimization best practices", category="usage", limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("workflow_kb_articles_found", count=len(kb_results))

        # Add KB context to response
        response = optimizations["message"]
        if kb_results:
            response += "\n\n**📚 Related best practice guides:**\n"
            for i, article in enumerate(kb_results, 1):
                response += f"{i}. {article['title']}\n"

        state["agent_response"] = response
        state["workflow_score"] = analysis["workflow_score"]
        state["time_savings_estimate"] = optimizations["time_saved_hours_per_week"]
        state["optimizations_suggested"] = len(analysis["inefficiencies"])
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "workflow_optimization_completed",
            score=analysis["workflow_score"],
            time_savings=optimizations["time_saved_hours_per_week"],
            status="resolved",
        )

        return state

    def _analyze_workflow(
        self, context: dict[str, Any], workflow: str, message: str
    ) -> dict[str, Any]:
        """Analyze workflow for inefficiencies"""
        feature_usage = context.get("feature_usage", {})
        team_size = context.get("seats_used", 1)
        context.get("plan", "free")
        account_age_days = context.get("account_age_days", 0)

        inefficiencies = []

        # Check if using automation
        if not feature_usage.get("automation_enabled", False):
            if feature_usage.get("project_count", 0) > 5 or account_age_days > 30:
                inefficiencies.append(
                    {
                        "type": "manual_repetition",
                        "description": "Manually repeating tasks that could be automated",
                        "impact": "high",
                        "time_saved_hours": 5,
                    }
                )

        # Check if using templates
        project_count = feature_usage.get("project_count", 0)
        if project_count > 10 and not feature_usage.get("uses_templates", False):
            inefficiencies.append(
                {
                    "type": "no_templates",
                    "description": "Creating projects from scratch instead of using templates",
                    "impact": "medium",
                    "time_saved_hours": 2,
                }
            )

        # Check collaboration usage for teams
        if team_size > 1 and not feature_usage.get("uses_collaboration", False):
            inefficiencies.append(
                {
                    "type": "poor_collaboration",
                    "description": "Not utilizing team collaboration features",
                    "impact": "medium",
                    "time_saved_hours": 3,
                }
            )

        # Check keyboard shortcuts usage
        if not feature_usage.get("uses_shortcuts", False) and account_age_days > 14:
            inefficiencies.append(
                {
                    "type": "no_shortcuts",
                    "description": "Not using keyboard shortcuts for common actions",
                    "impact": "low",
                    "time_saved_hours": 1,
                }
            )

        # Check bulk operations
        if feature_usage.get("manual_bulk_operations", 0) > 0:
            inefficiencies.append(
                {
                    "type": "manual_bulk_ops",
                    "description": "Performing actions one-by-one instead of in bulk",
                    "impact": "medium",
                    "time_saved_hours": 2,
                }
            )

        # Check integration opportunities
        if team_size > 3 and not feature_usage.get("uses_integrations", False):
            inefficiencies.append(
                {
                    "type": "no_integrations",
                    "description": "Not integrating with other tools you use daily",
                    "impact": "medium",
                    "time_saved_hours": 4,
                }
            )

        # Check search vs browse behavior
        if feature_usage.get("browse_heavy", False) and not feature_usage.get("uses_search", False):
            inefficiencies.append(
                {
                    "type": "browse_instead_search",
                    "description": "Browsing through lists instead of using search",
                    "impact": "low",
                    "time_saved_hours": 1,
                }
            )

        # Check notification settings
        if feature_usage.get("notification_overload", False):
            inefficiencies.append(
                {
                    "type": "notification_overload",
                    "description": "Too many notifications causing distractions",
                    "impact": "low",
                    "time_saved_hours": 1,
                }
            )

        return {
            "inefficiencies": inefficiencies,
            "workflow_score": self._calculate_workflow_score(inefficiencies),
        }

    def _calculate_workflow_score(self, inefficiencies: list[dict]) -> int:
        """Calculate workflow efficiency score (0-100)"""
        base_score = 100

        for inefficiency in inefficiencies:
            impact = inefficiency["impact"]
            if impact == "high":
                base_score -= 30
            elif impact == "medium":
                base_score -= 15
            else:  # low
                base_score -= 5

        return max(base_score, 0)

    def _generate_optimizations(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate optimization recommendations"""
        inefficiencies = analysis["inefficiencies"]

        if not inefficiencies:
            return {
                "message": """**🎉 Excellent! Your workflow is optimized!**

Your efficiency score is **{}/100**

You're already using best practices:
✓ Automation enabled
✓ Using templates
✓ Team collaboration active
✓ Keyboard shortcuts mastered

**Keep it up!** Continue monitoring your workflow for new optimization opportunities.""".format(
                    analysis["workflow_score"]
                ),
                "time_saved_hours_per_week": 0,
            }

        message = f"""**📊 Workflow Analysis Complete**

Your efficiency score: **{analysis["workflow_score"]}/100**

I found **{len(inefficiencies)} opportunities** to optimize your workflow:

"""

        time_saved = 0

        for i, inefficiency in enumerate(inefficiencies, 1):
            hours = inefficiency["time_saved_hours"]
            time_saved += hours

            if inefficiency["type"] == "manual_repetition":
                message += f"""
**{i}. ⚡ Enable Automation** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Set up automation rules to handle repetitive tasks
   - **How:** Settings → Automation → Create Rule
   - **Examples:**
     • Auto-assign tasks based on tags or keywords
     • Send notifications when status changes
     • Update due dates automatically
     • Move tasks between projects based on conditions

"""
            elif inefficiency["type"] == "no_templates":
                message += f"""
**{i}. 📋 Create Templates** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Create project templates for common workflows
   - **How:** Project → More → Save as Template
   - **Examples:**
     • Weekly sprint template
     • Client onboarding checklist
     • Bug report template
     • Content creation workflow

"""
            elif inefficiency["type"] == "poor_collaboration":
                message += f"""
**{i}. 👥 Enable Team Features** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Use @mentions, shared views, and comments
   - **How:** Invite team → Use @mentions in tasks
   - **Benefits:**
     • Reduce meetings by 50% with async collaboration
     • Real-time updates for everyone
     • Clear task ownership
     • Centralized communication

"""
            elif inefficiency["type"] == "no_shortcuts":
                message += f"""
**{i}. ⌨️ Learn Keyboard Shortcuts** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Master the most common shortcuts
   - **Essential shortcuts:**
     • `Ctrl/Cmd + K` - Quick search
     • `C` - Create new task
     • `E` - Edit selected item
     • `/ ` - Focus search
     • `?` - Show all shortcuts

"""
            elif inefficiency["type"] == "manual_bulk_ops":
                message += f"""
**{i}. 📦 Use Bulk Operations** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Select multiple items and act on them at once
   - **How:** Shift+Click to select range, Ctrl/Cmd+Click for individuals
   - **Bulk actions:**
     • Assign to team member
     • Change status
     • Add tags
     • Move to different project
     • Delete multiple items

"""
            elif inefficiency["type"] == "no_integrations":
                message += f"""
**{i}. 🔌 Connect Integrations** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Integrate with tools you use daily
   - **How:** Settings → Integrations → Connect
   - **Popular integrations:**
     • Slack (notifications)
     • Google Calendar (sync deadlines)
     • GitHub (link code to tasks)
     • Zapier (connect anything)

"""
            elif inefficiency["type"] == "browse_instead_search":
                message += f"""
**{i}. 🔍 Use Search Instead of Browse** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Use powerful search to find what you need instantly
   - **How:** Press `/` or Ctrl/Cmd+K anytime
   - **Search tips:**
     • Filter by status, assignee, date
     • Use quotes for exact matches
     • Save frequent searches
     • Use advanced filters

"""
            elif inefficiency["type"] == "notification_overload":
                message += f"""
**{i}. 🔕 Optimize Notifications** (Save ~{hours} hours/week)
   - **Current:** {inefficiency["description"]}
   - **Better:** Configure smart notifications for what matters
   - **How:** Settings → Notifications → Customize
   - **Best practices:**
     • Only get notified when @mentioned
     • Digest mode for low-priority updates
     • Quiet hours during focus time
     • Different settings for mobile vs desktop

"""

        message += f"""
---

**💰 Total potential time savings: ~{time_saved} hours/week**

**🎯 Recommended action plan:**
1. Start with the highest-impact optimization (usually #1)
2. Implement one change this week
3. Measure the impact
4. Move to the next optimization

**Need help?** Let me know which optimization you'd like to implement first, and I'll walk you through it step-by-step!
"""

        return {"message": message, "time_saved_hours_per_week": time_saved}


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Analyze workflow with inefficiencies
        print("=" * 60)
        print("Test 1: Workflow with multiple inefficiencies")
        print("=" * 60)

        state = create_initial_state("Can you analyze my workflow and suggest improvements?")
        state["customer_metadata"] = {
            "feature_usage": {
                "automation_enabled": False,
                "project_count": 15,
                "uses_templates": False,
                "uses_collaboration": False,
            },
            "seats_used": 5,
            "plan": "premium",
            "account_age_days": 90,
        }

        agent = WorkflowOptimizer()
        result = await agent.process(state)

        print(f"\nWorkflow Score: {result.get('workflow_score')}/100")
        print(f"Time Savings: {result.get('time_savings_estimate')} hours/week")
        print(f"Optimizations: {result.get('optimizations_suggested')}")
        print(f"\nResponse:\n{result['agent_response'][:500]}...")

        # Test 2: Optimized workflow
        print("\n" + "=" * 60)
        print("Test 2: Already optimized workflow")
        print("=" * 60)

        state2 = create_initial_state("How's my workflow looking?")
        state2["customer_metadata"] = {
            "feature_usage": {
                "automation_enabled": True,
                "project_count": 20,
                "uses_templates": True,
                "uses_collaboration": True,
                "uses_shortcuts": True,
                "uses_integrations": True,
            },
            "seats_used": 10,
            "account_age_days": 180,
        }

        result2 = await agent.process(state2)

        print(f"\nWorkflow Score: {result2.get('workflow_score')}/100")
        print(f"\nResponse:\n{result2['agent_response']}")

    asyncio.run(test())
