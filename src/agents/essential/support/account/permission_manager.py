"""
Permission Manager Agent - Manages roles, permissions, and access control.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("permission_manager", tier="essential", category="account")
class PermissionManager(BaseAgent):
    """Permission Manager - Specialist in roles and permissions management."""

    ROLES = {
        "owner": {"level": 4, "description": "Full control, only 1 per account"},
        "admin": {"level": 3, "description": "Full control except billing"},
        "member": {"level": 2, "description": "Create and edit content"},
        "viewer": {"level": 1, "description": "Read-only access"},
    }

    PERMISSIONS = {
        "read": "View all content",
        "write": "Create and edit content",
        "delete": "Delete content",
        "manage_team": "Invite/remove team members",
        "manage_billing": "Access billing info",
        "manage_sso": "Configure SSO (owner only)",
    }

    def __init__(self):
        config = AgentConfig(
            name="permission_manager",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("permission_manager_processing_started")
        state = self.update_state(state)

        message = state["current_message"]
        action = self._detect_permission_action(message)

        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        response = self._generate_permission_guide(action)

        state["agent_response"] = response
        state["permission_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("permission_processing_completed", action=action)
        return state

    def _detect_permission_action(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["explain", "what is", "difference", "roles"]):
            return "explain"
        elif any(w in msg_lower for w in ["change", "update", "modify"]):
            return "change"
        elif any(w in msg_lower for w in ["audit", "review", "check"]):
            return "audit"
        return "view"

    def _generate_permission_guide(self, action: str) -> str:
        if action == "explain":
            return """**🔐 Role Hierarchy and Permissions**

**Role Levels:**

**Level 4 - Owner:**
- Full account control
- Billing access
- Cannot be removed
- Only 1 per account

**Level 3 - Admin:**
- Manage team and projects
- All permissions except billing
- Can invite/remove members
- Cannot change owner

**Level 2 - Member:**
- Create and edit content
- Create new projects
- Cannot manage team
- Cannot access billing

**Level 1 - Viewer:**
- Read-only access
- Can comment
- Cannot edit anything
- Cannot create projects

**Permission Comparison:**

| Permission | Owner | Admin | Member | Viewer |
|-----------|-------|-------|--------|--------|
| View content | ✅ | ✅ | ✅ | ✅ |
| Comment | ✅ | ✅ | ✅ | ✅ |
| Create/edit | ✅ | ✅ | ✅ | ❌ |
| Delete own | ✅ | ✅ | ✅ | ❌ |
| Delete others | ✅ | ✅ | ❌ | ❌ |
| Manage team | ✅ | ✅ | ❌ | ❌ |
| Access billing | ✅ | ❌ | ❌ | ❌ |

**Best Practices:**
✅ Start with least privilege
✅ Use Viewer for external users
✅ Limit Admins to 2-3 people
✅ Regular permission audits

**Quick Access:**
Settings > Team > Permissions"""

        elif action == "change":
            return """**🔄 Change User Permissions**

**How to Change Roles:**

**Step 1: Navigate**
Settings > Team > Team Members

**Step 2: Select User**
Click on user name

**Step 3: Change Role**
Click "Change Role" > Select new role > Confirm

**Changes Apply:** Immediately

**Permission Requirements:**
- **Owner:** Can change anyone's role
- **Admin:** Can change Member and Viewer roles only
- **Member/Viewer:** Cannot change roles

**Important Notes:**
- Owner role requires ownership transfer
- User must refresh to see new permissions
- All changes are logged in audit trail

**Quick Change:**
Settings > Team > User > Change Role"""

        elif action == "audit":
            return """**📊 Permission Audit**

**Review Team Permissions:**
Settings > Team > Permissions Audit

**What to Check:**

**1. Role Distribution:**
- Too many Admins? (recommend max 2-3)
- Appropriate role levels?
- External users as Viewers?

**2. Inactive Users:**
- Users not logged in >30 days
- Consider removing or demoting

**3. External Access:**
- Contractors with appropriate access?
- Clients using Viewer role?

**4. Permission Changes:**
- Review recent role changes
- Verify all changes were authorized

**Security Score:**
Audit improves your security score

**Export Audit:**
Settings > Team > Export Permission Report (CSV)

**Best Practices:**
✅ Monthly permission reviews
✅ Remove inactive users
✅ Limit high-privilege roles
✅ Document role changes"""

        else:  # view
            return """**👁️ View User Permissions**

**Check Permissions:**
Settings > Team > Team Members > Select User

**What You'll See:**

**Current Role:** Member
**Permission Level:** 2/4

**Permissions:**
✅ Read all content
✅ Write and edit content
✅ Comment on everything
✅ Create new projects
❌ Invite team members
❌ Delete others' content
❌ Access billing

**Project-Specific Permissions:**
Some permissions can be overridden per project

**Recent Changes:**
- Nov 10: Promoted from Viewer to Member
- Oct 15: Added to Project Beta

**Quick Actions:**
- [Change Role]
- [View Activity]
- [Remove from Team]

**View All Permissions:**
Settings > Team > Permissions Matrix"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        agent = PermissionManager()
        state = create_initial_state("What are the different roles?")
        result = await agent.process(state)
        print(f"Action: {result.get('permission_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
