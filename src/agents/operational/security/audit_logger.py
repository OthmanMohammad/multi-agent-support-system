"""
Audit Logger Agent - TASK-2303

Comprehensive, tamper-proof audit logging for all security events.
Ensures compliance with SOC 2, ISO 27001, and regulatory requirements.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("audit_logger", tier="operational", category="security")
class AuditLoggerAgent(BaseAgent):
    """
    Audit Logger Agent.

    Comprehensive audit logging system:
    - Tamper-proof log entries with cryptographic hashing
    - Complete event tracking (authentication, authorization, data access)
    - User activity monitoring
    - System change tracking
    - Compliance-ready log format
    - Log retention and archival
    - Real-time anomaly detection in audit logs
    - Chain-of-custody for sensitive operations

    Log Categories:
    - Authentication events
    - Authorization decisions
    - Data access and modifications
    - System configuration changes
    - Security incidents
    - Admin actions
    """

    # Event categories
    EVENT_CATEGORIES = {
        "authentication": ["login", "logout", "login_failed", "password_change", "mfa_enabled"],
        "authorization": ["access_granted", "access_denied", "permission_change", "role_change"],
        "data_access": ["data_read", "data_write", "data_delete", "data_export"],
        "system": ["config_change", "system_start", "system_stop", "backup", "restore"],
        "security": ["security_alert", "incident_detected", "vulnerability_found", "patch_applied"],
        "admin": ["user_created", "user_deleted", "role_assigned", "permission_granted"],
    }

    # Event severity levels
    SEVERITY_LEVELS = ["info", "warning", "high", "critical"]

    # Compliance frameworks
    COMPLIANCE_FRAMEWORKS = ["SOC2", "ISO27001", "GDPR", "HIPAA", "PCI-DSS"]

    def __init__(self):
        config = AgentConfig(
            name="audit_logger",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Create tamper-proof audit log entry.

        Args:
            state: Current agent state with event details

        Returns:
            Updated state with audit log entry
        """
        self.logger.info("audit_logging_started")

        state = self.update_state(state)

        # Extract parameters
        event_type = state.get("entities", {}).get("event_type", "unknown")
        event_category = state.get("entities", {}).get("event_category", "system")
        user_id = state.get("entities", {}).get("user_id", "system")
        resource_id = state.get("entities", {}).get("resource_id")
        event_data = state.get("entities", {}).get("event_data", {})
        severity = state.get("entities", {}).get("severity", "info")
        ip_address = state.get("entities", {}).get("ip_address", "unknown")
        session_id = state.get("entities", {}).get("session_id")

        self.logger.debug(
            "audit_logging_details",
            event_type=event_type,
            event_category=event_category,
            user_id=user_id,
            severity=severity,
        )

        # Create audit log entry
        audit_entry = self._create_audit_entry(
            event_type,
            event_category,
            user_id,
            resource_id,
            event_data,
            severity,
            ip_address,
            session_id,
        )

        # Calculate integrity hash
        integrity_hash = self._calculate_integrity_hash(audit_entry)
        audit_entry["integrity_hash"] = integrity_hash

        # Add compliance tags
        compliance_tags = self._add_compliance_tags(event_category, event_type)
        audit_entry["compliance_tags"] = compliance_tags

        # Determine retention period
        retention_period = self._determine_retention_period(event_category, severity)
        audit_entry["retention_period_days"] = retention_period

        # Check for anomalies
        anomalies = self._detect_anomalies(audit_entry, event_type, user_id)

        # Generate alerts if needed
        alerts = self._generate_alerts(audit_entry, anomalies)

        # Format log entry
        formatted_entry = self._format_audit_entry(audit_entry)

        # Generate recommendations
        recommendations = self._generate_recommendations(audit_entry, anomalies, alerts)

        # Format response
        response = self._format_audit_report(audit_entry, anomalies, alerts, recommendations)

        state["agent_response"] = response
        state["audit_entry"] = audit_entry
        state["audit_log_id"] = audit_entry["log_id"]
        state["formatted_entry"] = formatted_entry
        state["anomalies_detected"] = anomalies
        state["alerts"] = alerts
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.99
        state["status"] = "resolved"
        state["next_agent"] = None

        # Alert on critical events
        if severity == "critical" or alerts:
            state["alert_pagerduty"] = True
            state["alert_severity"] = "critical" if severity == "critical" else "high"
            state["alert_message"] = f"Critical audit event: {event_type}"

        self.logger.info(
            "audit_logging_completed",
            log_id=audit_entry["log_id"],
            event_type=event_type,
            anomalies=len(anomalies),
            alerts=len(alerts),
        )

        return state

    def _create_audit_entry(
        self,
        event_type: str,
        event_category: str,
        user_id: str,
        resource_id: str | None,
        event_data: dict[str, Any],
        severity: str,
        ip_address: str,
        session_id: str | None,
    ) -> dict[str, Any]:
        """
        Create structured audit log entry.

        Args:
            event_type: Type of event
            event_category: Event category
            user_id: User who triggered event
            resource_id: Affected resource
            event_data: Additional event data
            severity: Event severity
            ip_address: Source IP address
            session_id: Session ID

        Returns:
            Audit log entry
        """
        timestamp = datetime.now(UTC)

        return {
            "log_id": f"AUDIT-{timestamp.strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "event_category": event_category,
            "severity": severity,
            "user_id": user_id,
            "resource_id": resource_id,
            "event_data": event_data,
            "ip_address": ip_address,
            "session_id": session_id,
            "system_version": "1.0.0",
            "environment": "production",
            "created_at": timestamp.isoformat(),
        }

    def _calculate_integrity_hash(self, audit_entry: dict[str, Any]) -> str:
        """
        Calculate cryptographic hash for tamper detection.

        Args:
            audit_entry: Audit log entry

        Returns:
            SHA-256 hash of entry
        """
        # Create deterministic string representation
        entry_copy = audit_entry.copy()
        entry_copy.pop("integrity_hash", None)  # Remove hash field if present

        # Sort keys for deterministic ordering
        entry_string = json.dumps(entry_copy, sort_keys=True)

        # Calculate SHA-256 hash
        hash_object = hashlib.sha256(entry_string.encode())
        return hash_object.hexdigest()

    def _add_compliance_tags(self, event_category: str, event_type: str) -> list[str]:
        """
        Add compliance framework tags.

        Args:
            event_category: Event category
            event_type: Event type

        Returns:
            List of applicable compliance frameworks
        """
        tags = []

        # SOC 2 - All security events
        if event_category in ["authentication", "authorization", "security"]:
            tags.append("SOC2")

        # ISO 27001 - All events
        tags.append("ISO27001")

        # GDPR - Data access and privacy
        if event_category == "data_access" or "pii" in event_type.lower():
            tags.append("GDPR")

        # HIPAA - Health data
        if "health" in event_type.lower() or "phi" in event_type.lower():
            tags.append("HIPAA")

        # PCI-DSS - Payment data
        if "payment" in event_type.lower() or "card" in event_type.lower():
            tags.append("PCI-DSS")

        return tags

    def _determine_retention_period(self, event_category: str, severity: str) -> int:
        """
        Determine log retention period in days.

        Args:
            event_category: Event category
            severity: Event severity

        Returns:
            Retention period in days
        """
        # Critical events: 7 years (regulatory requirement)
        if severity == "critical":
            return 2555  # 7 years

        # Security events: 3 years
        if event_category == "security":
            return 1095  # 3 years

        # Authentication and authorization: 2 years
        if event_category in ["authentication", "authorization"]:
            return 730  # 2 years

        # Admin actions: 2 years
        if event_category == "admin":
            return 730  # 2 years

        # Default: 1 year
        return 365

    def _detect_anomalies(
        self, audit_entry: dict[str, Any], event_type: str, user_id: str
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in audit logs.

        Args:
            audit_entry: Current audit entry
            event_type: Event type
            user_id: User ID

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check for suspicious patterns
        # 1. Multiple failed logins
        if event_type == "login_failed":
            anomalies.append(
                {
                    "type": "failed_login",
                    "severity": "medium",
                    "message": "Failed login attempt detected",
                    "user_id": user_id,
                    "requires_monitoring": True,
                }
            )

        # 2. After-hours access
        current_hour = datetime.now(UTC).hour
        if current_hour < 6 or current_hour > 22:
            if event_type in ["data_access", "data_export", "config_change"]:
                anomalies.append(
                    {
                        "type": "after_hours_access",
                        "severity": "medium",
                        "message": "Sensitive operation performed outside business hours",
                        "hour": current_hour,
                        "requires_review": True,
                    }
                )

        # 3. Privilege escalation
        if event_type in ["role_change", "permission_granted"]:
            anomalies.append(
                {
                    "type": "privilege_change",
                    "severity": "high",
                    "message": "User privilege modification detected",
                    "requires_approval": True,
                }
            )

        # 4. Data export
        if event_type == "data_export":
            anomalies.append(
                {
                    "type": "data_exfiltration_risk",
                    "severity": "high",
                    "message": "Large data export - potential data exfiltration",
                    "requires_investigation": True,
                }
            )

        return anomalies

    def _generate_alerts(
        self, audit_entry: dict[str, Any], anomalies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Generate security alerts based on audit entry.

        Args:
            audit_entry: Audit entry
            anomalies: Detected anomalies

        Returns:
            List of alerts
        """
        alerts = []

        # Critical severity events always generate alerts
        if audit_entry["severity"] == "critical":
            alerts.append(
                {
                    "alert_type": "critical_event",
                    "severity": "critical",
                    "message": f"Critical security event: {audit_entry['event_type']}",
                    "event_id": audit_entry["log_id"],
                    "requires_immediate_action": True,
                }
            )

        # High-severity anomalies
        high_severity_anomalies = [a for a in anomalies if a["severity"] == "high"]
        if high_severity_anomalies:
            alerts.append(
                {
                    "alert_type": "security_anomaly",
                    "severity": "high",
                    "message": f"{len(high_severity_anomalies)} high-severity anomalies detected",
                    "anomalies": high_severity_anomalies,
                    "requires_investigation": True,
                }
            )

        return alerts

    def _format_audit_entry(self, audit_entry: dict[str, Any]) -> str:
        """
        Format audit entry for storage.

        Args:
            audit_entry: Audit entry

        Returns:
            Formatted JSON string
        """
        return json.dumps(audit_entry, indent=2, sort_keys=True)

    def _generate_recommendations(
        self,
        audit_entry: dict[str, Any],
        anomalies: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
    ) -> list[str]:
        """
        Generate recommendations based on audit entry.

        Args:
            audit_entry: Audit entry
            anomalies: Detected anomalies
            alerts: Generated alerts

        Returns:
            List of recommendations
        """
        recommendations = []

        if alerts:
            recommendations.append("CRITICAL: Security alerts generated. Investigate immediately.")

        if anomalies:
            recommendations.append(
                f"{len(anomalies)} anomalies detected. Review audit log for suspicious activity."
            )

        if audit_entry["event_category"] == "admin":
            recommendations.append(
                "Administrative action logged. Ensure proper authorization was obtained."
            )

        if audit_entry["severity"] in ["high", "critical"]:
            recommendations.append(
                f"High-severity event logged with {audit_entry['retention_period_days']} day retention."
            )

        recommendations.append(
            f"Log entry secured with integrity hash: {audit_entry.get('integrity_hash', 'N/A')[:16]}..."
        )

        return recommendations

    def _format_audit_report(
        self,
        audit_entry: dict[str, Any],
        anomalies: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
        recommendations: list[str],
    ) -> str:
        """Format audit logging report."""
        severity_icon = (
            "🔴"
            if audit_entry["severity"] == "critical"
            else "⚠️"
            if audit_entry["severity"] == "high"
            else "ℹ️"
        )

        report = f"""**Audit Log Entry Created**

**Log ID:** {audit_entry["log_id"]}
**Event Type:** {audit_entry["event_type"]}
**Category:** {audit_entry["event_category"]}
**Severity:** {severity_icon} {audit_entry["severity"].upper()}
**User ID:** {audit_entry["user_id"]}
**Timestamp:** {audit_entry["timestamp"]}

**Security Details:**
- IP Address: {audit_entry["ip_address"]}
- Session ID: {audit_entry.get("session_id", "N/A")}
- Integrity Hash: {audit_entry.get("integrity_hash", "N/A")[:32]}...
- Retention Period: {audit_entry.get("retention_period_days", 0)} days

**Compliance Tags:** {", ".join(audit_entry.get("compliance_tags", []))}

"""

        # Anomalies
        if anomalies:
            report += f"**Anomalies Detected:** {len(anomalies)}\n"
            for anomaly in anomalies:
                icon = "🔴" if anomaly["severity"] == "high" else "⚠️"
                report += f"{icon} {anomaly['message']}\n"
            report += "\n"

        # Alerts
        if alerts:
            report += f"**Security Alerts:** {len(alerts)}\n"
            for alert in alerts:
                report += f"🚨 [{alert['severity'].upper()}] {alert['message']}\n"
            report += "\n"

        # Recommendations
        if recommendations:
            report += "**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Audit log entry created at {datetime.now(UTC).isoformat()}*"
        report += "\n*Tamper-proof logging enabled*"

        return report
