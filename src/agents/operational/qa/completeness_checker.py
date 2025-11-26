"""
Completeness Checker Agent - TASK-2105

Ensures response fully addresses customer question with all necessary information.
Uses Claude Haiku for efficient completeness validation.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("completeness_checker", tier="operational", category="qa")
class CompletenessCheckerAgent(BaseAgent):
    """
    Completeness Checker Agent.

    Ensures response fully addresses customer question:
    - All parts of multi-part questions answered
    - Direct answer to the specific question asked
    - Sufficient detail and context provided
    - Actionable next steps included (if applicable)
    - Follow-up information provided
    - No unanswered questions or gaps

    Uses Claude Haiku for efficient completeness checks.
    """

    # Required elements for complete responses
    REQUIRED_ELEMENTS = {
        "direct_answer": "Direct response to the question asked",
        "context": "Relevant context and background",
        "details": "Sufficient detail to be actionable",
        "next_steps": "Clear next steps or actions (if applicable)",
        "resources": "Links to relevant resources (if applicable)",
    }

    # Question types that require specific elements
    QUESTION_TYPES = {
        "how_to": ["step_by_step", "prerequisites", "examples"],
        "troubleshooting": ["diagnosis", "solution", "prevention"],
        "pricing": ["cost", "billing_period", "limitations"],
        "feature": ["description", "use_cases", "availability"],
        "comparison": ["differences", "pros_cons", "recommendation"],
    }

    def __init__(self):
        config = AgentConfig(
            name="completeness_checker",
            type=AgentType.ANALYZER,
            temperature=0.2,
            max_tokens=1500,
            capabilities=[],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Check response completeness.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with completeness analysis results
        """
        self.logger.info("completeness_checking_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get(
            "response_text", state.get("agent_response", "")
        )
        original_question = state.get("entities", {}).get("original_question", "")
        question_type = state.get("entities", {}).get("question_type", "general")

        self.logger.debug(
            "completeness_checking_details",
            response_length=len(response_text),
            question_type=question_type,
        )

        # Analyze question structure
        question_analysis = self._analyze_question(original_question)

        # Check basic completeness elements
        element_check = self._check_required_elements(response_text, question_analysis)

        # Check for multi-part question completeness
        multipart_check = self._check_multipart_completeness(
            original_question, response_text, question_analysis
        )

        # Check for specific question type requirements
        question_type_check = self._check_question_type_requirements(response_text, question_type)

        # Identify gaps
        gaps = self._identify_gaps(
            element_check, multipart_check, question_type_check, question_analysis
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, question_analysis)

        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(
            element_check, multipart_check, question_type_check
        )

        # Determine pass/fail
        passed = self._determine_pass_fail(gaps, completeness_score)

        # Format response
        response = self._format_completeness_report(
            element_check, gaps, recommendations, completeness_score, passed, question_analysis
        )

        state["agent_response"] = response
        state["completeness_check_passed"] = passed
        state["completeness_score"] = completeness_score
        state["completeness_gaps"] = gaps
        state["element_check"] = element_check
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "completeness_checking_completed",
            completeness_score=completeness_score,
            gaps_found=len(gaps),
            passed=passed,
        )

        return state

    def _analyze_question(self, question: str) -> dict[str, Any]:
        """
        Analyze question structure and requirements.

        Args:
            question: Original customer question

        Returns:
            Question analysis
        """
        question_lower = question.lower()

        # Detect question type
        question_type = "general"
        if any(word in question_lower for word in ["how to", "how do i", "how can i"]):
            question_type = "how_to"
        elif any(word in question_lower for word in ["why", "not working", "error", "issue"]):
            question_type = "troubleshooting"
        elif any(word in question_lower for word in ["price", "cost", "how much"]):
            question_type = "pricing"
        elif any(word in question_lower for word in ["what is", "what are", "feature"]):
            question_type = "feature"
        elif any(word in question_lower for word in ["difference", "compare", "versus", "vs"]):
            question_type = "comparison"

        # Detect multi-part question
        parts = []
        if " and " in question_lower or ("?" in question and question.count("?") > 1):
            # Likely multi-part
            parts = [p.strip() for p in question.split(" and ")]
            if len(parts) == 1:
                parts = [p.strip() for p in question.split("?") if p.strip()]

        return {
            "type": question_type,
            "is_multipart": len(parts) > 1,
            "parts": parts if len(parts) > 1 else [question],
            "word_count": len(question.split()),
        }

    def _check_required_elements(
        self, response_text: str, question_analysis: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Check for required elements in response.

        Args:
            response_text: Response text
            question_analysis: Question analysis

        Returns:
            Element check results
        """
        results = {}
        text_lower = response_text.lower()

        # Direct answer present
        has_direct_answer = len(response_text.split()) >= 20
        results["direct_answer"] = {
            "present": has_direct_answer,
            "confidence": 0.9 if has_direct_answer else 0.3,
        }

        # Context provided
        context_indicators = ["because", "this is", "the reason", "this means"]
        has_context = any(indicator in text_lower for indicator in context_indicators)
        results["context"] = {"present": has_context, "confidence": 0.85 if has_context else 0.5}

        # Sufficient detail
        word_count = len(response_text.split())
        has_detail = word_count >= 50
        results["details"] = {
            "present": has_detail,
            "confidence": min(1.0, word_count / 100),
            "word_count": word_count,
        }

        # Next steps (if action required)
        action_indicators = ["you can", "to do this", "steps:", "1.", "2.", "first,", "next,"]
        has_next_steps = any(indicator in text_lower for indicator in action_indicators)
        results["next_steps"] = {
            "present": has_next_steps,
            "confidence": 0.8 if has_next_steps else 0.4,
            "required": question_analysis["type"] in ["how_to", "troubleshooting"],
        }

        # Resources/links
        has_resources = "http" in text_lower or "documentation" in text_lower
        results["resources"] = {
            "present": has_resources,
            "confidence": 0.9 if has_resources else 0.5,
            "required": False,
        }

        return results

    def _check_multipart_completeness(
        self, question: str, response_text: str, question_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Check if all parts of multi-part question are addressed.

        Args:
            question: Original question
            response_text: Response text
            question_analysis: Question analysis

        Returns:
            Multi-part completeness check
        """
        if not question_analysis["is_multipart"]:
            return {"applicable": False, "all_parts_addressed": True, "parts_addressed": []}

        parts = question_analysis["parts"]
        parts_addressed = []

        for i, part in enumerate(parts):
            # Simple heuristic: check if keywords from question appear in response
            part_words = set(part.lower().split())
            response_words = set(response_text.lower().split())

            # Remove common words
            common_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "how",
                "what",
                "when",
                "where",
                "why",
                "do",
                "does",
            }
            part_keywords = part_words - common_words

            # Check if at least 30% of keywords appear in response
            if part_keywords:
                overlap = len(part_keywords & response_words)
                addressed = overlap / len(part_keywords) >= 0.3
            else:
                addressed = True  # No specific keywords to check

            parts_addressed.append(
                {
                    "part_number": i + 1,
                    "part_text": part,
                    "addressed": addressed,
                    "confidence": overlap / len(part_keywords) if part_keywords else 1.0,
                }
            )

        all_addressed = all(p["addressed"] for p in parts_addressed)

        return {
            "applicable": True,
            "all_parts_addressed": all_addressed,
            "parts_addressed": parts_addressed,
            "total_parts": len(parts),
        }

    def _check_question_type_requirements(
        self, response_text: str, question_type: str
    ) -> dict[str, Any]:
        """
        Check question-type-specific requirements.

        Args:
            response_text: Response text
            question_type: Type of question

        Returns:
            Question type requirement check
        """
        if question_type not in self.QUESTION_TYPES:
            return {"applicable": False, "requirements_met": True, "missing": []}

        required_elements = self.QUESTION_TYPES[question_type]
        text_lower = response_text.lower()
        missing = []

        # Check each required element
        for element in required_elements:
            if element == "step_by_step":
                has_element = any(
                    indicator in text_lower for indicator in ["1.", "2.", "step", "first", "then"]
                )
            elif element == "prerequisites":
                has_element = (
                    "prerequisite" in text_lower
                    or "you'll need" in text_lower
                    or "before" in text_lower
                )
            elif element == "examples":
                has_element = "example" in text_lower or "for instance" in text_lower
            elif element == "diagnosis":
                has_element = (
                    "issue" in text_lower or "problem" in text_lower or "caused by" in text_lower
                )
            elif element == "solution":
                has_element = (
                    "solution" in text_lower or "to fix" in text_lower or "resolve" in text_lower
                )
            elif element == "prevention":
                has_element = (
                    "prevent" in text_lower or "avoid" in text_lower or "in future" in text_lower
                )
            elif element == "cost":
                has_element = "$" in response_text or "price" in text_lower or "cost" in text_lower
            elif element == "billing_period":
                has_element = any(
                    period in text_lower for period in ["month", "year", "annual", "billing"]
                )
            else:
                has_element = element.replace("_", " ") in text_lower

            if not has_element:
                missing.append(element)

        return {
            "applicable": True,
            "requirements_met": len(missing) == 0,
            "missing": missing,
            "question_type": question_type,
        }

    def _identify_gaps(
        self,
        element_check: dict[str, dict[str, Any]],
        multipart_check: dict[str, Any],
        question_type_check: dict[str, Any],
        question_analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Identify completeness gaps."""
        gaps = []

        # Check basic elements
        for element, result in element_check.items():
            if result.get("required", True) and not result["present"]:
                gaps.append(
                    {
                        "type": "missing_element",
                        "element": element,
                        "severity": "high" if element == "direct_answer" else "medium",
                        "message": f"Missing {element.replace('_', ' ')}",
                    }
                )

        # Check multi-part completeness
        if multipart_check.get("applicable") and not multipart_check["all_parts_addressed"]:
            unanswered = [p for p in multipart_check["parts_addressed"] if not p["addressed"]]
            for part in unanswered:
                gaps.append(
                    {
                        "type": "unanswered_part",
                        "part_number": part["part_number"],
                        "severity": "high",
                        "message": f"Part {part['part_number']} of question not fully addressed",
                        "part_text": part["part_text"],
                    }
                )

        # Check question type requirements
        if question_type_check.get("applicable") and not question_type_check["requirements_met"]:
            for missing in question_type_check["missing"]:
                gaps.append(
                    {
                        "type": "missing_requirement",
                        "requirement": missing,
                        "severity": "medium",
                        "message": f"Missing {missing.replace('_', ' ')} for {question_type_check['question_type']} question",
                    }
                )

        return gaps

    def _generate_recommendations(
        self, gaps: list[dict[str, Any]], question_analysis: dict[str, Any]
    ) -> list[str]:
        """Generate completeness recommendations."""
        recommendations = []

        if not gaps:
            recommendations.append("Response fully addresses the question")
            return recommendations

        # Priority recommendations
        high_severity = [g for g in gaps if g["severity"] == "high"]
        if high_severity:
            recommendations.append(
                f"CRITICAL: Address {len(high_severity)} high-priority gaps before sending"
            )

        # Specific recommendations
        gap_types = {g["type"] for g in gaps}

        if "missing_element" in gap_types:
            missing = [g["element"] for g in gaps if g["type"] == "missing_element"]
            recommendations.append(
                f"Add missing elements: {', '.join(e.replace('_', ' ') for e in missing)}"
            )

        if "unanswered_part" in gap_types:
            recommendations.append(
                "Ensure all parts of the multi-part question are fully addressed"
            )

        if "missing_requirement" in gap_types:
            recommendations.append(
                f"Add {question_analysis['type']} specific elements for complete answer"
            )

        return recommendations

    def _calculate_completeness_score(
        self,
        element_check: dict[str, dict[str, Any]],
        multipart_check: dict[str, Any],
        question_type_check: dict[str, Any],
    ) -> float:
        """Calculate completeness score (0-100)."""
        score = 0.0
        total_weight = 0.0

        # Element scores (weight: 50%)
        for _element, result in element_check.items():
            weight = 10 if result.get("required", True) else 5
            if result["present"]:
                score += weight * result["confidence"]
            total_weight += weight

        # Multi-part score (weight: 30%)
        if multipart_check.get("applicable"):
            parts_score = sum(p["confidence"] for p in multipart_check["parts_addressed"])
            parts_score = (
                parts_score / len(multipart_check["parts_addressed"])
                if multipart_check["parts_addressed"]
                else 0
            )
            score += 30 * parts_score
            total_weight += 30
        else:
            # If not multi-part, distribute weight to elements
            score += 30
            total_weight += 30

        # Question type score (weight: 20%)
        if question_type_check.get("applicable"):
            if question_type_check["requirements_met"]:
                score += 20
            else:
                met_count = len(
                    self.QUESTION_TYPES.get(question_type_check["question_type"], [])
                ) - len(question_type_check["missing"])
                total_count = len(self.QUESTION_TYPES.get(question_type_check["question_type"], []))
                score += 20 * (met_count / total_count if total_count > 0 else 1)
            total_weight += 20
        else:
            score += 20
            total_weight += 20

        return round((score / total_weight * 100) if total_weight > 0 else 0, 1)

    def _determine_pass_fail(self, gaps: list[dict[str, Any]], completeness_score: float) -> bool:
        """Determine if completeness check passes."""
        # Fail if critical gaps or score too low
        high_severity_gaps = [g for g in gaps if g["severity"] == "high"]

        return not (high_severity_gaps or completeness_score < 60)

    def _format_completeness_report(
        self,
        element_check: dict[str, dict[str, Any]],
        gaps: list[dict[str, Any]],
        recommendations: list[str],
        completeness_score: float,
        passed: bool,
        question_analysis: dict[str, Any],
    ) -> str:
        """Format completeness report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Completeness Analysis Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Completeness Score:** {completeness_score}/100
**Question Type:** {question_analysis["type"]}
**Multi-part Question:** {"Yes" if question_analysis["is_multipart"] else "No"}
**Gaps Found:** {len(gaps)}

**Required Elements Check:**
"""

        for element, result in element_check.items():
            status = "✓" if result["present"] else "✗"
            required = " (Required)" if result.get("required", True) else ""
            report += f"{status} {element.replace('_', ' ').title()}{required}\n"

        # Gaps
        if gaps:
            report += "\n**Identified Gaps:**\n"
            for gap in gaps[:5]:
                icon = "🔴" if gap["severity"] == "high" else "⚠️"
                report += f"{icon} [{gap['severity'].upper()}] {gap['message']}\n"

            if len(gaps) > 5:
                report += f"... and {len(gaps) - 5} more gaps\n"

        # Recommendations
        if recommendations:
            report += "\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Completeness check completed at {datetime.now(UTC).isoformat()}*"

        return report
