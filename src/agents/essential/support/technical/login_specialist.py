"""
Login Specialist Agent - Resolves login and authentication issues.

Specialist for password resets, account unlocks, 2FA issues, SSO problems.
"""

from typing import Dict, Any, Optional

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("login_specialist", tier="essential", category="technical")
class LoginSpecialist(BaseAgent):
    """
    Login Specialist Agent - Specialist for authentication issues.

    Handles:
    - Password resets
    - Account lockouts
    - 2FA/MFA issues
    - SSO problems
    - Session management
    """

    def __init__(self):
        config = AgentConfig(
            name="login_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE
            ],
            kb_category="account",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process login issue requests"""
        self.logger.info("login_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_email = state.get("customer_metadata", {}).get("email", state.get("customer_id"))

        self.logger.debug(
            "login_issue_processing_started",
            message_preview=message[:100],
            customer_email=customer_email,
            turn_count=state["turn_count"]
        )

        # Detect login issue type
        login_issue = self._detect_login_issue(message)

        self.logger.info(
            "login_issue_detected",
            issue_type=login_issue
        )

        # Handle the specific login issue
        if login_issue == "forgot_password":
            response = await self._handle_password_reset(customer_email)
        elif login_issue == "locked":
            response = await self._unlock_account(customer_email)
        elif login_issue == "2fa_issue":
            response = self._handle_2fa_issue(customer_email)
        elif login_issue == "sso_issue":
            response = self._handle_sso_issue(message)
        elif login_issue == "session_expired":
            response = self._handle_session_issue()
        else:
            response = await self._diagnose_login_issue(customer_email, message)

        # Search KB for login help
        kb_results = await self.search_knowledge_base(
            message,
            category="account",
            limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "login_kb_articles_found",
                count=len(kb_results)
            )

        formatted_response = self._format_response(response, kb_results)

        state["agent_response"] = formatted_response
        state["login_issue_type"] = login_issue
        state["login_action_taken"] = response.get("action")
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "login_issue_resolved",
            issue_type=login_issue,
            action=response.get("action"),
            status="resolved"
        )

        return state

    def _detect_login_issue(self, message: str) -> str:
        """Detect the type of login issue"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["forgot password", "reset password", "can't remember password"]):
            return "forgot_password"
        elif any(word in message_lower for word in ["locked", "locked out", "too many attempts"]):
            return "locked"
        elif any(word in message_lower for word in ["2fa", "two factor", "authenticator", "verification code"]):
            return "2fa_issue"
        elif any(word in message_lower for word in ["sso", "single sign", "saml", "oauth"]):
            return "sso_issue"
        elif any(word in message_lower for word in ["session", "logged out", "keep logging out"]):
            return "session_expired"
        else:
            return "unknown"

    async def _handle_password_reset(self, email: str) -> Dict[str, Any]:
        """Send password reset email"""
        self.logger.info(
            "password_reset_initiated",
            email=email
        )

        # In production: Call auth API to send reset email
        # auth_service.send_password_reset(email)

        message = f"""I've sent a password reset link to **{email}**.

**Next steps:**
1. Check your email (including spam folder)
2. Click the reset link (valid for 1 hour)
3. Create a new password

**Password requirements:**
- At least 8 characters
- Include uppercase letter (A-Z)
- Include lowercase letter (a-z)
- Include number (0-9)
- Include special character (!@#$%^&*)

**Haven't received it?**
Let me know and I'll resend it. If you don't see it after 5 minutes, check:
- Spam/junk folder
- Email address is correct
- Email filters"""

        return {
            "message": message,
            "action": "password_reset_sent"
        }

    async def _unlock_account(self, email: str) -> Dict[str, Any]:
        """Unlock locked account"""
        self.logger.info(
            "account_unlock_initiated",
            email=email
        )

        # In production: Call auth API to unlock account
        # auth_service.unlock_account(email)

        message = f"""I've unlocked your account for **{email}**.

**What happened:**
Your account was locked after 5 failed login attempts (security measure).

**You can now:**
1. Try logging in again
2. If you forgot your password, click "Forgot Password"
3. Use the correct email and password

**Security tips:**
- Enable 2FA (two-factor authentication) for extra security
- Use a strong, unique password
- Consider using a password manager
- Don't share your password

**Still can't log in?**
Let me know and I can:
- Send a password reset link
- Check if there are other issues
- Verify your account details"""

        return {
            "message": message,
            "action": "account_unlocked"
        }

    def _handle_2fa_issue(self, email: str) -> Dict[str, Any]:
        """Handle 2FA problems"""
        self.logger.info(
            "2fa_issue_handling_started",
            email=email
        )

        message = """Having trouble with two-factor authentication?

**Common issues:**

**1. Lost your phone/authenticator app?**
- Use backup codes (check your email or account settings)
- If no backup codes, I can disable 2FA (requires identity verification)

**2. Not receiving codes?**
- Check authenticator app time sync (Settings > Time sync)
- Ensure app notifications are enabled
- Try SMS backup method (if configured)
- Regenerate codes

**3. Wrong codes?**
- Make sure device time is correct (2FA is time-based)
- Try generating a new code
- Wait 30 seconds for code to refresh

**4. Lost backup codes?**
- I can generate new backup codes (requires verification)

**Disable 2FA temporarily:**
I can disable 2FA so you can log in, but I'll need to verify your identity first:
- Security questions, OR
- Email verification, OR
- Support ticket with ID

Would you like me to disable 2FA? (You can re-enable it after logging in)"""

        return {
            "message": message,
            "action": "2fa_troubleshooting_provided"
        }

    def _handle_sso_issue(self, message: str) -> Dict[str, Any]:
        """Handle SSO/SAML issues"""
        self.logger.info("sso_issue_handling_started")

        response_message = """SSO (Single Sign-On) troubleshooting:

**Common SSO issues:**

**1. "Access Denied" or "Not Authorized"**
- Contact your IT admin - they need to grant you access
- You may not be in the correct user group
- SSO configuration may be incomplete

**2. Redirect loop or infinite redirect**
- Clear browser cookies and cache
- Try incognito/private mode
- Contact IT admin - SSO settings may need adjustment

**3. "Invalid SAML Response"**
- SSO configuration issue on your org's side
- IT admin needs to check SAML settings
- Certificate may be expired

**4. Can't find SSO login page**
- Use your company's specific SSO URL
- Don't use the regular login page
- Ask IT admin for the correct URL

**Quick fixes to try:**
1. Clear browser cookies
2. Try incognito mode
3. Use different browser
4. Check with IT admin

**For IT Admins:**
If you're setting up SSO, you'll need:
- SAML metadata URL
- Entity ID
- ACS URL
- Certificate

Would you like me to escalate this to our SSO support team?"""

        return {
            "message": response_message,
            "action": "sso_troubleshooting_provided"
        }

    def _handle_session_issue(self) -> Dict[str, Any]:
        """Handle session expiration issues"""
        self.logger.info("session_issue_handling_started")

        message = """Being logged out frequently? Here's how to fix it:

**Common causes:**

**1. Session timeout**
- Sessions expire after 24 hours of inactivity
- Solution: Check "Remember me" when logging in

**2. Browser settings**
- Cookies are being cleared automatically
- Privacy mode/incognito always logs you out
- Solution: Allow cookies for our site

**3. Multiple devices**
- Logging in elsewhere logs you out here
- Solution: Enable "multiple sessions" in Settings

**4. Browser extensions**
- Privacy extensions may clear cookies
- Ad blockers may interfere
- Solution: Whitelist our site

**Quick fixes:**
1. **Check "Remember me"** when logging in
2. **Allow cookies** for our domain
3. **Disable privacy mode** for our site
4. **Stay logged in** setting (Settings > Security)

**For organizations:**
Your IT admin can configure session timeout in Settings > Security > Session Management

Would you like me to enable "stay logged in" for your account?"""

        return {
            "message": message,
            "action": "session_troubleshooting_provided"
        }

    async def _diagnose_login_issue(self, email: str, message: str) -> Dict[str, Any]:
        """Diagnose general login issue"""
        self.logger.info("general_login_diagnosis_started")

        response_message = f"""Let me help you troubleshoot your login issue.

**Quick diagnostics:**

**1. Check your credentials**
- Email: {email}
- Password: (try resetting if unsure)

**2. Common issues:**
- Caps Lock is on
- Wrong email address
- Account doesn't exist
- Account not activated

**3. Browser issues:**
- Clear cookies and cache
- Try incognito mode
- Update your browser
- Disable extensions

**Try this:**
1. Go to login page
2. Click "Forgot Password"
3. Enter: {email}
4. Check email for reset link
5. Create new password

**Still can't log in?**

Tell me which error you're seeing:
- "Invalid email or password"
- "Account not found"
- "Account locked"
- "Too many attempts"
- Something else

I can help once I know the specific error!"""

        return {
            "message": response_message,
            "action": "diagnosis_provided"
        }

    def _format_response(self, response: Dict[str, Any], kb_results: list) -> str:
        """Format response with KB context"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n**Related help articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"

        return response["message"] + kb_context


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Forgot password
        print("=" * 60)
        print("Test 1: Forgot password")
        print("=" * 60)

        state = create_initial_state("I forgot my password")
        state["customer_metadata"] = {"email": "test@example.com"}

        agent = LoginSpecialist()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Issue type: {result.get('login_issue_type')}")
        print(f"Action: {result.get('login_action_taken')}")

        # Test 2: Account locked
        print("\n" + "=" * 60)
        print("Test 2: Account locked")
        print("=" * 60)

        state2 = create_initial_state("My account is locked after too many login attempts")
        state2["customer_metadata"] = {"email": "user@example.com"}

        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Issue type: {result2.get('login_issue_type')}")

        # Test 3: 2FA issue
        print("\n" + "=" * 60)
        print("Test 3: 2FA issue")
        print("=" * 60)

        state3 = create_initial_state("I lost my authenticator app")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")
        print(f"Issue type: {result3.get('login_issue_type')}")

    asyncio.run(test())
