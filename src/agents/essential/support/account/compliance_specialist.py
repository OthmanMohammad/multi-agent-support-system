"""
Compliance Specialist Agent - Handles GDPR, CCPA, and compliance requests.
"""

from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("compliance_specialist", tier="essential", category="account")
class ComplianceSpecialist(BaseAgent):
    """Compliance Specialist - Handles GDPR, CCPA, and regulatory compliance."""

    SUPPORTED_REGULATIONS = {
        "gdpr": "General Data Protection Regulation (EU)",
        "ccpa": "California Consumer Privacy Act (US)",
        "hipaa": "Health Insurance Portability (US)",
        "soc2": "SOC 2 Compliance",
        "iso27001": "ISO 27001 Information Security"
    }

    GDPR_RIGHTS = {
        "access": "Right to access data",
        "rectification": "Right to correct data",
        "erasure": "Right to be forgotten",
        "portability": "Right to transfer data",
        "restrict": "Right to restrict processing",
        "object": "Right to object to processing"
    }

    def __init__(self):
        config = AgentConfig(
            name="compliance_specialist",
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
        self.logger.info("compliance_processing_started")
        state = self.update_state(state)
        
        message = state["current_message"]
        action = self._detect_compliance_action(message)
        
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results
        
        response = self._generate_compliance_guide(action)
        
        state["agent_response"] = response
        state["compliance_action"] = action
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"
        
        self.logger.info("compliance_processing_completed", action=action)
        return state

    def _detect_compliance_action(self, message: str) -> str:
        msg_lower = message.lower()
        if "gdpr" in msg_lower:
            return "gdpr_request"
        elif "ccpa" in msg_lower or "california" in msg_lower:
            return "ccpa_request"
        elif any(w in msg_lower for w in ["dpa", "data processing agreement"]):
            return "dpa"
        elif any(w in msg_lower for w in ["soc", "iso", "certification", "certified"]):
            return "certifications"
        return "overview"

    def _generate_compliance_guide(self, action: str) -> str:
        if action == "gdpr_request":
            return """**📋 GDPR Data Subject Rights**

**Your GDPR Rights:**

**1. Right to Access (DSAR)**
- Request all your personal data
- Receive within 30 days (we aim for 48h)
- Settings > Privacy > Download My Data

**2. Right to Rectification**
- Correct inaccurate data
- Settings > Profile > Edit

**3. Right to Erasure ("Right to be Forgotten")**
- Delete your personal data
- Settings > Account > Delete Account
- 30-day grace period

**4. Right to Data Portability**
- Export data in machine-readable format
- JSON, CSV, XML formats
- Settings > Export Data

**5. Right to Restrict Processing**
- Limit how we use your data
- Settings > Privacy > Restrict Processing

**6. Right to Object**
- Object to data processing
- Contact: privacy@example.com

**How to Exercise Rights:**
1. Submit request via Settings
2. Verify your identity
3. Fulfillment within 30 days
4. Confirmation email sent

**GDPR Compliance:**
- Request logged immediately
- Fulfillment: 48 hours (30 days legal)
- All actions audit-logged

**Contact Data Protection Officer:**
Email: dpo@example.com (EU customers)

**Quick Access:**
Settings > Privacy > GDPR Rights"""

        elif action == "ccpa_request":
            return """**📋 CCPA Rights (California Residents)**

**Your CCPA Rights:**

**1. Right to Know**
- What data we collect
- How we use it
- Who we share with
- Settings > Privacy > Download My Data

**2. Right to Delete**
- Request deletion of personal data
- Settings > Account > Delete Account
- Fulfilled within 45 days

**3. Right to Opt-Out of Sale**
- **We DO NOT sell your data**
- We never have and never will
- No action needed

**4. Right to Non-Discrimination**
- Same price and service
- No retaliation for exercising rights

**Data We Collect:**
✅ Identifiers (name, email)
✅ Commercial info (subscription)
✅ Internet activity (usage)
✅ Geolocation (IP-based)

**Data We DON'T Collect:**
❌ Social Security number
❌ Financial account numbers
❌ Medical information
❌ Biometric data

**Data NOT Sold:**
We do NOT sell to advertisers or data brokers

**How to Exercise Rights:**
1. Settings > Privacy > CCPA Request
2. Verify identity
3. Fulfillment within 45 days

**Contact:**
Email: privacy@example.com
Phone: 1-800-PRIVACY

**Quick Access:**
Settings > Privacy > CCPA Rights"""

        elif action == "dpa":
            return """**📄 Data Processing Agreement (DPA)**

**For GDPR Compliance - Article 28**

**Download DPA:**
https://legal.example.com/dpa.pdf
Format: PDF (signed)
Last updated: January 1, 2025

**Key Terms:**

**1. Roles:**
- Controller: You (the customer)
- Processor: Us (the service)

**2. Data Processing Scope:**
- Only as instructed by you
- For providing the service
- Not for our own purposes

**3. Security Measures:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Access controls (RBAC)
- Regular security audits

**4. Sub-processors:**
- AWS (hosting) - USA
- Stripe (payments) - USA
- SendGrid (email) - USA
Full list: https://example.com/subprocessors

**5. Data Breach Notification:**
- We notify you within 24 hours
- Provide details for GDPR reporting
- Assist with notification obligations

**6. Data Subject Rights:**
- We assist with DSAR requests
- Tools for data export
- Support for deletion requests

**7. Audit Rights:**
- You can audit our compliance
- SOC 2 reports available
- Annual third-party audits

**Standard Contractual Clauses (SCCs):**
For EU-US transfers
EU Commission approved
https://legal.example.com/sccs.pdf

**Download Documents:**
- DPA (signed): https://legal.example.com/dpa.pdf
- SCCs: https://legal.example.com/sccs.pdf
- Sub-processors: https://example.com/subprocessors

**Custom DPA:**
Enterprise customers can request custom terms
Contact: legal@example.com"""

        elif action == "certifications":
            return """**🏆 Compliance Certifications**

**Our Certifications:**

**SOC 2 Type II** ✅
- Status: Certified
- Report Date: December 2024
- Valid Until: December 2025
- Auditor: BigFour Auditing
- Trust Criteria: Security, Availability, Confidentiality

**Download Report:**
https://compliance.example.com/soc2
Requirements: NDA required
Contact: compliance@example.com

**ISO 27001:2013** ✅
- Status: Certified
- Certificate #: ISO27001-2024-ABC123
- Issued: January 2024
- Valid Until: January 2027
- Scope: Information Security Management

**Download Certificate:**
https://compliance.example.com/iso27001.pdf
Public document - no restrictions

**GDPR Compliant** ✅
- EU General Data Protection Regulation
- Privacy by design
- Data processing agreement
- DPO appointed for EU customers

**CCPA Compliant** ✅
- California Consumer Privacy Act
- Consumer rights portal
- Do not sell personal info

**HIPAA-Ready** ⚠️
- Note: No official HIPAA certification exists
- BAA available for healthcare customers
- HIPAA-compliant infrastructure
- Contact: hipaa@example.com

**Security Standards:**
- Encryption: AES-256 (rest), TLS 1.3 (transit)
- Access Control: RBAC, MFA
- Monitoring: 24/7 security operations
- Audits: Annual penetration testing

**Request Certification Documents:**
Email: compliance@example.com
Include: Company name, reason, NDA (for SOC 2)"""

        else:  # overview
            return """**📋 Compliance & Privacy Overview**

**Regulations We Comply With:**
- GDPR (EU)
- CCPA (California)
- SOC 2 Type II
- ISO 27001:2013
- HIPAA-ready (with BAA)

**Your Data Rights:**

**Under GDPR & CCPA:**
✅ Access your data
✅ Correct your data
✅ Delete your data
✅ Export your data
✅ Restrict processing
✅ Object to processing

**Our Certifications:**
✅ SOC 2 Type II (Security, Availability)
✅ ISO 27001:2013 (Information Security)
✅ GDPR Compliant
✅ CCPA Compliant
✅ HIPAA-ready (with BAA)

**Data Protection:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Regular security audits
- 24/7 security monitoring

**Privacy Practices:**
- Privacy by design
- Data minimization
- Transparent processing
- User control

**Legal Documents:**
- Privacy Policy: https://example.com/privacy
- Terms of Service: https://example.com/terms
- DPA: https://legal.example.com/dpa
- Cookie Policy: https://example.com/cookies

**Common Requests:**

**1. Access My Data (DSAR):**
Settings > Privacy > Download My Data

**2. Delete My Data:**
Settings > Account > Delete Account

**3. Export My Data:**
Settings > Account > Export Data

**4. Get DPA/BAA:**
https://legal.example.com/dpa

**5. SOC 2 Report:**
Email: compliance@example.com (NDA required)

**Contact:**
Privacy: privacy@example.com
Compliance: compliance@example.com
DPO: dpo@example.com (EU customers)
Security: security@example.com

**Quick Access:**
Settings > Privacy > Compliance"""

if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        agent = ComplianceSpecialist()
        state = create_initial_state("What are my GDPR rights?")
        result = await agent.process(state)
        print(f"Action: {result.get('compliance_action')}")
        print(f"Response: {result['agent_response'][:200]}...")

    asyncio.run(test())
