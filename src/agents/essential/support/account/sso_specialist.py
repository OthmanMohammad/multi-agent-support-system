"""
SSO Specialist Agent - Helps configure SAML/OAuth SSO for enterprise customers.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("sso_specialist", tier="essential", category="account")
class SSOSpecialist(BaseAgent):
    """SSO Specialist - Specialist in SAML/OAuth SSO configuration."""

    SUPPORTED_PROVIDERS = {
        "okta": "Okta",
        "azure_ad": "Azure Active Directory / Microsoft Entra ID",
        "google_workspace": "Google Workspace",
        "onelogin": "OneLogin",
        "auth0": "Auth0",
        "custom_saml": "Custom SAML 2.0 Provider",
    }

    def __init__(self):
        config = AgentConfig(
            name="sso_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("sso_specialist_processing_started")
        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        plan = customer_context.get("plan", "free")

        # Check enterprise requirement
        if plan not in ["enterprise"]:
            state["agent_response"] = self._sso_upgrade_required()
            state["response_confidence"] = 0.9
            state["next_agent"] = None
            state["status"] = "resolved"
            return state

        provider = self._detect_sso_provider(message)
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        response = self._generate_sso_guide(provider)

        state["agent_response"] = response
        state["sso_provider"] = provider
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("sso_processing_completed", provider=provider)
        return state

    def _detect_sso_provider(self, message: str) -> str:
        msg_lower = message.lower()
        if "okta" in msg_lower:
            return "okta"
        elif "azure" in msg_lower or "microsoft" in msg_lower:
            return "azure_ad"
        elif "google" in msg_lower:
            return "google_workspace"
        return "general"

    def _sso_upgrade_required(self) -> str:
        return """**Single Sign-On (SSO) - Enterprise Feature**

SSO is available on our Enterprise plan.

**Benefits of SSO:**
✅ Centralized authentication
✅ Enhanced security (enforce 2FA policies)
✅ Simplified user management
✅ Better compliance (SAML 2.0)
✅ Auto-provision/deprovision users

**Supported Identity Providers:**
- Okta
- Azure Active Directory / Microsoft Entra ID
- Google Workspace
- OneLogin
- Auth0
- Any SAML 2.0 provider

**Pricing:**
Enterprise plan: Starting at $1,000/month
- Includes SSO for unlimited users
- Advanced security features
- Priority support

**Want to upgrade?**
Contact: sales@example.com
Schedule demo: https://example.com/demo"""

    def _generate_sso_guide(self, provider: str) -> str:
        if provider == "okta":
            return """**Set Up SSO with Okta**

**PREREQUISITES:**
✅ Enterprise plan active
✅ Okta admin access
✅ Domain ownership verified

**STEP 1: Configure in Okta**
1. Okta Admin > Applications > Create App Integration
2. Sign-in method: SAML 2.0
3. App name: YourCompany

**STEP 2: Configure SAML**
**Single Sign-On URL:**
https://app.example.com/auth/saml/callback

**Audience URI:**
https://app.example.com/auth/saml/metadata

**Attribute Statements:**
- email → user.email
- firstName → user.firstName
- lastName → user.lastName

**STEP 3: Get Okta Metadata**
- Go to "Sign On" tab
- Copy "Identity Provider metadata" URL

**STEP 4: Configure in Our Platform**
Settings > Company > SSO > Configure
- Provider: Okta
- Metadata URL: (paste from Step 3)
- Default Role: Member

**STEP 5: Assign Users in Okta**
Applications > YourCompany > Assignments > Assign

**STEP 6: Test SSO**
https://app.example.com/sso/test

**STEP 7: Enable for Production**
Settings > Company > SSO > Enable
⚠️ This will require ALL users to use SSO

**Troubleshooting:**
- "Invalid SSO": Check metadata URL
- "User not found": Ensure email matches
- "SAML assertion invalid": Check certificate"""

        elif provider == "azure_ad":
            return """**Set Up SSO with Azure AD**

**PREREQUISITES:**
✅ Enterprise plan
✅ Azure AD admin access
✅ Domain verified

**STEP 1: Create Enterprise App**
Azure Portal > Azure AD > Enterprise Applications > New Application
Name: YourCompany

**STEP 2: Configure SAML**
Single sign-on > SAML

**Identifier (Entity ID):**
https://app.example.com/auth/saml/metadata

**Reply URL:**
https://app.example.com/auth/saml/callback

**Attributes:**
- email → user.mail
- firstname → user.givenname
- lastname → user.surname

**STEP 3: Download Certificate**
- SAML Signing Certificate
- Download "Certificate (Base64)"

**STEP 4: Configure in Our Platform**
Settings > Company > SSO
- Provider: Azure AD
- SSO Login URL: (from Azure)
- Entity ID: (from Azure)
- Certificate: (paste content)
- Email Domain: yourcompany.com

**STEP 5: Assign Users**
Enterprise Applications > YourCompany > Users and groups

**STEP 6: Test SSO**
https://app.example.com/sso/test

**✅ SSO Configured Successfully!**

**Advanced:** Enable SCIM for auto-provisioning"""

        elif provider == "google_workspace":
            return """**Set Up SSO with Google Workspace**

**PREREQUISITES:**
✅ Enterprise plan
✅ Google Workspace Super Admin
✅ Domain verified

**STEP 1: Add SAML App**
admin.google.com > Apps > Web and mobile apps
Add app > Add custom SAML app

**STEP 2: Download IDP Info**
- SSO URL
- Entity ID
- Certificate

**STEP 3: Configure Service Provider**
**ACS URL:**
https://app.example.com/auth/saml/callback

**Entity ID:**
https://app.example.com/auth/saml/metadata

**Name ID:** Primary email

**STEP 4: Attribute Mapping**
- email → Primary email
- firstName → First name
- lastName → Last name

**STEP 5: Configure in Our Platform**
Settings > Company > SSO
- Provider: Google Workspace
- Enter details from Step 2

**STEP 6: Turn On App**
User access > ON for everyone

**✅ Done!** Test at: https://app.example.com/sso/test"""

        else:  # general
            return """**SSO Configuration - General Guide**

**Supported Providers:**
- Okta
- Azure Active Directory
- Google Workspace
- OneLogin
- Auth0
- Custom SAML 2.0

**General Setup Process:**

**1. Configure in Your IdP**
Create SAML application with our details

**2. Service Provider Details:**
**Entity ID:** https://app.example.com/auth/saml/metadata
**ACS URL:** https://app.example.com/auth/saml/callback
**NameID Format:** emailAddress

**3. Required Attributes:**
- email (required)
- firstName (optional)
- lastName (optional)
- groups (optional, for role mapping)

**4. Configure in Our Platform:**
Settings > Company > SSO > Manual Configuration
- SSO Login URL (from IdP)
- Entity ID (from IdP)
- X.509 Certificate (from IdP)

**5. Test & Enable:**
Test connection, then enable for production

**Need help with specific provider?**
Let me know: "Setup SSO with Okta/Azure/Google"

**Contact:** support@example.com for SSO assistance"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        agent = SSOSpecialist()
        state = create_initial_state(
            "How do I setup SSO with Okta?", context={"customer_metadata": {"plan": "enterprise"}}
        )
        result = await agent.process(state)
        print(f"Provider: {result.get('sso_provider')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
