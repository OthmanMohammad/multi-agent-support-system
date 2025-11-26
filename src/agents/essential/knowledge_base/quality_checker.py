"""
KB Quality Checker Agent.

Automatically evaluates KB article quality using LLM-based criteria.
Ensures knowledge base maintains high standards.

"""

import json
import re
from datetime import datetime, timedelta

from src.agents.base import AgentConfig
from src.agents.base.agent_types import AgentType
from src.agents.base.base_agent import BaseAgent
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


class KBQualityChecker(BaseAgent):
    """
    Knowledge Base Quality Checker Agent.

    Automatically evaluates KB article quality and suggests improvements.
    Uses both automated checks and LLM-based analysis.
    """

    def __init__(self):
        """Initialize KB Quality Checker agent."""
        config = AgentConfig(
            name="kb_quality_checker",
            type=AgentType.SPECIALIST,
            # Fast for quality checks
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1024,
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info("kb_quality_checker_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and check article quality.

        Args:
            state: AgentState with article data

        Returns:
            Updated state with quality assessment
        """
        article = {
            "article_id": state.get("article_id"),
            "title": state.get("article_title"),
            "content": state.get("article_content"),
            "category": state.get("article_category"),
            "created_at": state.get("article_created_at"),
            "updated_at": state.get("article_updated_at"),
        }

        self.logger.info(
            "kb_quality_check_started",
            article_id=article.get("article_id"),
            title=article.get("title", "")[:50],
        )

        # Check quality
        quality_report = await self.check_quality(article)

        # Update state
        state = self.update_state(
            state, quality_score=quality_report["quality_score"], quality_report=quality_report
        )

        self.logger.info(
            "kb_quality_check_completed",
            article_id=article.get("article_id"),
            quality_score=quality_report["quality_score"],
            issues_count=len(quality_report.get("issues", [])),
        )

        return state

    async def check_quality(self, article: dict) -> dict:
        """
        Check article quality.

        Args:
            article: Article dict with title, content, etc.

        Returns:
            Quality assessment dict
        """
        # Perform automated checks first
        automated_scores = self._automated_checks(article)

        # Perform LLM-based quality check
        llm_assessment = await self._llm_quality_check(article)

        # Combine scores
        final_scores = {
            "completeness": int(
                (automated_scores["completeness"] + llm_assessment["completeness"]) / 2
            ),
            "clarity": llm_assessment["clarity"],
            "accuracy": llm_assessment["accuracy"],
            "examples": int((automated_scores["examples"] + llm_assessment["examples"]) / 2),
            "formatting": automated_scores["formatting"],
        }

        # Calculate overall quality score (weighted average)
        quality_score = int(
            final_scores["completeness"] * 0.25
            + final_scores["clarity"] * 0.25
            + final_scores["accuracy"] * 0.20
            + final_scores["examples"] * 0.15
            + final_scores["formatting"] * 0.15
        )

        return {
            "article_id": article.get("article_id"),
            "quality_score": quality_score,
            "scores": final_scores,
            "issues": llm_assessment.get("issues", []),
            "strengths": llm_assessment.get("strengths", []),
            "needs_update": self._needs_update(article),
            "confidence": llm_assessment.get("confidence", 0.8),
        }

    def _automated_checks(self, article: dict) -> dict:
        """
        Perform automated quality checks (no LLM).

        Args:
            article: Article dict

        Returns:
            Dict with automated scores
        """
        content = article.get("content", "")

        # Completeness check
        completeness_score = self._check_completeness(content)

        # Examples check
        examples_score = self._check_examples(content)

        # Formatting check
        formatting_score = self._check_formatting(content)

        return {
            "completeness": completeness_score,
            "examples": examples_score,
            "formatting": formatting_score,
        }

    def _check_completeness(self, content: str) -> int:
        """
        Check if article has all necessary sections.

        Returns:
            Score 0-100
        """
        score = 50  # Base score

        # Check for common sections
        sections_found = 0
        total_sections = 5

        if re.search(r"(##\s*Overview|##\s*Introduction)", content, re.IGNORECASE):
            sections_found += 1

        if re.search(r"(##\s*Steps|##\s*Instructions|##\s*How to)", content, re.IGNORECASE):
            sections_found += 1

        if re.search(r"(##\s*Examples?|##\s*Usage)", content, re.IGNORECASE):
            sections_found += 1

        if re.search(r"(##\s*Notes?|##\s*Important|##\s*Tips)", content, re.IGNORECASE):
            sections_found += 1

        if re.search(r"(##\s*Related|##\s*See also|##\s*Resources)", content, re.IGNORECASE):
            sections_found += 1

        # Add bonus for sections found
        score += int((sections_found / total_sections) * 50)

        return min(score, 100)

    def _check_examples(self, content: str) -> int:
        """
        Check if article has code examples, screenshots, etc.

        Returns:
            Score 0-100
        """
        score = 0

        # Check for code blocks
        code_blocks = len(re.findall(r"```[\s\S]*?```", content))
        if code_blocks > 0:
            score += 40

        # Check for inline code
        inline_code = len(re.findall(r"`[^`]+`", content))
        if inline_code > 3:
            score += 20

        # Check for images
        images = len(re.findall(r"!\[.*?\]\(.*?\)", content))
        if images > 0:
            score += 20

        # Check for links
        links = len(re.findall(r"\[.*?\]\(.*?\)", content))
        if links > 2:
            score += 20

        return min(score, 100)

    def _check_formatting(self, content: str) -> int:
        """
        Check article formatting quality.

        Returns:
            Score 0-100
        """
        score = 50  # Base score

        # Check for headings
        headings = len(re.findall(r"^#+\s+.+$", content, re.MULTILINE))
        if headings >= 3:
            score += 15

        # Check for lists
        lists = len(re.findall(r"^[\*\-\+]\s+.+$", content, re.MULTILINE))
        if lists >= 3:
            score += 10

        # Check for numbered lists
        numbered = len(re.findall(r"^\d+\.\s+.+$", content, re.MULTILINE))
        if numbered >= 2:
            score += 10

        # Check for bold/italic
        if re.search(r"\*\*.+?\*\*|__.+?__", content):
            score += 5

        # Check for tables
        if re.search(r"\|.+\|", content):
            score += 10

        return min(score, 100)

    async def _llm_quality_check(self, article: dict) -> dict:
        """
        Use LLM to assess quality.

        Args:
            article: Article dict

        Returns:
            Dict with LLM assessment
        """
        system_prompt = """You are a Knowledge Base Quality Checker.

Evaluate the given KB article on these criteria:
1. Completeness (0-100): Does it cover the topic fully?
2. Clarity (0-100): Is it easy to understand?
3. Accuracy (0-100): Is it technically correct?
4. Examples (0-100): Does it have good examples?

Also identify:
- Issues (with severity and suggestions)
- Strengths (what's done well)
- Confidence in your assessment (0-1)

Return ONLY valid JSON with this structure:
{
  "completeness": 85,
  "clarity": 90,
  "accuracy": 95,
  "examples": 75,
  "issues": [
    {
      "severity": "medium",
      "category": "examples",
      "description": "Missing code examples",
      "suggestion": "Add Python/JS examples"
    }
  ],
  "strengths": [
    "Clear step-by-step instructions",
    "Good use of screenshots"
  ],
  "confidence": 0.88
}"""

        user_prompt = f"""**Article Title:** {article.get("title", "Untitled")}

**Category:** {article.get("category", "general")}

**Content:**
{article.get("content", "")[:3000]}

Evaluate this article's quality."""

        try:
            response = await self.call_llm(
                system_prompt=system_prompt,
                user_message=user_prompt,
                max_tokens=1024,
                conversation_history=[],  # Quality checks are standalone, no conversation context
            )

            # Parse JSON response
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r"\{[\s\S]*\}", response)
            assessment = json.loads(json_match.group(0)) if json_match else json.loads(response)

            return assessment

        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(
                "llm_quality_check_parsing_failed", error=str(e), error_type=type(e).__name__
            )
            # Fallback if LLM doesn't return valid JSON
            return {
                "completeness": 70,
                "clarity": 70,
                "accuracy": 70,
                "examples": 70,
                "issues": [],
                "strengths": [],
                "confidence": 0.5,
            }

    def _needs_update(self, article: dict) -> bool:
        """
        Determine if article needs updating based on age.

        Args:
            article: Article dict

        Returns:
            True if needs update
        """
        updated_at = article.get("updated_at")
        if not updated_at:
            return False

        try:
            # Parse date
            if isinstance(updated_at, str):
                updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            else:
                updated_date = updated_at

            # Check if older than 6 months
            days_old = (datetime.now(updated_date.tzinfo or None) - updated_date).days
            return days_old > 180

        except (ValueError, AttributeError, TypeError):
            return False

    async def batch_check_articles(self, articles: list[dict]) -> list[dict]:
        """
        Check quality of multiple articles.

        Args:
            articles: List of article dicts

        Returns:
            List of quality reports
        """
        reports = []
        for article in articles:
            report = await self.check_quality(article)
            reports.append(report)

        return reports


if __name__ == "__main__":
    # Test KB Quality Checker
    import asyncio

    async def test():
        print("=" * 60)
        print("TESTING KB QUALITY CHECKER")
        print("=" * 60)

        checker = KBQualityChecker()

        # Test article
        test_article = {
            "article_id": "kb_test_123",
            "title": "Complete Guide to Upgrading",
            "content": """
## Overview
This guide explains how to upgrade your plan.

## Steps
1. Navigate to Settings
2. Click on Billing
3. Select your plan
4. Confirm upgrade

## Examples
```python
# Example API call
upgrade_plan(user_id="123", plan="premium")
```

## Important Notes
- You'll be charged a prorated amount
- Upgrade takes effect immediately

## Related
- [Plan Comparison](/kb/plans)
            """,
            "category": "billing",
            "updated_at": (datetime.now() - timedelta(days=30)).isoformat(),
        }

        print("\nChecking article quality...")
        report = await checker.check_quality(test_article)

        print(f"\nQuality Score: {report['quality_score']}/100")
        print("\nComponent Scores:")
        for component, score in report["scores"].items():
            print(f"  {component.capitalize()}: {score}/100")

        print(f"\nIssues: {len(report['issues'])}")
        for issue in report["issues"]:
            print(f"  - [{issue.get('severity', 'unknown')}] {issue.get('description', 'N/A')}")

        print(f"\nStrengths: {len(report['strengths'])}")
        for strength in report["strengths"]:
            print(f"  - {strength}")

        print(f"\nNeeds Update: {report['needs_update']}")
        print(f"Confidence: {report['confidence']}")

        print("\n✓ KB Quality Checker tests completed!")

    asyncio.run(test())
