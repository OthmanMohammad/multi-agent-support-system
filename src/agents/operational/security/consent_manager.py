"""
Consent Manager Agent - TASK-2308

Manages GDPR/CCPA consent and data subject rights.
Handles consent tracking, opt-out mechanisms, and data access requests.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("consent_manager", tier="operational", category="security")
class ConsentManagerAgent(BaseAgent):
    """
    Consent Manager Agent.

    Comprehensive consent and data rights management:
    - Consent capture and tracking
    - Purpose-specific consent (GDPR Article 6)
    - Consent withdrawal processing
    - Data subject access requests (DSAR)
    - Right to erasure (GDPR Article 17)
    - Right to portability (GDPR Article 20)
    - Right to rectification (GDPR Article 16)
    - Opt-out mechanism (CCPA)
    - Marketing preferences
    - Cookie consent management

    Compliance:
    - GDPR: Explicit consent, granular purposes
    - CCPA: Opt-out of sale, do not sell
    - DSAR response: 30 days (GDPR), 45 days (CCPA)
    """

    # Consent purposes
    CONSENT_PURPOSES = {
        "essential": {
            "name": "Essential Services",
            "description": "Required for service functionality",
            "required": True,
            "default": True
        },
        "analytics": {
            "name": "Analytics & Performance",
            "description": "Usage analytics and performance monitoring",
            "required": False,
            "default": False
        },
        "marketing": {
            "name": "Marketing Communications",
            "description": "Promotional emails and offers",
            "required": False,
            "default": False
        },
        "personalization": {
            "name": "Personalization",
            "description": "Personalized content and recommendations",
            "required": False,
            "default": False
        },
        "third_party_sharing": {
            "name": "Third-Party Sharing",
            "description": "Sharing data with partners",
            "required": False,
            "default": False
        }
    }

    # Data subject rights
    DATA_SUBJECT_RIGHTS = [
        "access",          # GDPR Article 15
        "rectification",   # GDPR Article 16
        "erasure",         # GDPR Article 17 (Right to be forgotten)
        "portability",     # GDPR Article 20
        "restriction",     # GDPR Article 18
        "objection",       # GDPR Article 21
        "opt_out_sale"     # CCPA
    ]

    # DSAR response timeline
    DSAR_RESPONSE_SLA = {
        "GDPR": timedelta(days=30),
        "CCPA": timedelta(days=45)
    }

    def __init__(self):
        config = AgentConfig(
            name="consent_manager",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2500,
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process consent and data rights request.

        Args:
            state: Current agent state with consent/rights request

        Returns:
            Updated state with processing results
        """
        self.logger.info("consent_management_started")

        state = self.update_state(state)

        # Extract parameters
        request_type = state.get("entities", {}).get("request_type", "consent_update")
        user_id = state.get("entities", {}).get("user_id", "unknown")
        consent_preferences = state.get("entities", {}).get("consent_preferences", {})
        dsar_type = state.get("entities", {}).get("dsar_type")  # access, erasure, portability
        jurisdiction = state.get("entities", {}).get("jurisdiction", "GDPR")  # GDPR or CCPA

        self.logger.debug(
            "consent_management_details",
            request_type=request_type,
            user_id=user_id,
            jurisdiction=jurisdiction
        )

        # Process based on request type
        if request_type == "consent_update":
            result = self._process_consent_update(user_id, consent_preferences)
        elif request_type == "consent_withdrawal":
            result = self._process_consent_withdrawal(user_id, consent_preferences)
        elif request_type == "dsar":
            result = self._process_dsar(user_id, dsar_type, jurisdiction)
        elif request_type == "opt_out":
            result = self._process_opt_out(user_id, jurisdiction)
        else:
            result = {"status": "error", "message": "Unknown request type"}

        # Validate consent state
        consent_valid = self._validate_consent_state(user_id, result)

        # Check compliance
        compliance_check = self._check_compliance(result, jurisdiction)

        # Generate audit trail
        audit_entry = self._create_audit_entry(
            request_type,
            user_id,
            result,
            jurisdiction
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            request_type,
            result,
            compliance_check
        )

        # Format response
        response = self._format_consent_report(
            request_type,
            user_id,
            result,
            consent_valid,
            compliance_check,
            audit_entry,
            recommendations
        )

        state["agent_response"] = response
        state["consent_result"] = result
        state["consent_valid"] = consent_valid
        state["compliance_check"] = compliance_check
        state["audit_entry"] = audit_entry
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.97
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "consent_management_completed",
            request_type=request_type,
            user_id=user_id,
            status=result.get("status")
        )

        return state

    def _process_consent_update(
        self,
        user_id: str,
        consent_preferences: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Process consent preference update.

        Args:
            user_id: User ID
            consent_preferences: Updated consent preferences

        Returns:
            Processing result
        """
        updated_consents = {}

        for purpose, granted in consent_preferences.items():
            if purpose in self.CONSENT_PURPOSES:
                purpose_def = self.CONSENT_PURPOSES[purpose]

                # Cannot withdraw essential consent
                if purpose_def["required"] and not granted:
                    return {
                        "status": "error",
                        "message": f"Cannot withdraw consent for essential purpose: {purpose}",
                        "purpose": purpose
                    }

                updated_consents[purpose] = {
                    "granted": granted,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "purpose": purpose_def["name"],
                    "description": purpose_def["description"]
                }

        return {
            "status": "success",
            "message": "Consent preferences updated",
            "user_id": user_id,
            "consents": updated_consents,
            "updated_at": datetime.now(UTC).isoformat()
        }

    def _process_consent_withdrawal(
        self,
        user_id: str,
        purposes: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Process consent withdrawal.

        Args:
            user_id: User ID
            purposes: Purposes to withdraw

        Returns:
            Processing result
        """
        withdrawn = []
        cannot_withdraw = []

        for purpose in purposes:
            if purpose in self.CONSENT_PURPOSES:
                purpose_def = self.CONSENT_PURPOSES[purpose]

                if purpose_def["required"]:
                    cannot_withdraw.append(purpose)
                else:
                    withdrawn.append({
                        "purpose": purpose,
                        "withdrawn_at": datetime.now(UTC).isoformat(),
                        "effect": self._get_withdrawal_effect(purpose)
                    })

        return {
            "status": "success",
            "message": f"Consent withdrawn for {len(withdrawn)} purposes",
            "user_id": user_id,
            "withdrawn": withdrawn,
            "cannot_withdraw": cannot_withdraw,
            "processed_at": datetime.now(UTC).isoformat()
        }

    def _process_dsar(
        self,
        user_id: str,
        dsar_type: str,
        jurisdiction: str
    ) -> Dict[str, Any]:
        """
        Process Data Subject Access Request.

        Args:
            user_id: User ID
            dsar_type: Type of request (access, erasure, portability)
            jurisdiction: GDPR or CCPA

        Returns:
            Processing result
        """
        request_id = f"DSAR-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        sla = self.DSAR_RESPONSE_SLA.get(jurisdiction, timedelta(days=30))
        deadline = datetime.now(UTC) + sla

        if dsar_type == "access":
            result = self._process_access_request(user_id, request_id, deadline)
        elif dsar_type == "erasure":
            result = self._process_erasure_request(user_id, request_id, deadline)
        elif dsar_type == "portability":
            result = self._process_portability_request(user_id, request_id, deadline)
        else:
            result = {
                "status": "error",
                "message": f"Unknown DSAR type: {dsar_type}"
            }

        return result

    def _process_access_request(
        self,
        user_id: str,
        request_id: str,
        deadline: datetime
    ) -> Dict[str, Any]:
        """Process right of access request (GDPR Article 15)."""
        return {
            "status": "accepted",
            "request_id": request_id,
            "request_type": "access",
            "user_id": user_id,
            "message": "Data access request accepted",
            "deadline": deadline.isoformat(),
            "data_categories": [
                "personal_information",
                "account_data",
                "communication_history",
                "usage_analytics",
                "consent_records"
            ],
            "format": "JSON",
            "delivery_method": "secure_download",
            "estimated_completion": deadline.isoformat()
        }

    def _process_erasure_request(
        self,
        user_id: str,
        request_id: str,
        deadline: datetime
    ) -> Dict[str, Any]:
        """Process right to erasure request (GDPR Article 17)."""
        return {
            "status": "accepted",
            "request_id": request_id,
            "request_type": "erasure",
            "user_id": user_id,
            "message": "Right to erasure request accepted",
            "deadline": deadline.isoformat(),
            "erasure_scope": [
                "personal_data",
                "account_information",
                "communication_logs",
                "preferences"
            ],
            "retained_data": [
                "transaction_records",  # Legal obligation (7 years)
                "audit_logs"  # Legitimate interest
            ],
            "retention_reason": "Legal and regulatory compliance",
            "estimated_completion": deadline.isoformat()
        }

    def _process_portability_request(
        self,
        user_id: str,
        request_id: str,
        deadline: datetime
    ) -> Dict[str, Any]:
        """Process right to data portability (GDPR Article 20)."""
        return {
            "status": "accepted",
            "request_id": request_id,
            "request_type": "portability",
            "user_id": user_id,
            "message": "Data portability request accepted",
            "deadline": deadline.isoformat(),
            "portable_data": [
                "profile_data",
                "preferences",
                "user_generated_content",
                "communication_history"
            ],
            "format": "JSON",
            "machine_readable": True,
            "estimated_completion": deadline.isoformat()
        }

    def _process_opt_out(self, user_id: str, jurisdiction: str) -> Dict[str, Any]:
        """Process CCPA opt-out of sale request."""
        return {
            "status": "success",
            "user_id": user_id,
            "message": "Opt-out of data sale processed",
            "jurisdiction": jurisdiction,
            "opt_out_scope": [
                "third_party_sharing",
                "data_sale",
                "targeted_advertising"
            ],
            "effective_date": datetime.now(UTC).isoformat(),
            "processed_at": datetime.now(UTC).isoformat()
        }

    def _get_withdrawal_effect(self, purpose: str) -> str:
        """Get effect of consent withdrawal."""
        effects = {
            "analytics": "Usage analytics will be disabled",
            "marketing": "No marketing emails will be sent",
            "personalization": "Personalized features will be disabled",
            "third_party_sharing": "Data will not be shared with partners"
        }
        return effects.get(purpose, "Consent withdrawn for this purpose")

    def _validate_consent_state(
        self,
        user_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Validate that consent state is valid."""
        # Essential consent must always be granted
        if "consents" in result:
            for purpose, consent_info in result["consents"].items():
                if purpose == "essential" and not consent_info.get("granted"):
                    return False

        return result.get("status") in ["success", "accepted"]

    def _check_compliance(
        self,
        result: Dict[str, Any],
        jurisdiction: str
    ) -> Dict[str, Any]:
        """Check compliance with regulations."""
        compliant = True
        issues = []

        # Check GDPR requirements
        if jurisdiction == "GDPR":
            # Explicit consent required
            if "consents" in result:
                for purpose, consent_info in result["consents"].items():
                    if purpose != "essential" and consent_info.get("granted"):
                        if "timestamp" not in consent_info:
                            compliant = False
                            issues.append(f"Missing timestamp for {purpose} consent")

            # DSAR response timeline
            if "deadline" in result:
                deadline = datetime.fromisoformat(result["deadline"])
                max_deadline = datetime.now(UTC) + timedelta(days=30)
                if deadline > max_deadline:
                    compliant = False
                    issues.append("DSAR response deadline exceeds GDPR 30-day requirement")

        # Check CCPA requirements
        if jurisdiction == "CCPA":
            if "deadline" in result:
                deadline = datetime.fromisoformat(result["deadline"])
                max_deadline = datetime.now(UTC) + timedelta(days=45)
                if deadline > max_deadline:
                    compliant = False
                    issues.append("DSAR response deadline exceeds CCPA 45-day requirement")

        return {
            "compliant": compliant,
            "jurisdiction": jurisdiction,
            "issues": issues,
            "checked_at": datetime.now(UTC).isoformat()
        }

    def _create_audit_entry(
        self,
        request_type: str,
        user_id: str,
        result: Dict[str, Any],
        jurisdiction: str
    ) -> Dict[str, Any]:
        """Create audit trail entry."""
        return {
            "audit_id": f"CONSENT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now(UTC).isoformat(),
            "request_type": request_type,
            "user_id": user_id,
            "status": result.get("status"),
            "jurisdiction": jurisdiction,
            "request_id": result.get("request_id"),
            "compliance_flags": [jurisdiction, "consent_tracking"],
            "retention_period_years": 7  # Legal requirement
        }

    def _generate_recommendations(
        self,
        request_type: str,
        result: Dict[str, Any],
        compliance_check: Dict[str, Any]
    ) -> List[str]:
        """Generate consent management recommendations."""
        recommendations = []

        if not compliance_check["compliant"]:
            recommendations.append(
                "COMPLIANCE ISSUE: " + "; ".join(compliance_check["issues"])
            )

        if request_type == "dsar":
            recommendations.append(
                f"DSAR request {result.get('request_id')} must be completed by "
                f"{result.get('deadline', 'deadline')[:10]}"
            )

        if request_type == "consent_withdrawal":
            withdrawn_count = len(result.get("withdrawn", []))
            if withdrawn_count > 0:
                recommendations.append(
                    f"Process {withdrawn_count} consent withdrawals. "
                    "Stop related data processing immediately."
                )

        if request_type == "erasure":
            recommendations.append(
                "Verify erasure completion and notify user within deadline. "
                "Maintain proof of deletion for 3 years."
            )

        recommendations.append(
            "Maintain audit trail for all consent changes per regulatory requirements."
        )

        return recommendations

    def _format_consent_report(
        self,
        request_type: str,
        user_id: str,
        result: Dict[str, Any],
        consent_valid: bool,
        compliance_check: Dict[str, Any],
        audit_entry: Dict[str, Any],
        recommendations: List[str]
    ) -> str:
        """Format consent management report."""
        status_icon = "✅" if result.get("status") in ["success", "accepted"] else "❌"
        compliance_icon = "✅" if compliance_check["compliant"] else "⚠️"

        report = f"""**Consent Management Report**

**Request Type:** {request_type.replace('_', ' ').upper()}
**User ID:** {user_id}
**Status:** {status_icon} {result.get('status', 'unknown').upper()}
**Jurisdiction:** {compliance_check['jurisdiction']}
**Compliance:** {compliance_icon} {"COMPLIANT" if compliance_check['compliant'] else "ISSUES FOUND"}

"""

        # Consent updates
        if "consents" in result:
            report += f"**Consent Preferences Updated:**\n"
            for purpose, consent_info in result["consents"].items():
                granted_icon = "✅" if consent_info["granted"] else "❌"
                report += f"{granted_icon} {consent_info['purpose']}\n"
                report += f"   {consent_info['description']}\n"
            report += "\n"

        # DSAR details
        if "request_id" in result:
            report += f"**DSAR Details:**\n"
            report += f"- Request ID: {result['request_id']}\n"
            report += f"- Type: {result.get('request_type', 'unknown')}\n"
            report += f"- Deadline: {result.get('deadline', 'unknown')[:10]}\n"

            if "data_categories" in result:
                report += f"- Data Categories: {', '.join(result['data_categories'])}\n"

            if "erasure_scope" in result:
                report += f"- Erasure Scope: {', '.join(result['erasure_scope'])}\n"

            report += "\n"

        # Compliance issues
        if not compliance_check["compliant"]:
            report += f"**Compliance Issues:**\n"
            for issue in compliance_check["issues"]:
                report += f"⚠️ {issue}\n"
            report += "\n"

        # Audit trail
        report += f"**Audit Trail:**\n"
        report += f"- Audit ID: {audit_entry['audit_id']}\n"
        report += f"- Timestamp: {audit_entry['timestamp']}\n"
        report += f"- Retention: {audit_entry['retention_period_years']} years\n\n"

        # Recommendations
        if recommendations:
            report += f"**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Consent management completed at {datetime.now(UTC).isoformat()}*"
        report += f"\n*Compliance: {compliance_check['jurisdiction']}*"

        return report
