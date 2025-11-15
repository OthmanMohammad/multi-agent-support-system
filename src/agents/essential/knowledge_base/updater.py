"""
KB Updater Agent.

Detects outdated content in the knowledge base and flags articles that need updating.
Ensures KB stays current with product changes.

Part of: STORY-002 Knowledge Base Swarm (TASK-206)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.database.connection import get_db_session
from src.database.models import KBArticle
from src.utils.logging.setup import get_logger


class KBUpdater(BaseAgent):
    """
    Knowledge Base Updater Agent.

    Detects outdated content and flags articles needing updates:
    - Articles older than 6 months
    - References to deprecated features
    - Low helpfulness scores
    - Broken links
    """

    # Thresholds
    AGE_THRESHOLD_DAYS = 180  # 6 months
    LOW_HELPFULNESS_THRESHOLD = 0.5
    MIN_QUALITY_SCORE = 70

    def __init__(self):
        """Initialize KB Updater agent."""
        config = AgentConfig(
            name="kb_updater",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",  # For content analysis
            temperature=0.1,
            max_tokens=512,
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info(
            "kb_updater_initialized",
            age_threshold_days=self.AGE_THRESHOLD_DAYS,
            low_helpfulness_threshold=self.LOW_HELPFULNESS_THRESHOLD,
            min_quality_score=self.MIN_QUALITY_SCORE
        )

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and check if article needs update.

        Args:
            state: AgentState with article data

        Returns:
            Updated state with update assessment
        """
        article = {
            "article_id": state.get("article_id"),
            "title": state.get("article_title"),
            "content": state.get("article_content"),
            "category": state.get("article_category"),
            "created_at": state.get("article_created_at"),
            "updated_at": state.get("article_updated_at"),
            "quality_score": state.get("quality_score"),
            "helpfulness_ratio": state.get("helpfulness_ratio")
        }

        self.logger.info(
            "kb_update_check_started",
            article_id=article.get("article_id"),
            title=article.get("title", "")[:50]
        )

        # Check if needs update
        update_check = await self.check_needs_update(article)

        # Update state
        state = self.update_state(
            state,
            needs_update=update_check["needs_update"],
            update_assessment=update_check
        )

        self.logger.info(
            "kb_update_check_completed",
            article_id=article.get("article_id"),
            needs_update=update_check["needs_update"],
            priority=update_check.get("update_priority", "none")
        )

        return state

    async def check_needs_update(self, article: Dict) -> Dict:
        """
        Check if article needs updating.

        Args:
            article: Article dict

        Returns:
            Update assessment dict
        """
        reasons = []
        needs_update = False

        # Check 1: Age
        age_check = self._check_age(article)
        if age_check:
            reasons.append(age_check)
            needs_update = True

        # Check 2: Low quality score
        quality_check = self._check_quality(article)
        if quality_check:
            reasons.append(quality_check)
            needs_update = True

        # Check 3: Low helpfulness
        helpfulness_check = self._check_helpfulness(article)
        if helpfulness_check:
            reasons.append(helpfulness_check)
            needs_update = True

        # Check 4: Deprecated features
        deprecated_check = self._check_deprecated_features(article)
        if deprecated_check:
            reasons.extend(deprecated_check)
            needs_update = True

        # Check 5: Broken links
        broken_links_check = self._check_broken_links(article)
        if broken_links_check:
            reasons.append(broken_links_check)
            needs_update = True

        # Determine priority
        priority = self._calculate_priority(reasons)

        # Generate suggestions
        suggestions = self._generate_suggestions(reasons, article)

        # Estimate effort
        effort = self._estimate_effort(reasons)

        return {
            "article_id": article.get("article_id"),
            "needs_update": needs_update,
            "update_priority": priority,
            "reasons": reasons,
            "suggested_updates": suggestions,
            "estimated_effort": effort,
            "last_checked_at": datetime.utcnow().isoformat()
        }

    def _check_age(self, article: Dict) -> Optional[Dict]:
        """Check if article is too old."""
        updated_at = article.get("updated_at")
        if not updated_at:
            return None

        try:
            if isinstance(updated_at, str):
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                updated_date = updated_at

            days_old = (datetime.now(updated_date.tzinfo or None) - updated_date).days

            if days_old > self.AGE_THRESHOLD_DAYS:
                severity = "high" if days_old > 365 else "medium"
                return {
                    "type": "age",
                    "severity": severity,
                    "description": f"Article not updated in {days_old // 30} months",
                    "detail": f"Last updated: {updated_at}"
                }

        except (ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                "age_check_failed",
                error=str(e),
                article_id=article.get("article_id")
            )

        return None

    def _check_quality(self, article: Dict) -> Optional[Dict]:
        """Check if article has low quality score."""
        quality_score = article.get("quality_score")

        if quality_score and quality_score < self.MIN_QUALITY_SCORE:
            return {
                "type": "low_quality",
                "severity": "medium",
                "description": f"Quality score below threshold ({quality_score}/100)",
                "detail": f"Minimum quality score: {self.MIN_QUALITY_SCORE}"
            }

        return None

    def _check_helpfulness(self, article: Dict) -> Optional[Dict]:
        """Check if article has low helpfulness ratio."""
        helpfulness = article.get("helpfulness_ratio")

        if helpfulness and helpfulness < self.LOW_HELPFULNESS_THRESHOLD:
            return {
                "type": "low_helpfulness",
                "severity": "medium",
                "description": f"Low helpfulness ratio ({helpfulness:.0%})",
                "detail": "Users find this article not helpful"
            }

        return None

    def _check_deprecated_features(self, article: Dict) -> List[Dict]:
        """Check if article references deprecated features."""
        content = article.get("content", "")
        reasons = []

        # Get list of deprecated features
        deprecated_features = self._get_deprecated_features()

        for feature in deprecated_features:
            # Check if article mentions this feature
            pattern = re.compile(feature["name"], re.IGNORECASE)
            if pattern.search(content):
                reasons.append({
                    "type": "deprecated_feature",
                    "severity": "high",
                    "description": f"References deprecated {feature['name']}",
                    "detail": f"{feature['name']} was deprecated in version {feature['deprecated_in']}"
                })

        return reasons

    def _check_broken_links(self, article: Dict) -> Optional[Dict]:
        """Check for broken internal links."""
        content = article.get("content", "")

        # Find all markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)

        broken_count = 0
        for link_text, link_url in links:
            # Check if internal link (starts with /)
            if link_url.startswith('/'):
                # Simple check: see if URL contains common broken patterns
                if any(pattern in link_url for pattern in ['old', 'deprecated', 'v1', 'legacy']):
                    broken_count += 1

        if broken_count > 0:
            return {
                "type": "broken_links",
                "severity": "low",
                "description": f"Potentially {broken_count} broken link(s)",
                "detail": "Review and update internal links"
            }

        return None

    def _get_deprecated_features(self) -> List[Dict]:
        """
        Get list of deprecated features from database or config.

        Returns:
            List of deprecated features
        """
        # In production, this would query a product_features table
        # For now, return hardcoded list
        return [
            {"name": "Dashboard v1", "deprecated_in": "2.0.0"},
            {"name": "Old API", "deprecated_in": "2.2.0"},
            {"name": "Legacy UI", "deprecated_in": "2.3.0"},
            {"name": "Classic Mode", "deprecated_in": "2.4.0"}
        ]

    def _calculate_priority(self, reasons: List[Dict]) -> str:
        """
        Calculate update priority based on reasons.

        Args:
            reasons: List of update reasons

        Returns:
            Priority level (low, medium, high, critical)
        """
        if not reasons:
            return "none"

        # Count severity levels
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for reason in reasons:
            severity = reason.get("severity", "low")
            severity_counts[severity] += 1

        # Determine priority
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] >= 2:
            return "high"
        elif severity_counts["high"] >= 1:
            return "high"
        elif severity_counts["medium"] >= 2:
            return "medium"
        else:
            return "low"

    def _generate_suggestions(self, reasons: List[Dict], article: Dict) -> List[str]:
        """
        Generate actionable update suggestions.

        Args:
            reasons: List of update reasons
            article: Article dict

        Returns:
            List of suggestions
        """
        suggestions = []
        seen_suggestions = set()

        for reason in reasons:
            reason_type = reason["type"]

            if reason_type == "age":
                if "Review all content" not in seen_suggestions:
                    suggestions.append("Review and update all content for accuracy")
                    seen_suggestions.add("Review all content")
                if "Update screenshots" not in seen_suggestions:
                    suggestions.append("Add screenshots from current product version")
                    seen_suggestions.add("Update screenshots")

            elif reason_type == "deprecated_feature":
                suggestions.append(f"Remove or update references to {reason.get('detail', 'deprecated features')}")
                if "Update to current" not in seen_suggestions:
                    suggestions.append("Update to current feature equivalents")
                    seen_suggestions.add("Update to current")

            elif reason_type == "low_quality":
                if "Improve structure" not in seen_suggestions:
                    suggestions.append("Improve article structure and completeness")
                    seen_suggestions.add("Improve structure")
                if "Add examples" not in seen_suggestions:
                    suggestions.append("Add more examples and screenshots")
                    seen_suggestions.add("Add examples")

            elif reason_type == "low_helpfulness":
                if "Review feedback" not in seen_suggestions:
                    suggestions.append("Review user feedback for common issues")
                    seen_suggestions.add("Review feedback")
                if "Clarify sections" not in seen_suggestions:
                    suggestions.append("Clarify confusing sections")
                    seen_suggestions.add("Clarify sections")

            elif reason_type == "broken_links":
                if "Update links" not in seen_suggestions:
                    suggestions.append("Update all internal links")
                    suggestions.append("Remove links to deprecated pages")
                    seen_suggestions.add("Update links")

        return suggestions[:5]  # Limit to top 5

    def _estimate_effort(self, reasons: List[Dict]) -> str:
        """
        Estimate effort to update article.

        Args:
            reasons: List of update reasons

        Returns:
            Effort estimate string
        """
        severity_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        total_severity = sum(
            severity_scores.get(r.get("severity", "low"), 1)
            for r in reasons
        )

        if total_severity >= 8:
            return "4+ hours (major rewrite)"
        elif total_severity >= 5:
            return "2-3 hours (significant updates)"
        elif total_severity >= 3:
            return "1-2 hours (moderate updates)"
        else:
            return "30-60 minutes (minor updates)"

    async def find_articles_needing_update(self, limit: int = 20) -> List[Dict]:
        """
        Find all articles that need updating.

        Args:
            limit: Max articles to return

        Returns:
            List of articles needing update
        """
        try:
            async with get_db_session() as session:
                # Get all active articles
                result = await session.execute(
                    select(KBArticle).where(KBArticle.is_active == 1)
                )
                articles = result.scalars().all()

                articles_needing_update = []

                for article in articles:
                    article_dict = {
                        "article_id": str(article.id),
                        "title": article.title,
                        "content": article.content,
                        "category": article.category,
                        "created_at": article.created_at,
                        "updated_at": article.updated_at,
                        "quality_score": article.quality_score,
                        "helpfulness_ratio": self._calculate_helpfulness_ratio(article)
                    }

                    check_result = await self.check_needs_update(article_dict)

                    if check_result["needs_update"]:
                        articles_needing_update.append(check_result)

                # Sort by priority
                priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
                articles_needing_update.sort(
                    key=lambda x: priority_order.get(x["update_priority"], 4)
                )

                return articles_needing_update[:limit]

        except SQLAlchemyError as e:
            self.logger.error(
                "find_articles_needing_update_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    def _calculate_helpfulness_ratio(self, article) -> float:
        """Calculate helpfulness ratio from article."""
        total_votes = (article.helpful_count or 0) + (article.not_helpful_count or 0)
        if total_votes == 0:
            return 0.5

        return (article.helpful_count or 0) / total_votes


if __name__ == "__main__":
    # Test KB Updater
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB UPDATER")
        print("=" * 60)

        updater = KBUpdater()

        # Test articles
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()

        test_articles = [
            {
                "article_id": "kb_old",
                "title": "Old Article with Deprecated Features",
                "content": "Use Dashboard v1 to access...",
                "updated_at": old_date,
                "quality_score": 60,
                "helpfulness_ratio": 0.35
            },
            {
                "article_id": "kb_recent",
                "title": "Recent High-Quality Article",
                "content": "Modern guide to...",
                "updated_at": recent_date,
                "quality_score": 90,
                "helpfulness_ratio": 0.92
            }
        ]

        print("\nTest 1: Check old article")
        check1 = await updater.check_needs_update(test_articles[0])
        print(f"Needs update: {check1['needs_update']}")
        print(f"Priority: {check1['update_priority']}")
        print(f"Reasons: {len(check1['reasons'])}")
        for reason in check1['reasons']:
            print(f"  - [{reason['severity']}] {reason['description']}")
        print(f"Suggestions: {len(check1['suggested_updates'])}")
        for suggestion in check1['suggested_updates']:
            print(f"  - {suggestion}")

        print("\nTest 2: Check recent article")
        check2 = await updater.check_needs_update(test_articles[1])
        print(f"Needs update: {check2['needs_update']}")
        print(f"Priority: {check2.get('update_priority', 'none')}")

        print("\nTest 3: Find articles needing update")
        articles = await updater.find_articles_needing_update(limit=5)
        print(f"Found {len(articles)} articles needing update")

        print("\n✓ KB Updater tests completed!")

    asyncio.run(test())
