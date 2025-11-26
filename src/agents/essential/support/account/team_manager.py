"""
Team Manager Agent - Handles team member management, invitations, and roles.

This agent specializes in team operations including inviting members, removing users,
changing roles, and managing team permissions and invitations.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("team_manager", tier="essential", category="account")
class TeamManager(BaseAgent):
    """
    Team Manager - Specialist in team member and role management.

    Handles:
    - Inviting team members
    - Removing team members
    - Changing user roles
    - Managing invitations
    - Team permissions
    """

    # Role hierarchy and permissions
    ROLES = {
        "owner": {
            "level": 4,
            "permissions": ["all"],
            "can_invite": True,
            "can_remove": True,
            "can_change_billing": True,
            "description": "Full control, cannot be removed, only 1 per account",
        },
        "admin": {
            "level": 3,
            "permissions": ["read", "write", "delete", "manage_team", "manage_projects"],
            "can_invite": True,
            "can_remove": True,
            "can_change_billing": False,
            "description": "Full control except billing and SSO",
        },
        "member": {
            "level": 2,
            "permissions": ["read", "write", "comment", "create_projects"],
            "can_invite": False,
            "can_remove": False,
            "can_change_billing": False,
            "description": "Can create and edit content, no team management",
        },
        "viewer": {
            "level": 1,
            "permissions": ["read", "comment"],
            "can_invite": False,
            "can_remove": False,
            "can_change_billing": False,
            "description": "Read-only access, can comment",
        },
    }

    # Plan limits for team size
    PLAN_LIMITS = {"free": 3, "basic": 10, "premium": 50, "enterprise": float("inf")}

    # Team action keywords
    TEAM_KEYWORDS = {
        "invite": ["invite", "add", "new member", "join", "add user"],
        "remove": ["remove", "delete", "kick", "remove user", "offboard"],
        "change_role": ["role", "permission", "promote", "demote", "change role", "upgrade"],
        "list": ["list", "show", "view team", "team members", "who is on"],
        "resend_invite": ["resend", "send again", "invitation", "invite again"],
    }

    def __init__(self):
        config = AgentConfig(
            name="team_manager",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process team management requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with team management response
        """
        self.logger.info("team_manager_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "team_processing_details", message_preview=message[:100], turn_count=state["turn_count"]
        )

        # Detect team action
        team_action = self._detect_team_action(message)
        self.logger.info("team_action_detected", action=team_action)

        # Search KB
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        # Generate response
        response = self._generate_team_response(team_action, customer_context, kb_results)

        state["agent_response"] = response
        state["team_action"] = team_action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("team_processing_completed", status="resolved")

        return state

    def _detect_team_action(self, message: str) -> str:
        """Detect team management action from message."""
        message_lower = message.lower()

        for action, keywords in self.TEAM_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return action

        return "general"

    def _generate_team_response(
        self, action: str, customer_context: dict[str, Any], kb_results: list
    ) -> str:
        """Generate team management response."""
        user_role = customer_context.get("role", "member")
        plan = customer_context.get("plan", "free")
        team_size = customer_context.get("team_size", 1)

        if action == "invite":
            response = self._guide_invite_member(user_role, plan, team_size)
        elif action == "remove":
            response = self._guide_remove_member(user_role)
        elif action == "change_role":
            response = self._guide_change_role(user_role)
        elif action == "list":
            response = self._guide_list_team(team_size)
        elif action == "resend_invite":
            response = self._guide_resend_invitation()
        else:
            response = self._guide_team_management()

        if kb_results:
            kb_context = "\n\n**📚 Related articles:**\n"
            for article in kb_results[:2]:
                kb_context += f"- {article.get('title', 'Help Article')}\n"
            response += kb_context

        return response

    def _guide_invite_member(self, user_role: str, plan: str, team_size: int) -> str:
        """Guide for inviting team members."""
        if not self.ROLES.get(user_role, {}).get("can_invite"):
            return f"""**⚠️ Permission Required**

Only **admins** and **owners** can invite team members.

**Your role:** {user_role.title()}

**To invite members:**
- Contact your admin or owner
- Request role upgrade if appropriate

**What you can do:**
- View team members (Settings > Team)
- Update your own profile"""

        limit = self.PLAN_LIMITS.get(plan, 3)
        remaining = limit - team_size

        if remaining <= 0 and limit != float("inf"):
            return f"""**⚠️ Team Member Limit Reached**

Your {plan.title()} plan allows **{limit} members**.
You currently have **{team_size} members**.

**Options:**
1. **Upgrade Plan** to get more seats
   - Basic: 10 members
   - Premium: 50 members
   - Enterprise: Unlimited

2. **Remove inactive members** to free up seats

**Upgrade Now:**
Settings > Billing > Upgrade Plan"""

        return f"""**👥 Invite Team Members**

**How to invite:**

**Step 1: Open Team Settings**
- Settings > Team > Invite Members

**Step 2: Enter Email & Select Role**
- **Email:** user@example.com
- **Role:** Choose from dropdown

**Step 3: Send Invitation**
- Click "Send Invitation"
- They'll receive email invite
- Invitation expires in 7 days

**Available Roles:**

**Owner** (1 per account):
- Full control including billing
- Cannot be removed

**Admin:**
- Manage team and projects
- Cannot access billing

**Member:**
- Create and edit content
- Cannot manage team

**Viewer:**
- Read-only access
- Can comment only

**Your Plan:** {plan.title()}
- **Limit:** {limit if limit != float("inf") else "Unlimited"} members
- **Current:** {team_size} members
- **Available:** {remaining if limit != float("inf") else "Unlimited"} seats

**Invitation Process:**
1. User receives email
2. They click "Accept Invitation"
3. They create account or log in
4. Added to your team

**Manage Invitations:**
- View pending invitations
- Resend invitation
- Cancel invitation
- Check expiration (7 days)

**Quick Invite:**
Settings > Team > Invite > Enter email > Select role > Send"""

    def _guide_remove_member(self, user_role: str) -> str:
        """Guide for removing team members."""
        if not self.ROLES.get(user_role, {}).get("can_remove"):
            return """**⚠️ Permission Required**

Only **admins** and **owners** can remove team members."""

        return """**🚫 Remove Team Member**

**How to remove:**

**Step 1: Navigate to Team**
- Settings > Team > Team Members

**Step 2: Select Member**
- Click on member name
- Click "Remove from Team"

**Step 3: Confirm Removal**
- Confirm action
- Member removed immediately

**What Happens:**
- ✅ Member loses access immediately
- ✅ Seat becomes available
- ✅ Their personal data retained for 30 days (GDPR)
- ✅ Can be re-invited anytime

**Important Notes:**
- ⚠️ Owner cannot be removed
- ⚠️ Removed members lose all access
- ✅ You can re-invite them later

**Best Practices:**
- Notify member before removal
- Export their important data first
- Document reason for audit purposes

**Quick Remove:**
Settings > Team > Member > Remove"""

    def _guide_change_role(self, user_role: str) -> str:
        """Guide for changing member roles."""
        if user_role not in ["owner", "admin"]:
            return """**⚠️ Permission Required**

Only **owners** and **admins** can change member roles."""

        return f"""**🔄 Change Member Role**

**How to change roles:**

**Step 1: Navigate to Team**
- Settings > Team > Team Members

**Step 2: Select Member**
- Click member name
- Click "Change Role"

**Step 3: Select New Role**
- Choose from dropdown
- Click "Update Role"
- Changes apply immediately

**Role Hierarchy:**

**Level 4 - Owner:**
- Full control
- Only 1 per account
- Cannot be changed (except ownership transfer)

**Level 3 - Admin:**
- Manage team and projects
- No billing access
- {"✅ You can change" if user_role == "owner" else "❌ Owner only"}

**Level 2 - Member:**
- Create and edit content
- No team management
- ✅ You can change

**Level 1 - Viewer:**
- Read-only access
- Can comment
- ✅ You can change

**Your Permissions ({user_role.title()}):**
- {"✅ Can change any role" if user_role == "owner" else "✅ Can change Member and Viewer roles only"}

**Common Role Changes:**
- Member → Admin: Promote for team management
- Admin → Member: Reduce permissions
- Member → Viewer: External stakeholder
- Viewer → Member: Grant edit access

**Quick Change:**
Settings > Team > Member > Change Role"""

    def _guide_list_team(self, team_size: int) -> str:
        """Guide for viewing team members."""
        return f"""**👥 View Team Members**

**Current Team:** {team_size} members

**How to view team:**

**Navigate to Team Settings:**
- Settings > Team > Team Members

**What You'll See:**

**Active Members:**
- Name and email
- Role (Owner, Admin, Member, Viewer)
- Last activity
- Join date

**Pending Invitations:**
- Invited email
- Invited role
- Sent date
- Expiration date (7 days)

**Sort & Filter:**
- By role
- By last activity
- By join date
- Search by name or email

**Member Actions:**
- View profile
- Change role (if permitted)
- Remove member (if permitted)
- View activity history

**Invitation Actions:**
- Resend invitation
- Cancel invitation
- Change invited role

**Export Team List:**
- Settings > Team > Export (CSV)
- Includes all members and roles
- Use for auditing

**Quick View:**
Settings > Team > View All Members"""

    def _guide_resend_invitation(self) -> str:
        """Guide for resending invitations."""
        return """**📧 Resend Team Invitation**

**How to resend:**

**Step 1: View Pending Invitations**
- Settings > Team > Pending Invitations

**Step 2: Select Invitation**
- Find the invitation
- Click "Resend Invitation"

**Step 3: Confirm**
- New email sent immediately
- Expiration reset to 7 days

**Why Resend:**
- User didn't receive email
- Invitation expired
- User lost the email

**Troubleshooting:**

**If user not receiving emails:**
- ✅ Check spam/junk folder
- ✅ Verify email address is correct
- ✅ Try different email address
- ✅ Contact support if persistent

**Invitation Status:**
- **Pending:** Waiting for acceptance
- **Expired:** After 7 days (resend to reset)
- **Accepted:** User joined team

**Quick Resend:**
Settings > Team > Pending Invitations > Resend"""

    def _guide_team_management(self) -> str:
        """General team management guide."""
        return """**👥 Team Management Guide**

**What You Can Do:**

**1. Invite Members:**
- Settings > Team > Invite
- Enter email and select role
- Send invitation

**2. Manage Roles:**
- View all team members
- Change member roles
- Promote or demote

**3. Remove Members:**
- Remove team access
- Seat freed immediately

**4. View Team:**
- See all active members
- Check pending invitations
- Export team list

**Roles Explained:**

**Owner (Level 4):**
- Full control
- Billing access
- Cannot be removed
- 1 per account

**Admin (Level 3):**
- Manage team
- Manage projects
- No billing access

**Member (Level 2):**
- Create & edit
- No team management

**Viewer (Level 1):**
- Read-only
- Can comment

**Best Practices:**
- ✅ Start with least privilege
- ✅ Use Viewer for external users
- ✅ Limit Admins to 2-3 people
- ✅ Regular team audits
- ✅ Remove inactive members

**Quick Actions:**
- Invite: Settings > Team > Invite
- Remove: Settings > Team > Member > Remove
- Change Role: Settings > Team > Member > Change Role

**Need specific help?** Tell me:
- "How to invite a member"
- "How to change someone's role"
- "How to remove a team member"
- "How to view my team"
"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("Testing Team Manager Agent")
        print("=" * 60)

        agent = TeamManager()

        # Test 1: Invite member
        state1 = create_initial_state(
            "How do I invite a team member?",
            context={"customer_metadata": {"plan": "premium", "role": "admin", "team_size": 5}},
        )
        result1 = await agent.process(state1)
        print(f"\nTest 1 - Action: {result1.get('team_action')}")
        print(f"Preview: {result1['agent_response'][:200]}...")

        # Test 2: Permission denied
        state2 = create_initial_state(
            "I want to remove someone",
            context={"customer_metadata": {"plan": "basic", "role": "member", "team_size": 3}},
        )
        result2 = await agent.process(state2)
        print(f"\nTest 2 - Action: {result2.get('team_action')}")
        print(f"Preview: {result2['agent_response'][:200]}...")

    asyncio.run(test())
