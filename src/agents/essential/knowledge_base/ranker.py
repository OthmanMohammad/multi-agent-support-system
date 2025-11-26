"""
KB Ranker Agent.

Re-ranks KB search results using multiple factors beyond semantic similarity.
Improves relevance by considering quality, recency, and historical helpfulness.

"""

import math
from datetime import datetime

from src.agents.base import AgentConfig
from src.agents.base.agent_types import AgentType
from src.agents.base.base_agent import BaseAgent
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


class KBRanker(BaseAgent):
    """
    Knowledge Base Ranker Agent.

    Re-ranks KB search results using weighted scoring:
    - Semantic similarity (50%)
    - Article quality (20%)
    - Recency (15%)
    - Historical helpfulness (15%)
    """

    # Ranking weights
    SIMILARITY_WEIGHT = 0.50
    QUALITY_WEIGHT = 0.20
    RECENCY_WEIGHT = 0.15
    HELPFULNESS_WEIGHT = 0.15

    def __init__(self):
        """Initialize KB Ranker agent."""
        config = AgentConfig(
            name="kb_ranker",
            type=AgentType.UTILITY,
            model="",  # No LLM needed for ranking
            temperature=0.0,
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info(
            "kb_ranker_initialized",
            similarity_weight=self.SIMILARITY_WEIGHT,
            quality_weight=self.QUALITY_WEIGHT,
            recency_weight=self.RECENCY_WEIGHT,
            helpfulness_weight=self.HELPFULNESS_WEIGHT,
        )

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and re-rank KB results.

        Args:
            state: AgentState with kb_results

        Returns:
            Updated state with ranked results
        """
        kb_results = state.get("kb_results", [])

        if not kb_results:
            self.logger.info("kb_ranker_no_results_to_rank")
            state = self.update_state(state, kb_ranked_results=[])
            return state

        self.logger.info("kb_ranking_started", articles_count=len(kb_results))

        # Re-rank results
        ranked_results = self.rank(kb_results)

        # Update state
        state = self.update_state(state, kb_ranked_results=ranked_results)

        self.logger.info(
            "kb_ranking_completed",
            articles_count=len(ranked_results),
            top_score=ranked_results[0]["final_score"] if ranked_results else 0,
        )

        return state

    def rank(self, articles: list[dict]) -> list[dict]:
        """
        Re-rank articles by multiple factors.

        Args:
            articles: List of KB article dicts from searcher

        Returns:
            Re-ranked list with scores
        """
        ranked_articles = []

        for idx, article in enumerate(articles):
            # Calculate individual scores
            similarity_score = article.get("similarity_score", 0.0)
            quality_score = self._normalize_quality_score(article.get("quality_score", None))
            recency_score = self._calculate_recency_score(
                article.get("created_at"), article.get("updated_at")
            )
            helpfulness_score = self._calculate_helpfulness_score(
                article.get("helpful_count", 0),
                article.get("not_helpful_count", 0),
                article.get("view_count", 0),
            )

            # Calculate weighted final score
            final_score = (
                similarity_score * self.SIMILARITY_WEIGHT
                + quality_score * self.QUALITY_WEIGHT
                + recency_score * self.RECENCY_WEIGHT
                + helpfulness_score * self.HELPFULNESS_WEIGHT
            )

            ranked_articles.append(
                {
                    **article,  # Keep all original fields
                    "final_score": round(final_score, 3),
                    "quality_score_normalized": round(quality_score, 3),
                    "recency_score": round(recency_score, 3),
                    "helpfulness_score": round(helpfulness_score, 3),
                    "original_rank": idx + 1,
                }
            )

        # Sort by final score (descending)
        ranked_articles.sort(key=lambda x: x["final_score"], reverse=True)

        # Add new rank and rank change
        for new_rank, article in enumerate(ranked_articles, 1):
            article["rank"] = new_rank
            article["rank_change"] = article["original_rank"] - new_rank

        return ranked_articles

    def _normalize_quality_score(self, quality_score: float | None) -> float:
        """
        Normalize quality score to 0-1 range.

        Args:
            quality_score: Quality score (0-100) or None

        Returns:
            Normalized score (0-1)
        """
        if quality_score is None:
            return 0.5  # Default to medium quality

        # Quality score is 0-100, normalize to 0-1
        return max(0.0, min(1.0, quality_score / 100.0))

    def _calculate_recency_score(
        self, created_at: str | datetime | None, updated_at: str | datetime | None = None
    ) -> float:
        """
        Calculate recency score (0-1).

        More recent = higher score.
        Uses exponential decay (half-life of 180 days).

        Args:
            created_at: Article creation date
            updated_at: Article update date (optional)

        Returns:
            Recency score (0-1)
        """
        if not created_at and not updated_at:
            return 0.5  # Default to medium if no dates

        # Use updated_at if available, else created_at
        date_str = updated_at if updated_at else created_at

        try:
            # Parse date
            if isinstance(date_str, str):
                article_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif isinstance(date_str, datetime):
                article_date = date_str
            else:
                return 0.5

            # Calculate days old
            days_old = (datetime.now(article_date.tzinfo) - article_date).days

            # Exponential decay: score = 0.5^(days / half_life)
            half_life_days = 180  # 6 months
            score = math.pow(0.5, days_old / half_life_days)

            return min(max(score, 0.0), 1.0)

        except (ValueError, AttributeError, TypeError) as e:
            self.logger.warning(
                "recency_score_calculation_failed", error=str(e), date_str=str(date_str)
            )
            return 0.5  # Default if date parsing fails

    def _calculate_helpfulness_score(
        self, helpful_count: int, not_helpful_count: int, view_count: int
    ) -> float:
        """
        Calculate helpfulness score (0-1).

        Uses Wilson score confidence interval
        (same algorithm as Reddit/HN for ranking).

        Args:
            helpful_count: Number of helpful votes
            not_helpful_count: Number of not helpful votes
            view_count: Number of views

        Returns:
            Helpfulness score (0-1)
        """
        if view_count == 0:
            return 0.5  # No data yet

        total_votes = helpful_count + not_helpful_count

        if total_votes == 0:
            # No feedback yet, use view count as proxy
            # More views = more trusted (up to a point)
            return min(0.5 + (view_count / 1000) * 0.1, 0.7)

        # Wilson score lower bound
        positive_ratio = helpful_count / total_votes
        z = 1.96  # 95% confidence

        try:
            numerator = (
                positive_ratio
                + z * z / (2 * total_votes)
                - z
                * math.sqrt(
                    (positive_ratio * (1 - positive_ratio) + z * z / (4 * total_votes))
                    / total_votes
                )
            )
            denominator = 1 + z * z / total_votes

            score = numerator / denominator

            return min(max(score, 0.0), 1.0)

        except (ValueError, ZeroDivisionError) as e:
            self.logger.warning(
                "helpfulness_score_calculation_failed",
                error=str(e),
                helpful_count=helpful_count,
                total_votes=total_votes,
            )
            # Fallback to simple ratio
            return positive_ratio


if __name__ == "__main__":
    # Test KB Ranker
    import asyncio
    from datetime import timedelta

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB RANKER")
        print("=" * 60)

        ranker = KBRanker()

        # Test articles with different characteristics
        now = datetime.now()
        test_articles = [
            {
                "article_id": "kb_1",
                "title": "High similarity, low quality",
                "similarity_score": 0.95,
                "quality_score": 40,
                "helpful_count": 5,
                "not_helpful_count": 10,
                "view_count": 50,
                "created_at": (now - timedelta(days=400)).isoformat(),
            },
            {
                "article_id": "kb_2",
                "title": "Medium similarity, high quality, recent",
                "similarity_score": 0.80,
                "quality_score": 95,
                "helpful_count": 50,
                "not_helpful_count": 2,
                "view_count": 500,
                "created_at": (now - timedelta(days=30)).isoformat(),
            },
            {
                "article_id": "kb_3",
                "title": "Lower similarity, good quality",
                "similarity_score": 0.75,
                "quality_score": 85,
                "helpful_count": 30,
                "not_helpful_count": 3,
                "view_count": 300,
                "created_at": (now - timedelta(days=90)).isoformat(),
            },
        ]

        print("\nOriginal ranking (by similarity):")
        for i, article in enumerate(test_articles, 1):
            print(f"  {i}. {article['title']}")
            print(f"     Similarity: {article['similarity_score']:.2f}")

        # Rank articles
        ranked = ranker.rank(test_articles)

        print("\nRe-ranked (by final score):")
        for i, article in enumerate(ranked, 1):
            print(f"  {i}. {article['title']}")
            print(f"     Final Score: {article['final_score']:.3f}")
            print(
                f"     Sim: {article['similarity_score']:.2f}, "
                f"Qual: {article['quality_score_normalized']:.2f}, "
                f"Recency: {article['recency_score']:.2f}, "
                f"Helpful: {article['helpfulness_score']:.2f}"
            )
            print(f"     Rank change: {article['rank_change']:+d}")

        # Test with state
        print("\nTest with state:")
        state = create_initial_state(message="test")
        state["kb_results"] = test_articles
        state = await ranker.process(state)
        print(f"Ranked {len(state['kb_ranked_results'])} articles")

        print("\n✓ KB Ranker tests completed!")

    asyncio.run(test())
