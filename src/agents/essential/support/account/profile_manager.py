"""
Profile Manager Agent - Handles profile, company info, and account settings updates.

This agent helps customers update their personal profile information, company details,
preferences, timezone settings, and other account-related configurations.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("profile_manager", tier="essential", category="account")
class ProfileManager(BaseAgent):
    """
    Profile Manager - Specialist in profile and account settings management.

    Handles:
    - Personal profile updates (name, email, phone, job title)
    - Company information updates
    - User preferences and settings
    - Timezone configuration
    - Profile picture management
    """

    # Update types supported
    UPDATE_TYPES = {
        "user": "Personal profile information",
        "company": "Company information (admin only)",
        "settings": "User preferences and settings",
        "timezone": "Timezone configuration",
        "avatar": "Profile picture upload",
    }

    # Allowed user profile fields
    ALLOWED_USER_FIELDS = ["name", "email", "phone", "avatar_url", "job_title", "department", "bio"]

    # Allowed company fields (admin/owner only)
    ALLOWED_COMPANY_FIELDS = [
        "company_name",
        "industry",
        "company_size",
        "website",
        "address",
        "billing_email",
    ]

    # Timezone-related keywords
    TIMEZONE_KEYWORDS = [
        "timezone",
        "time zone",
        "utc",
        "gmt",
        "time",
        "clock",
        "eastern",
        "pacific",
        "central",
    ]

    # Profile-related keywords
    PROFILE_KEYWORDS = {
        "user": ["name", "email", "phone", "profile", "contact", "job title", "department"],
        "company": ["company", "organization", "business", "billing email", "industry"],
        "settings": ["preferences", "settings", "language", "notifications", "date format"],
        "timezone": ["timezone", "time zone", "utc", "gmt", "clock"],
    }

    def __init__(self):
        config = AgentConfig(
            name="profile_manager",
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
        Process profile update requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with profile management response
        """
        self.logger.info("profile_manager_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "profile_processing_details",
            message_preview=message[:100],
            turn_count=state["turn_count"],
            customer_plan=customer_context.get("plan", "free"),
        )

        # Detect update type from message
        update_type = self._detect_update_type(message)
        self.logger.info("profile_update_type_detected", update_type=update_type)

        # Extract update data from entities if available
        update_data = state.get("entities", {}).get("profile_data", {})

        # Search knowledge base for profile-related articles
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("profile_kb_articles_found", count=len(kb_results))

        # Generate profile management response
        response = self._generate_profile_response(
            update_type, update_data, customer_context, kb_results
        )

        state["agent_response"] = response
        state["profile_update_type"] = update_type
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("profile_processing_completed", status="resolved", update_type=update_type)

        return state

    def _detect_update_type(self, message: str) -> str:
        """
        Detect what type of profile update user wants.

        Args:
            message: User's message

        Returns:
            Update type identifier
        """
        message_lower = message.lower()

        # Check for specific update types
        for update_type, keywords in self.PROFILE_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                return update_type

        # Default to user profile
        return "user"

    def _generate_profile_response(
        self,
        update_type: str,
        update_data: dict[str, Any],
        customer_context: dict[str, Any],
        kb_results: list,
    ) -> str:
        """
        Generate profile management response.

        Args:
            update_type: Type of profile update
            update_data: Update data from entities
            customer_context: Customer metadata
            kb_results: Knowledge base search results

        Returns:
            Formatted profile management guide
        """
        # Generate type-specific response
        if update_type == "user":
            response = self._guide_user_profile_update(customer_context, update_data)
        elif update_type == "company":
            response = self._guide_company_profile_update(customer_context, update_data)
        elif update_type == "settings":
            response = self._guide_preferences_update(customer_context, update_data)
        elif update_type == "timezone":
            response = self._guide_timezone_update(customer_context, update_data)
        else:
            response = self._guide_general_profile_help()

        # Add KB context if available
        if kb_results:
            kb_context = "\n\n**📚 Related help articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article.get('title', 'Help Article')}\n"
            response += kb_context

        return response

    def _guide_user_profile_update(
        self, customer_context: dict[str, Any], update_data: dict[str, Any]
    ) -> str:
        """Guide for updating user profile."""
        customer_context.get("role", "member")

        return """**👤 Update Your Profile**

**How to update your profile:**

**Step 1: Navigate to Settings**
- Click your avatar (top right)
- Select "Profile Settings"

**Step 2: Update Your Information**

**Personal Information:**
- ✏️ **Name:** Your full name
- 📧 **Email:** Your email address
- 📱 **Phone:** Contact number (optional)
- 🏢 **Job Title:** Your position
- 📂 **Department:** Your team/department

**Step 3: Save Changes**
- Click "Save Profile"
- Changes take effect immediately

**Updating Your Email:**
1. Enter new email address
2. We'll send verification email
3. Click verification link
4. Email updated once verified

**Profile Picture:**
- Click "Upload Photo"
- Max size: 5MB
- Formats: JPG, PNG, GIF
- Recommended: 400x400px square

**Privacy Settings:**
- Control who can see your profile
- Manage email visibility
- Set calendar availability

**Quick Links:**
- Settings > Profile: Update personal info
- Settings > Privacy: Control visibility
- Settings > Notifications: Email preferences

**Need help with a specific field?** Let me know what you'd like to update!"""

    def _guide_company_profile_update(
        self, customer_context: dict[str, Any], update_data: dict[str, Any]
    ) -> str:
        """Guide for updating company profile."""
        user_role = customer_context.get("role", "member")

        # Check if user has permission
        if user_role not in ["owner", "admin"]:
            return f"""**⚠️ Permission Required**

Only **account owners** and **admins** can update company information.

**Your current role:** {user_role.title()}

**To update company info:**
1. Contact your account owner or admin
2. Or request role upgrade if appropriate

**What you CAN update:**
- Your personal profile (Settings > Profile)
- Your preferences (Settings > Preferences)
- Your notification settings

**Need help with something else?** I can help you update your personal information!"""

        return """**🏢 Update Company Information**

**How to update company details:**

**Step 1: Navigate to Company Settings**
- Settings > Company > Company Profile

**Step 2: Update Company Information**

**Basic Information:**
- 🏢 **Company Name:** Official business name
- 🏭 **Industry:** Your industry sector
- 👥 **Company Size:** Number of employees
- 🌐 **Website:** Company website URL
- 📍 **Address:** Business address

**Billing Information:**
- 💳 **Billing Email:** Where invoices are sent
- 📄 **Tax ID:** For invoicing (if applicable)
- 🏦 **Billing Address:** For tax purposes

**Step 3: Save Changes**
- Click "Save Company Profile"
- Changes reflected immediately
- Billing email changes affect invoice delivery

**Important Notes:**
- ⚠️ Changing billing email affects where invoices go
- 📧 Billing contact receives payment notifications
- 🏷️ Company name appears on all invoices

**Company Logo:**
- Upload: Settings > Company > Branding
- Max size: 2MB
- Recommended: 200x200px PNG with transparency

**Domain Verification:**
- Verify your company domain
- Enable SSO (Enterprise plan)
- Auto-add team members with your domain

**Quick Links:**
- Settings > Company: Update company info
- Settings > Branding: Logo and colors
- Settings > Team: Manage team members

**Need help with specific fields?** Let me know what you'd like to change!"""

    def _guide_preferences_update(
        self, customer_context: dict[str, Any], update_data: dict[str, Any]
    ) -> str:
        """Guide for updating user preferences."""
        return """**⚙️ Update Your Preferences**

**How to update preferences:**

**Step 1: Open Preferences**
- Settings > Preferences

**Step 2: Customize Your Settings**

**Language & Region:**
- 🌐 **Language:** Interface language
- 📅 **Date Format:** MM/DD/YYYY, DD/MM/YYYY, etc.
- 🕐 **Time Format:** 12-hour or 24-hour
- 💱 **Currency:** Display currency

**Email Notifications:**
- 📧 **Mentions:** When someone @mentions you
- 📋 **Assignments:** When assigned to tasks
- 💬 **Comments:** New comments on your items
- 📊 **Weekly Digest:** Summary email (Monday mornings)

**Desktop Notifications:**
- 🔔 **Browser Notifications:** Real-time alerts
- 🔊 **Sound Alerts:** Notification sounds
- 🎨 **Desktop Badges:** Unread count badges

**Default Settings:**
- 👀 **Default View:** List, Board, Calendar
- 🗂️ **Default Project:** Which project opens first
- 🎯 **Default Filter:** Your preferred filter
- ⌨️ **Keyboard Shortcuts:** Enable/disable

**Privacy Preferences:**
- 👁️ **Profile Visibility:** Public, Team, Private
- 📆 **Calendar Sharing:** Share availability
- 🔍 **Search Visibility:** Appear in team search
- 📊 **Analytics:** Opt in/out of usage analytics

**Accessibility:**
- 🎨 **High Contrast:** Enhanced visibility
- ⌨️ **Keyboard Navigation:** Full keyboard control
- 📖 **Screen Reader:** Optimized for screen readers
- 🔍 **Text Size:** Adjust font size

**Step 3: Save Preferences**
- Click "Save Preferences"
- Most changes apply immediately
- Some may require page refresh

**Popular Settings:**
- Enable weekly digest to reduce email noise
- Use keyboard shortcuts for faster navigation
- Set default view to your preferred layout
- Enable desktop notifications for urgent items

**Quick Access:**
- Settings > Preferences: All user preferences
- Settings > Notifications: Email and push settings
- Settings > Accessibility: Accessibility features

**Need help configuring something specific?** Let me know!"""

    def _guide_timezone_update(
        self, customer_context: dict[str, Any], update_data: dict[str, Any]
    ) -> str:
        """Guide for updating timezone."""
        update_data.get("timezone", "UTC")

        return """**🌍 Update Your Timezone**

**Why timezone matters:**
- Email delivery times
- Notification timing
- Deadline calculations
- Audit log timestamps
- Meeting scheduling

**How to update timezone:**

**Step 1: Open Profile Settings**
- Settings > Profile > Timezone

**Step 2: Select Your Timezone**
- Search for your city
- Or select from dropdown
- Preview shows current time in selected timezone

**Step 3: Confirm Change**
- Click "Update Timezone"
- Changes apply immediately

**Common Timezones:**

**Americas:**
- America/New_York (EST/EDT)
- America/Chicago (CST/CDT)
- America/Denver (MST/MDT)
- America/Los_Angeles (PST/PDT)

**Europe:**
- Europe/London (GMT/BST)
- Europe/Paris (CET/CEST)
- Europe/Berlin (CET/CEST)

**Asia/Pacific:**
- Asia/Tokyo (JST)
- Asia/Singapore (SGT)
- Australia/Sydney (AEDT/AEST)

**What Changes:**
- ✅ Email delivery times adjusted to your timezone
- ✅ Due dates show in your local time
- ✅ Notifications sent at appropriate times
- ✅ Audit logs display in your timezone
- ✅ Calendar events in your time

**What Doesn't Change:**
- ❌ Team members' timezones (everyone has their own)
- ❌ Server times (always UTC internally)
- ❌ Historical timestamps (keep original timezone)

**Working Across Timezones:**
- Use "View in my timezone" feature
- Calendar shows all times in your timezone
- Team availability shows their local time
- Meeting scheduler accounts for all timezones

**Automatic Timezone Detection:**
- Enable: Settings > Profile > Auto-detect timezone
- Updates when you travel
- Override manually if needed

**Daylight Saving Time:**
- Automatically handled by timezone database
- No manual adjustment needed
- Transitions happen automatically

**Quick Links:**
- Settings > Profile > Timezone: Change timezone
- Settings > Calendar: View team availability
- Settings > Preferences: Date/time format

**Need help selecting the right timezone?** Let me know your location!"""

    def _guide_general_profile_help(self) -> str:
        """General profile management help."""
        return """**👤 Profile Management Guide**

**What you can update:**

**1. Personal Profile:**
- Name, email, phone number
- Job title and department
- Profile picture
- Bio and contact info

**2. Company Information** (Admin/Owner only):
- Company name and details
- Industry and company size
- Website and address
- Billing email and tax info

**3. Preferences & Settings:**
- Language and regional settings
- Date/time formats
- Notification preferences
- Default views and filters

**4. Privacy Settings:**
- Profile visibility
- Calendar sharing
- Search visibility
- Data sharing preferences

**5. Timezone:**
- Your local timezone
- Automatic timezone detection
- Working hours settings

**Quick Actions:**

**Update Your Name:**
Settings > Profile > Name > Save

**Change Your Email:**
Settings > Profile > Email > Verify New Email

**Upload Profile Picture:**
Settings > Profile > Upload Photo (max 5MB)

**Update Company Info:**
Settings > Company > Company Profile > Save
(Admin/Owner only)

**Change Timezone:**
Settings > Profile > Timezone > Select > Save

**Update Preferences:**
Settings > Preferences > Customize > Save

**Security Best Practices:**
- ✅ Use work email for account
- ✅ Keep contact info up to date
- ✅ Verify email changes
- ✅ Use professional profile picture
- ✅ Review privacy settings regularly

**Common Questions:**

**Q: Can I change my account email?**
A: Yes! Settings > Profile > Email. You'll need to verify the new email.

**Q: Who can see my profile?**
A: Depends on your privacy settings. Default is "Team members only".

**Q: Can I use a nickname?**
A: Yes, enter your preferred name in the Name field.

**Q: How do I update company logo?**
A: Settings > Company > Branding > Upload Logo (Admin/Owner only)

**Need help with something specific?** Just let me know what you'd like to update:
- "Update my name"
- "Change company information"
- "Update timezone"
- "Change email address"
- "Update preferences"

I'm here to help! 😊"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("Testing Profile Manager Agent")
        print("=" * 60)

        # Test 1: User profile update
        print("\nTest 1: User Profile Update")
        print("-" * 60)

        state1 = create_initial_state(
            "How do I update my email address?",
            context={"customer_metadata": {"plan": "premium", "role": "member"}},
        )

        agent = ProfileManager()
        result1 = await agent.process(state1)

        print(f"Update Type: {result1.get('profile_update_type')}")
        print(f"Status: {result1.get('status')}")
        print(f"\nResponse preview:\n{result1['agent_response'][:300]}...")

        # Test 2: Company profile update
        print("\n\nTest 2: Company Profile Update")
        print("-" * 60)

        state2 = create_initial_state(
            "I need to update our company name",
            context={"customer_metadata": {"plan": "enterprise", "role": "owner"}},
        )

        result2 = await agent.process(state2)

        print(f"Update Type: {result2.get('profile_update_type')}")
        print(f"Status: {result2.get('status')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:300]}...")

        # Test 3: Timezone update
        print("\n\nTest 3: Timezone Update")
        print("-" * 60)

        state3 = create_initial_state(
            "How do I change my timezone to Pacific time?",
            context={"customer_metadata": {"plan": "basic"}},
        )

        result3 = await agent.process(state3)

        print(f"Update Type: {result3.get('profile_update_type')}")
        print(f"Status: {result3.get('status')}")
        print(f"\nResponse preview:\n{result3['agent_response'][:300]}...")

    asyncio.run(test())
