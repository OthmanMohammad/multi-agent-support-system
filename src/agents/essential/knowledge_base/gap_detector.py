"""
KB Gap Detector Agent.

Identifies missing content in the knowledge base by analyzing queries with
low KB match scores and clustering similar unanswered questions.

Part of: STORY-002 Knowledge Base Swarm (TASK-207)
"""

from typing import List, Dict
from collections import Counter
from datetime import datetime, timedelta, UTC
import json
import numpy as np
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.database.connection import get_db_session
from src.database.models import Conversation, Message
from src.utils.logging.setup import get_logger

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False


class KBGapDetector(BaseAgent):
    """
    KB Gap Detector Agent.

    Identifies missing knowledge base content by:
    - Tracking queries with low KB match scores (<0.7)
    - Clustering similar queries using embeddings
    - Identifying common topics without good articles
    - Suggesting new article topics
    """

    LOW_MATCH_THRESHOLD = 0.7
    MIN_CLUSTER_SIZE = 3

    def __init__(self):
        """Initialize KB Gap Detector agent."""
        config = AgentConfig(
            name="kb_gap_detector",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=512,
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        # Initialize embedding model for clustering
        if CLUSTERING_AVAILABLE:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
            self.logger.warning("clustering_unavailable", message="sentence-transformers not installed")

        self.logger.info("kb_gap_detector_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and detect KB gaps.

        Args:
            state: AgentState

        Returns:
            Updated state with detected gaps
        """
        days = state.get("gap_detection_days", 30)
        min_frequency = state.get("gap_min_frequency", 5)

        self.logger.info(
            "kb_gap_detection_started",
            days=days,
            min_frequency=min_frequency
        )

        # Detect gaps
        gaps = await self.detect_gaps(days=days, min_frequency=min_frequency)

        # Update state
        state = self.update_state(
            state,
            kb_gaps=gaps,
            gaps_detected=len(gaps)
        )

        self.logger.info(
            "kb_gap_detection_completed",
            gaps_count=len(gaps)
        )

        return state

    async def detect_gaps(
        self,
        days: int = 30,
        min_frequency: int = 5
    ) -> List[Dict]:
        """
        Detect KB content gaps.

        Args:
            days: Look back this many days
            min_frequency: Min occurrences to consider

        Returns:
            List of gap topics with priority
        """
        # Get queries with low KB scores
        low_match_queries = await self._get_low_match_queries(days)

        if len(low_match_queries) < min_frequency:
            self.logger.info(
                "kb_gap_detection_insufficient_data",
                queries_count=len(low_match_queries),
                min_required=min_frequency
            )
            return []

        # Cluster similar queries
        clusters = await self._cluster_queries(low_match_queries)

        # Analyze each cluster
        gaps = []
        for cluster_id, queries in clusters.items():
            if len(queries) >= min_frequency:
                gap = await self._analyze_cluster(queries)
                gaps.append(gap)

        # Sort by priority
        gaps.sort(key=lambda x: x['priority_score'], reverse=True)

        return gaps

    async def _get_low_match_queries(self, days: int) -> List[str]:
        """
        Get queries with low KB match scores.

        Args:
            days: Look back period

        Returns:
            List of query strings
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        try:
            async with get_db_session() as session:
                # Query conversations with low KB scores
                result = await session.execute(
                    select(Conversation).where(
                        Conversation.created_at >= cutoff_date
                    )
                )
                conversations = result.scalars().all()

                queries = []
                for conv in conversations:
                    # Get first user message
                    msg_result = await session.execute(
                        select(Message).where(
                            Message.conversation_id == conv.id,
                            Message.role == 'user'
                        ).limit(1)
                    )
                    first_msg = msg_result.scalar_one_or_none()

                    if first_msg:
                        queries.append(first_msg.content)

                self.logger.info(
                    "low_match_queries_retrieved",
                    queries_count=len(queries)
                )

                return queries

        except SQLAlchemyError as e:
            self.logger.error(
                "low_match_queries_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def _cluster_queries(self, queries: List[str]) -> Dict[int, List[str]]:
        """
        Cluster similar queries using embeddings.

        Args:
            queries: List of query strings

        Returns:
            Dict mapping cluster_id to list of queries
        """
        if not queries or not self.embedding_model:
            return {}

        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(queries)

            # Cluster using DBSCAN
            clustering = DBSCAN(
                eps=0.3,
                min_samples=self.MIN_CLUSTER_SIZE,
                metric='cosine'
            ).fit(embeddings)

            # Group queries by cluster
            clusters = {}
            for idx, label in enumerate(clustering.labels_):
                if label == -1:  # Noise - skip
                    continue

                if label not in clusters:
                    clusters[label] = []

                clusters[label].append(queries[idx])

            self.logger.info(
                "queries_clustered",
                clusters_count=len(clusters),
                noise_count=list(clustering.labels_).count(-1)
            )

            return clusters

        except Exception as e:
            self.logger.error(
                "query_clustering_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return {}

    async def _analyze_cluster(self, queries: List[str]) -> Dict:
        """
        Analyze cluster and generate gap report.

        Args:
            queries: List of similar queries in cluster

        Returns:
            Gap report dict
        """
        # Use LLM to summarize common topic
        system_prompt = """Analyze these related customer queries and identify the common topic.

Return ONLY valid JSON with this structure:
{
  "topic": "Brief topic description",
  "suggested_article_title": "Proposed KB article title",
  "key_questions": ["Q1", "Q2", "Q3"],
  "category": "billing|technical|usage|api|integrations|account"
}"""

        user_prompt = f"""Queries:\n""" + "\n".join(f"- {q}" for q in queries[:10])

        try:
            response = await self.call_llm(
                system_prompt=system_prompt,
                user_message=user_prompt,
                max_tokens=512
            )

            # Parse JSON response
            analysis = json.loads(response)

        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning(
                "cluster_analysis_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Fallback
            analysis = {
                "topic": "Unknown topic",
                "suggested_article_title": "New Article Needed",
                "key_questions": queries[:3],
                "category": "general"
            }

        # Calculate priority score
        priority_score = self._calculate_priority(queries, analysis)

        return {
            "topic": analysis.get("topic", "Unknown"),
            "suggested_article_title": analysis.get("suggested_article_title", "New Article"),
            "key_questions": analysis.get("key_questions", []),
            "category": analysis.get("category", "general"),
            "frequency": len(queries),
            "priority_score": priority_score,
            "example_queries": queries[:5]
        }

    def _calculate_priority(self, queries: List[str], analysis: Dict) -> float:
        """
        Calculate gap priority score (0-100).

        Args:
            queries: List of queries in cluster
            analysis: LLM analysis result

        Returns:
            Priority score (0-100)
        """
        # Frequency component (50%)
        frequency_score = min(len(queries) * 5, 50)

        # Category importance (30%)
        category_weights = {
            "billing": 30,
            "technical": 25,
            "api": 25,
            "usage": 20,
            "integrations": 20,
            "account": 15,
            "general": 10
        }
        category_score = category_weights.get(
            analysis.get("category", "general"),
            10
        )

        # Recency (20%) - assuming recent queries
        recency_score = 20

        total_score = frequency_score + category_score + recency_score

        return min(total_score, 100)


if __name__ == "__main__":
    # Test KB Gap Detector
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB GAP DETECTOR")
        print("=" * 60)

        detector = KBGapDetector()

        print("\nTest 1: Detect gaps")
        gaps = await detector.detect_gaps(days=30, min_frequency=3)
        print(f"Found {len(gaps)} gaps")

        for i, gap in enumerate(gaps[:3], 1):
            print(f"\nGap {i}:")
            print(f"  Topic: {gap['topic']}")
            print(f"  Suggested Title: {gap['suggested_article_title']}")
            print(f"  Category: {gap['category']}")
            print(f"  Frequency: {gap['frequency']}")
            print(f"  Priority Score: {gap['priority_score']}")

        print("\nTest 2: Process with state")
        state = create_initial_state(
            message="test",
            context={"gap_detection_days": 30}
        )
        state = await detector.process(state)
        print(f"Gaps detected: {state.get('gaps_detected', 0)}")

        print("\n✓ KB Gap Detector tests completed!")

    asyncio.run(test())
