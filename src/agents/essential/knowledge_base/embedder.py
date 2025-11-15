"""
KB Embedder Agent.

Generates vector embeddings for new and updated KB articles and loads them into Qdrant.

Part of: STORY-002 Knowledge Base Swarm (TASK-210)
"""

from typing import List, Dict
import uuid

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.core.config import get_settings
from src.utils.logging.setup import get_logger

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False


class KBEmbedder(BaseAgent):
    """
    KB Embedder Agent.

    Generates embeddings for KB articles and loads into Qdrant:
    - Generates embeddings for new articles
    - Updates embeddings for modified articles
    - Chunks long articles (>512 tokens)
    - Stores embeddings in Qdrant
    - Handles batch processing
    """

    CHUNK_SIZE = 512  # tokens (words approximation)
    CHUNK_OVERLAP = 50  # tokens

    def __init__(self):
        """Initialize KB Embedder agent."""
        config = AgentConfig(
            name="kb_embedder",
            type=AgentType.UTILITY,
            model="",  # No LLM needed
            temperature=0.0,
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        if not EMBEDDING_AVAILABLE:
            self.logger.error(
                "embedding_dependencies_missing",
                message="sentence-transformers or qdrant-client not installed"
            )
            self.qdrant_client = None
            self.embedding_model = None
            return

        settings = get_settings()

        # Initialize Qdrant client
        try:
            self.qdrant_client = QdrantClient(
                url=settings.qdrant.url,
                api_key=settings.qdrant.api_key,
                timeout=settings.qdrant.timeout
            )
            self.collection_name = settings.qdrant.collection_name
        except Exception as e:
            self.logger.error(
                "qdrant_client_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.qdrant_client = None

        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            self.logger.error(
                "embedding_model_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.embedding_model = None

        self.logger.info(
            "kb_embedder_initialized",
            collection_name=getattr(self, 'collection_name', 'unknown')
        )

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and embed articles.

        Args:
            state: AgentState

        Returns:
            Updated state with embedding results
        """
        articles = state.get("articles_to_embed", [])

        if not articles:
            self.logger.info("kb_embedder_no_articles")
            return state

        self.logger.info(
            "kb_embedding_started",
            articles_count=len(articles)
        )

        # Batch embed articles
        results = await self.batch_embed_articles(articles)

        # Update state
        state = self.update_state(
            state,
            embedding_results=results
        )

        self.logger.info(
            "kb_embedding_completed",
            success_count=results["success"],
            failed_count=results["failed"]
        )

        return state

    async def embed_article(self, article: Dict) -> Dict:
        """
        Generate embeddings for article and store in Qdrant.

        Args:
            article: Article dict with id, title, content

        Returns:
            Result dict with success status
        """
        if not self.qdrant_client or not self.embedding_model:
            return {
                "success": False,
                "error": "Embedder not properly initialized"
            }

        article_id = str(article.get("id", article.get("article_id", "")))
        title = article.get("title", "")
        content = article.get("content", "")

        # Combine title + content
        full_text = f"{title}\n\n{content}"

        # Check if needs chunking
        word_count = len(full_text.split())
        if word_count > self.CHUNK_SIZE:
            chunks = self._chunk_text(full_text)
        else:
            chunks = [full_text]

        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks)

            # Create points for Qdrant
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "doc_id": article_id,
                        "article_id": article_id,
                        "title": title,
                        "content": chunk,
                        "category": article.get("category", ""),
                        "tags": article.get("tags", []),
                        "url": article.get("url", f"/kb/{article_id}"),
                        "chunk_index": idx,
                        "total_chunks": len(chunks)
                    }
                )
                points.append(point)

            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            self.logger.info(
                "article_embedded",
                article_id=article_id,
                chunks_created=len(chunks)
            )

            return {
                "success": True,
                "article_id": article_id,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings)
            }

        except Exception as e:
            self.logger.error(
                "article_embedding_failed",
                error=str(e),
                error_type=type(e).__name__,
                article_id=article_id
            )
            return {
                "success": False,
                "article_id": article_id,
                "error": str(e)
            }

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split long text into chunks with overlap.

        Args:
            text: Full text

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk_words = words[i:i + self.CHUNK_SIZE]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

        return chunks

    async def batch_embed_articles(self, articles: List[Dict]) -> Dict:
        """
        Embed multiple articles in batch.

        Args:
            articles: List of article dicts

        Returns:
            Batch result summary
        """
        results = {
            "total": len(articles),
            "success": 0,
            "failed": 0,
            "total_chunks": 0
        }

        for article in articles:
            result = await self.embed_article(article)

            if result["success"]:
                results["success"] += 1
                results["total_chunks"] += result.get("chunks_created", 0)
            else:
                results["failed"] += 1

        return results

    async def delete_article_embeddings(self, article_id: str) -> bool:
        """
        Delete all embeddings for an article.

        Args:
            article_id: Article ID

        Returns:
            Success status
        """
        if not self.qdrant_client:
            return False

        try:
            # Delete by filter
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="article_id",
                            match=MatchValue(value=article_id)
                        )
                    ]
                )
            )

            self.logger.info(
                "article_embeddings_deleted",
                article_id=article_id
            )

            return True

        except Exception as e:
            self.logger.error(
                "article_embeddings_deletion_failed",
                error=str(e),
                error_type=type(e).__name__,
                article_id=article_id
            )
            return False


if __name__ == "__main__":
    # Test KB Embedder
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB EMBEDDER")
        print("=" * 60)

        embedder = KBEmbedder()

        # Test short article
        print("\nTest 1: Embed short article")
        short_article = {
            "id": "kb_test_short",
            "title": "Short Article",
            "content": "This is a short article about testing.",
            "category": "test",
            "tags": ["test"]
        }

        result = await embedder.embed_article(short_article)
        print(f"Success: {result.get('success', False)}")
        print(f"Chunks created: {result.get('chunks_created', 0)}")

        # Test long article
        print("\nTest 2: Embed long article (requires chunking)")
        long_content = " ".join(["word"] * 600)  # 600 words
        long_article = {
            "id": "kb_test_long",
            "title": "Long Article",
            "content": long_content,
            "category": "test"
        }

        result = await embedder.embed_article(long_article)
        print(f"Success: {result.get('success', False)}")
        print(f"Chunks created: {result.get('chunks_created', 0)}")

        # Test batch
        print("\nTest 3: Batch embed articles")
        articles = [
            {"id": f"kb_batch_{i}", "title": f"Article {i}", "content": "Test content"}
            for i in range(3)
        ]

        batch_results = await embedder.batch_embed_articles(articles)
        print(f"Total: {batch_results['total']}")
        print(f"Success: {batch_results['success']}")
        print(f"Failed: {batch_results['failed']}")

        # Test deletion
        print("\nTest 4: Delete article embeddings")
        deleted = await embedder.delete_article_embeddings("kb_test_short")
        print(f"Deleted: {deleted}")

        print("\n✓ KB Embedder tests completed!")

    asyncio.run(test())
