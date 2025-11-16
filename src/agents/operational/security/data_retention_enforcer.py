"""
Data Retention Enforcer Agent - TASK-2307

Enforces data retention and deletion policies for compliance.
Automates data lifecycle management per GDPR, CCPA, and SOC 2 requirements.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("data_retention_enforcer", tier="operational", category="security")
class DataRetentionEnforcerAgent(BaseAgent):
    """
    Data Retention Enforcer Agent.

    Automated data lifecycle management:
    - Policy-based retention periods
    - Automated data deletion
    - Legal hold management
    - Audit log retention
    - Backup retention
    - PII data minimization
    - Right to erasure (GDPR Article 17)
    - Data archival and purging

    Retention Policies:
    - User data: Per consent or legal requirement
    - Audit logs: 7 years (compliance)
    - Payment data: 7 years (tax/PCI-DSS)
    - Communication logs: 2 years
    - Session data: 90 days
    - Temporary data: 30 days
    """

    # Default retention periods (in days)
    RETENTION_POLICIES = {
        "user_data": {
            "default_days": 2555,  # 7 years
            "after_deletion_request": 30,  # Grace period
            "inactive_account": 730  # 2 years of inactivity
        },
        "audit_logs": {
            "security_events": 2555,  # 7 years
            "access_logs": 730,  # 2 years
            "system_logs": 365  # 1 year
        },
        "payment_data": {
            "transaction_records": 2555,  # 7 years (tax)
            "credit_card_info": 0,  # Never store (PCI-DSS)
            "billing_history": 2555  # 7 years
        },
        "communication": {
            "support_tickets": 730,  # 2 years
            "emails": 730,  # 2 years
            "chat_logs": 365  # 1 year
        },
        "session_data": {
            "active_sessions": 1,  # 24 hours
            "session_history": 90  # 90 days
        },
        "temporary_data": {
            "cache": 7,  # 7 days
            "uploads": 30,  # 30 days
            "drafts": 90  # 90 days
        }
    }

    # Data classification
    DATA_CLASSIFICATIONS = {
        "public": 365,  # 1 year default
        "internal": 730,  # 2 years default
        "confidential": 2555,  # 7 years default
        "restricted": 2555  # 7 years default
    }

    # Deletion methods
    DELETION_METHODS = {
        "standard": "Marked as deleted, purged after grace period",
        "immediate": "Immediate permanent deletion",
        "secure_wipe": "Cryptographic secure deletion",
        "anonymize": "PII removed, statistical data retained"
    }

    def __init__(self):
        config = AgentConfig(
            name="data_retention_enforcer",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2500,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Enforce data retention policies.

        Args:
            state: Current agent state with enforcement context

        Returns:
            Updated state with retention enforcement results
        """
        self.logger.info("data_retention_enforcement_started")

        state = self.update_state(state)

        # Extract parameters
        enforcement_mode = state.get("entities", {}).get("enforcement_mode", "audit")  # audit, enforce, report
        data_inventory = state.get("entities", {}).get("data_inventory", [])
        deletion_requests = state.get("entities", {}).get("deletion_requests", [])
        legal_holds = state.get("entities", {}).get("legal_holds", [])
        override_policies = state.get("entities", {}).get("override_policies", {})

        self.logger.debug(
            "retention_enforcement_details",
            mode=enforcement_mode,
            data_records=len(data_inventory),
            deletion_requests=len(deletion_requests)
        )

        # Scan data inventory for retention compliance
        compliance_results = self._scan_data_inventory(
            data_inventory,
            legal_holds,
            override_policies
        )

        # Identify expired data
        expired_data = self._identify_expired_data(compliance_results)

        # Process deletion requests (GDPR Right to Erasure)
        deletion_results = self._process_deletion_requests(
            deletion_requests,
            legal_holds
        )

        # Execute deletions if in enforcement mode
        deletion_actions = []
        if enforcement_mode == "enforce":
            deletion_actions = self._execute_deletions(
                expired_data,
                deletion_results
            )

        # Check legal hold compliance
        legal_hold_violations = self._check_legal_holds(
            expired_data,
            deletion_actions,
            legal_holds
        )

        # Generate retention report
        retention_report = self._generate_retention_report(
            compliance_results,
            expired_data,
            deletion_actions
        )

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(compliance_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            compliance_results,
            expired_data,
            deletion_results,
            legal_hold_violations
        )

        # Format response
        response = self._format_enforcement_report(
            enforcement_mode,
            compliance_results,
            expired_data,
            deletion_actions,
            deletion_results,
            compliance_score,
            legal_hold_violations,
            recommendations
        )

        state["agent_response"] = response
        state["retention_compliance"] = compliance_results
        state["expired_data_count"] = len(expired_data)
        state["deletions_executed"] = len(deletion_actions)
        state["deletion_requests_processed"] = len(deletion_results)
        state["compliance_score"] = compliance_score
        state["legal_hold_violations"] = legal_hold_violations
        state["retention_report"] = retention_report
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.94
        state["status"] = "resolved"
        state["next_agent"] = None

        # Alert on legal hold violations
        if legal_hold_violations:
            state["alert_pagerduty"] = True
            state["alert_severity"] = "critical"
            state["alert_message"] = f"Legal hold violation: {len(legal_hold_violations)} records"

        self.logger.info(
            "retention_enforcement_completed",
            mode=enforcement_mode,
            expired_count=len(expired_data),
            deletions=len(deletion_actions),
            compliance_score=compliance_score
        )

        return state

    def _scan_data_inventory(
        self,
        data_inventory: List[Dict[str, Any]],
        legal_holds: List[Dict[str, Any]],
        override_policies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scan data inventory for retention compliance.

        Args:
            data_inventory: List of data records
            legal_holds: Active legal holds
            override_policies: Custom retention policies

        Returns:
            Compliance results for each record
        """
        results = []

        for record in data_inventory:
            data_type = record.get("data_type", "unknown")
            category = record.get("category", "user_data")
            created_at = datetime.fromisoformat(record.get("created_at", datetime.utcnow().isoformat()))
            last_accessed = datetime.fromisoformat(record.get("last_accessed", created_at.isoformat()))

            # Get retention period
            retention_days = self._get_retention_period(
                data_type,
                category,
                override_policies
            )

            # Calculate expiry
            expiry_date = created_at + timedelta(days=retention_days)
            days_until_expiry = (expiry_date - datetime.utcnow()).days

            # Check if on legal hold
            on_legal_hold = self._is_on_legal_hold(record, legal_holds)

            # Determine compliance status
            if on_legal_hold:
                status = "legal_hold"
            elif days_until_expiry < 0:
                status = "expired"
            elif days_until_expiry < 30:
                status = "expiring_soon"
            else:
                status = "compliant"

            results.append({
                "record_id": record.get("id"),
                "data_type": data_type,
                "category": category,
                "created_at": created_at.isoformat(),
                "retention_days": retention_days,
                "expiry_date": expiry_date.isoformat(),
                "days_until_expiry": days_until_expiry,
                "status": status,
                "on_legal_hold": on_legal_hold,
                "data_size_mb": record.get("size_mb", 0)
            })

        return results

    def _get_retention_period(
        self,
        data_type: str,
        category: str,
        override_policies: Dict[str, Any]
    ) -> int:
        """Get retention period for data type."""
        # Check for override
        if data_type in override_policies:
            return override_policies[data_type]

        # Get from standard policies
        if category in self.RETENTION_POLICIES:
            category_policies = self.RETENTION_POLICIES[category]
            if data_type in category_policies:
                return category_policies[data_type]
            if "default_days" in category_policies:
                return category_policies["default_days"]

        # Default: 1 year
        return 365

    def _is_on_legal_hold(
        self,
        record: Dict[str, Any],
        legal_holds: List[Dict[str, Any]]
    ) -> bool:
        """Check if record is on legal hold."""
        record_id = record.get("id")

        for hold in legal_holds:
            if record_id in hold.get("record_ids", []):
                return True

            # Check by category
            if record.get("category") in hold.get("categories", []):
                return True

            # Check by date range
            created_at = datetime.fromisoformat(record.get("created_at", ""))
            hold_start = datetime.fromisoformat(hold.get("start_date", ""))
            hold_end = datetime.fromisoformat(hold.get("end_date", datetime.utcnow().isoformat()))

            if hold_start <= created_at <= hold_end:
                return True

        return False

    def _identify_expired_data(
        self,
        compliance_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify expired data that should be deleted."""
        return [
            record for record in compliance_results
            if record["status"] == "expired" and not record["on_legal_hold"]
        ]

    def _process_deletion_requests(
        self,
        deletion_requests: List[Dict[str, Any]],
        legal_holds: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process user deletion requests (GDPR Right to Erasure).

        Args:
            deletion_requests: User deletion requests
            legal_holds: Active legal holds

        Returns:
            Processing results
        """
        results = []

        for request in deletion_requests:
            user_id = request.get("user_id")
            request_date = datetime.fromisoformat(request.get("request_date", datetime.utcnow().isoformat()))
            data_categories = request.get("categories", ["all"])

            # Check if data is on legal hold
            legal_hold_applies = any(
                user_id in hold.get("user_ids", [])
                for hold in legal_holds
            )

            if legal_hold_applies:
                status = "deferred_legal_hold"
                deletion_date = None
                reason = "Data subject to active legal hold"
            else:
                # GDPR: Process within 30 days
                deletion_date = request_date + timedelta(days=30)
                status = "scheduled"
                reason = "Right to erasure request approved"

            results.append({
                "user_id": user_id,
                "request_date": request_date.isoformat(),
                "categories": data_categories,
                "status": status,
                "deletion_date": deletion_date.isoformat() if deletion_date else None,
                "reason": reason
            })

        return results

    def _execute_deletions(
        self,
        expired_data: List[Dict[str, Any]],
        deletion_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute data deletions.

        Args:
            expired_data: Expired data records
            deletion_results: Approved deletion requests

        Returns:
            Deletion actions taken
        """
        actions = []

        # Delete expired data
        for record in expired_data:
            action = {
                "record_id": record["record_id"],
                "data_type": record["data_type"],
                "deletion_method": self._get_deletion_method(record["data_type"]),
                "deleted_at": datetime.utcnow().isoformat(),
                "reason": "retention_period_expired",
                "data_size_mb": record.get("data_size_mb", 0),
                "status": "deleted"
            }
            actions.append(action)

        # Process user deletion requests
        for request in deletion_results:
            if request["status"] == "scheduled":
                deletion_date = datetime.fromisoformat(request["deletion_date"])
                if deletion_date <= datetime.utcnow():
                    action = {
                        "user_id": request["user_id"],
                        "categories": request["categories"],
                        "deletion_method": "secure_wipe",
                        "deleted_at": datetime.utcnow().isoformat(),
                        "reason": "right_to_erasure",
                        "status": "deleted"
                    }
                    actions.append(action)

        return actions

    def _get_deletion_method(self, data_type: str) -> str:
        """Get appropriate deletion method for data type."""
        sensitive_types = ["payment_data", "health_data", "credentials", "pii"]

        if any(s in data_type.lower() for s in sensitive_types):
            return "secure_wipe"
        elif "audit" in data_type.lower():
            return "anonymize"
        else:
            return "standard"

    def _check_legal_holds(
        self,
        expired_data: List[Dict[str, Any]],
        deletion_actions: List[Dict[str, Any]],
        legal_holds: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for legal hold violations."""
        violations = []

        # Check if any deleted data was on legal hold
        for action in deletion_actions:
            record_id = action.get("record_id")

            for hold in legal_holds:
                if record_id in hold.get("record_ids", []):
                    violations.append({
                        "record_id": record_id,
                        "legal_hold_id": hold.get("hold_id"),
                        "violation_type": "deleted_data_on_hold",
                        "severity": "critical",
                        "detected_at": datetime.utcnow().isoformat()
                    })

        return violations

    def _calculate_compliance_score(
        self,
        compliance_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate retention compliance score (0-100)."""
        if not compliance_results:
            return 100.0

        compliant = len([r for r in compliance_results if r["status"] == "compliant"])
        expiring_soon = len([r for r in compliance_results if r["status"] == "expiring_soon"])
        expired = len([r for r in compliance_results if r["status"] == "expired"])

        total = len(compliance_results)

        # Score calculation
        score = (compliant / total) * 100
        score -= (expiring_soon / total) * 10  # Minor penalty for expiring soon
        score -= (expired / total) * 30  # Major penalty for expired

        return max(round(score, 1), 0.0)

    def _generate_retention_report(
        self,
        compliance_results: List[Dict[str, Any]],
        expired_data: List[Dict[str, Any]],
        deletion_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive retention report."""
        total_size_mb = sum(r.get("data_size_mb", 0) for r in compliance_results)
        expired_size_mb = sum(r.get("data_size_mb", 0) for r in expired_data)
        deleted_size_mb = sum(a.get("data_size_mb", 0) for a in deletion_actions)

        return {
            "report_date": datetime.utcnow().isoformat(),
            "total_records": len(compliance_results),
            "total_size_mb": round(total_size_mb, 2),
            "compliant_records": len([r for r in compliance_results if r["status"] == "compliant"]),
            "expired_records": len(expired_data),
            "expired_size_mb": round(expired_size_mb, 2),
            "records_deleted": len(deletion_actions),
            "storage_freed_mb": round(deleted_size_mb, 2),
            "expiring_30_days": len([r for r in compliance_results if r["status"] == "expiring_soon"])
        }

    def _generate_recommendations(
        self,
        compliance_results: List[Dict[str, Any]],
        expired_data: List[Dict[str, Any]],
        deletion_results: List[Dict[str, Any]],
        legal_hold_violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate retention recommendations."""
        recommendations = []

        if legal_hold_violations:
            recommendations.append(
                f"CRITICAL: {len(legal_hold_violations)} legal hold violations detected. "
                "Review and restore affected data immediately."
            )

        if expired_data:
            recommendations.append(
                f"{len(expired_data)} records exceeded retention period. "
                "Delete to maintain compliance and reduce storage costs."
            )

        expiring_soon = [r for r in compliance_results if r["status"] == "expiring_soon"]
        if expiring_soon:
            recommendations.append(
                f"{len(expiring_soon)} records expiring within 30 days. "
                "Review for legal hold or extension requirements."
            )

        deferred_requests = [r for r in deletion_results if r["status"] == "deferred_legal_hold"]
        if deferred_requests:
            recommendations.append(
                f"{len(deferred_requests)} deletion requests deferred due to legal holds. "
                "Monitor hold status and process when cleared."
            )

        total_size = sum(r.get("data_size_mb", 0) for r in compliance_results)
        if total_size > 10000:  # > 10 GB
            recommendations.append(
                f"Large data volume ({total_size:.0f} MB). "
                "Consider archival or tiered storage for older data."
            )

        recommendations.append(
            "Schedule monthly retention policy reviews to ensure ongoing compliance."
        )

        return recommendations

    def _format_enforcement_report(
        self,
        enforcement_mode: str,
        compliance_results: List[Dict[str, Any]],
        expired_data: List[Dict[str, Any]],
        deletion_actions: List[Dict[str, Any]],
        deletion_results: List[Dict[str, Any]],
        compliance_score: float,
        legal_hold_violations: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> str:
        """Format retention enforcement report."""
        mode_icon = "🔍" if enforcement_mode == "audit" else "⚙️" if enforcement_mode == "enforce" else "📊"
        compliance_icon = "✅" if compliance_score >= 90 else "⚠️" if compliance_score >= 70 else "❌"

        report = f"""**Data Retention Enforcement Report**

**Mode:** {mode_icon} {enforcement_mode.upper()}
**Compliance Score:** {compliance_icon} {compliance_score}/100
**Total Records:** {len(compliance_results)}
**Expired Records:** {len(expired_data)}
**Deletions Executed:** {len(deletion_actions)}

**Compliance Breakdown:**
"""

        # Count by status
        status_counts = {}
        for record in compliance_results:
            status = record["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in sorted(status_counts.items()):
            icon = "✅" if status == "compliant" else "⚠️" if status == "expiring_soon" else "❌"
            report += f"{icon} {status.replace('_', ' ').title()}: {count}\n"

        # Deletion requests
        if deletion_results:
            report += f"\n**User Deletion Requests (GDPR):** {len(deletion_results)}\n"
            for request in deletion_results[:3]:
                status_icon = "✅" if request["status"] == "scheduled" else "⏳"
                report += f"{status_icon} User {request['user_id']}: {request['status']}\n"
                if request.get("deletion_date"):
                    report += f"   Scheduled: {request['deletion_date'][:10]}\n"

        # Legal hold violations
        if legal_hold_violations:
            report += f"\n**LEGAL HOLD VIOLATIONS:** {len(legal_hold_violations)}\n"
            for violation in legal_hold_violations:
                report += f"🔴 Record {violation['record_id']}: {violation['violation_type']}\n"

        # Storage impact
        if deletion_actions:
            freed_mb = sum(a.get("data_size_mb", 0) for a in deletion_actions)
            report += f"\n**Storage Freed:** {freed_mb:.2f} MB\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Retention enforcement completed at {datetime.utcnow().isoformat()}*"
        report += f"\n*Next enforcement: {(datetime.utcnow() + timedelta(days=7)).isoformat()[:10]}*"

        return report
