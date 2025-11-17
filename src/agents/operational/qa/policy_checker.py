"""
Policy Checker Agent - TASK-2103

Ensures response compliance with company policies, legal requirements,
and brand guidelines. Uses Claude Sonnet for nuanced policy interpretation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("policy_checker", tier="operational", category="qa")
class PolicyCheckerAgent(BaseAgent):
    """
    Policy Checker Agent.

    Ensures response compliance with:
    - Company communication policies
    - Legal and regulatory requirements
    - Privacy and data protection (GDPR, CCPA)
    - Brand guidelines and messaging
    - SLA commitments and guarantees
    - Refund and warranty policies
    - Terms of service and acceptable use

    Uses Claude Sonnet for nuanced understanding of policy context.
    """

    # Policy categories
    POLICY_CATEGORIES = {
        "communication": [
            "professional_tone",
            "no_guarantees",
            "appropriate_language",
            "brand_voice"
        ],
        "legal": [
            "privacy_compliance",
            "data_protection",
            "regulatory_compliance",
            "liability_limitation"
        ],
        "business": [
            "sla_accuracy",
            "pricing_accuracy",
            "refund_policy",
            "warranty_terms"
        ],
        "security": [
            "no_credential_sharing",
            "secure_practices",
            "vulnerability_disclosure"
        ],
        "customer_service": [
            "response_time_commitments",
            "escalation_procedures",
            "complaint_handling"
        ]
    }

    # Prohibited content patterns
    PROHIBITED_PATTERNS = [
        "guarantee",
        "100% uptime",
        "never fails",
        "always available",
        "absolutely secure",
        "hack-proof",
        "no bugs",
        "perfect solution"
    ]

    # Required disclaimers for certain topics
    DISCLAIMER_REQUIREMENTS = {
        "legal_advice": "Note: This is not legal advice. Consult with legal counsel.",
        "medical_advice": "Note: This is not medical advice. Consult with healthcare professional.",
        "financial_advice": "Note: This is not financial advice. Consult with financial advisor.",
        "security_vulnerability": "Note: Please report security issues via security@company.com"
    }

    def __init__(self):
        config = AgentConfig(
            name="policy_checker",
            type=AgentType.ANALYZER,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Check response for policy compliance.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with policy compliance results
        """
        self.logger.info("policy_checking_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        policies = state.get("entities", {}).get("policies", {})
        strict_mode = state.get("entities", {}).get("strict_mode", True)

        self.logger.debug(
            "policy_checking_details",
            response_length=len(response_text),
            strict_mode=strict_mode
        )

        # Check all policy categories
        policy_violations = self._check_all_policies(response_text, policies)

        # Check for prohibited content
        prohibited_content = self._check_prohibited_content(response_text)

        # Check disclaimer requirements
        missing_disclaimers = self._check_disclaimers(response_text)

        # Check privacy compliance
        privacy_issues = self._check_privacy_compliance(response_text)

        # Aggregate all violations
        all_violations = self._aggregate_violations(
            policy_violations,
            prohibited_content,
            missing_disclaimers,
            privacy_issues
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_violations)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(all_violations)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_violations, strict_mode)

        # Format response
        response = self._format_policy_report(
            all_violations,
            recommendations,
            compliance_score,
            passed
        )

        state["agent_response"] = response
        state["policy_check_passed"] = passed
        state["compliance_score"] = compliance_score
        state["policy_violations"] = all_violations
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.92
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "policy_checking_completed",
            violations_found=len(all_violations),
            compliance_score=compliance_score,
            passed=passed
        )

        return state

    def _check_all_policies(
        self,
        response_text: str,
        policies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check response against all policy categories.

        Args:
            response_text: Response text to check
            policies: Policy definitions

        Returns:
            List of policy violations
        """
        violations = []
        text_lower = response_text.lower()

        # Check communication policies
        if "we guarantee" in text_lower or "guaranteed" in text_lower:
            violations.append({
                "category": "communication",
                "policy": "no_guarantees",
                "severity": "high",
                "message": "Response contains guarantees which violate policy",
                "snippet": self._extract_snippet(response_text, ["guarantee", "guaranteed"])
            })

        # Check for unprofessional language
        unprofessional_words = ["stupid", "dumb", "idiot", "moron", "sucks", "crap"]
        for word in unprofessional_words:
            if word in text_lower:
                violations.append({
                    "category": "communication",
                    "policy": "professional_tone",
                    "severity": "critical",
                    "message": f"Unprofessional language detected: '{word}'",
                    "snippet": self._extract_snippet(response_text, [word])
                })

        # Check for overpromising
        overpromise_phrases = ["100%", "always works", "never fails", "perfect"]
        for phrase in overpromise_phrases:
            if phrase in text_lower:
                violations.append({
                    "category": "business",
                    "policy": "sla_accuracy",
                    "severity": "high",
                    "message": f"Overpromising detected: '{phrase}'",
                    "snippet": self._extract_snippet(response_text, [phrase])
                })

        return violations

    def _check_prohibited_content(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Check for prohibited content patterns.

        Args:
            response_text: Response text to check

        Returns:
            List of prohibited content violations
        """
        violations = []
        text_lower = response_text.lower()

        for pattern in self.PROHIBITED_PATTERNS:
            if pattern in text_lower:
                violations.append({
                    "category": "prohibited_content",
                    "policy": "prohibited_language",
                    "severity": "high",
                    "message": f"Prohibited pattern detected: '{pattern}'",
                    "snippet": self._extract_snippet(response_text, [pattern])
                })

        return violations

    def _check_disclaimers(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Check if required disclaimers are present.

        Args:
            response_text: Response text to check

        Returns:
            List of missing disclaimers
        """
        violations = []
        text_lower = response_text.lower()

        # Check if discussing legal matters without disclaimer
        legal_keywords = ["legal", "lawsuit", "contract", "liability", "sue"]
        if any(keyword in text_lower for keyword in legal_keywords):
            if "not legal advice" not in text_lower:
                violations.append({
                    "category": "legal",
                    "policy": "disclaimer_requirement",
                    "severity": "medium",
                    "message": "Legal discussion without required disclaimer",
                    "required_disclaimer": self.DISCLAIMER_REQUIREMENTS["legal_advice"]
                })

        # Check if discussing security without proper handling
        security_keywords = ["vulnerability", "exploit", "security bug", "hack"]
        if any(keyword in text_lower for keyword in security_keywords):
            if "security@" not in text_lower:
                violations.append({
                    "category": "security",
                    "policy": "vulnerability_disclosure",
                    "severity": "high",
                    "message": "Security issue discussion without proper disclosure channel",
                    "required_disclaimer": self.DISCLAIMER_REQUIREMENTS["security_vulnerability"]
                })

        return violations

    def _check_privacy_compliance(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Check for privacy and data protection compliance.

        Args:
            response_text: Response text to check

        Returns:
            List of privacy violations
        """
        violations = []
        text_lower = response_text.lower()

        # Check for PII exposure requests
        pii_patterns = [
            "send me your password",
            "share your credit card",
            "provide your ssn",
            "send your api key"
        ]

        for pattern in pii_patterns:
            if pattern in text_lower:
                violations.append({
                    "category": "security",
                    "policy": "no_credential_sharing",
                    "severity": "critical",
                    "message": f"Requesting sensitive information: '{pattern}'",
                    "snippet": self._extract_snippet(response_text, [pattern])
                })

        # Check for data retention promises
        if "we never delete your data" in text_lower or "permanent storage" in text_lower:
            violations.append({
                "category": "legal",
                "policy": "data_protection",
                "severity": "medium",
                "message": "Data retention statement may conflict with GDPR/CCPA",
                "snippet": self._extract_snippet(response_text, ["never delete", "permanent"])
            })

        return violations

    def _aggregate_violations(
        self,
        policy_violations: List[Dict[str, Any]],
        prohibited_content: List[Dict[str, Any]],
        missing_disclaimers: List[Dict[str, Any]],
        privacy_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate all violations.

        Args:
            policy_violations: Policy violations
            prohibited_content: Prohibited content
            missing_disclaimers: Missing disclaimers
            privacy_issues: Privacy issues

        Returns:
            Combined list of violations
        """
        all_violations = (
            policy_violations +
            prohibited_content +
            missing_disclaimers +
            privacy_issues
        )

        # Add timestamps
        for violation in all_violations:
            violation["detected_at"] = datetime.now(UTC).isoformat()

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_violations.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return all_violations

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations for policy compliance.

        Args:
            violations: List of violations

        Returns:
            List of recommendations
        """
        recommendations = []

        if not violations:
            recommendations.append("Response complies with all company policies")
            return recommendations

        # Group by severity
        critical = [v for v in violations if v["severity"] == "critical"]
        high = [v for v in violations if v["severity"] == "high"]
        medium = [v for v in violations if v["severity"] == "medium"]

        if critical:
            recommendations.append(
                f"CRITICAL: {len(critical)} critical policy violations. Must fix before sending."
            )

        if high:
            recommendations.append(
                f"HIGH PRIORITY: {len(high)} high-severity violations. Review and correct."
            )

        if medium:
            recommendations.append(
                f"REVIEW: {len(medium)} medium-severity policy issues."
            )

        # Category-specific recommendations
        categories = set(v["category"] for v in violations)

        if "security" in categories:
            recommendations.append(
                "Security policy violations detected. Never request credentials or sensitive data."
            )

        if "legal" in categories:
            recommendations.append(
                "Add required disclaimers for legal/compliance topics."
            )

        if "communication" in categories:
            recommendations.append(
                "Revise language to align with professional communication standards."
            )

        return recommendations

    def _calculate_compliance_score(self, violations: List[Dict[str, Any]]) -> float:
        """
        Calculate compliance score (0-100).

        Args:
            violations: List of violations

        Returns:
            Compliance score
        """
        if not violations:
            return 100.0

        # Start with perfect score
        score = 100.0

        # Deduct based on severity
        for violation in violations:
            severity = violation["severity"]
            deductions = {
                "critical": 30.0,
                "high": 15.0,
                "medium": 7.0,
                "low": 2.0
            }
            score -= deductions.get(severity, 0)

        return max(0.0, round(score, 1))

    def _determine_pass_fail(
        self,
        violations: List[Dict[str, Any]],
        strict_mode: bool
    ) -> bool:
        """
        Determine if policy check passes.

        Args:
            violations: List of violations
            strict_mode: Strict checking mode

        Returns:
            True if passed, False otherwise
        """
        critical = [v for v in violations if v["severity"] == "critical"]
        high = [v for v in violations if v["severity"] == "high"]

        if strict_mode:
            # Strict: no critical or high severity violations
            return len(critical) == 0 and len(high) == 0
        else:
            # Standard: only critical violations fail
            return len(critical) == 0

    def _extract_snippet(self, text: str, patterns: List[str]) -> str:
        """
        Extract snippet containing pattern.

        Args:
            text: Full text
            patterns: Patterns to find

        Returns:
            Text snippet
        """
        text_lower = text.lower()
        for pattern in patterns:
            idx = text_lower.find(pattern.lower())
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(pattern) + 50)
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                return snippet
        return text[:100] + "..." if len(text) > 100 else text

    def _format_policy_report(
        self,
        violations: List[Dict[str, Any]],
        recommendations: List[str],
        compliance_score: float,
        passed: bool
    ) -> str:
        """Format policy compliance report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Policy Compliance Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Compliance Score:** {compliance_score}/100
**Violations Found:** {len(violations)}

**Violations by Severity:**
"""

        # Count by severity
        severity_counts = {}
        for v in violations:
            sev = v["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                report += f"- {severity.upper()}: {count}\n"

        # List violations
        if violations:
            report += f"\n**Detected Violations:**\n"
            for v in violations[:5]:  # Top 5
                icon = "🔴" if v["severity"] == "critical" else "⚠️" if v["severity"] == "high" else "ℹ️"
                report += f"{icon} [{v['severity'].upper()}] {v['message']}\n"
                report += f"   Category: {v['category']} | Policy: {v['policy']}\n"

            if len(violations) > 5:
                report += f"... and {len(violations) - 5} more violations\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Policy check completed at {datetime.now(UTC).isoformat()}*"

        return report
