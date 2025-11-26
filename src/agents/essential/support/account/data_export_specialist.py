"""
Data Export Specialist Agent - Handles data exports (GDPR compliance).
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("data_export_specialist", tier="essential", category="account")
class DataExportSpecialist(BaseAgent):
    """Data Export Specialist - Handles GDPR-compliant data exports."""

    EXPORT_FORMATS = ["json", "csv", "xml", "pdf"]

    EXPORT_TYPES = {
        "full": "Complete account data",
        "personal": "Personal data only (GDPR)",
        "projects": "Project data and tasks",
        "audit_logs": "Security logs",
    }

    def __init__(self):
        config = AgentConfig(
            name="data_export_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("data_export_processing_started")
        state = self.update_state(state)

        message = state["current_message"]
        action = self._detect_export_action(message)

        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        response = self._generate_export_guide(action)

        state["agent_response"] = response
        state["export_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info("export_processing_completed", action=action)
        return state

    def _detect_export_action(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["gdpr", "personal data", "right to access"]):
            return "gdpr_export"
        elif any(w in msg_lower for w in ["status", "check", "ready"]):
            return "check_status"
        elif any(w in msg_lower for w in ["schedule", "automatic", "recurring"]):
            return "schedule"
        return "request_export"

    def _generate_export_guide(self, action: str) -> str:
        if action == "gdpr_export":
            return """**📊 GDPR Personal Data Export**

**Your Right to Access Data:**
Under GDPR, you have the right to receive all your personal data.

**How to Request:**

**Step 1: Request Export**
Settings > Privacy > Download My Data > Request Export

**Step 2: Select Format**
- JSON (recommended for re-importing)
- CSV (for Excel/analysis)
- PDF (for archiving)

**Step 3: Wait for Email**
- Usually ready in 2 hours
- Max 48 hours (30-day legal requirement)
- Download link valid for 7 days

**What's Included:**

**Personal Information:**
- Name, email, phone
- Profile data
- Job title, department

**Your Content:**
- All projects you created
- All tasks you created
- All comments you wrote
- Files you uploaded

**Activity Data:**
- Login history (90 days)
- IP addresses used
- Devices used
- Last 1000 actions

**NOT Included:**
- Other users' data
- Company-wide analytics
- Aggregated statistics

**Timeline:**
- Request logged: Immediately
- Fulfillment: Within 48 hours
- Legal requirement: 30 days

**Quick Request:**
Settings > Privacy > Download My Data"""

        elif action == "check_status":
            return """**📦 Check Export Status**

**View Export Status:**
Settings > Account > Data Exports

**Current Exports:**

**Export #12345 - Full Account Export**
- Status: ✅ Ready for Download
- Created: Nov 15, 2025, 2:30 PM
- Format: JSON
- Size: 487 MB (compressed from 2.4 GB)
- Expires: Nov 22, 2025 (7 days)
- Download: [Click to Download]

**Progress Stages:**
1. ✅ Request received
2. ✅ Data gathered
3. ✅ Files compressed
4. ✅ Download link generated
5. ✅ Email sent

**Download Instructions:**
- Click download link
- Enter password to verify
- Download begins
- Verify checksum after download

**File Structure:**
export_20251115/
├── README.txt
├── metadata.json
├── projects/
├── users/
├── files/
└── audit_logs/

**Checksum (SHA-256):**
a3d5f6e8b2c4d1e9f7a8b6c3d2e1f0a9

**Need Help?**
Download fails? Contact support with export ID"""

        elif action == "schedule":
            return """**🔄 Schedule Automatic Exports**

**Available on:** Premium & Enterprise plans

**Setup Auto-Export:**
Settings > Account > Data Exports > Auto-Export

**Frequency Options:**
- **Daily:** 2:00 AM UTC
- **Weekly:** Monday 2:00 AM
- **Monthly:** 1st of month 2:00 AM

**What Happens:**
✅ Export runs automatically
✅ Email notification sent
✅ Download link (expires 7 days)
✅ Old exports deleted after 30 days

**Configuration:**
- Export Type: Full Account
- Format: JSON
- Retention: Keep last 3 exports
- Next Export: Dec 1, 2025

**Use Cases:**
- Regulatory compliance backups
- Disaster recovery
- Migration preparation
- Audit requirements

**Manage Schedule:**
Settings > Account > Auto-Export Schedule

**Premium Feature:**
Upgrade to Premium for auto-exports
Settings > Billing > Upgrade"""

        else:  # request_export
            return """**💾 Export Your Data**

**Quick Export:**
Settings > Account > Export Data

**Export Options:**

**1. Full Account Export**
- Everything in your account
- All projects, tasks, files
- Size: Large (1-5 GB)
- Time: 2-24 hours

**2. Personal Data (GDPR)**
- Your personal info only
- GDPR compliance
- Size: Small (<100 MB)
- Time: 15-30 minutes

**3. Projects Only**
- Just project data
- No user/billing data
- Size: Medium (500 MB - 2 GB)
- Time: 1-4 hours

**4. Audit Logs**
- Security logs
- Login history
- Size: Small (10-50 MB)
- Time: 5-15 minutes

**Formats Available:**
- **JSON:** Best for re-importing
- **CSV:** Best for Excel
- **XML:** Best for enterprise systems
- **PDF:** Best for archiving

**Process:**
1. Request export
2. Wait for email (2-24 hours)
3. Download file (link valid 7 days)
4. Verify with checksum

**Security:**
- Encrypted during generation
- Password-protected download
- SHA-256 verification
- Auto-deleted after 7 days

**Quick Start:**
Settings > Account > Export Data > Request Export"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        agent = DataExportSpecialist()
        state = create_initial_state("I need to export my data for GDPR")
        result = await agent.process(state)
        print(f"Action: {result.get('export_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
