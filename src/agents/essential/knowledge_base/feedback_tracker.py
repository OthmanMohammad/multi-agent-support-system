"""
KB Feedback Tracker Agent.

Tracks KB article usage and effectiveness metrics. Feeds data to KB Ranker
and Quality Checker for continuous improvement.

Part of: STORY-002 Knowledge Base Swarm (TASK-204)
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base import AgentConfig
from src.agents.base.agent_types import AgentType
from src.agents.base.base_agent import BaseAgent
from src.database.connection import get_db_session
from src.database.models import KBArticle, KBUsage
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


class KBFeedbackTracker(BaseAgent):
    """
    Knowledge Base Feedback Tracker Agent.

    Tracks KB article usage and effectiveness metrics:
    - Article views
    - Helpful/not helpful votes
    - Resolution metrics (time, CSAT)
    - Usage patterns
    """

    def __init__(self):
        """Initialize KB Feedback Tracker agent."""
        config = AgentConfig(
            name="kb_feedback_tracker",
            type=AgentType.UTILITY,
            model="",  # No LLM needed
            temperature=0.0,
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info("kb_feedback_tracker_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and track KB feedback.

        Args:
            state: AgentState with article usage info

        Returns:
            Updated state with tracking confirmation
        """
        # Extract tracking info from state
        article_id = state.get("article_id")
        event_type = state.get("event_type", "viewed")
        conversation_id = state.get("conversation_id")
        customer_id = state.get("customer_id")
        metadata = state.get("feedback_metadata", {})

        if not article_id:
            # No article to track
            self.logger.debug("kb_feedback_tracker_no_article_id")
            return state

        self.logger.info(
            "kb_feedback_tracking_started", article_id=article_id, event_type=event_type
        )

        # Track the event
        result = await self.track_event(
            article_id=article_id,
            event_type=event_type,
            conversation_id=conversation_id,
            customer_id=customer_id,
            metadata=metadata,
        )

        # Update state
        state = self.update_state(
            state, feedback_tracked=result["tracked"], article_stats=result["article_stats"]
        )

        self.logger.info(
            "kb_feedback_tracking_completed", tracked=result["tracked"], article_id=article_id
        )

        return state

    async def track_event(
        self,
        article_id: str,
        event_type: str,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Track KB article usage event.

        Args:
            article_id: KB article ID
            event_type: Type of event (viewed, helpful, not_helpful, resolved_with)
            conversation_id: Associated conversation
            customer_id: Customer who triggered event
            metadata: Additional event metadata

        Returns:
            Dict with tracking status and article stats
        """
        metadata = metadata or {}

        try:
            async with get_db_session() as session:
                # Create usage record
                usage_record = KBUsage(
                    article_id=article_id,
                    event_type=event_type,
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    resolution_time_seconds=metadata.get("resolution_time_seconds"),
                    csat_score=metadata.get("csat_score"),
                    metadata=metadata,
                    created_at=datetime.now(UTC),
                )

                session.add(usage_record)

                # Update article aggregated stats
                await self._update_article_stats(session, article_id, event_type, metadata)

                # Commit is automatic in get_db_session context manager

                # Get current article stats
                article_stats = await self.get_article_stats(article_id)

                self.logger.info("kb_event_tracked", article_id=article_id, event_type=event_type)

                return {"tracked": True, "article_stats": article_stats}

        except SQLAlchemyError as e:
            self.logger.error(
                "kb_feedback_tracking_failed",
                error=str(e),
                error_type=type(e).__name__,
                article_id=article_id,
                event_type=event_type,
            )
            return {"tracked": False, "article_stats": {}}

    async def _update_article_stats(
        self, session, article_id: str, event_type: str, metadata: dict
    ):
        """
        Update aggregated article statistics.

        Args:
            session: Database session
            article_id: Article to update
            event_type: Event type
            metadata: Event metadata
        """
        # Get article
        result = await session.execute(select(KBArticle).where(KBArticle.id == article_id))
        article = result.scalar_one_or_none()

        if not article:
            self.logger.warning("kb_article_not_found_for_stats_update", article_id=article_id)
            return

        # Increment counters based on event type
        if event_type == "viewed":
            article.view_count = (article.view_count or 0) + 1

        elif event_type == "helpful":
            article.helpful_count = (article.helpful_count or 0) + 1

        elif event_type == "not_helpful":
            article.not_helpful_count = (article.not_helpful_count or 0) + 1

        elif event_type == "resolved_with":
            # Track resolution metrics
            if "resolution_time_seconds" in metadata:
                # Update running average
                current_avg = article.avg_resolution_time_seconds or 0
                current_count = article.resolution_count or 0
                new_time = metadata["resolution_time_seconds"]

                article.avg_resolution_time_seconds = (current_avg * current_count + new_time) / (
                    current_count + 1
                )
                article.resolution_count = current_count + 1

            if "csat_score" in metadata:
                # Update running average CSAT
                current_avg = article.avg_csat or 0
                current_count = article.csat_count or 0
                new_csat = metadata["csat_score"]

                article.avg_csat = (current_avg * current_count + new_csat) / (current_count + 1)
                article.csat_count = current_count + 1

        # Update timestamp
        article.last_used_at = datetime.now(UTC)

    async def get_article_stats(self, article_id: str) -> dict:
        """
        Get current statistics for an article.

        Args:
            article_id: Article ID

        Returns:
            Dict with article statistics
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(select(KBArticle).where(KBArticle.id == article_id))
                article = result.scalar_one_or_none()

                if not article:
                    return {}

                total_votes = (article.helpful_count or 0) + (article.not_helpful_count or 0)
                helpfulness_ratio = 0.0
                if total_votes > 0:
                    helpfulness_ratio = (article.helpful_count or 0) / total_votes

                return {
                    "article_id": str(article.id),
                    "title": article.title,
                    "total_views": article.view_count or 0,
                    "helpful_count": article.helpful_count or 0,
                    "not_helpful_count": article.not_helpful_count or 0,
                    "helpfulness_ratio": round(helpfulness_ratio, 3),
                    "avg_resolution_time_seconds": article.avg_resolution_time_seconds,
                    "avg_csat": round(article.avg_csat, 2) if article.avg_csat else None,
                    "resolution_count": article.resolution_count or 0,
                    "last_used_at": article.last_used_at.isoformat()
                    if article.last_used_at
                    else None,
                }

        except SQLAlchemyError as e:
            self.logger.error(
                "kb_article_stats_retrieval_failed", error=str(e), article_id=article_id
            )
            return {}

    async def get_top_articles(self, limit: int = 10, metric: str = "helpful") -> list[dict]:
        """
        Get top performing articles.

        Args:
            limit: Number of articles to return
            metric: Sort by metric (helpful, views, csat, resolution_time)

        Returns:
            List of top articles
        """
        try:
            async with get_db_session() as session:
                query = select(KBArticle).where(KBArticle.is_active == 1)

                if metric == "helpful":
                    query = query.order_by(KBArticle.helpful_count.desc())
                elif metric == "views":
                    query = query.order_by(KBArticle.view_count.desc())
                elif metric == "csat":
                    query = query.order_by(KBArticle.avg_csat.desc())
                elif metric == "resolution_time":
                    query = query.order_by(KBArticle.avg_resolution_time_seconds.asc())

                query = query.limit(limit)

                result = await session.execute(query)
                articles = result.scalars().all()

                return [await self.get_article_stats(str(article.id)) for article in articles]

        except SQLAlchemyError as e:
            self.logger.error("kb_top_articles_retrieval_failed", error=str(e), metric=metric)
            return []

    async def get_low_performing_articles(
        self, threshold: float = 0.5, limit: int = 10
    ) -> list[dict]:
        """
        Get articles with low helpfulness ratio.

        Args:
            threshold: Helpfulness ratio threshold (0-1)
            limit: Max articles to return

        Returns:
            List of low-performing articles
        """
        try:
            async with get_db_session() as session:
                # Get articles with enough votes to be statistically significant
                min_votes = 10
                query = select(KBArticle).where(
                    KBArticle.is_active == 1,
                    (KBArticle.helpful_count + KBArticle.not_helpful_count) >= min_votes,
                )

                result = await session.execute(query)
                articles = result.scalars().all()

                # Calculate helpfulness ratio and filter
                low_performers = []
                for article in articles:
                    total_votes = (article.helpful_count or 0) + (article.not_helpful_count or 0)
                    if total_votes > 0:
                        ratio = (article.helpful_count or 0) / total_votes
                        if ratio < threshold:
                            stats = await self.get_article_stats(str(article.id))
                            stats["helpfulness_ratio"] = ratio
                            low_performers.append(stats)

                # Sort by ratio (worst first)
                low_performers.sort(key=lambda x: x["helpfulness_ratio"])

                return low_performers[:limit]

        except SQLAlchemyError as e:
            self.logger.error(
                "kb_low_performing_articles_retrieval_failed", error=str(e), threshold=threshold
            )
            return []


if __name__ == "__main__":
    # Test KB Feedback Tracker
    import asyncio
    import uuid

    async def test():
        print("=" * 60)
        print("TESTING KB FEEDBACK TRACKER")
        print("=" * 60)

        tracker = KBFeedbackTracker()

        # Generate test article ID
        test_article_id = str(uuid.uuid4())

        print("\nTest 1: Track view event")
        result = await tracker.track_event(article_id=test_article_id, event_type="viewed")
        print(f"Tracked: {result['tracked']}")

        print("\nTest 2: Track helpful vote")
        result = await tracker.track_event(article_id=test_article_id, event_type="helpful")
        print(f"Tracked: {result['tracked']}")

        print("\nTest 3: Track resolution")
        result = await tracker.track_event(
            article_id=test_article_id,
            event_type="resolved_with",
            metadata={"resolution_time_seconds": 120, "csat_score": 5},
        )
        print(f"Tracked: {result['tracked']}")
        if result["article_stats"]:
            print(f"Stats: {result['article_stats']}")

        print("\nTest 4: Get top articles")
        top_articles = await tracker.get_top_articles(limit=5, metric="views")
        print(f"Found {len(top_articles)} top articles")

        print("\n✓ KB Feedback Tracker tests completed!")

    asyncio.run(test())
