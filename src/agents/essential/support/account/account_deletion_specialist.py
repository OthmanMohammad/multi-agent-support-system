"""
Account Deletion Specialist Agent - Handles account deletion with GDPR compliance.
"""

from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("account_deletion_specialist", tier="essential", category="account")
class AccountDeletionSpecialist(BaseAgent):
    """Account Deletion Specialist - Handles GDPR-compliant account deletion."""

    DELETION_GRACE_PERIOD_DAYS = 30
    
    RETENTION_REQUIREMENTS = {
        "billing": 2555,  # 7 years for tax
        "audit_logs": 90,
        "support_tickets": 365
    }

    def __init__(self):
        config = AgentConfig(
            name="account_deletion_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("deletion_processing_started")
        state = self.update_state(state)
        
        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        action = self._detect_deletion_action(message)
        
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results
        
        response = self._generate_deletion_guide(action, customer_context)
        
        state["agent_response"] = response
        state["deletion_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"
        
        self.logger.info("deletion_processing_completed", action=action)
        return state

    def _detect_deletion_action(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["cancel", "stop", "undo"]):
            return "cancel_deletion"
        elif any(w in msg_lower for w in ["export", "backup", "download"]):
            return "export_before_delete"
        elif any(w in msg_lower for w in ["alternative", "instead", "pause"]):
            return "alternatives"
        return "request_deletion"

    def _generate_deletion_guide(self, action: str, customer_context: Dict[str, Any]) -> str:
        user_role = customer_context.get("role", "member")
        plan = customer_context.get("plan", "free")
        has_team = customer_context.get("team_size", 1) > 1

        if action == "request_deletion":
            if has_team and user_role != "owner":
                return f"""**⚠️ Cannot Delete Account**

Only the **account owner** can delete the account.

**Your role:** {user_role.title()}

**Options:**
1. **Leave the team** instead
   Settings > Team > Leave Team

2. **Contact owner** to delete entire account
   Owner email: {customer_context.get('owner_email', 'owner@example.com')}

3. **Delete your personal data** (GDPR)
   Settings > Privacy > Delete My Data"""

            if plan in ["basic", "premium", "enterprise"]:
                return f"""**⚠️ Active Subscription Detected**

You have an active {plan.title()} subscription.

**Before Deleting:**

**1. Cancel Subscription**
Settings > Billing > Cancel Subscription
- Current period ends: Dec 1, 2025
- No refund for current period

**2. Wait for Period to End**
Or contact support for immediate cancellation

**Alternative: Downgrade to Free**
- Keep account and data
- No more charges
- Limited to free features

Settings > Billing > Downgrade to Free"""

            return """**⚠️ Account Deletion Request**

**Before You Go:**

**What Will Be Deleted:**
✅ All your projects and tasks
✅ All uploaded files
✅ All comments and discussions
✅ Your profile and settings
✅ Team members' access
✅ All integrations and API keys

**What We Keep (Legal):**
- Billing records (7 years)
- Audit logs (90 days)
- Support tickets (1 year)

**⏱️ 30-Day Grace Period:**
- Account deactivated: Immediately
- Data retained: 30 days
- Permanent deletion: Dec 15, 2025
- Can cancel anytime before then

**⚠️ THIS CANNOT BE UNDONE AFTER 30 DAYS**

**Have you backed up your data?**
Export your data first: Settings > Export

**Ready to proceed?**
Type "DELETE MY ACCOUNT" to confirm

**Or explore alternatives:**
- Pause account (keep data, stop charges)
- Downgrade to free
- Archive projects"""

        elif action == "cancel_deletion":
            return """**✅ Cancel Account Deletion**

**How to Cancel:**
1. Click cancellation link in email
2. Or: Settings > Account > Cancel Deletion
3. Quote deletion ID if contacting support

**What Gets Restored:**
✅ Account access
✅ All projects and data
✅ Team member access
✅ Integrations and API keys
✅ Settings and preferences

**After Cancellation:**
1. Reactivate subscription (if you had one)
2. Review your data
3. Update payment method (if needed)

**Cancellation Window:**
30 days from deletion request

**Quick Cancel:**
Support: support@example.com
Include: Deletion ID"""

        elif action == "export_before_delete":
            return """**💾 Export Before Deletion**

**⚠️ IMPORTANT: Export first!**

**Quick Export:**
Settings > Account > Export Data

**Recommended: Full Account Export**
- Everything in your account
- Format: ZIP (JSON + files)
- Time: 2-4 hours
- Size: 500 MB - 5 GB

**Export Process:**
1. Request Export
   Settings > Export Data > Full Account

2. Wait for Email
   Usually 2-4 hours

3. Download & Verify
   Download ZIP file
   Verify checksum

4. Store Safely
   External drive or cloud storage
   Don't rely on our servers!

**What's Included:**
✅ All projects and tasks (JSON)
✅ All uploaded files (original)
✅ All comments
✅ Team member list
✅ Activity history
✅ Settings backup

**After Export:**
Once downloaded and verified:
Settings > Account > Delete Account

**Need Help:**
I can start the export for you now"""

        else:  # alternatives
            return """**🔄 Alternatives to Deletion**

**Instead of Deleting:**

**1. Pause Account**
- Stop all charges
- Keep data for 90 days
- Reactivate anytime
- No penalty

**2. Downgrade to Free**
- Keep all data
- No charges
- Basic features
- Upgrade anytime

**3. Archive Projects**
- Hide unused projects
- Reduce clutter
- Keep historical data
- Restore anytime

**4. Export & Take a Break**
- Download all data
- Delete if you want
- We keep backups 30 days
- Come back if needed

**Why Are You Leaving?**

**If Too Expensive:**
→ Downgrade to free plan (no charges)

**If Missing Features:**
→ Tell us what you need (we might have it!)

**If Switching Tools:**
→ We'll help you export data

**If No Longer Needed:**
→ Pause instead of delete

**Which option sounds best?**
Let me help you set it up!"""

if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        agent = AccountDeletionSpecialist()
        state = create_initial_state(
            "I want to delete my account",
            context={"customer_metadata": {"plan": "free", "role": "owner", "team_size": 1}}
        )
        result = await agent.process(state)
        print(f"Action: {result.get('deletion_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
