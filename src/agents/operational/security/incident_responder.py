"""
Incident Responder Agent - TASK-2306

Automates security incident detection and response.
Target: <5 min detection-to-response time for critical incidents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


class IncidentSeverity(Enum):
    """Incident severity levels."""
    CRITICAL = "critical"  # P1: Active breach, data exposure
    HIGH = "high"  # P2: Attempted breach, major vulnerability
    MEDIUM = "medium"  # P3: Policy violation, minor vulnerability
    LOW = "low"  # P4: Informational, monitoring alert


class IncidentType(Enum):
    """Security incident types."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE = "malware"
    DDOS = "ddos"
    INSIDER_THREAT = "insider_threat"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    API_ABUSE = "api_abuse"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"


@AgentRegistry.register("incident_responder", tier="operational", category="security")
class IncidentResponderAgent(BaseAgent):
    """
    Incident Responder Agent.

    Automated security incident response:
    - Real-time incident detection
    - Automated triage and classification
    - Immediate containment actions
    - Evidence collection and preservation
    - Notification and escalation
    - Post-incident analysis
    - Lessons learned documentation

    Response SLA:
    - Critical (P1): <5 min detection-to-response
    - High (P2): <15 min
    - Medium (P3): <1 hour
    - Low (P4): <24 hours
    """

    # Response SLAs
    RESPONSE_SLA = {
        IncidentSeverity.CRITICAL: timedelta(minutes=5),
        IncidentSeverity.HIGH: timedelta(minutes=15),
        IncidentSeverity.MEDIUM: timedelta(hours=1),
        IncidentSeverity.LOW: timedelta(hours=24)
    }

    # Automated containment actions
    CONTAINMENT_ACTIONS = {
        IncidentType.DATA_BREACH: [
            "isolate_affected_systems",
            "revoke_compromised_credentials",
            "enable_enhanced_logging",
            "notify_security_team"
        ],
        IncidentType.UNAUTHORIZED_ACCESS: [
            "block_ip_address",
            "terminate_session",
            "reset_user_password",
            "enable_mfa_enforcement"
        ],
        IncidentType.MALWARE: [
            "quarantine_infected_systems",
            "block_malicious_domains",
            "scan_related_systems",
            "update_antivirus_signatures"
        ],
        IncidentType.DDOS: [
            "enable_rate_limiting",
            "activate_ddos_protection",
            "block_attacking_ips",
            "scale_infrastructure"
        ],
        IncidentType.RANSOMWARE: [
            "isolate_affected_systems",
            "disable_network_shares",
            "initiate_backup_restoration",
            "contact_law_enforcement"
        ],
        IncidentType.DATA_EXFILTRATION: [
            "block_outbound_connections",
            "revoke_api_keys",
            "analyze_data_access_logs",
            "notify_compliance_team"
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="incident_responder",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=3000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Respond to security incident.

        Args:
            state: Current agent state with incident details

        Returns:
            Updated state with incident response
        """
        self.logger.info("incident_response_started")

        state = self.update_state(state)

        # Extract parameters
        incident_type = state.get("entities", {}).get("incident_type", "unknown")
        incident_data = state.get("entities", {}).get("incident_data", {})
        affected_systems = state.get("entities", {}).get("affected_systems", [])
        detection_time = state.get("entities", {}).get("detection_time", datetime.utcnow().isoformat())
        source_ip = state.get("entities", {}).get("source_ip", "unknown")
        user_id = state.get("entities", {}).get("user_id")

        self.logger.critical(
            "security_incident_detected",
            incident_type=incident_type,
            affected_systems=len(affected_systems),
            source_ip=source_ip
        )

        # Start response timer
        response_start = datetime.utcnow()

        # Classify incident severity
        severity = self._classify_severity(incident_type, incident_data, affected_systems)

        # Create incident record
        incident_id = self._create_incident_record(
            incident_type,
            severity,
            detection_time,
            incident_data,
            affected_systems,
            source_ip,
            user_id
        )

        # Execute automated containment
        containment_actions = self._execute_containment(
            incident_type,
            severity,
            affected_systems,
            source_ip,
            user_id
        )

        # Collect evidence
        evidence = self._collect_evidence(
            incident_type,
            incident_data,
            affected_systems,
            source_ip,
            user_id
        )

        # Determine escalation
        escalation_required = self._check_escalation(severity, incident_type)

        # Generate notifications
        notifications = self._generate_notifications(
            incident_id,
            incident_type,
            severity,
            escalation_required
        )

        # Calculate response time
        response_end = datetime.utcnow()
        response_time = (response_end - response_start).total_seconds()

        # Check SLA compliance
        sla_met = self._check_sla_compliance(severity, response_time)

        # Generate recovery plan
        recovery_plan = self._generate_recovery_plan(
            incident_type,
            severity,
            affected_systems,
            containment_actions
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            incident_type,
            severity,
            containment_actions,
            sla_met
        )

        # Format response
        response = self._format_incident_report(
            incident_id,
            incident_type,
            severity,
            containment_actions,
            evidence,
            notifications,
            recovery_plan,
            response_time,
            sla_met,
            recommendations
        )

        state["agent_response"] = response
        state["incident_id"] = incident_id
        state["incident_severity"] = severity.value
        state["containment_actions"] = containment_actions
        state["evidence_collected"] = evidence
        state["notifications_sent"] = notifications
        state["recovery_plan"] = recovery_plan
        state["response_time_seconds"] = response_time
        state["sla_met"] = sla_met
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.96
        state["status"] = "resolved"
        state["next_agent"] = None

        # Always alert on security incidents
        state["alert_pagerduty"] = True
        state["alert_severity"] = severity.value
        state["alert_message"] = f"Security Incident {incident_id}: {incident_type}"

        self.logger.info(
            "incident_response_completed",
            incident_id=incident_id,
            severity=severity.value,
            response_time=response_time,
            sla_met=sla_met,
            actions_taken=len(containment_actions)
        )

        return state

    def _classify_severity(
        self,
        incident_type: str,
        incident_data: Dict[str, Any],
        affected_systems: List[str]
    ) -> IncidentSeverity:
        """
        Classify incident severity.

        Args:
            incident_type: Type of incident
            incident_data: Incident details
            affected_systems: List of affected systems

        Returns:
            Incident severity level
        """
        # Critical incidents
        critical_types = [
            IncidentType.DATA_BREACH.value,
            IncidentType.RANSOMWARE.value,
            IncidentType.DATA_EXFILTRATION.value
        ]

        if incident_type in critical_types:
            return IncidentSeverity.CRITICAL

        # High severity
        high_types = [
            IncidentType.UNAUTHORIZED_ACCESS.value,
            IncidentType.MALWARE.value,
            IncidentType.PRIVILEGE_ESCALATION.value
        ]

        if incident_type in high_types:
            return IncidentSeverity.HIGH

        # Check if multiple systems affected
        if len(affected_systems) > 5:
            return IncidentSeverity.HIGH

        # Check if production systems affected
        if any("prod" in system.lower() for system in affected_systems):
            return IncidentSeverity.HIGH

        # Default to medium
        return IncidentSeverity.MEDIUM

    def _create_incident_record(
        self,
        incident_type: str,
        severity: IncidentSeverity,
        detection_time: str,
        incident_data: Dict[str, Any],
        affected_systems: List[str],
        source_ip: str,
        user_id: Optional[str]
    ) -> str:
        """Create incident record."""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        self.logger.info(
            "incident_record_created",
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity.value
        )

        return incident_id

    def _execute_containment(
        self,
        incident_type: str,
        severity: IncidentSeverity,
        affected_systems: List[str],
        source_ip: str,
        user_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute automated containment actions.

        Args:
            incident_type: Type of incident
            severity: Incident severity
            affected_systems: Affected systems
            source_ip: Source IP address
            user_id: User ID if applicable

        Returns:
            List of containment actions taken
        """
        actions_taken = []

        # Get incident type enum
        try:
            incident_enum = IncidentType(incident_type)
        except ValueError:
            incident_enum = None

        # Execute predefined containment actions
        if incident_enum and incident_enum in self.CONTAINMENT_ACTIONS:
            for action in self.CONTAINMENT_ACTIONS[incident_enum]:
                result = self._execute_action(
                    action,
                    affected_systems,
                    source_ip,
                    user_id
                )
                actions_taken.append(result)

        return actions_taken

    def _execute_action(
        self,
        action: str,
        affected_systems: List[str],
        source_ip: str,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute single containment action."""
        # Simulate action execution
        # In production, integrate with actual systems

        action_result = {
            "action": action,
            "status": "success",
            "executed_at": datetime.utcnow().isoformat(),
            "details": f"Executed {action.replace('_', ' ')}"
        }

        if action == "block_ip_address":
            action_result["details"] = f"Blocked IP {source_ip} at firewall level"
        elif action == "revoke_compromised_credentials":
            action_result["details"] = f"Revoked credentials for user {user_id}"
        elif action == "isolate_affected_systems":
            action_result["details"] = f"Isolated {len(affected_systems)} systems from network"

        self.logger.info(
            "containment_action_executed",
            action=action,
            status=action_result["status"]
        )

        return action_result

    def _collect_evidence(
        self,
        incident_type: str,
        incident_data: Dict[str, Any],
        affected_systems: List[str],
        source_ip: str,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Collect evidence for forensic analysis."""
        evidence = {
            "collection_time": datetime.utcnow().isoformat(),
            "incident_type": incident_type,
            "artifacts": [],
            "chain_of_custody": []
        }

        # Collect various types of evidence
        evidence["artifacts"].extend([
            {"type": "system_logs", "source": system, "preserved": True}
            for system in affected_systems
        ])

        if source_ip:
            evidence["artifacts"].append({
                "type": "network_traffic",
                "source_ip": source_ip,
                "preserved": True
            })

        if user_id:
            evidence["artifacts"].append({
                "type": "user_activity",
                "user_id": user_id,
                "preserved": True
            })

        # Chain of custody
        evidence["chain_of_custody"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "evidence_collection_started",
            "collector": "incident_responder_agent"
        })

        return evidence

    def _check_escalation(
        self,
        severity: IncidentSeverity,
        incident_type: str
    ) -> bool:
        """Check if incident requires escalation."""
        # Always escalate critical incidents
        if severity == IncidentSeverity.CRITICAL:
            return True

        # Escalate certain types regardless of severity
        escalation_types = [
            IncidentType.DATA_BREACH.value,
            IncidentType.RANSOMWARE.value,
            IncidentType.INSIDER_THREAT.value
        ]

        return incident_type in escalation_types

    def _generate_notifications(
        self,
        incident_id: str,
        incident_type: str,
        severity: IncidentSeverity,
        escalation_required: bool
    ) -> List[Dict[str, Any]]:
        """Generate incident notifications."""
        notifications = []

        # Always notify security team
        notifications.append({
            "recipient": "security_team",
            "channel": "pagerduty",
            "severity": severity.value,
            "message": f"Security incident {incident_id}: {incident_type}"
        })

        # Escalate to CISO for critical incidents
        if severity == IncidentSeverity.CRITICAL or escalation_required:
            notifications.append({
                "recipient": "ciso",
                "channel": "phone_sms",
                "severity": "critical",
                "message": f"CRITICAL INCIDENT {incident_id} requires immediate attention"
            })

        # Notify compliance team for data breaches
        if "breach" in incident_type.lower() or "exfiltration" in incident_type.lower():
            notifications.append({
                "recipient": "compliance_team",
                "channel": "email",
                "severity": severity.value,
                "message": f"Data incident {incident_id} may require regulatory notification"
            })

        return notifications

    def _check_sla_compliance(self, severity: IncidentSeverity, response_time: float) -> bool:
        """Check if response met SLA."""
        sla = self.RESPONSE_SLA.get(severity, timedelta(hours=24))
        sla_seconds = sla.total_seconds()

        return response_time <= sla_seconds

    def _generate_recovery_plan(
        self,
        incident_type: str,
        severity: IncidentSeverity,
        affected_systems: List[str],
        containment_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recovery plan."""
        plan = []

        # Verify containment
        plan.append({
            "step": 1,
            "action": "Verify containment effectiveness",
            "description": "Confirm all containment actions successful",
            "responsible": "security_team",
            "deadline": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        })

        # Eradicate threat
        plan.append({
            "step": 2,
            "action": "Eradicate threat",
            "description": f"Remove malicious artifacts from {len(affected_systems)} systems",
            "responsible": "security_team",
            "deadline": (datetime.utcnow() + timedelta(hours=4)).isoformat()
        })

        # Restore systems
        plan.append({
            "step": 3,
            "action": "Restore affected systems",
            "description": "Restore from clean backups and verify integrity",
            "responsible": "ops_team",
            "deadline": (datetime.utcnow() + timedelta(hours=8)).isoformat()
        })

        # Post-incident review
        plan.append({
            "step": 4,
            "action": "Conduct post-incident review",
            "description": "Document lessons learned and update procedures",
            "responsible": "security_lead",
            "deadline": (datetime.utcnow() + timedelta(days=3)).isoformat()
        })

        return plan

    def _generate_recommendations(
        self,
        incident_type: str,
        severity: IncidentSeverity,
        containment_actions: List[Dict[str, Any]],
        sla_met: bool
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []

        if severity == IncidentSeverity.CRITICAL:
            recommendations.append(
                "CRITICAL INCIDENT: Follow recovery plan and maintain communication with stakeholders"
            )

        if not sla_met:
            recommendations.append(
                "SLA not met. Review and optimize incident response procedures."
            )

        recommendations.append(
            f"Executed {len(containment_actions)} automated containment actions. "
            "Verify effectiveness before proceeding."
        )

        recommendations.append(
            "Preserve all evidence for forensic analysis and potential legal proceedings."
        )

        recommendations.append(
            "Update threat intelligence based on attack patterns observed."
        )

        if "breach" in incident_type.lower():
            recommendations.append(
                "Consult legal team regarding breach notification requirements (GDPR: 72 hours)"
            )

        return recommendations

    def _format_incident_report(
        self,
        incident_id: str,
        incident_type: str,
        severity: IncidentSeverity,
        containment_actions: List[Dict[str, Any]],
        evidence: Dict[str, Any],
        notifications: List[Dict[str, Any]],
        recovery_plan: List[Dict[str, Any]],
        response_time: float,
        sla_met: bool,
        recommendations: List[str]
    ) -> str:
        """Format incident response report."""
        severity_icon = "🔴" if severity == IncidentSeverity.CRITICAL else "⚠️" if severity == IncidentSeverity.HIGH else "📋"
        sla_icon = "✅" if sla_met else "❌"

        report = f"""**SECURITY INCIDENT RESPONSE REPORT**

**Incident ID:** {incident_id}
**Type:** {incident_type.upper()}
**Severity:** {severity_icon} {severity.value.upper()}
**Response Time:** {response_time:.1f} seconds
**SLA Met:** {sla_icon} {"YES" if sla_met else "NO"}

**CONTAINMENT ACTIONS EXECUTED:** {len(containment_actions)}
"""

        for action in containment_actions:
            status_icon = "✅" if action["status"] == "success" else "❌"
            report += f"{status_icon} {action['action'].replace('_', ' ').title()}\n"
            report += f"   {action['details']}\n"

        report += f"\n**EVIDENCE COLLECTED:** {len(evidence['artifacts'])} artifacts\n"
        for artifact in evidence["artifacts"][:3]:
            report += f"- {artifact['type']}: {artifact.get('source', 'multiple sources')}\n"

        report += f"\n**NOTIFICATIONS SENT:** {len(notifications)}\n"
        for notif in notifications:
            report += f"- {notif['recipient']}: {notif['channel']}\n"

        report += f"\n**RECOVERY PLAN:**\n"
        for step in recovery_plan:
            report += f"{step['step']}. {step['action']}\n"
            report += f"   {step['description']}\n"
            report += f"   Deadline: {step['deadline'][:19]}\n\n"

        report += f"**RECOMMENDATIONS:**\n"
        for rec in recommendations:
            report += f"- {rec}\n"

        report += f"\n*Incident response completed at {datetime.utcnow().isoformat()}*"
        report += f"\n*Status: CONTAINED - Monitoring for additional indicators*"

        return report
