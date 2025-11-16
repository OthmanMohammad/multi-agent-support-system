"""
KB Searcher Agent.

Performs semantic search across knowledge base articles using Qdrant vector database.
This is the foundation for all KB-powered agent responses.

"""

from typing import List, Dict, Optional
import time

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType, AgentCapability
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.core.config import get_settings
from src.utils.logging.setup import get_logger
from src.vector_store import VectorStore


class KBSearcher(BaseAgent):
    """
    Knowledge Base Searcher Agent.

    Performs semantic search across KB articles using vector similarity.
    Returns top N articles sorted by relevance score.

    Capabilities:
    - Semantic search using sentence-transformers
    - Category filtering
    - Tag filtering
    - Similarity threshold filtering
    """

    def __init__(self):
        """Initialize KB Searcher agent."""
        config = AgentConfig(
            name="kb_searcher",
            type=AgentType.UTILITY,
            model="",  # No LLM needed for search
            temperature=0.0,
            capabilities=[AgentCapability.KB_SEARCH],
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        # Initialize vector store
        self.vector_store = VectorStore()

        self.logger.info(
            "kb_searcher_initialized",
            collection_name=self.vector_store.collection_name
        )

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and perform KB search.

        Args:
            state: AgentState with query

        Returns:
            Updated state with search results
        """
        start_time = time.time()

        query = state.get("current_message", "")
        limit = state.get("kb_search_limit", 5)
        min_similarity = state.get("kb_min_similarity", 0.7)
        category = state.get("kb_category_filter", None)
        tags = state.get("kb_tags_filter", None)

        self.logger.info(
            "kb_search_started",
            query_preview=query[:100],
            limit=limit,
            min_similarity=min_similarity,
            category=category
        )

        # Perform search
        results = self.search(
            query=query,
            limit=limit,
            min_similarity=min_similarity,
            category=category,
            tags=tags
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Update state
        state = self.update_state(
            state,
            kb_results=results,
            kb_search_latency_ms=latency_ms,
            kb_total_results=len(results)
        )

        self.logger.info(
            "kb_search_completed",
            results_count=len(results),
            latency_ms=latency_ms,
            top_score=results[0]["similarity_score"] if results else 0
        )

        return state

    def search(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.7,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search KB articles by semantic similarity.

        Args:
            query: Search query
            limit: Max results to return
            min_similarity: Minimum similarity score (0-1)
            category: Filter by category (optional)
            tags: Filter by tags (optional)

        Returns:
            List of articles with metadata
        """
        try:
            # Search using vector store
            results = self.vector_store.search(
                query=query,
                category=category,
                limit=limit * 2,  # Get more to filter by min_similarity
                score_threshold=min_similarity
            )

            # Filter by tags if provided
            if tags:
                filtered_results = []
                for result in results:
                    article_tags = result.get("tags", [])
                    if any(tag in article_tags for tag in tags):
                        filtered_results.append(result)
                results = filtered_results

            # Limit to requested number
            results = results[:limit]

            # Ensure consistent format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "article_id": result.get("doc_id"),
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "category": result.get("category", ""),
                    "tags": result.get("tags", []),
                    "similarity_score": result.get("similarity_score", 0.0),
                    "url": result.get("url", f"/kb/{result.get('doc_id', '')}")
                })

            return formatted_results

        except Exception as e:
            self.logger.error(
                "kb_search_failed",
                error=str(e),
                error_type=type(e).__name__,
                query_preview=query[:100]
            )
            return []

    async def search_by_intent(
        self,
        intent: str,
        user_message: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        Search KB articles based on classified intent.

        Maps intent to category and performs targeted search.

        Args:
            intent: Classified user intent
            user_message: Original user message
            limit: Max results

        Returns:
            List of relevant articles
        """
        # Map intent to category
        intent_to_category = {
            "billing_upgrade": "billing",
            "billing_downgrade": "billing",
            "billing_refund": "billing",
            "billing_invoice": "billing",
            "technical_bug": "technical",
            "technical_sync": "technical",
            "technical_performance": "technical",
            "feature_create": "usage",
            "feature_edit": "usage",
            "feature_invite": "usage",
            "feature_export": "usage",
            "integration_api": "api",
            "integration_webhook": "api",
            "account_login": "account",
        }

        category = intent_to_category.get(intent, None)

        self.logger.info(
            "kb_search_by_intent",
            intent=intent,
            category=category
        )

        return self.search(
            query=user_message,
            category=category,
            limit=limit
        )


if __name__ == "__main__":
    # Test KB Searcher
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB SEARCHER")
        print("=" * 60)

        searcher = KBSearcher()

        # Test 1: Basic search
        print("\nTest 1: Basic search for 'upgrade plan'")
        results = searcher.search(query="How do I upgrade my plan?", limit=3)
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     Category: {result['category']}")
            print(f"     Score: {result['similarity_score']:.3f}")

        # Test 2: Category search
        print("\nTest 2: Category search (billing)")
        results = searcher.search(
            query="billing question",
            category="billing",
            limit=3
        )
        print(f"Found {len(results)} results in 'billing'")

        # Test 3: With state
        print("\nTest 3: Process with state")
        state = create_initial_state(
            message="How do I invite team members?",
            context={"kb_search_limit": 2}
        )
        state = await searcher.process(state)
        print(f"Results: {state['kb_total_results']}")
        print(f"Latency: {state['kb_search_latency_ms']}ms")

        print("\n✓ KB Searcher tests completed!")

    asyncio.run(test())
