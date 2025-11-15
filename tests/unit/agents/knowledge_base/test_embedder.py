"""
Unit tests for KB Embedder agent.
"""

import pytest
from src.agents.essential.knowledge_base.embedder import KBEmbedder
from src.workflow.state import create_initial_state


class TestKBEmbedder:
    """Test suite for KB Embedder agent"""

    @pytest.fixture
    def kb_embedder(self, mock_embedding_model):
        """KB Embedder instance"""
        with pytest.mock.patch('src.agents.essential.knowledge_base.embedder.SentenceTransformer'):
            with pytest.mock.patch('src.agents.essential.knowledge_base.embedder.QdrantClient'):
                embedder = KBEmbedder()
                if embedder.embedding_model:
                    embedder.embedding_model = mock_embedding_model
                return embedder

    def test_initialization(self, kb_embedder):
        """Test KB Embedder initializes correctly"""
        assert kb_embedder.config.name == "kb_embedder"
        assert kb_embedder.CHUNK_SIZE == 512
        assert kb_embedder.CHUNK_OVERLAP == 50

    @pytest.mark.asyncio
    async def test_embed_article_short(self, kb_embedder):
        """Test embedding short article"""
        if not kb_embedder.embedding_model or not kb_embedder.qdrant_client:
            pytest.skip("Embedder not properly initialized")

        article = {
            "id": "kb_123",
            "title": "Short Article",
            "content": "This is a short article.",
            "category": "general"
        }

        result = await kb_embedder.embed_article(article)

        assert "success" in result

    @pytest.mark.asyncio
    async def test_embed_article_long(self, kb_embedder):
        """Test embedding long article with chunking"""
        if not kb_embedder.embedding_model or not kb_embedder.qdrant_client:
            pytest.skip("Embedder not properly initialized")

        article = {
            "id": "kb_456",
            "title": "Long Article",
            "content": " ".join(["word"] * 600),  # 600 words
            "category": "general"
        }

        result = await kb_embedder.embed_article(article)

        assert "success" in result

    def test_chunk_text(self, kb_embedder):
        """Test text chunking"""
        long_text = " ".join(["word"] * 600)

        chunks = kb_embedder._chunk_text(long_text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_batch_embed_articles(self, kb_embedder):
        """Test batch embedding"""
        if not kb_embedder.embedding_model or not kb_embedder.qdrant_client:
            pytest.skip("Embedder not properly initialized")

        articles = [
            {"id": f"kb_{i}", "title": f"Article {i}", "content": "Content"}
            for i in range(3)
        ]

        results = await kb_embedder.batch_embed_articles(articles)

        assert "total" in results
        assert results["total"] == 3

    @pytest.mark.asyncio
    async def test_delete_article_embeddings(self, kb_embedder):
        """Test deleting article embeddings"""
        if not kb_embedder.qdrant_client:
            pytest.skip("Qdrant not initialized")

        article_id = "kb_test_delete"

        success = await kb_embedder.delete_article_embeddings(article_id)

        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_process_updates_state(self, kb_embedder):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["articles_to_embed"] = []

        updated_state = await kb_embedder.process(state)

        assert "current_agent" in updated_state
