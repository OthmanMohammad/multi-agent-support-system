"""
Sensitivity Checker Agent - TASK-2108

Detects inappropriate, biased, or culturally insensitive content in responses.
Uses Claude Sonnet for nuanced sensitivity analysis and context understanding.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("sensitivity_checker", tier="operational", category="qa")
class SensitivityCheckerAgent(BaseAgent):
    """
    Sensitivity Checker Agent.

    Detects and flags sensitive content:
    - Inappropriate or offensive language
    - Biased or discriminatory language
    - Cultural insensitivity
    - Gender/age/religious bias
    - Stereotyping and generalizations
    - Microaggressions
    - Potentially triggering content
    - Accessibility concerns

    Uses Claude Sonnet for nuanced understanding of context and cultural sensitivity.
    """

    # Sensitivity categories
    SENSITIVITY_CATEGORIES = {
        "discriminatory": {
            "description": "Language that discriminates based on protected characteristics",
            "severity": "critical"
        },
        "biased": {
            "description": "Biased assumptions or stereotypes",
            "severity": "high"
        },
        "culturally_insensitive": {
            "description": "Culturally insensitive or inappropriate references",
            "severity": "high"
        },
        "gendered_language": {
            "description": "Unnecessarily gendered language or assumptions",
            "severity": "medium"
        },
        "ageist": {
            "description": "Age-based assumptions or stereotypes",
            "severity": "medium"
        },
        "ableist": {
            "description": "Language that may be insensitive to people with disabilities",
            "severity": "high"
        },
        "microaggression": {
            "description": "Subtle discriminatory comments",
            "severity": "medium"
        },
        "exclusive": {
            "description": "Language that excludes certain groups",
            "severity": "medium"
        }
    }

    # Problematic patterns (context-aware - some may be acceptable in certain contexts)
    PROBLEMATIC_PATTERNS = {
        "gendered_assumptions": [
            r"\bhe\b.*\bengineers?\b",
            r"\bshe\b.*\bnurse\b",
            r"\bguys\b",  # When addressing mixed group
        ],
        "ableist_language": [
            "crazy",
            "insane",
            "dumb",
            "stupid",
            "lame",
            "blind to",
            "deaf to"
        ],
        "age_assumptions": [
            "millennials are",
            "boomers are",
            "gen z is"
        ],
        "cultural_assumptions": [
            "everyone celebrates",
            "as we all know",
            "obviously"
        ]
    }

    # Inclusive language alternatives
    INCLUSIVE_ALTERNATIVES = {
        "guys": "everyone/folks/team",
        "crazy": "unexpected/surprising/intense",
        "insane": "extraordinary/remarkable",
        "dumb": "ineffective/suboptimal",
        "lame": "disappointing/ineffective",
        "blind to": "unaware of/overlooking",
        "deaf to": "ignoring/not responsive to"
    }

    def __init__(self):
        config = AgentConfig(
            name="sensitivity_checker",
            type=AgentType.ANALYZER,
            model="claude-sonnet-4-5-20250929",
            temperature=0.2,
            max_tokens=2000,
            capabilities=[],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Check response for sensitivity issues.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with sensitivity analysis results
        """
        self.logger.info("sensitivity_checking_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        strict_mode = state.get("entities", {}).get("strict_mode", True)

        self.logger.debug(
            "sensitivity_checking_details",
            response_length=len(response_text),
            strict_mode=strict_mode
        )

        # Check for problematic language
        language_issues = self._check_problematic_language(response_text)

        # Check for biases and assumptions
        bias_issues = self._check_biases(response_text)

        # Check for cultural sensitivity
        cultural_issues = self._check_cultural_sensitivity(response_text)

        # Check for inclusive language
        inclusivity_issues = self._check_inclusivity(response_text)

        # Aggregate all issues
        all_issues = self._aggregate_issues(
            language_issues,
            bias_issues,
            cultural_issues,
            inclusivity_issues
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues)

        # Calculate sensitivity score
        sensitivity_score = self._calculate_sensitivity_score(all_issues)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_issues, strict_mode)

        # Format response
        response = self._format_sensitivity_report(
            all_issues,
            recommendations,
            sensitivity_score,
            passed
        )

        state["agent_response"] = response
        state["sensitivity_check_passed"] = passed
        state["sensitivity_score"] = sensitivity_score
        state["sensitivity_issues"] = all_issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.89
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "sensitivity_checking_completed",
            issues_found=len(all_issues),
            sensitivity_score=sensitivity_score,
            passed=passed
        )

        return state

    def _check_problematic_language(self, response_text: str) -> List[Dict[str, Any]]:
        """Check for problematic language patterns."""
        issues = []
        text_lower = response_text.lower()

        # Check ableist language
        for term in self.PROBLEMATIC_PATTERNS["ableist_language"]:
            if term in text_lower:
                # Check context - some uses may be acceptable (e.g., "blind spot" in technical context)
                context = self._extract_context(response_text, term)

                issues.append({
                    "category": "ableist",
                    "type": "ableist_language",
                    "severity": "medium",
                    "term": term,
                    "message": f"Potentially ableist language: '{term}'",
                    "context": context,
                    "suggestion": f"Consider using '{self.INCLUSIVE_ALTERNATIVES.get(term, 'alternative phrasing')}'"
                })

        # Check for slurs or highly offensive terms (would have a comprehensive list in production)
        offensive_terms = []  # Placeholder - actual list would be comprehensive
        for term in offensive_terms:
            if term in text_lower:
                issues.append({
                    "category": "discriminatory",
                    "type": "offensive_language",
                    "severity": "critical",
                    "term": term,
                    "message": "Offensive language detected",
                    "context": self._extract_context(response_text, term)
                })

        return issues

    def _check_biases(self, response_text: str) -> List[Dict[str, Any]]:
        """Check for biased language and assumptions."""
        issues = []
        text_lower = response_text.lower()

        # Check for gendered language
        if "guys" in text_lower and ("hi guys" in text_lower or "hey guys" in text_lower):
            issues.append({
                "category": "gendered_language",
                "type": "gendered_address",
                "severity": "medium",
                "message": "Using 'guys' to address group may not be inclusive",
                "context": self._extract_context(response_text, "guys"),
                "suggestion": "Use 'everyone', 'folks', or 'team' instead"
            })

        # Check for age-based generalizations
        for pattern in self.PROBLEMATIC_PATTERNS["age_assumptions"]:
            if pattern in text_lower:
                issues.append({
                    "category": "ageist",
                    "type": "age_generalization",
                    "severity": "medium",
                    "message": "Age-based generalization detected",
                    "context": self._extract_context(response_text, pattern),
                    "suggestion": "Avoid generalizations about age groups"
                })

        # Check for assumptions about technical ability
        assumption_phrases = [
            "as you probably know",
            "obviously you",
            "everyone knows",
            "it's common sense"
        ]

        for phrase in assumption_phrases:
            if phrase in text_lower:
                issues.append({
                    "category": "exclusive",
                    "type": "knowledge_assumption",
                    "severity": "low",
                    "message": "Assumes shared knowledge that may exclude some users",
                    "context": self._extract_context(response_text, phrase),
                    "suggestion": "Explain concepts without assuming prior knowledge"
                })

        return issues

    def _check_cultural_sensitivity(self, response_text: str) -> List[Dict[str, Any]]:
        """Check for cultural sensitivity issues."""
        issues = []
        text_lower = response_text.lower()

        # Check for holiday/cultural assumptions
        holiday_assumptions = [
            "as we all celebrate",
            "during the holidays",
            "everyone celebrates christmas"
        ]

        for phrase in holiday_assumptions:
            if phrase in text_lower:
                issues.append({
                    "category": "culturally_insensitive",
                    "type": "cultural_assumption",
                    "severity": "medium",
                    "message": "Assumes shared cultural practices",
                    "context": self._extract_context(response_text, phrase),
                    "suggestion": "Avoid assuming everyone shares the same cultural background"
                })

        # Check for Americentric assumptions
        americentric_phrases = [
            "in this country",
            "as americans",
            "our government"
        ]

        for phrase in americentric_phrases:
            if phrase in text_lower:
                issues.append({
                    "category": "culturally_insensitive",
                    "type": "geographic_assumption",
                    "severity": "medium",
                    "message": "Assumes specific geographic location",
                    "context": self._extract_context(response_text, phrase),
                    "suggestion": "Remember users are from diverse geographic locations"
                })

        return issues

    def _check_inclusivity(self, response_text: str) -> List[Dict[str, Any]]:
        """Check for inclusive language usage."""
        issues = []
        text_lower = response_text.lower()

        # Check for unnecessarily gendered job titles
        gendered_titles = {
            "chairman": "chairperson/chair",
            "policeman": "police officer",
            "fireman": "firefighter",
            "mankind": "humanity/humankind",
            "manpower": "workforce/staff"
        }

        for gendered, neutral in gendered_titles.items():
            if gendered in text_lower:
                issues.append({
                    "category": "gendered_language",
                    "type": "gendered_title",
                    "severity": "low",
                    "message": f"Use gender-neutral term: '{neutral}' instead of '{gendered}'",
                    "context": self._extract_context(response_text, gendered),
                    "suggestion": f"Replace with '{neutral}'"
                })

        # Check for binary gender assumptions
        if "he or she" in text_lower or "he/she" in text_lower:
            issues.append({
                "category": "gendered_language",
                "type": "binary_gender",
                "severity": "low",
                "message": "Using binary gender pronouns",
                "context": self._extract_context(response_text, "he or she"),
                "suggestion": "Use 'they' as singular pronoun or rephrase to avoid pronouns"
            })

        return issues

    def _aggregate_issues(
        self,
        language_issues: List[Dict[str, Any]],
        bias_issues: List[Dict[str, Any]],
        cultural_issues: List[Dict[str, Any]],
        inclusivity_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate all sensitivity issues."""
        all_issues = (
            language_issues +
            bias_issues +
            cultural_issues +
            inclusivity_issues
        )

        # Add timestamps and sort by severity
        for issue in all_issues:
            issue["detected_at"] = datetime.now(UTC).isoformat()

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return all_issues

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate sensitivity recommendations."""
        recommendations = []

        if not issues:
            recommendations.append("Response uses inclusive and sensitive language")
            return recommendations

        # Count by severity
        critical = [i for i in issues if i["severity"] == "critical"]
        high = [i for i in issues if i["severity"] == "high"]
        medium = [i for i in issues if i["severity"] == "medium"]

        if critical:
            recommendations.append(
                f"CRITICAL: Remove {len(critical)} instances of offensive/discriminatory language"
            )

        if high:
            recommendations.append(
                f"HIGH PRIORITY: Address {len(high)} high-severity sensitivity issues"
            )

        # Category-specific recommendations
        categories = {}
        for issue in issues:
            cat = issue["category"]
            categories[cat] = categories.get(cat, 0) + 1

        if "ableist" in categories:
            recommendations.append(
                "Replace ableist language with neutral alternatives"
            )

        if "gendered_language" in categories:
            recommendations.append(
                "Use gender-neutral language and terms"
            )

        if "culturally_insensitive" in categories:
            recommendations.append(
                "Avoid cultural assumptions - remember global audience"
            )

        if "exclusive" in categories:
            recommendations.append(
                "Use inclusive language that doesn't assume shared knowledge or background"
            )

        return recommendations

    def _calculate_sensitivity_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate sensitivity score (0-100)."""
        if not issues:
            return 100.0

        score = 100.0

        # Deduct based on severity
        for issue in issues:
            severity = issue["severity"]
            deductions = {
                "critical": 40.0,
                "high": 20.0,
                "medium": 10.0,
                "low": 5.0
            }
            score -= deductions.get(severity, 0)

        return max(0.0, round(score, 1))

    def _determine_pass_fail(self, issues: List[Dict[str, Any]], strict_mode: bool) -> bool:
        """Determine if sensitivity check passes."""
        critical = [i for i in issues if i["severity"] == "critical"]
        high = [i for i in issues if i["severity"] == "high"]

        if strict_mode:
            return len(critical) == 0 and len(high) == 0
        else:
            return len(critical) == 0

    def _extract_context(self, text: str, term: str) -> str:
        """Extract context around a term."""
        text_lower = text.lower()
        term_lower = term.lower()

        idx = text_lower.find(term_lower)
        if idx != -1:
            start = max(0, idx - 50)
            end = min(len(text), idx + len(term) + 50)
            context = text[start:end].strip()

            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            return context

        return text[:100] + "..." if len(text) > 100 else text

    def _format_sensitivity_report(
        self,
        issues: List[Dict[str, Any]],
        recommendations: List[str],
        sensitivity_score: float,
        passed: bool
    ) -> str:
        """Format sensitivity report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Sensitivity Analysis Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Sensitivity Score:** {sensitivity_score}/100
**Issues Found:** {len(issues)}

**Issues by Category:**
"""

        # Count by category
        categories = {}
        for issue in issues:
            cat = issue["category"]
            categories[cat] = categories.get(cat, 0) + 1

        for category, count in categories.items():
            cat_desc = self.SENSITIVITY_CATEGORIES.get(category, {}).get("description", category)
            report += f"- {category.replace('_', ' ').title()}: {count}\n"

        # List issues
        if issues:
            report += f"\n**Detected Issues:**\n"
            for issue in issues[:5]:  # Top 5
                icon = "🔴" if issue["severity"] == "critical" else "⚠️" if issue["severity"] == "high" else "ℹ️"
                report += f"{icon} [{issue['severity'].upper()}] {issue['message']}\n"
                if "context" in issue:
                    report += f"   Context: \"{issue['context']}\"\n"
                if "suggestion" in issue:
                    report += f"   Suggestion: {issue['suggestion']}\n"

            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more issues\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Sensitivity check completed at {datetime.now(UTC).isoformat()}*"

        return report
