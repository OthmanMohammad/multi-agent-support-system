"""
Penetration Test Coordinator Agent - TASK-2310

Coordinates quarterly penetration testing and security assessments.
Manages vendor coordination, scope definition, and remediation tracking.
"""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


class TestPhase(Enum):
    """Penetration test phases."""

    PLANNING = "planning"
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"
    REMEDIATION = "remediation"
    RETEST = "retest"


class TestType(Enum):
    """Types of penetration tests."""

    EXTERNAL = "external"  # External-facing systems
    INTERNAL = "internal"  # Internal network
    WEB_APP = "web_application"
    API = "api"
    MOBILE = "mobile_app"
    CLOUD = "cloud_infrastructure"
    SOCIAL_ENGINEERING = "social_engineering"
    WIRELESS = "wireless"
    PHYSICAL = "physical_security"


@AgentRegistry.register("pen_test_coordinator", tier="operational", category="security")
class PenTestCoordinatorAgent(BaseAgent):
    """
    Penetration Test Coordinator Agent.

    Comprehensive pen test management:
    - Quarterly pen test scheduling
    - Scope definition and approval
    - Vendor/team coordination
    - Test execution monitoring
    - Finding triage and prioritization
    - Remediation tracking
    - Retest coordination
    - Compliance reporting (SOC 2, ISO 27001)

    Testing Framework:
    - OWASP Top 10
    - MITRE ATT&CK
    - PTES (Penetration Testing Execution Standard)
    - NIST SP 800-115

    Schedule:
    - External pen test: Quarterly
    - Internal pen test: Bi-annually
    - Web app pen test: After major releases
    """

    # Test schedules (in days)
    TEST_SCHEDULES = {
        TestType.EXTERNAL: 90,  # Quarterly
        TestType.INTERNAL: 180,  # Bi-annually
        TestType.WEB_APP: 90,  # Quarterly or after release
        TestType.API: 90,  # Quarterly
        TestType.CLOUD: 180,  # Bi-annually
        TestType.SOCIAL_ENGINEERING: 365,  # Annually
        TestType.WIRELESS: 365,  # Annually
        TestType.PHYSICAL: 365,  # Annually
    }

    # Finding severity levels (aligned with CVSS)
    SEVERITY_LEVELS = {
        "critical": {"cvss_range": (9.0, 10.0), "remediation_sla_days": 7},
        "high": {"cvss_range": (7.0, 8.9), "remediation_sla_days": 30},
        "medium": {"cvss_range": (4.0, 6.9), "remediation_sla_days": 90},
        "low": {"cvss_range": (0.1, 3.9), "remediation_sla_days": 180},
        "informational": {"cvss_range": (0.0, 0.0), "remediation_sla_days": 365},
    }

    # OWASP Top 10 2021
    OWASP_TOP_10 = [
        "A01:2021-Broken Access Control",
        "A02:2021-Cryptographic Failures",
        "A03:2021-Injection",
        "A04:2021-Insecure Design",
        "A05:2021-Security Misconfiguration",
        "A06:2021-Vulnerable and Outdated Components",
        "A07:2021-Identification and Authentication Failures",
        "A08:2021-Software and Data Integrity Failures",
        "A09:2021-Security Logging and Monitoring Failures",
        "A10:2021-Server-Side Request Forgery",
    ]

    def __init__(self):
        config = AgentConfig(
            name="pen_test_coordinator",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=3000,
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Coordinate penetration testing activities.

        Args:
            state: Current agent state with pen test request

        Returns:
            Updated state with coordination results
        """
        self.logger.info("pen_test_coordination_started")

        state = self.update_state(state)

        # Extract parameters
        action = state.get("entities", {}).get(
            "action", "schedule"
        )  # schedule, findings_review, remediation_track
        test_type = state.get("entities", {}).get("test_type", TestType.EXTERNAL.value)
        test_scope = state.get("entities", {}).get("test_scope", {})
        findings = state.get("entities", {}).get("findings", [])
        previous_tests = state.get("entities", {}).get("previous_tests", [])

        self.logger.debug(
            "pen_test_coordination_details",
            action=action,
            test_type=test_type,
            findings_count=len(findings),
        )

        # Process based on action
        if action == "schedule":
            result = self._schedule_pen_test(test_type, test_scope, previous_tests)
        elif action == "findings_review":
            result = self._review_findings(findings, test_type)
        elif action == "remediation_track":
            result = self._track_remediation(findings)
        elif action == "retest":
            result = self._coordinate_retest(findings, test_type)
        else:
            result = {"status": "error", "message": "Unknown action"}

        # Check compliance requirements
        compliance_status = self._check_compliance_requirements(test_type, previous_tests)

        # Generate test plan if scheduling
        test_plan = None
        if action == "schedule":
            test_plan = self._generate_test_plan(test_type, test_scope)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(findings) if findings else None

        # Generate recommendations
        recommendations = self._generate_recommendations(
            action, result, compliance_status, risk_metrics
        )

        # Format response
        response = self._format_coordination_report(
            action, test_type, result, test_plan, compliance_status, risk_metrics, recommendations
        )

        state["agent_response"] = response
        state["coordination_result"] = result
        state["test_plan"] = test_plan
        state["compliance_status"] = compliance_status
        state["risk_metrics"] = risk_metrics
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.92
        state["status"] = "resolved"
        state["next_agent"] = None

        # Alert if compliance gap or critical findings
        if not compliance_status.get("compliant") or (
            risk_metrics and risk_metrics.get("critical_count", 0) > 0
        ):
            state["alert_pagerduty"] = True
            state["alert_severity"] = "high"
            state["alert_message"] = "Pen test compliance gap or critical findings"

        self.logger.info(
            "pen_test_coordination_completed",
            action=action,
            test_type=test_type,
            status=result.get("status"),
        )

        return state

    def _schedule_pen_test(
        self, test_type: str, test_scope: dict[str, Any], previous_tests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Schedule penetration test.

        Args:
            test_type: Type of pen test
            test_scope: Scope of testing
            previous_tests: Previous test history

        Returns:
            Scheduling result
        """
        try:
            test_type_enum = TestType(test_type)
        except ValueError:
            return {"status": "error", "message": f"Invalid test type: {test_type}"}

        # Calculate next test date based on schedule
        schedule_days = self.TEST_SCHEDULES.get(test_type_enum, 90)
        last_test_date = self._get_last_test_date(test_type, previous_tests)

        if last_test_date:
            next_test_date = last_test_date + timedelta(days=schedule_days)
        else:
            # First test - schedule for next month
            next_test_date = datetime.now(UTC) + timedelta(days=30)

        # Generate test ID
        test_id = f"PENTEST-{datetime.now(UTC).strftime('%Y%m%d')}-{test_type.upper()[:3]}"

        return {
            "status": "scheduled",
            "test_id": test_id,
            "test_type": test_type,
            "scheduled_date": next_test_date.isoformat(),
            "schedule_frequency_days": schedule_days,
            "last_test_date": last_test_date.isoformat() if last_test_date else None,
            "scope": test_scope,
            "phases": [phase.value for phase in TestPhase],
            "estimated_duration_days": self._estimate_duration(test_type_enum),
            "compliance_requirement": self._get_compliance_requirement(test_type_enum),
        }

    def _review_findings(self, findings: list[dict[str, Any]], test_type: str) -> dict[str, Any]:
        """
        Review and triage pen test findings.

        Args:
            findings: List of findings
            test_type: Type of test

        Returns:
            Review results
        """
        # Categorize findings by severity
        categorized = {"critical": [], "high": [], "medium": [], "low": [], "informational": []}

        for finding in findings:
            finding.get("severity", "informational")
            cvss_score = finding.get("cvss_score", 0.0)

            # Validate severity matches CVSS
            validated_severity = self._validate_severity(cvss_score)

            categorized_finding = {
                "finding_id": finding.get("id", f"FIND-{len(categorized[validated_severity]) + 1}"),
                "title": finding.get("title", "Unknown finding"),
                "severity": validated_severity,
                "cvss_score": cvss_score,
                "description": finding.get("description", ""),
                "affected_systems": finding.get("affected_systems", []),
                "remediation": finding.get("remediation", ""),
                "remediation_sla_days": self.SEVERITY_LEVELS[validated_severity][
                    "remediation_sla_days"
                ],
                "remediation_deadline": (
                    datetime.now(UTC)
                    + timedelta(
                        days=self.SEVERITY_LEVELS[validated_severity]["remediation_sla_days"]
                    )
                ).isoformat(),
            }

            categorized[validated_severity].append(categorized_finding)

        # Map to OWASP Top 10
        owasp_mapping = self._map_to_owasp(findings)

        return {
            "status": "reviewed",
            "total_findings": len(findings),
            "findings_by_severity": {
                severity: len(items) for severity, items in categorized.items()
            },
            "categorized_findings": categorized,
            "owasp_mapping": owasp_mapping,
            "reviewed_at": datetime.now(UTC).isoformat(),
        }

    def _track_remediation(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Track remediation progress.

        Args:
            findings: List of findings with remediation status

        Returns:
            Remediation tracking results
        """
        remediation_status = {"completed": [], "in_progress": [], "not_started": [], "overdue": []}

        for finding in findings:
            finding_id = finding.get("id", "unknown")
            status = finding.get("remediation_status", "not_started")
            deadline = datetime.fromisoformat(
                finding.get("remediation_deadline", datetime.now(UTC).isoformat())
            )

            tracking_item = {
                "finding_id": finding_id,
                "title": finding.get("title", "Unknown"),
                "severity": finding.get("severity", "informational"),
                "status": status,
                "deadline": deadline.isoformat(),
                "days_until_deadline": (deadline - datetime.now(UTC)).days,
            }

            if status == "completed":
                remediation_status["completed"].append(tracking_item)
            elif deadline < datetime.now(UTC) and status != "completed":
                tracking_item["overdue_by_days"] = (datetime.now(UTC) - deadline).days
                remediation_status["overdue"].append(tracking_item)
            elif status == "in_progress":
                remediation_status["in_progress"].append(tracking_item)
            else:
                remediation_status["not_started"].append(tracking_item)

        # Calculate completion percentage
        total = len(findings)
        completed = len(remediation_status["completed"])
        completion_percentage = (completed / total * 100) if total > 0 else 0

        return {
            "status": "tracked",
            "total_findings": total,
            "completed": completed,
            "completion_percentage": round(completion_percentage, 1),
            "remediation_status": remediation_status,
            "overdue_count": len(remediation_status["overdue"]),
            "tracked_at": datetime.now(UTC).isoformat(),
        }

    def _coordinate_retest(self, findings: list[dict[str, Any]], test_type: str) -> dict[str, Any]:
        """
        Coordinate retest of remediated findings.

        Args:
            findings: Findings to retest
            test_type: Type of test

        Returns:
            Retest coordination results
        """
        # Filter findings that claim to be remediated
        remediated_findings = [f for f in findings if f.get("remediation_status") == "completed"]

        retest_id = f"RETEST-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        retest_date = datetime.now(UTC) + timedelta(days=7)  # Schedule retest in 1 week

        return {
            "status": "scheduled",
            "retest_id": retest_id,
            "original_test_type": test_type,
            "scheduled_date": retest_date.isoformat(),
            "findings_to_retest": len(remediated_findings),
            "retest_scope": [f.get("id") for f in remediated_findings],
            "estimated_duration_days": 2,
            "success_criteria": "All remediated findings must be verified as fixed",
        }

    def _get_last_test_date(
        self, test_type: str, previous_tests: list[dict[str, Any]]
    ) -> datetime | None:
        """Get date of last test of this type."""
        matching_tests = [t for t in previous_tests if t.get("test_type") == test_type]

        if not matching_tests:
            return None

        # Get most recent test
        most_recent = max(
            matching_tests,
            key=lambda t: datetime.fromisoformat(t.get("completion_date", "2000-01-01")),
        )

        return datetime.fromisoformat(most_recent.get("completion_date"))

    def _estimate_duration(self, test_type: TestType) -> int:
        """Estimate test duration in days."""
        durations = {
            TestType.EXTERNAL: 5,
            TestType.INTERNAL: 7,
            TestType.WEB_APP: 5,
            TestType.API: 3,
            TestType.MOBILE: 5,
            TestType.CLOUD: 7,
            TestType.SOCIAL_ENGINEERING: 10,
            TestType.WIRELESS: 3,
            TestType.PHYSICAL: 2,
        }
        return durations.get(test_type, 5)

    def _get_compliance_requirement(self, test_type: TestType) -> str:
        """Get compliance requirement for test type."""
        if test_type in [TestType.EXTERNAL, TestType.INTERNAL]:
            return "SOC 2 Type II, ISO 27001 (annual)"
        elif test_type == TestType.WEB_APP:
            return "PCI-DSS (quarterly for payment apps)"
        else:
            return "Security best practice"

    def _validate_severity(self, cvss_score: float) -> str:
        """Validate severity based on CVSS score."""
        for severity, info in self.SEVERITY_LEVELS.items():
            min_score, max_score = info["cvss_range"]
            if min_score <= cvss_score <= max_score:
                return severity
        return "informational"

    def _map_to_owasp(self, findings: list[dict[str, Any]]) -> dict[str, int]:
        """Map findings to OWASP Top 10 categories."""
        owasp_count = dict.fromkeys(self.OWASP_TOP_10, 0)

        for finding in findings:
            # Simple keyword matching (in production, use more sophisticated mapping)
            title = finding.get("title", "").lower()
            description = finding.get("description", "").lower()
            text = title + " " + description

            if "access control" in text or "authorization" in text:
                owasp_count["A01:2021-Broken Access Control"] += 1
            elif "crypto" in text or "encryption" in text:
                owasp_count["A02:2021-Cryptographic Failures"] += 1
            elif "injection" in text or "sql" in text or "xss" in text:
                owasp_count["A03:2021-Injection"] += 1
            elif "authentication" in text or "session" in text:
                owasp_count["A07:2021-Identification and Authentication Failures"] += 1
            elif "misconfiguration" in text or "configuration" in text:
                owasp_count["A05:2021-Security Misconfiguration"] += 1

        return {k: v for k, v in owasp_count.items() if v > 0}

    def _check_compliance_requirements(
        self, test_type: str, previous_tests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Check if testing meets compliance requirements."""
        try:
            test_type_enum = TestType(test_type)
        except ValueError:
            return {"compliant": False, "reason": "Invalid test type"}

        schedule_days = self.TEST_SCHEDULES.get(test_type_enum, 90)
        last_test_date = self._get_last_test_date(test_type, previous_tests)

        if not last_test_date:
            return {
                "compliant": False,
                "reason": "No previous tests found",
                "action_required": "Schedule initial pen test",
            }

        days_since_last_test = (datetime.now(UTC) - last_test_date).days
        overdue = days_since_last_test > schedule_days

        return {
            "compliant": not overdue,
            "test_type": test_type,
            "schedule_days": schedule_days,
            "last_test_date": last_test_date.isoformat(),
            "days_since_last_test": days_since_last_test,
            "overdue": overdue,
            "next_test_due": (last_test_date + timedelta(days=schedule_days)).isoformat(),
        }

    def _generate_test_plan(self, test_type: str, test_scope: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed test plan."""
        return {
            "test_type": test_type,
            "methodology": "PTES (Penetration Testing Execution Standard)",
            "frameworks": ["OWASP Top 10", "MITRE ATT&CK", "NIST SP 800-115"],
            "phases": [
                {
                    "phase": TestPhase.RECONNAISSANCE.value,
                    "duration_days": 1,
                    "activities": ["Information gathering", "OSINT", "Footprinting"],
                },
                {
                    "phase": TestPhase.SCANNING.value,
                    "duration_days": 1,
                    "activities": [
                        "Port scanning",
                        "Service enumeration",
                        "Vulnerability scanning",
                    ],
                },
                {
                    "phase": TestPhase.EXPLOITATION.value,
                    "duration_days": 2,
                    "activities": ["Exploit vulnerable services", "Gain initial access"],
                },
                {
                    "phase": TestPhase.POST_EXPLOITATION.value,
                    "duration_days": 1,
                    "activities": ["Privilege escalation", "Lateral movement", "Data access"],
                },
                {
                    "phase": TestPhase.REPORTING.value,
                    "duration_days": 2,
                    "activities": ["Finding documentation", "Report generation", "Presentation"],
                },
            ],
            "scope": test_scope,
            "rules_of_engagement": {
                "testing_hours": "Business hours only",
                "dos_testing": "Prohibited",
                "social_engineering": "Pre-approved targets only",
                "data_handling": "No exfiltration of real data",
            },
        }

    def _calculate_risk_metrics(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate risk metrics from findings."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}

        total_cvss = 0.0

        for finding in findings:
            severity = finding.get("severity", "informational")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            total_cvss += finding.get("cvss_score", 0.0)

        avg_cvss = total_cvss / len(findings) if findings else 0.0

        # Calculate overall risk score (weighted)
        risk_score = (
            severity_counts["critical"] * 10
            + severity_counts["high"] * 5
            + severity_counts["medium"] * 2
            + severity_counts["low"] * 1
        )

        return {
            "total_findings": len(findings),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "informational_count": severity_counts["informational"],
            "average_cvss": round(avg_cvss, 1),
            "risk_score": risk_score,
            "risk_level": "critical"
            if risk_score > 50
            else "high"
            if risk_score > 20
            else "medium",
        }

    def _generate_recommendations(
        self,
        action: str,
        result: dict[str, Any],
        compliance_status: dict[str, Any],
        risk_metrics: dict[str, Any] | None,
    ) -> list[str]:
        """Generate pen test recommendations."""
        recommendations = []

        if not compliance_status.get("compliant"):
            recommendations.append(
                f"COMPLIANCE GAP: {compliance_status.get('reason')}. "
                f"{compliance_status.get('action_required', 'Schedule pen test')}"
            )

        if risk_metrics:
            if risk_metrics["critical_count"] > 0:
                recommendations.append(
                    f"CRITICAL: {risk_metrics['critical_count']} critical findings. "
                    "Remediate within 7 days."
                )

            if risk_metrics["risk_level"] in ["critical", "high"]:
                recommendations.append(
                    f"Overall risk level: {risk_metrics['risk_level']}. "
                    "Prioritize remediation efforts."
                )

        if action == "schedule":
            recommendations.append(
                f"Test scheduled for {result.get('scheduled_date', 'unknown')[:10]}. "
                "Coordinate with vendor and internal teams."
            )

        if action == "remediation_track" and result.get("overdue_count", 0) > 0:
            recommendations.append(
                f"{result['overdue_count']} findings overdue for remediation. "
                "Escalate to engineering leadership."
            )

        recommendations.append(
            "Maintain pen test artifacts for compliance audits (SOC 2, ISO 27001)"
        )

        return recommendations

    def _format_coordination_report(
        self,
        action: str,
        test_type: str,
        result: dict[str, Any],
        test_plan: dict[str, Any] | None,
        compliance_status: dict[str, Any],
        risk_metrics: dict[str, Any] | None,
        recommendations: list[str],
    ) -> str:
        """Format pen test coordination report."""
        compliance_icon = "✅" if compliance_status.get("compliant") else "⚠️"

        report = f"""**Penetration Test Coordination Report**

**Action:** {action.upper().replace("_", " ")}
**Test Type:** {test_type}
**Compliance Status:** {compliance_icon} {"COMPLIANT" if compliance_status.get("compliant") else "GAP DETECTED"}

"""

        # Scheduling details
        if action == "schedule":
            report += "**Test Scheduled:**\n"
            report += f"- Test ID: {result.get('test_id')}\n"
            report += f"- Scheduled Date: {result.get('scheduled_date', 'unknown')[:10]}\n"
            report += f"- Duration: {result.get('estimated_duration_days')} days\n"
            report += f"- Frequency: Every {result.get('schedule_frequency_days')} days\n\n"

            if test_plan:
                report += "**Test Plan:**\n"
                report += f"- Methodology: {test_plan['methodology']}\n"
                report += f"- Frameworks: {', '.join(test_plan['frameworks'])}\n"
                report += f"- Phases: {len(test_plan['phases'])}\n\n"

        # Findings review
        if action == "findings_review" and risk_metrics:
            report += "**Findings Summary:**\n"
            report += f"- Total: {risk_metrics['total_findings']}\n"
            report += f"- 🔴 Critical: {risk_metrics['critical_count']}\n"
            report += f"- ⚠️ High: {risk_metrics['high_count']}\n"
            report += f"- 📋 Medium: {risk_metrics['medium_count']}\n"
            report += f"- ℹ️ Low: {risk_metrics['low_count']}\n"
            report += f"- Average CVSS: {risk_metrics['average_cvss']}\n"
            report += f"- Risk Level: {risk_metrics['risk_level'].upper()}\n\n"

        # Remediation tracking
        if action == "remediation_track":
            report += "**Remediation Progress:**\n"
            report += f"- Completion: {result.get('completion_percentage', 0)}%\n"
            report += (
                f"- Completed: {result.get('completed', 0)}/{result.get('total_findings', 0)}\n"
            )
            report += f"- Overdue: {result.get('overdue_count', 0)}\n\n"

        # Compliance
        if not compliance_status.get("compliant"):
            report += "**Compliance Gap:**\n"
            report += f"- {compliance_status.get('reason')}\n"
            report += f"- Last Test: {compliance_status.get('last_test_date', 'None')[:10]}\n"
            report += f"- Next Due: {compliance_status.get('next_test_due', 'unknown')[:10]}\n\n"

        # Recommendations
        if recommendations:
            report += "**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Coordination completed at {datetime.now(UTC).isoformat()}*"
        report += "\n*Compliance: SOC 2, ISO 27001, PCI-DSS*"

        return report
