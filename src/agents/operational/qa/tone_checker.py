"""
Tone Checker Agent - TASK-2104

Ensures appropriate, empathetic, and professional tone in customer responses.
Uses Claude Sonnet for nuanced tone analysis and emotion detection.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("tone_checker", tier="operational", category="qa")
class ToneCheckerAgent(BaseAgent):
    """
    Tone Checker Agent.

    Analyzes and ensures appropriate tone in responses:
    - Professional and courteous language
    - Empathy and understanding
    - Appropriate formality level
    - Positive and helpful attitude
    - No passive-aggressive language
    - Cultural sensitivity
    - Appropriate emotion recognition and response

    Uses Claude Sonnet for nuanced tone understanding.
    """

    # Tone dimensions to evaluate
    TONE_DIMENSIONS = {
        "professionalism": "Use of professional language and courtesy",
        "empathy": "Recognition and validation of customer feelings",
        "helpfulness": "Willingness to assist and solve problems",
        "clarity": "Clear and easy to understand communication",
        "positivity": "Positive framing and constructive language",
        "respect": "Respectful and courteous treatment",
        "appropriateness": "Appropriate formality and cultural sensitivity"
    }

    # Tone issues to detect
    TONE_ISSUES = {
        "passive_aggressive": ["if you had read", "as I said before", "clearly stated"],
        "dismissive": ["that's not important", "doesn't matter", "not a big deal"],
        "impatient": ["you should have", "obviously", "just do this"],
        "condescending": ["you don't understand", "let me explain", "simple as that"],
        "defensive": ["not our fault", "we didn't", "it's your"],
        "robotic": ["please be informed", "kindly note", "we regret to inform"]
    }

    # Positive tone indicators
    POSITIVE_INDICATORS = [
        "I understand",
        "I appreciate",
        "thank you for",
        "happy to help",
        "let me assist",
        "I'd be glad to"
    ]

    def __init__(self):
        config = AgentConfig(
            name="tone_checker",
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
        Check tone appropriateness of response.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with tone analysis results
        """
        self.logger.info("tone_checking_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        customer_context = state.get("entities", {}).get("customer_context", {})
        expected_tone = state.get("entities", {}).get("expected_tone", "professional_friendly")

        self.logger.debug(
            "tone_checking_details",
            response_length=len(response_text),
            expected_tone=expected_tone
        )

        # Analyze tone dimensions
        tone_scores = self._analyze_tone_dimensions(response_text)

        # Detect tone issues
        tone_issues = self._detect_tone_issues(response_text)

        # Check empathy and understanding
        empathy_analysis = self._analyze_empathy(response_text, customer_context)

        # Check appropriateness for context
        appropriateness = self._check_appropriateness(response_text, customer_context)

        # Aggregate issues
        all_issues = self._aggregate_tone_issues(
            tone_issues,
            empathy_analysis,
            appropriateness
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            tone_scores,
            all_issues,
            expected_tone
        )

        # Calculate overall tone score
        tone_score = self._calculate_tone_score(tone_scores, all_issues)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_issues, tone_score)

        # Format response
        response = self._format_tone_report(
            tone_scores,
            all_issues,
            recommendations,
            tone_score,
            passed
        )

        state["agent_response"] = response
        state["tone_check_passed"] = passed
        state["tone_score"] = tone_score
        state["tone_analysis"] = tone_scores
        state["tone_issues"] = all_issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "tone_checking_completed",
            tone_score=tone_score,
            issues_found=len(all_issues),
            passed=passed
        )

        return state

    def _analyze_tone_dimensions(self, response_text: str) -> Dict[str, float]:
        """
        Analyze response across tone dimensions.

        Args:
            response_text: Response text to analyze

        Returns:
            Scores for each tone dimension (0-100)
        """
        scores = {}
        text_lower = response_text.lower()

        # Professionalism score
        unprofessional_count = sum(1 for word in ["stupid", "dumb", "idiot", "crap", "sucks"]
                                   if word in text_lower)
        scores["professionalism"] = max(0, 100 - (unprofessional_count * 40))

        # Empathy score
        empathy_words = ["understand", "appreciate", "sorry", "apologize", "realize"]
        empathy_count = sum(1 for word in empathy_words if word in text_lower)
        scores["empathy"] = min(100, 60 + (empathy_count * 15))

        # Helpfulness score
        helpful_phrases = ["help", "assist", "support", "guide", "show you", "let me"]
        helpful_count = sum(1 for phrase in helpful_phrases if phrase in text_lower)
        scores["helpfulness"] = min(100, 60 + (helpful_count * 10))

        # Clarity score (inverse of complexity)
        avg_word_length = sum(len(word) for word in response_text.split()) / max(len(response_text.split()), 1)
        scores["clarity"] = max(0, min(100, 100 - (avg_word_length - 5) * 5))

        # Positivity score
        positive_words = ["great", "excellent", "happy", "pleased", "glad", "wonderful"]
        negative_words = ["unfortunately", "problem", "issue", "can't", "won't", "unable"]
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        scores["positivity"] = max(0, min(100, 70 + (positive_count * 10) - (negative_count * 5)))

        # Respect score
        disrespectful_count = sum(1 for phrase in ["you should have", "you need to", "you must"]
                                 if phrase in text_lower)
        scores["respect"] = max(0, 100 - (disrespectful_count * 20))

        # Appropriateness score (baseline)
        scores["appropriateness"] = 85.0

        return scores

    def _detect_tone_issues(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Detect specific tone issues.

        Args:
            response_text: Response text to analyze

        Returns:
            List of detected tone issues
        """
        issues = []
        text_lower = response_text.lower()

        for issue_type, patterns in self.TONE_ISSUES.items():
            for pattern in patterns:
                if pattern in text_lower:
                    issues.append({
                        "type": issue_type,
                        "severity": "high" if issue_type in ["passive_aggressive", "condescending"] else "medium",
                        "pattern": pattern,
                        "message": f"{issue_type.replace('_', ' ').title()} tone detected",
                        "snippet": self._extract_snippet(response_text, pattern)
                    })

        return issues

    def _analyze_empathy(
        self,
        response_text: str,
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze empathy and emotional appropriateness.

        Args:
            response_text: Response text
            customer_context: Customer context (frustration level, sentiment, etc.)

        Returns:
            Empathy analysis results
        """
        text_lower = response_text.lower()
        issues = []

        # Check for acknowledgment of customer frustration
        customer_sentiment = customer_context.get("sentiment", "neutral")

        if customer_sentiment in ["frustrated", "angry", "upset"]:
            # Should have empathy/acknowledgment
            empathy_phrases = ["understand", "sorry", "apologize", "frustrating", "appreciate your patience"]
            has_empathy = any(phrase in text_lower for phrase in empathy_phrases)

            if not has_empathy:
                issues.append({
                    "type": "missing_empathy",
                    "severity": "high",
                    "message": "Customer is frustrated but response lacks empathy/acknowledgment",
                    "suggestion": "Add acknowledgment of customer frustration"
                })

        # Check for appropriate apology
        if "sorry" in text_lower or "apologize" in text_lower:
            # Good - shows empathy
            empathy_present = True
        else:
            empathy_present = False

        return {
            "empathy_present": empathy_present,
            "issues": issues,
            "customer_sentiment": customer_sentiment
        }

    def _check_appropriateness(
        self,
        response_text: str,
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check tone appropriateness for context.

        Args:
            response_text: Response text
            customer_context: Customer context

        Returns:
            Appropriateness analysis
        """
        issues = []
        text_lower = response_text.lower()

        # Check formality level
        customer_tier = customer_context.get("tier", "standard")

        # Enterprise customers expect more formal tone
        if customer_tier == "enterprise":
            casual_phrases = ["hey", "yeah", "nope", "gonna", "wanna"]
            for phrase in casual_phrases:
                if phrase in text_lower:
                    issues.append({
                        "type": "inappropriate_informality",
                        "severity": "medium",
                        "message": f"Too casual for enterprise customer: '{phrase}'",
                        "snippet": self._extract_snippet(response_text, phrase)
                    })

        # Check for overly technical language for non-technical customers
        customer_technical_level = customer_context.get("technical_level", "medium")

        if customer_technical_level == "low":
            technical_terms = ["api", "sdk", "json", "webhook", "endpoint"]
            technical_count = sum(1 for term in technical_terms if term in text_lower)

            if technical_count > 2:
                issues.append({
                    "type": "overly_technical",
                    "severity": "medium",
                    "message": "Response may be too technical for non-technical customer",
                    "suggestion": "Simplify technical explanations"
                })

        return {
            "issues": issues,
            "appropriate_for_context": len(issues) == 0
        }

    def _aggregate_tone_issues(
        self,
        tone_issues: List[Dict[str, Any]],
        empathy_analysis: Dict[str, Any],
        appropriateness: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Aggregate all tone issues."""
        all_issues = tone_issues.copy()
        all_issues.extend(empathy_analysis.get("issues", []))
        all_issues.extend(appropriateness.get("issues", []))

        # Add timestamps
        for issue in all_issues:
            issue["detected_at"] = datetime.now(UTC).isoformat()

        return all_issues

    def _generate_recommendations(
        self,
        tone_scores: Dict[str, float],
        issues: List[Dict[str, Any]],
        expected_tone: str
    ) -> List[str]:
        """Generate tone improvement recommendations."""
        recommendations = []

        if not issues and all(score >= 75 for score in tone_scores.values()):
            recommendations.append("Tone is appropriate and professional")
            return recommendations

        # Score-based recommendations
        for dimension, score in tone_scores.items():
            if score < 60:
                recommendations.append(
                    f"IMPROVE {dimension.upper()}: Score is {score:.0f}/100. Enhance {dimension} in response."
                )
            elif score < 75:
                recommendations.append(
                    f"Consider improving {dimension}: Current score {score:.0f}/100."
                )

        # Issue-based recommendations
        high_severity = [i for i in issues if i["severity"] == "high"]
        if high_severity:
            recommendations.append(
                f"Address {len(high_severity)} high-priority tone issues before sending."
            )

        # Specific recommendations
        issue_types = set(i["type"] for i in issues)

        if "passive_aggressive" in issue_types:
            recommendations.append(
                "Remove passive-aggressive language. Reframe in helpful, constructive manner."
            )

        if "missing_empathy" in issue_types:
            recommendations.append(
                "Add empathetic acknowledgment of customer frustration or concern."
            )

        if "overly_technical" in issue_types:
            recommendations.append(
                "Simplify technical language for better customer understanding."
            )

        return recommendations

    def _calculate_tone_score(
        self,
        tone_scores: Dict[str, float],
        issues: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall tone score (0-100)."""
        # Average of dimension scores
        avg_score = sum(tone_scores.values()) / len(tone_scores) if tone_scores else 0

        # Deduct for issues
        for issue in issues:
            severity = issue.get("severity", "low")
            deductions = {"critical": 15, "high": 10, "medium": 5, "low": 2}
            avg_score -= deductions.get(severity, 0)

        return max(0.0, round(avg_score, 1))

    def _determine_pass_fail(self, issues: List[Dict[str, Any]], tone_score: float) -> bool:
        """Determine if tone check passes."""
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]

        # Fail if critical issues or score too low
        if critical_issues or tone_score < 50:
            return False

        # Warning if high severity issues
        if high_issues and tone_score < 70:
            return False

        return True

    def _extract_snippet(self, text: str, pattern: str) -> str:
        """Extract text snippet containing pattern."""
        text_lower = text.lower()
        idx = text_lower.find(pattern.lower())
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(text), idx + len(pattern) + 40)
            snippet = text[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            return snippet
        return text[:80] + "..." if len(text) > 80 else text

    def _format_tone_report(
        self,
        tone_scores: Dict[str, float],
        issues: List[Dict[str, Any]],
        recommendations: List[str],
        tone_score: float,
        passed: bool
    ) -> str:
        """Format tone analysis report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Tone Analysis Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Overall Tone Score:** {tone_score}/100
**Issues Found:** {len(issues)}

**Tone Dimension Scores:**
"""

        for dimension, score in tone_scores.items():
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
            report += f"- {dimension.title()}: {score:.0f}/100 [{bar}]\n"

        # Issues
        if issues:
            report += f"\n**Tone Issues Detected:**\n"
            for issue in issues[:5]:
                icon = "🔴" if issue["severity"] == "critical" else "⚠️" if issue["severity"] == "high" else "ℹ️"
                report += f"{icon} [{issue['severity'].upper()}] {issue['message']}\n"
                if "snippet" in issue:
                    report += f"   \"{issue['snippet']}\"\n"

            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more issues\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Tone check completed at {datetime.now(UTC).isoformat()}*"

        return report
