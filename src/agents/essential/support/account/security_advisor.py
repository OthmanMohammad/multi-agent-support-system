"""
Security Advisor Agent - Provides security best practices, 2FA setup, and audit log guidance.
"""

from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("security_advisor", tier="essential", category="account")
class SecurityAdvisor(BaseAgent):
    """Security Advisor - Specialist in security configuration and best practices."""

    SECURITY_FEATURES = {
        "2fa": "Two-factor authentication",
        "sso": "Single Sign-On (Enterprise)",
        "session_timeout": "Auto-logout after inactivity",
        "ip_whitelist": "IP restrictions (Enterprise)",
        "audit_logs": "Security event logging",
        "password_policy": "Strong password requirements"
    }

    def __init__(self):
        config = AgentConfig(
            name="security_advisor",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("security_advisor_processing_started")
        state = self.update_state(state)
        
        message = state["current_message"]
        action = self._detect_security_action(message)
        
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results
        
        response = self._generate_security_guide(action)
        
        state["agent_response"] = response
        state["security_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"
        
        self.logger.info("security_processing_completed", action=action)
        return state

    def _detect_security_action(self, message: str) -> str:
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["2fa", "two factor", "authenticator"]):
            return "setup_2fa"
        elif any(word in msg_lower for word in ["audit", "log", "history", "activity"]):
            return "audit_review"
        elif any(word in msg_lower for word in ["score", "rating", "security check"]):
            return "security_score"
        return "best_practices"

    def _generate_security_guide(self, action: str) -> str:
        if action == "setup_2fa":
            return """**🔐 Set Up Two-Factor Authentication (2FA)**

**Step 1: Choose Authenticator App**
Recommended apps:
- **Authy** (multi-device sync)
- **Google Authenticator** (simple, secure)
- **1Password** (if you use password manager)

**Step 2: Enable 2FA**
Settings > Security > Two-Factor Authentication > Enable

**Step 3: Scan QR Code**
1. Open authenticator app
2. Scan QR code displayed
3. App generates 6-digit code

**Step 4: Verify & Save Backup Codes**
1. Enter 6-digit code
2. Save backup codes (print or download)
3. Store in safe place

**⚠️ IMPORTANT:**
- If you lose your phone, use backup codes
- Each backup code works once
- Generate new codes after using one

**Lost Your Phone?**
Use backup code to log in, then set up 2FA on new device

**Quick Setup:**
Settings > Security > 2FA > Enable"""

        elif action == "audit_review":
            return """**🔍 Security Audit Log Review**

**View Your Audit Logs:**
Settings > Security > Audit Logs

**What's Logged:**
✅ Login attempts (successful & failed)
✅ Password changes
✅ Team member changes
✅ Permission modifications
✅ API key usage
✅ Security settings changes

**Review Checklist:**

**1. Check Recent Logins:**
- Recognize all locations?
- All devices familiar?
- Any suspicious IPs?

**2. Monitor Failed Attempts:**
- Multiple failed logins?
- Unknown IP addresses?
- Unusual times/locations?

**3. Review Access Changes:**
- Team member additions
- Role modifications
- Permission updates

**Security Score:**
View your security score to identify improvement areas

**Download Logs:**
Settings > Security > Audit Logs > Export (CSV, JSON)

**Set Up Alerts:**
Get notified of suspicious activity automatically"""

        elif action == "security_score":
            return """**🛡️ Your Security Score**

**Improve Your Score (100 points max):**

**Account Security (40 points):**
- ✅ Strong password (20/20)
- ❌ 2FA not enabled (-20) 🔴 HIGH PRIORITY

**Access Control (30 points):**
- ✅ Team permissions configured (15/15)
- ⚠️ Session timeout too long (10/15)

**API & Keys (20 points):**
- ⚠️ 3 unused API keys (-5)
- ✅ API key rotation (15/15)

**Monitoring (10 points):**
- ✅ Audit logs reviewed (10/10)

**Your Score: 75/100**

**To Reach 100:**
1. **Enable 2FA** (+20 points) - Takes 2 min
2. **Reduce session timeout** (+5 points)
3. **Revoke unused API keys** (+5 points)

**Quick Actions:**
Settings > Security > Enable 2FA"""

        else:  # best_practices
            return """**🔒 Security Best Practices**

**Account Security:**

**1. Enable 2FA** ⚠️ HIGH PRIORITY
- Protects against 99.9% of account takeovers
- Use authenticator app (more secure than SMS)

**2. Use Strong Passwords**
- Minimum 12 characters
- Mix letters, numbers, symbols
- Use password manager
- Never reuse passwords

**3. Regular Password Updates**
- Change every 90 days
- Immediately if breach suspected

**API & Integration Security:**

**1. Rotate API Keys Regularly**
- Generate new keys every 90 days
- Delete unused keys immediately
- Never commit keys to Git

**2. Limit API Key Permissions**
- Use read-only when possible
- Scope keys to specific resources

**Team Security:**

**1. Principle of Least Privilege**
- Give minimum required access
- Use Viewer role for external users
- Regularly audit permissions

**2. Offboarding Checklist:**
- Remove from team immediately
- Revoke API keys they created
- Review their recent activity

**Security Score: 75/100**

**Quick Wins:**
✅ Enable 2FA (+20 points)
✅ Revoke unused API keys (+5)
✅ Reduce session timeout (+5)

**Start Here:**
Settings > Security > Enable 2FA"""

if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        agent = SecurityAdvisor()
        state = create_initial_state("How do I enable 2FA?")
        result = await agent.process(state)
        print(f"Action: {result.get('security_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
