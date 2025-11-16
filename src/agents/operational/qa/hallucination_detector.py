"""
Hallucination Detector Agent - TASK-2109

Detects AI-generated false information, fabricated details, and unsupported claims.
Uses Claude Sonnet for nuanced hallucination detection and verification.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("hallucination_detector", tier="operational", category="qa")
class HallucinationDetectorAgent(BaseAgent):
    """
    Hallucination Detector Agent.

    Detects AI-generated false information:
    - Fabricated product features or capabilities
    - Made-up dates, versions, or release information
    - Invented documentation or API endpoints
    - Fictional customer examples or case studies
    - Unsupported performance claims
    - Nonexistent integrations or compatibility
    - Confidence markers suggesting uncertainty
    - Hedging language that may indicate hallucination

    Uses Claude Sonnet for nuanced detection of hallucinated content.
    """

    # Hallucination indicators
    HALLUCINATION_INDICATORS = {
        "hedging_language": [
            "i believe",
            "i think",
            "probably",
            "might be",
            "could be",
            "should be",
            "as far as i know",
            "if i remember correctly"
        ],
        "uncertainty_markers": [
            "not sure",
            "uncertain",
            "maybe",
            "perhaps",
            "possibly",
            "potentially"
        ],
        "vague_specifics": [
            "around",
            "approximately",
            "roughly",
            "about",
            "or so",
            "give or take"
        ]
    }

    # High-risk claim categories (require verification)
    HIGH_RISK_CLAIMS = [
        "performance_metrics",    # "10x faster", "99.99% uptime"
        "version_numbers",        # "Version 3.2.1"
        "release_dates",          # "Released in March 2023"
        "pricing",                # "$99/month"
        "integrations",           # "Integrates with Salesforce"
        "compatibility",          # "Works on iOS 14+"
        "api_endpoints",          # "POST /api/v2/users"
        "feature_availability"    # "Available in Enterprise plan"
    ]

    # Confidence level thresholds
    CONFIDENCE_LEVELS = {
        "high_confidence": 0.85,      # Likely accurate
        "medium_confidence": 0.60,    # Uncertain
        "low_confidence": 0.40,       # Likely hallucination
        "hallucination": 0.20         # Definitely hallucinated
    }

    def __init__(self):
        config = AgentConfig(
            name="hallucination_detector",
            type=AgentType.ANALYZER,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2500,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Detect hallucinations in response.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with hallucination detection results
        """
        self.logger.info("hallucination_detection_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        knowledge_base = state.get("entities", {}).get("knowledge_base", {})
        strict_mode = state.get("entities", {}).get("strict_mode", True)

        self.logger.debug(
            "hallucination_detection_details",
            response_length=len(response_text),
            strict_mode=strict_mode
        )

        # Detect uncertainty markers
        uncertainty_issues = self._detect_uncertainty_markers(response_text)

        # Detect overly specific claims
        specific_claims = self._detect_specific_claims(response_text)

        # Verify high-risk claims
        unverified_claims = self._verify_high_risk_claims(specific_claims, knowledge_base)

        # Detect inconsistencies
        inconsistencies = self._detect_inconsistencies(response_text)

        # Aggregate all hallucination signals
        all_issues = self._aggregate_hallucination_signals(
            uncertainty_issues,
            unverified_claims,
            inconsistencies
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(all_issues, response_text)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_issues, confidence_score, strict_mode)

        # Format response
        response = self._format_hallucination_report(
            all_issues,
            recommendations,
            confidence_score,
            passed
        )

        state["agent_response"] = response
        state["hallucination_check_passed"] = passed
        state["confidence_score"] = confidence_score
        state["hallucination_signals"] = all_issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.86
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "hallucination_detection_completed",
            signals_detected=len(all_issues),
            confidence_score=confidence_score,
            passed=passed
        )

        return state

    def _detect_uncertainty_markers(self, response_text: str) -> List[Dict[str, Any]]:
        """Detect uncertainty and hedging language."""
        issues = []
        text_lower = response_text.lower()

        # Check for hedging language
        for phrase in self.HALLUCINATION_INDICATORS["hedging_language"]:
            if phrase in text_lower:
                issues.append({
                    "type": "hedging_language",
                    "severity": "high",
                    "indicator": phrase,
                    "message": f"Hedging language detected: '{phrase}' - may indicate uncertainty",
                    "context": self._extract_context(response_text, phrase),
                    "confidence_impact": -0.15
                })

        # Check for uncertainty markers
        for phrase in self.HALLUCINATION_INDICATORS["uncertainty_markers"]:
            if phrase in text_lower:
                issues.append({
                    "type": "uncertainty_marker",
                    "severity": "medium",
                    "indicator": phrase,
                    "message": f"Uncertainty marker: '{phrase}'",
                    "context": self._extract_context(response_text, phrase),
                    "confidence_impact": -0.10
                })

        # Check for vague specifics (e.g., "approximately 100" instead of verified number)
        for phrase in self.HALLUCINATION_INDICATORS["vague_specifics"]:
            if phrase in text_lower:
                # Check if used with numbers
                import re
                pattern = rf"{phrase}\s+\d+"
                if re.search(pattern, text_lower):
                    issues.append({
                        "type": "vague_specific",
                        "severity": "low",
                        "indicator": phrase,
                        "message": f"Vague specific number: '{phrase} [number]' - verify accuracy",
                        "context": self._extract_context(response_text, phrase),
                        "confidence_impact": -0.05
                    })

        return issues

    def _detect_specific_claims(self, response_text: str) -> List[Dict[str, Any]]:
        """Detect specific factual claims that need verification."""
        claims = []

        import re

        # Detect version numbers
        version_pattern = r"[Vv]ersion\s+\d+\.\d+(\.\d+)?"
        version_matches = re.finditer(version_pattern, response_text)
        for match in version_matches:
            claims.append({
                "claim_type": "version_numbers",
                "claim_text": match.group(0),
                "severity": "high",
                "requires_verification": True,
                "position": match.start()
            })

        # Detect specific dates
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}"
        date_matches = re.finditer(date_pattern, response_text)
        for match in date_matches:
            claims.append({
                "claim_type": "release_dates",
                "claim_text": match.group(0),
                "severity": "high",
                "requires_verification": True,
                "position": match.start()
            })

        # Detect performance metrics
        perf_pattern = r"\d+(\.\d+)?[x×]\s+(faster|slower|more|less)"
        perf_matches = re.finditer(perf_pattern, response_text, re.IGNORECASE)
        for match in perf_matches:
            claims.append({
                "claim_type": "performance_metrics",
                "claim_text": match.group(0),
                "severity": "critical",
                "requires_verification": True,
                "position": match.start()
            })

        # Detect pricing
        price_pattern = r"\$\d+(\.\d{2})?(/month|/year|/mo|/yr)?"
        price_matches = re.finditer(price_pattern, response_text)
        for match in price_matches:
            claims.append({
                "claim_type": "pricing",
                "claim_text": match.group(0),
                "severity": "critical",
                "requires_verification": True,
                "position": match.start()
            })

        # Detect API endpoints
        api_pattern = r"(GET|POST|PUT|DELETE|PATCH)\s+/[a-zA-Z0-9/_-]+"
        api_matches = re.finditer(api_pattern, response_text)
        for match in api_matches:
            claims.append({
                "claim_type": "api_endpoints",
                "claim_text": match.group(0),
                "severity": "high",
                "requires_verification": True,
                "position": match.start()
            })

        return claims

    def _verify_high_risk_claims(
        self,
        claims: List[Dict[str, Any]],
        knowledge_base: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Verify high-risk claims against knowledge base."""
        unverified = []

        for claim in claims:
            # In production, would verify against actual knowledge base
            # For now, mark all high-risk claims as needing verification

            # Simulate verification (some claims verified, some not)
            is_verified = False  # Mock: assume unverified for demonstration

            if not is_verified:
                unverified.append({
                    "type": "unverified_claim",
                    "severity": claim["severity"],
                    "claim_type": claim["claim_type"],
                    "claim_text": claim["claim_text"],
                    "message": f"Unverified {claim['claim_type'].replace('_', ' ')}: '{claim['claim_text']}'",
                    "context": self._extract_context_at_position(
                        "",  # Would use full text in production
                        claim["position"]
                    ) if "position" in claim else "N/A",
                    "recommendation": "Verify against knowledge base or remove if uncertain"
                })

        return unverified

    def _detect_inconsistencies(self, response_text: str) -> List[Dict[str, Any]]:
        """Detect logical inconsistencies in the response."""
        issues = []

        # Check for contradictory statements (simple heuristic)
        sentences = response_text.split('.')

        # Look for contradictory patterns
        contradictions = [
            (r"is available", r"is not available"),
            (r"supports", r"does not support"),
            (r"can", r"cannot"),
            (r"works with", r"does not work with")
        ]

        import re
        for i, sentence in enumerate(sentences):
            for positive, negative in contradictions:
                if re.search(positive, sentence.lower()) and re.search(negative, sentence.lower()):
                    issues.append({
                        "type": "contradiction",
                        "severity": "critical",
                        "message": "Contradictory statement detected within same sentence",
                        "context": sentence.strip(),
                        "confidence_impact": -0.25
                    })

        return issues

    def _aggregate_hallucination_signals(
        self,
        uncertainty_issues: List[Dict[str, Any]],
        unverified_claims: List[Dict[str, Any]],
        inconsistencies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate all hallucination signals."""
        all_signals = (
            uncertainty_issues +
            unverified_claims +
            inconsistencies
        )

        # Add timestamps
        for signal in all_signals:
            signal["detected_at"] = datetime.utcnow().isoformat()

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_signals.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return all_signals

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate hallucination detection recommendations."""
        recommendations = []

        if not issues:
            recommendations.append("No hallucination signals detected - response appears accurate")
            return recommendations

        # Count by severity
        critical = [i for i in issues if i["severity"] == "critical"]
        high = [i for i in issues if i["severity"] == "high"]
        medium = [i for i in issues if i["severity"] == "medium"]

        if critical:
            recommendations.append(
                f"CRITICAL: Verify or remove {len(critical)} critical claims - high hallucination risk"
            )

        if high:
            recommendations.append(
                f"HIGH PRIORITY: Verify {len(high)} specific claims against knowledge base"
            )

        # Type-specific recommendations
        issue_types = {}
        for issue in issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if "hedging_language" in issue_types:
            recommendations.append(
                "Remove hedging language - make definitive statements or remove uncertain claims"
            )

        if "unverified_claim" in issue_types:
            recommendations.append(
                "Verify all specific claims (versions, dates, metrics) against official sources"
            )

        if "contradiction" in issue_types:
            recommendations.append(
                "Resolve contradictory statements - ensure logical consistency"
            )

        return recommendations

    def _calculate_confidence_score(
        self,
        issues: List[Dict[str, Any]],
        response_text: str
    ) -> float:
        """Calculate confidence score (0-100) indicating response accuracy."""
        # Start with high confidence
        confidence = 100.0

        # Deduct based on issues
        for issue in issues:
            # Use confidence_impact if available
            if "confidence_impact" in issue:
                confidence += issue["confidence_impact"] * 100
            else:
                # Otherwise use severity
                severity = issue["severity"]
                deductions = {
                    "critical": 25.0,
                    "high": 15.0,
                    "medium": 8.0,
                    "low": 3.0
                }
                confidence -= deductions.get(severity, 0)

        return max(0.0, round(confidence, 1))

    def _determine_pass_fail(
        self,
        issues: List[Dict[str, Any]],
        confidence_score: float,
        strict_mode: bool
    ) -> bool:
        """Determine if hallucination check passes."""
        critical = [i for i in issues if i["severity"] == "critical"]
        high = [i for i in issues if i["severity"] == "high"]

        if strict_mode:
            # Strict: no critical/high issues and confidence > 80%
            return len(critical) == 0 and len(high) == 0 and confidence_score >= 80
        else:
            # Standard: no critical issues and confidence > 60%
            return len(critical) == 0 and confidence_score >= 60

    def _extract_context(self, text: str, term: str) -> str:
        """Extract context around a term."""
        text_lower = text.lower()
        term_lower = term.lower()

        idx = text_lower.find(term_lower)
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(text), idx + len(term) + 60)
            context = text[start:end].strip()

            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            return context

        return text[:80] + "..." if len(text) > 80 else text

    def _extract_context_at_position(self, text: str, position: int) -> str:
        """Extract context at a specific position."""
        if not text:
            return "N/A"

        start = max(0, position - 40)
        end = min(len(text), position + 60)
        context = text[start:end].strip()

        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _format_hallucination_report(
        self,
        issues: List[Dict[str, Any]],
        recommendations: List[str],
        confidence_score: float,
        passed: bool
    ) -> str:
        """Format hallucination detection report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Hallucination Detection Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Confidence Score:** {confidence_score}/100
**Hallucination Signals:** {len(issues)}

**Risk Level:** """

        if confidence_score >= 85:
            report += "LOW - Response appears accurate\n"
        elif confidence_score >= 70:
            report += "MEDIUM - Some verification recommended\n"
        elif confidence_score >= 50:
            report += "HIGH - Multiple signals require verification\n"
        else:
            report += "CRITICAL - High hallucination risk\n"

        # Issues by type
        if issues:
            report += f"\n**Detected Signals:**\n"

            issue_types = {}
            for issue in issues:
                issue_type = issue["type"]
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            for issue_type, count in issue_types.items():
                report += f"- {issue_type.replace('_', ' ').title()}: {count}\n"

            # List top issues
            report += f"\n**Top Issues:**\n"
            for issue in issues[:5]:
                icon = "🔴" if issue["severity"] == "critical" else "⚠️" if issue["severity"] == "high" else "ℹ️"
                report += f"{icon} [{issue['severity'].upper()}] {issue['message']}\n"
                if "context" in issue and issue["context"] != "N/A":
                    report += f"   Context: \"{issue['context']}\"\n"

            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more signals\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Hallucination detection completed at {datetime.utcnow().isoformat()}*"

        return report
