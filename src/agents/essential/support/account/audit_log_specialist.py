"""
Audit Log Specialist Agent - Helps search, explain, and analyze audit logs.
"""

from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("audit_log_specialist", tier="essential", category="account")
class AuditLogSpecialist(BaseAgent):
    """Audit Log Specialist - Specialist in security audit logs and analysis."""

    EVENT_TYPES = {
        "auth": "Authentication events (login, logout, 2FA)",
        "user": "User management (create, update, delete)",
        "permission": "Permission changes (role changes)",
        "data": "Data access and modifications",
        "security": "Security events (failed logins)",
        "api": "API access and key usage",
        "billing": "Billing changes",
        "settings": "Account settings changes"
    }

    RETENTION_PERIODS = {
        "free": 30,
        "basic": 30,
        "premium": 90,
        "enterprise": 365
    }

    def __init__(self):
        config = AgentConfig(
            name="audit_log_specialist",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("audit_log_processing_started")
        state = self.update_state(state)
        
        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        plan = customer_context.get("plan", "free")
        action = self._detect_audit_action(message)
        
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results
        
        response = self._generate_audit_guide(action, plan)
        
        state["agent_response"] = response
        state["audit_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"
        
        self.logger.info("audit_processing_completed", action=action)
        return state

    def _detect_audit_action(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["search", "find", "look for", "filter"]):
            return "search"
        elif any(w in msg_lower for w in ["explain", "what is", "details"]):
            return "explain"
        elif any(w in msg_lower for w in ["export", "download", "save"]):
            return "export"
        elif any(w in msg_lower for w in ["alert", "notify", "notification"]):
            return "setup_alerts"
        elif any(w in msg_lower for w in ["summary", "overview", "report"]):
            return "summary"
        return "guide"

    def _generate_audit_guide(self, action: str, plan: str) -> str:
        retention_days = self.RETENTION_PERIODS.get(plan, 30)

        if action == "search":
            return f"""**🔍 Search Audit Logs**

**Access Logs:**
Settings > Security > Audit Logs

**Your Plan:** {plan.title()}
**Retention:** Last {retention_days} days

**Search Options:**

**By Event Type:**
- Authentication: Logins, logouts, 2FA
- User Management: Member changes
- Permissions: Role changes
- Security: Failed logins, suspicious activity
- API: API key usage

**By User:**
Search: "user:john@example.com"
Shows all actions by or affecting john

**By IP Address:**
Search: "ip:203.0.113.42"
Shows all events from this IP

**By Date Range:**
Search: "date:2025-11-01 to 2025-11-15"
Custom date range

**Recent Events (Example):**

1. ⚠️ **Failed Login Attempt**
   - Date: Nov 15, 2025, 2:30 AM
   - User: john@example.com
   - IP: 203.0.113.42 (Moscow, Russia)
   - Action: Auto-locked after 5 attempts

2. ✅ **Password Changed**
   - Date: Nov 15, 2025, 9:15 AM
   - User: john@example.com
   - IP: 192.0.2.1 (San Francisco)
   - Verification: Email sent

**Export Results:**
Settings > Security > Audit Logs > Export (CSV, JSON)

**Setup Alerts:**
Get notified of suspicious activity automatically

**Filter by Severity:**
- 🔴 Critical (immediate attention)
- 🟡 Warning (review soon)
- 🟢 Info (normal activity)

**Quick Search:**
Settings > Security > Audit Logs > Search"""

        elif action == "explain":
            return """**📖 Understanding Audit Log Events**

**Common Event Types:**

**Authentication Events:**
- **login.success:** Successful login
- **login.failed:** Failed login attempt
- **2fa.enabled:** 2FA activated
- **password.changed:** Password updated

**User Management:**
- **user.created:** New user added
- **user.deleted:** User removed
- **user.role_changed:** Role modified

**Security Events:**
- **account.locked:** Auto-locked (5 failed attempts)
- **suspicious_ip:** Login from unusual location
- **api_key.created:** New API key generated
- **api_key.revoked:** API key deleted

**Event Details:**

**Event ID:** evt_abc123
**Timestamp:** 2025-11-15 02:30:45 UTC
**Event Type:** login.failed
**Severity:** WARNING

**What Happened:**
Failed login attempt from unusual location

**Details:**
- User: john@example.com
- IP: 203.0.113.42
- Location: Moscow, Russia
- Device: Chrome on Windows
- Attempt: 3 of 5

**Context:**
- Previous attempts: 2:28 AM, 2:29 AM
- Account locked: 2:32 AM (automatic)
- Email sent: 2:35 AM

**Risk Assessment:**
🔴 HIGH - Unusual location, multiple attempts

**Actions Taken:**
✅ Account locked
✅ Security email sent
✅ IP flagged

**Recommended:**
- Review recent activity
- Change password if suspicious
- Enable 2FA

**View Full Event:**
Settings > Security > Audit Logs > Event Details"""

        elif action == "export":
            return f"""**💾 Export Audit Logs**

**How to Export:**
Settings > Security > Audit Logs > Export

**Export Options:**

**Format:**
- CSV - For Excel/analysis
- JSON - For SIEM integration
- PDF - For archival

**Date Range:**
- Last 7 days
- Last 30 days
- Last {retention_days} days (your plan limit)
- Custom range

**Event Types:**
- All events
- Authentication only
- Security events only
- Custom selection

**What's Included:**
- Timestamp (UTC)
- Event ID
- Event type
- Actor (who did it)
- Target (what was affected)
- IP address & location
- Device information
- Result (success/failure)
- Metadata

**File Format (CSV Example):**
timestamp,event_id,type,actor,ip,location,result
2025-11-15 02:30:45,evt_123,login.failed,john@...,203.0.113.42,Moscow,failed

**Use Cases:**
- Compliance audits (SOC 2, ISO 27001)
- Security investigations
- SIEM integration
- Archival and retention
- Forensic analysis

**SIEM Integration:**
Export for popular tools:
- Splunk (JSON)
- ELK Stack (JSON)
- Datadog (JSON)
- Azure Sentinel (CSV)

**Scheduled Exports:** (Premium/Enterprise)
Settings > Security > Auto-Export
- Daily, Weekly, Monthly
- Email, S3, SFTP

**Quick Export:**
Settings > Security > Audit Logs > Export"""

        elif action == "setup_alerts":
            return """**🔔 Setup Audit Log Alerts**

**Configure Alerts:**
Settings > Security > Audit Logs > Alerts

**What You'll Be Alerted About:**

**Critical Security Events:**
🔴 Failed login attempts (5+ in 1 hour)
🔴 Account lockouts
🔴 Password changes from new devices
🔴 2FA disabled
🔴 API keys created/deleted

**Suspicious Activity:**
🟡 Logins from unusual locations
🟡 Logins at unusual times
🟡 Multiple failed API requests
🟡 Team member deletions

**Important Changes:**
🔵 Team members added/removed
🔵 Billing changes
🔵 Role changes
🔵 Settings modifications

**Alert Delivery:**

**Email:**
- Immediate (critical)
- Daily digest (others)

**Slack:**
- Real-time to #security channel

**In-App:**
- Notification center

**SMS:** (Enterprise only)

**Example Alert:**

📧 **Email Alert (Critical):**
Subject: 🔴 SECURITY ALERT: Failed Login Attempts

5 failed attempts for john@example.com
IP: 203.0.113.42 (Moscow, Russia)
Action: Account locked

[View Details] [Investigate]

**Alert Rules:**

**Predefined:**
✅ Multiple failed logins (3+ in 1 hour)
✅ Login from new country
✅ API key created
✅ Team member with admin added
✅ SSO changes

**Custom Rules:** (Enterprise)
Create your own alert conditions

**Manage Alerts:**
- Enable/disable specific alerts
- Change notification channels
- Adjust thresholds
- Snooze temporarily

**Quick Setup:**
Settings > Security > Alerts > Enable All"""

        elif action == "summary":
            return f"""**📊 Security Summary - Last 30 Days**

**Overview:**
- Total Events: 2,450
- Critical: 3 (0.1%) ⚠️
- Warnings: 47 (1.9%)
- Normal: 2,400 (98%)

**🔴 Critical Events (3):**

1. **Failed Login Attempts → Locked**
   - Date: Nov 15
   - User: john@example.com
   - Attempts: 5 from Russia
   - Status: ✅ Resolved (password changed, 2FA enabled)

2. **API Key Exposed**
   - Date: Nov 8
   - Key: api_xyz789
   - Detection: GitHub scanner
   - Status: ✅ Key revoked, new key generated

3. **Unusual Data Export**
   - Date: Nov 3
   - User: contractor@example.com
   - Size: 2.4 GB
   - Status: ✅ Verified legitimate

**Activity Breakdown:**

**Authentication:**
- Successful logins: 1,247
- Failed logins: 23 (1.8%)
- 2FA challenges: 342
- Password changes: 8

**User Management:**
- Members added: 5
- Members removed: 2
- Role changes: 6

**API Activity:**
- API calls: 45,234
- Failed requests: 234 (0.5%)
- Rate limits hit: 18

**Geographic Activity:**
- San Francisco, CA: 65%
- New York, NY: 20%
- London, UK: 10%
- Other: 5%

**Security Score: 75/100**

**Improvements:**
⚠️ Enable 2FA for all users (+15)
⚠️ Reduce API errors (+5)
⚠️ Review contractor access (+5)

**Recommendations:**
1. Enforce 2FA (12 users without)
2. Investigate API errors
3. Review external access

**Export Report:**
Settings > Security > Summary > Export PDF"""

        else:  # guide
            return f"""**📋 Audit Log Guide**

**What Are Audit Logs?**
Complete record of security-relevant events in your account.

**Access Logs:**
Settings > Security > Audit Logs

**Your Plan:** {plan.title()}
**Retention:** {retention_days} days

**What's Logged:**
- Authentication events
- User management
- Permission changes
- Data access
- Security events
- API usage
- Settings changes

**Common Use Cases:**

**1. Security Investigation**
Search for suspicious activity
Review failed login attempts
Investigate unusual access patterns

**2. Compliance Audit**
Export for SOC 2, ISO 27001
GDPR compliance verification
Annual security reviews

**3. User Activity Review**
Track specific user actions
Offboarding checklist
Access control audit

**4. Permission Changes**
Review role modifications
Verify authorized changes
Audit access grants

**Search Examples:**

**By Event Type:**
- "login.failed" - Failed logins
- "user.created" - New users
- "api.key.created" - API keys

**By User:**
- "user:john@example.com"

**By Date:**
- "date:2025-11-01 to 2025-11-15"

**By IP:**
- "ip:203.0.113.42"

**Best Practices:**
✅ Weekly security reviews
✅ Monthly exports for compliance
✅ Enable security alerts
✅ Investigate all critical events

**Quick Actions:**
- Search Logs: Settings > Security > Audit Logs
- Export Logs: Settings > Security > Export
- Setup Alerts: Settings > Security > Alerts

**Need Help?**
- Search specific events
- Explain event details
- Setup automated alerts
- Export for compliance"""

if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        agent = AuditLogSpecialist()
        state = create_initial_state(
            "How do I search audit logs?",
            context={"customer_metadata": {"plan": "premium"}}
        )
        result = await agent.process(state)
        print(f"Action: {result.get('audit_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
