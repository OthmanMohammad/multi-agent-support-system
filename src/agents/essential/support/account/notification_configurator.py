"""
Notification Configurator Agent - Handles email, Slack, and in-app notification settings.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("notification_configurator", tier="essential", category="account")
class NotificationConfigurator(BaseAgent):
    """Notification Configurator - Specialist in notification preferences configuration."""

    NOTIFICATION_CHANNELS = ["email", "in_app", "slack", "mobile_push", "desktop"]

    NOTIFICATION_TYPES = {
        "mentions": "When someone @mentions you",
        "assignments": "When assigned to tasks",
        "comments": "New comments on your items",
        "due_dates": "Task due date reminders",
        "status_changes": "Status updates on watched items",
        "team_activity": "Team member activity",
        "weekly_digest": "Weekly summary email",
        "updates": "Product updates and announcements",
    }

    def __init__(self):
        config = AgentConfig(
            name="notification_configurator",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process notification configuration requests."""
        self.logger.info("notification_configurator_processing_started")
        state = self.update_state(state)

        message = state["current_message"]
        action = self._detect_notification_action(message)

        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        response = self._generate_notification_guide(action)

        state["agent_response"] = response
        state["notification_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("notification_processing_completed", action=action)
        return state

    def _detect_notification_action(self, message: str) -> str:
        """Detect notification configuration action."""
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["slack", "integrate", "webhook"]):
            return "setup_slack"
        elif any(word in msg_lower for word in ["mute", "stop", "pause", "silence"]):
            return "mute"
        elif any(word in msg_lower for word in ["digest", "summary", "weekly"]):
            return "digest"
        return "configure"

    def _generate_notification_guide(self, action: str) -> str:
        """Generate notification configuration guide."""
        if action == "setup_slack":
            return """**🔔 Connect Slack Notifications**

**Step 1: Install Slack App**
Settings > Integrations > Slack > Connect

**Step 2: Authorize**
- Click "Add to Slack"
- Select your workspace
- Authorize permissions

**Step 3: Configure Channels**
- Choose notification channels
- Select notification types
- Set quiet hours

**What you'll receive:**
✅ @mentions (immediate)
✅ Task assignments
✅ Due date reminders
✅ Weekly summary

**Slack Commands:**
- `/task-create` - Create task
- `/mute` - Mute notifications
- `/digest` - Get daily digest

**Manage:** Settings > Integrations > Slack"""

        elif action == "mute":
            return """**🔕 Mute Notifications**

**Quick Mute Options:**

**1 Hour:** Focus mode
**2-4 Hours:** Deep work session
**24 Hours:** Rest of day
**Weekend:** Friday 5 PM - Monday 9 AM

**What's Muted:**
- Email notifications
- In-app notifications
- Mobile push
- Slack messages

**What's NOT Muted:**
- Critical security alerts
- Billing notifications
- System maintenance

**Unmute Early:**
Settings > Notifications > Unmute

**Quick Mute:**
Settings > Notifications > Do Not Disturb"""

        elif action == "digest":
            return """**📊 Email Digest Configuration**

**Available Frequencies:**
- **Daily:** Every morning at 9 AM
- **Weekly:** Monday mornings
- **Bi-weekly:** Every other Monday
- **Monthly:** 1st of each month

**What's Included:**
✅ Tasks assigned to you
✅ Unread comments
✅ Upcoming due dates
✅ Team activity summary
✅ Completed milestones

**Configure:**
Settings > Notifications > Email Digest

**Pro Tip:** Use digest mode to reduce inbox noise!"""

        else:  # configure
            return """**⚙️ Notification Settings**

**Configure Notifications:**

**Email Notifications:**
- @Mentions: Immediate
- Assignments: Immediate
- Comments: Optional
- Due Dates: 24h before
- Weekly Digest: Monday 9 AM

**In-App Notifications:**
- Real-time alerts: ✅
- Sound: ✅
- Desktop notifications: ✅
- Badge count: ✅

**Mobile Push:**
- Enabled: ✅
- Quiet Hours: 10 PM - 8 AM
- Critical alerts only during quiet hours

**Slack Integration:**
- Connect workspace for Slack notifications
- Settings > Integrations > Slack

**Quick Settings:**
Settings > Notifications

**Need help?** Let me know:
- "Setup Slack notifications"
- "Mute notifications"
- "Configure email digest"
"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        agent = NotificationConfigurator()
        state = create_initial_state("How do I setup Slack notifications?")
        result = await agent.process(state)
        print(f"Action: {result.get('notification_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
