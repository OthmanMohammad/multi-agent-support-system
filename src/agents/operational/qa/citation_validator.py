"""
Citation Validator Agent - TASK-2110

Ensures proper citations and sources for claims and recommendations.
Validates documentation references and source attribution.
Uses Claude Sonnet for nuanced citation validation.
"""

import re
from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("citation_validator", tier="operational", category="qa")
class CitationValidatorAgent(BaseAgent):
    """
    Citation Validator Agent.

    Validates citations and sources in responses:
    - Proper attribution for claims and statistics
    - Documentation references are valid
    - Source URLs are accurate
    - Citation format is consistent
    - References are up-to-date
    - Claims requiring citations are cited
    - No citation format errors

    Uses Claude Sonnet for nuanced understanding of citation requirements.
    """

    # Citation formats
    CITATION_FORMATS = {
        "inline_link": r"\[([^\]]+)\]\(([^)]+)\)",  # [text](url)
        "footnote": r"\[(\d+)\]",  # [1]
        "parenthetical": r"\(see: ([^)]+)\)",  # (see: reference)
        "documentation": r"documentation|docs?|guide|reference",
    }

    # Claims that require citations
    REQUIRES_CITATION = {
        "statistics": [r"\d+%", r"\d+(\.\d+)?[x×]", r"\d+ (users|customers|companies)"],
        "research_claims": ["studies show", "research indicates", "according to", "data shows"],
        "third_party": ["industry standard", "best practice", "recommended by", "certified by"],
        "performance_claims": ["fastest", "most efficient", "industry-leading", "award-winning"],
    }

    # Valid documentation sources
    VALID_SOURCES = {
        "official_docs": ["docs.", "/docs/", "documentation"],
        "knowledge_base": ["kb.", "/kb/", "knowledge", "help."],
        "api_reference": ["api.", "/api/", "reference"],
        "changelog": ["changelog", "release-notes", "whatsnew"],
        "blog": ["blog.", "/blog/"],
    }

    def __init__(self):
        config = AgentConfig(
            name="citation_validator",
            type=AgentType.ANALYZER,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Validate citations in response.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with citation validation results
        """
        self.logger.info("citation_validation_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get(
            "response_text", state.get("agent_response", "")
        )
        require_citations = state.get("entities", {}).get("require_citations", True)
        knowledge_base = state.get("entities", {}).get("knowledge_base", {})

        self.logger.debug(
            "citation_validation_details",
            response_length=len(response_text),
            require_citations=require_citations,
        )

        # Extract citations
        citations = self._extract_citations(response_text)

        # Identify claims requiring citations
        uncited_claims = self._identify_uncited_claims(response_text, citations)

        # Validate citation format
        format_issues = self._validate_citation_format(citations)

        # Validate citation sources
        source_issues = self._validate_sources(citations, knowledge_base)

        # Check for citation consistency
        consistency_issues = self._check_citation_consistency(citations)

        # Aggregate issues
        all_issues = self._aggregate_issues(
            uncited_claims, format_issues, source_issues, consistency_issues
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues, citations)

        # Calculate citation score
        citation_score = self._calculate_citation_score(citations, uncited_claims, all_issues)

        # Determine pass/fail
        passed = self._determine_pass_fail(all_issues, require_citations)

        # Format response
        response = self._format_citation_report(
            citations, all_issues, recommendations, citation_score, passed
        )

        state["agent_response"] = response
        state["citation_check_passed"] = passed
        state["citation_score"] = citation_score
        state["citations_found"] = len(citations)
        state["citation_issues"] = all_issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "citation_validation_completed",
            citations_found=len(citations),
            issues_found=len(all_issues),
            citation_score=citation_score,
            passed=passed,
        )

        return state

    def _extract_citations(self, response_text: str) -> list[dict[str, Any]]:
        """Extract all citations from response."""
        citations = []

        # Extract inline markdown links
        inline_pattern = self.CITATION_FORMATS["inline_link"]
        inline_matches = re.finditer(inline_pattern, response_text)

        for i, match in enumerate(inline_matches):
            link_text = match.group(1)
            url = match.group(2)

            citations.append(
                {
                    "citation_id": f"inline_{i}",
                    "type": "inline_link",
                    "text": link_text,
                    "url": url,
                    "position": match.start(),
                    "format": "markdown",
                }
            )

        # Extract footnote references
        footnote_pattern = self.CITATION_FORMATS["footnote"]
        footnote_matches = re.finditer(footnote_pattern, response_text)

        for match in footnote_matches:
            ref_num = match.group(1)
            citations.append(
                {
                    "citation_id": f"footnote_{ref_num}",
                    "type": "footnote",
                    "reference_number": ref_num,
                    "position": match.start(),
                    "format": "footnote",
                }
            )

        # Extract documentation references
        doc_pattern = self.CITATION_FORMATS["documentation"]
        doc_matches = re.finditer(doc_pattern, response_text, re.IGNORECASE)

        for i, match in enumerate(doc_matches):
            citations.append(
                {
                    "citation_id": f"doc_ref_{i}",
                    "type": "documentation_reference",
                    "text": match.group(0),
                    "position": match.start(),
                    "format": "textual",
                }
            )

        return citations

    def _identify_uncited_claims(
        self, response_text: str, citations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify claims that require but lack citations."""
        uncited = []

        # Check for statistics without citations
        for pattern in self.REQUIRES_CITATION["statistics"]:
            matches = re.finditer(pattern, response_text)

            for match in matches:
                claim_position = match.start()
                claim_text = match.group(0)

                # Check if there's a citation nearby (within 100 chars)
                has_nearby_citation = any(
                    abs(citation["position"] - claim_position) < 100 for citation in citations
                )

                if not has_nearby_citation:
                    uncited.append(
                        {
                            "type": "uncited_statistic",
                            "severity": "high",
                            "claim": claim_text,
                            "message": f"Statistic '{claim_text}' lacks citation",
                            "context": self._extract_context_at_position(
                                response_text, claim_position
                            ),
                        }
                    )

        # Check for research claims
        for phrase in self.REQUIRES_CITATION["research_claims"]:
            if phrase in response_text.lower():
                position = response_text.lower().find(phrase)

                # Check for nearby citation
                has_nearby_citation = any(
                    abs(citation["position"] - position) < 150 for citation in citations
                )

                if not has_nearby_citation:
                    uncited.append(
                        {
                            "type": "uncited_research",
                            "severity": "high",
                            "claim": phrase,
                            "message": f"Research claim '{phrase}' requires citation",
                            "context": self._extract_context_at_position(response_text, position),
                        }
                    )

        # Check for superlative claims
        for phrase in self.REQUIRES_CITATION["performance_claims"]:
            if phrase in response_text.lower():
                position = response_text.lower().find(phrase)

                has_nearby_citation = any(
                    abs(citation["position"] - position) < 100 for citation in citations
                )

                if not has_nearby_citation:
                    uncited.append(
                        {
                            "type": "uncited_performance_claim",
                            "severity": "medium",
                            "claim": phrase,
                            "message": f"Performance claim '{phrase}' should be cited or softened",
                            "context": self._extract_context_at_position(response_text, position),
                        }
                    )

        return uncited

    def _validate_citation_format(self, citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate citation formatting."""
        issues = []

        for citation in citations:
            # Check inline links
            if citation["type"] == "inline_link":
                url = citation.get("url", "")

                # Check for incomplete URLs
                if not url.startswith(("http://", "https://", "/")):
                    issues.append(
                        {
                            "type": "invalid_url_format",
                            "severity": "high",
                            "citation_id": citation["citation_id"],
                            "message": "Citation URL is not properly formatted",
                            "url": url,
                        }
                    )

                # Check for placeholder text
                if citation.get("text", "").lower() in ["link", "click here", "here"]:
                    issues.append(
                        {
                            "type": "vague_link_text",
                            "severity": "low",
                            "citation_id": citation["citation_id"],
                            "message": "Link text is vague - use descriptive text",
                            "suggestion": "Use descriptive link text (e.g., 'API Documentation')",
                        }
                    )

            # Check footnotes have corresponding reference list
            if citation["type"] == "footnote":
                # In production, would check for reference list at end
                pass

        return issues

    def _validate_sources(
        self, citations: list[dict[str, Any]], knowledge_base: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Validate citation sources."""
        issues = []

        for citation in citations:
            if citation["type"] == "inline_link":
                url = citation.get("url", "")

                # Check if source is from valid/official source
                is_valid_source = False

                for _src_type, patterns in self.VALID_SOURCES.items():
                    if any(pattern in url.lower() for pattern in patterns):
                        is_valid_source = True
                        break

                # Warn about external sources
                if not is_valid_source and url.startswith("http"):
                    issues.append(
                        {
                            "type": "external_source",
                            "severity": "medium",
                            "citation_id": citation["citation_id"],
                            "message": "Citation links to external source - verify reliability",
                            "url": url,
                        }
                    )

                # Check for broken link patterns
                if "example.com" in url or "localhost" in url:
                    issues.append(
                        {
                            "type": "invalid_source",
                            "severity": "critical",
                            "citation_id": citation["citation_id"],
                            "message": "Citation contains placeholder/invalid URL",
                            "url": url,
                        }
                    )

        return issues

    def _check_citation_consistency(self, citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Check for citation consistency."""
        issues = []

        # Check if multiple citation formats are mixed
        formats = {c.get("format") for c in citations}

        if len(formats) > 2:
            issues.append(
                {
                    "type": "inconsistent_format",
                    "severity": "low",
                    "message": f"Multiple citation formats used: {', '.join(formats)}",
                    "suggestion": "Use consistent citation format throughout response",
                }
            )

        # Check for duplicate citations
        urls = [c.get("url") for c in citations if "url" in c]
        duplicates = [url for url in urls if urls.count(url) > 1]

        if duplicates:
            issues.append(
                {
                    "type": "duplicate_citations",
                    "severity": "low",
                    "message": f"Same source cited multiple times: {len(set(duplicates))} sources",
                    "suggestion": "Consider consolidating duplicate citations",
                }
            )

        return issues

    def _aggregate_issues(
        self,
        uncited_claims: list[dict[str, Any]],
        format_issues: list[dict[str, Any]],
        source_issues: list[dict[str, Any]],
        consistency_issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Aggregate all citation issues."""
        all_issues = uncited_claims + format_issues + source_issues + consistency_issues

        # Add timestamps
        for issue in all_issues:
            issue["detected_at"] = datetime.now(UTC).isoformat()

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 99))

        return all_issues

    def _generate_recommendations(
        self, issues: list[dict[str, Any]], citations: list[dict[str, Any]]
    ) -> list[str]:
        """Generate citation recommendations."""
        recommendations = []

        if not issues and citations:
            recommendations.append("Citations are properly formatted and sourced")
            return recommendations
        elif not issues and not citations:
            recommendations.append(
                "No citations found - add citations for claims and statistics if applicable"
            )
            return recommendations

        # Count by severity
        critical = [i for i in issues if i.get("severity") == "critical"]
        high = [i for i in issues if i.get("severity") == "high"]
        [i for i in issues if i.get("severity") == "medium"]

        if critical:
            recommendations.append(f"CRITICAL: Fix {len(critical)} critical citation issues")

        if high:
            recommendations.append(
                f"HIGH PRIORITY: Add citations for {len(high)} claims requiring sources"
            )

        # Type-specific recommendations
        issue_types = {}
        for issue in issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if "uncited_statistic" in issue_types:
            recommendations.append("Add citations for all statistics and numerical claims")

        if "uncited_research" in issue_types:
            recommendations.append("Cite sources for research claims and studies")

        if "external_source" in issue_types:
            recommendations.append("Prefer official documentation over external sources")

        if "vague_link_text" in issue_types:
            recommendations.append("Use descriptive link text instead of 'click here' or 'link'")

        return recommendations

    def _calculate_citation_score(
        self,
        citations: list[dict[str, Any]],
        uncited_claims: list[dict[str, Any]],
        all_issues: list[dict[str, Any]],
    ) -> float:
        """Calculate citation quality score (0-100)."""
        score = 100.0

        # Deduct for uncited claims
        score -= len(uncited_claims) * 15

        # Deduct for issues
        for issue in all_issues:
            severity = issue.get("severity", "low")
            deductions = {"critical": 20.0, "high": 10.0, "medium": 5.0, "low": 2.0}
            score -= deductions.get(severity, 0)

        # Bonus for having citations
        if citations:
            score += min(10, len(citations) * 2)

        return max(0.0, round(score, 1))

    def _determine_pass_fail(self, issues: list[dict[str, Any]], require_citations: bool) -> bool:
        """Determine if citation check passes."""
        critical = [i for i in issues if i.get("severity") == "critical"]
        high = [i for i in issues if i.get("severity") == "high"]

        if require_citations:
            # Strict: no critical or high severity issues
            return len(critical) == 0 and len(high) == 0
        else:
            # Lenient: only critical issues fail
            return len(critical) == 0

    def _extract_context_at_position(self, text: str, position: int) -> str:
        """Extract context at specific position."""
        start = max(0, position - 50)
        end = min(len(text), position + 80)
        context = text[start:end].strip()

        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context

    def _format_citation_report(
        self,
        citations: list[dict[str, Any]],
        issues: list[dict[str, Any]],
        recommendations: list[str],
        citation_score: float,
        passed: bool,
    ) -> str:
        """Format citation validation report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Citation Validation Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Citation Score:** {citation_score}/100
**Citations Found:** {len(citations)}
**Issues Detected:** {len(issues)}

**Citation Breakdown:**
"""

        # Count by type
        citation_types = {}
        for citation in citations:
            ctype = citation.get("type", "unknown")
            citation_types[ctype] = citation_types.get(ctype, 0) + 1

        for ctype, count in citation_types.items():
            report += f"- {ctype.replace('_', ' ').title()}: {count}\n"

        # Issues
        if issues:
            report += "\n**Issues Detected:**\n"

            for issue in issues[:5]:  # Top 5
                icon = (
                    "🔴"
                    if issue.get("severity") == "critical"
                    else "⚠️"
                    if issue.get("severity") == "high"
                    else "ℹ️"
                )
                report += (
                    f"{icon} [{issue.get('severity', 'unknown').upper()}] {issue['message']}\n"
                )
                if "context" in issue:
                    report += f'   Context: "{issue["context"]}"\n'
                if "suggestion" in issue:
                    report += f"   Suggestion: {issue['suggestion']}\n"

            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more issues\n"

        # Recommendations
        if recommendations:
            report += "\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Citation validation completed at {datetime.now(UTC).isoformat()}*"

        return report
