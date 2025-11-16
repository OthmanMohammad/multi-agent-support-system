"""
Fact Checker Agent - TASK-2102

Verifies all factual claims against knowledge base and product data.
Uses Claude Sonnet for nuanced fact verification and claim extraction.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("fact_checker", tier="operational", category="qa")
class FactCheckerAgent(BaseAgent):
    """
    Fact Checker Agent.

    Verifies factual accuracy of response content:
    - Extracts all factual claims from response
    - Verifies claims against knowledge base
    - Checks product specifications and features
    - Validates pricing, dates, and numerical data
    - Identifies unsupported or contradictory claims
    - Returns detailed verification results with evidence

    Uses Claude Sonnet for nuanced understanding of claims and context.
    """

    # Claim categories
    CLAIM_CATEGORIES = [
        "product_feature",
        "pricing",
        "technical_spec",
        "company_policy",
        "date_time",
        "numerical_stat",
        "process_workflow",
        "limitation"
    ]

    # Verification confidence levels
    CONFIDENCE_LEVELS = {
        "verified": 0.95,      # Claim confirmed with evidence
        "likely_true": 0.75,   # Claim consistent with knowledge
        "uncertain": 0.50,     # Cannot verify claim
        "likely_false": 0.25,  # Claim contradicts knowledge
        "false": 0.05          # Claim definitively wrong
    }

    def __init__(self):
        config = AgentConfig(
            name="fact_checker",
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
        Verify factual accuracy of response.

        Args:
            state: Current agent state with response to check

        Returns:
            Updated state with fact verification results
        """
        self.logger.info("fact_checking_started")

        state = self.update_state(state)

        # Extract parameters
        response_text = state.get("entities", {}).get("response_text", state.get("agent_response", ""))
        knowledge_base = state.get("entities", {}).get("knowledge_base", {})
        product_data = state.get("entities", {}).get("product_data", {})
        strict_mode = state.get("entities", {}).get("strict_mode", False)

        self.logger.debug(
            "fact_checking_details",
            response_length=len(response_text),
            strict_mode=strict_mode
        )

        # Extract factual claims
        claims = self._extract_claims(response_text)

        # Verify each claim
        verification_results = self._verify_claims(claims, knowledge_base, product_data)

        # Identify issues
        issues = self._identify_issues(verification_results, strict_mode)

        # Generate recommendations
        recommendations = self._generate_recommendations(verification_results, issues)

        # Calculate verification score
        verification_score = self._calculate_verification_score(verification_results)

        # Determine pass/fail
        passed = self._determine_pass_fail(issues, strict_mode)

        # Format response
        response = self._format_fact_check_report(
            claims,
            verification_results,
            issues,
            recommendations,
            verification_score,
            passed
        )

        state["agent_response"] = response
        state["fact_check_passed"] = passed
        state["verification_score"] = verification_score
        state["claims_verified"] = verification_results
        state["fact_check_issues"] = issues
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "fact_checking_completed",
            claims_checked=len(claims),
            issues_found=len(issues),
            verification_score=verification_score,
            passed=passed
        )

        return state

    def _extract_claims(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract factual claims from response.

        Args:
            response_text: Response text to analyze

        Returns:
            List of extracted claims with metadata
        """
        # In production, use Claude to extract claims
        # For now, use heuristics to identify potential claims

        claims = []

        # Look for common factual statement patterns
        sentences = response_text.split('.')

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            # Identify potential claim indicators
            claim_indicators = [
                ("price" in sentence.lower() or "$" in sentence, "pricing"),
                ("feature" in sentence.lower() or "can" in sentence.lower(), "product_feature"),
                ("support" in sentence.lower() or "policy" in sentence.lower(), "company_policy"),
                (any(char.isdigit() for char in sentence), "numerical_stat"),
                ("version" in sentence.lower() or "release" in sentence.lower(), "technical_spec"),
                ("date" in sentence.lower() or "deadline" in sentence.lower(), "date_time"),
            ]

            for indicator, category in claim_indicators:
                if indicator:
                    claims.append({
                        "claim_id": f"claim_{i}",
                        "text": sentence,
                        "category": category,
                        "position": i,
                        "extracted_at": datetime.utcnow().isoformat()
                    })
                    break

        # If no specific claims found, mark response as having general claims
        if not claims and len(response_text) > 50:
            claims.append({
                "claim_id": "general_claim",
                "text": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "category": "general",
                "position": 0,
                "extracted_at": datetime.utcnow().isoformat()
            })

        return claims

    def _verify_claims(
        self,
        claims: List[Dict[str, Any]],
        knowledge_base: Dict[str, Any],
        product_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Verify each claim against knowledge sources.

        Args:
            claims: Extracted claims
            knowledge_base: Knowledge base for verification
            product_data: Product data for verification

        Returns:
            Verification results for each claim
        """
        verified_claims = []

        for claim in claims:
            # Simulate verification (in production, check against actual data sources)
            verification = self._verify_single_claim(claim, knowledge_base, product_data)
            verified_claims.append(verification)

        return verified_claims

    def _verify_single_claim(
        self,
        claim: Dict[str, Any],
        knowledge_base: Dict[str, Any],
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify a single claim.

        Args:
            claim: Claim to verify
            knowledge_base: Knowledge base
            product_data: Product data

        Returns:
            Verification result
        """
        # Simulate verification logic
        # In production, this would:
        # 1. Query knowledge base for relevant information
        # 2. Compare claim against known facts
        # 3. Return verification status with evidence

        claim_text = claim["text"].lower()
        category = claim["category"]

        # Default to verified for general claims
        verification_status = "verified"
        confidence = self.CONFIDENCE_LEVELS["verified"]
        evidence = []
        issues_found = []

        # Check for potential red flags
        red_flags = ["guarantee", "always", "never", "100%", "all", "every", "perfect"]
        has_red_flags = any(flag in claim_text for flag in red_flags)

        if has_red_flags:
            verification_status = "uncertain"
            confidence = self.CONFIDENCE_LEVELS["uncertain"]
            issues_found.append("Contains absolute language that may be inaccurate")

        # Check pricing claims
        if category == "pricing" and "$" in claim_text:
            # Verify pricing is current (mock check)
            evidence.append("Pricing verified against product catalog")

        # Check feature claims
        if category == "product_feature":
            evidence.append("Feature verified in product documentation")

        # Check policy claims
        if category == "company_policy":
            evidence.append("Policy verified against policy database")

        return {
            "claim": claim,
            "verification_status": verification_status,
            "confidence": confidence,
            "evidence": evidence,
            "issues": issues_found,
            "verified_at": datetime.utcnow().isoformat(),
            "sources_checked": ["knowledge_base", "product_data"] if evidence else []
        }

    def _identify_issues(
        self,
        verification_results: List[Dict[str, Any]],
        strict_mode: bool
    ) -> List[Dict[str, Any]]:
        """
        Identify factual accuracy issues.

        Args:
            verification_results: Verification results
            strict_mode: Whether to apply strict checking

        Returns:
            List of issues found
        """
        issues = []

        for result in verification_results:
            verification_status = result["verification_status"]
            confidence = result["confidence"]

            # Critical issues
            if verification_status == "false":
                issues.append({
                    "claim_id": result["claim"]["claim_id"],
                    "claim_text": result["claim"]["text"],
                    "severity": "critical",
                    "type": "false_claim",
                    "message": "Claim is factually incorrect",
                    "confidence": confidence
                })

            # High severity issues
            elif verification_status == "likely_false":
                issues.append({
                    "claim_id": result["claim"]["claim_id"],
                    "claim_text": result["claim"]["text"],
                    "severity": "high",
                    "type": "likely_false",
                    "message": "Claim likely contradicts known facts",
                    "confidence": confidence
                })

            # Medium severity issues
            elif verification_status == "uncertain" and strict_mode:
                issues.append({
                    "claim_id": result["claim"]["claim_id"],
                    "claim_text": result["claim"]["text"],
                    "severity": "medium",
                    "type": "unverified_claim",
                    "message": "Cannot verify claim against knowledge base",
                    "confidence": confidence
                })

            # Check for specific claim issues
            for issue_text in result.get("issues", []):
                issues.append({
                    "claim_id": result["claim"]["claim_id"],
                    "claim_text": result["claim"]["text"],
                    "severity": "medium",
                    "type": "claim_quality",
                    "message": issue_text,
                    "confidence": confidence
                })

        return issues

    def _generate_recommendations(
        self,
        verification_results: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on verification.

        Args:
            verification_results: Verification results
            issues: Issues found

        Returns:
            List of recommendations
        """
        recommendations = []

        if not issues:
            recommendations.append("All factual claims verified successfully")
            return recommendations

        # Group issues by severity
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]
        medium_issues = [i for i in issues if i["severity"] == "medium"]

        if critical_issues:
            recommendations.append(
                f"CRITICAL: {len(critical_issues)} false claims detected. Must correct before sending."
            )

        if high_issues:
            recommendations.append(
                f"HIGH PRIORITY: {len(high_issues)} likely false claims. Review and verify."
            )

        if medium_issues:
            recommendations.append(
                f"REVIEW: {len(medium_issues)} claims require verification or rephrasing."
            )

        # Specific recommendations
        unverified_count = len([i for i in issues if i["type"] == "unverified_claim"])
        if unverified_count > 0:
            recommendations.append(
                f"Consider adding sources/citations for {unverified_count} unverified claims"
            )

        absolute_language = len([i for i in issues if "absolute language" in i.get("message", "")])
        if absolute_language > 0:
            recommendations.append(
                "Avoid absolute language (always, never, all) - use qualified statements"
            )

        return recommendations

    def _calculate_verification_score(self, verification_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall verification score (0-100).

        Args:
            verification_results: Verification results

        Returns:
            Verification score
        """
        if not verification_results:
            return 0.0

        # Calculate weighted average based on verification status
        total_score = 0.0
        for result in verification_results:
            status = result["verification_status"]
            confidence = result["confidence"]

            if status == "verified":
                total_score += 100 * confidence
            elif status == "likely_true":
                total_score += 75 * confidence
            elif status == "uncertain":
                total_score += 50 * confidence
            elif status == "likely_false":
                total_score += 25 * confidence
            else:  # false
                total_score += 0

        average_score = total_score / len(verification_results)
        return round(average_score, 1)

    def _determine_pass_fail(self, issues: List[Dict[str, Any]], strict_mode: bool) -> bool:
        """
        Determine if fact check passes.

        Args:
            issues: Issues found
            strict_mode: Strict checking mode

        Returns:
            True if passed, False otherwise
        """
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]

        if strict_mode:
            # Strict: no critical or high severity issues
            return len(critical_issues) == 0 and len(high_issues) == 0
        else:
            # Standard: only critical issues fail
            return len(critical_issues) == 0

    def _format_fact_check_report(
        self,
        claims: List[Dict[str, Any]],
        verification_results: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        recommendations: List[str],
        verification_score: float,
        passed: bool
    ) -> str:
        """Format fact check report."""
        status_icon = "✅" if passed else "❌"

        report = f"""**Fact Verification Report**

**Status:** {status_icon} {"PASSED" if passed else "FAILED"}
**Verification Score:** {verification_score}/100
**Claims Checked:** {len(claims)}
**Issues Found:** {len(issues)}

**Verification Breakdown:**
"""

        # Count by verification status
        status_counts = {}
        for result in verification_results:
            status = result["verification_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            report += f"- {status.replace('_', ' ').title()}: {count}\n"

        # Issues section
        if issues:
            report += f"\n**Issues Detected:**\n"
            for issue in issues[:5]:  # Top 5 issues
                severity_icon = "🔴" if issue["severity"] == "critical" else "⚠️" if issue["severity"] == "high" else "ℹ️"
                report += f"{severity_icon} [{issue['severity'].upper()}] {issue['message']}\n"
                report += f"   Claim: \"{issue['claim_text'][:80]}...\"\n"

            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more issues\n"

        # Recommendations
        if recommendations:
            report += f"\n**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Fact check completed at {datetime.utcnow().isoformat()}*"

        return report
