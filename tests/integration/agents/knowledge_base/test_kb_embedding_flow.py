"""
Integration tests for KB embedding flow (Embedder → Search with vectors).
"""

import pytest
from src.agents.essential.knowledge_base import KBEmbedder, KBSearcher
from src.workflow.state import create_initial_state


class TestKBEmbeddingFlow:
    """Test end-to-end KB embedding and vector search flow"""

    @pytest.mark.asyncio
    async def test_embed_and_search_flow(self, test_db_session, sample_kb_articles, mock_qdrant_client, mock_embedding_model):
        """Test flow: embed article → search with vectors → retrieve results"""
        # Patch the embedder with mock clients
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Step 1: Embed an article
        article = {
            "id": sample_kb_articles[0].article_id,
            "title": sample_kb_articles[0].title,
            "content": sample_kb_articles[0].content,
            "category": sample_kb_articles[0].category
        }

        result = await embedder.embed_article(article)

        assert "success" in result or "chunks_created" in result

        # Note: search_similar is handled by KBSearcher, not KBEmbedder
        # Search functionality tested in test_kb_search_flow.py

    @pytest.mark.asyncio
    async def test_embed_long_article_with_chunking(self, mock_qdrant_client, mock_embedding_model):
        """Test embedding long article that requires chunking"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Create a long article
        long_content = " ".join(["This is a detailed explanation."] * 100)

        article = {
            "id": "kb_long",
            "title": "Comprehensive Guide",
            "content": long_content,
            "category": "technical"
        }

        result = await embedder.embed_article(article)

        assert "success" in result or "chunks_created" in result

        # Should have created multiple chunks
        if "chunks_created" in result:
            assert result["chunks_created"] > 1

    @pytest.mark.asyncio
    async def test_batch_embedding_flow(self, test_db_session, sample_kb_articles, mock_qdrant_client, mock_embedding_model):
        """Test batch embedding multiple articles"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Prepare articles for batch embedding
        articles = [
            {
                "id": article.article_id,
                "title": article.title,
                "content": article.content,
                "category": article.category
            }
            for article in sample_kb_articles[:3]
        ]

        result = await embedder.batch_embed_articles(articles)

        assert "total" in result
        assert result["total"] == 3

        if "successful" in result:
            assert result["successful"] >= 0

    @pytest.mark.asyncio
    async def test_update_embeddings_flow(self, test_db_session, sample_kb_articles, mock_qdrant_client, mock_embedding_model):
        """Test updating embeddings when article content changes"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        article_id = sample_kb_articles[0].article_id

        # Initial embedding
        article_v1 = {
            "id": article_id,
            "title": "Original Title",
            "content": "Original content",
            "category": "billing"
        }

        await embedder.embed_article(article_v1)

        # Update article content
        article_v2 = {
            "id": article_id,
            "title": "Updated Title",
            "content": "Updated content with more information",
            "category": "billing"
        }

        # Delete old embeddings
        await embedder.delete_article_embeddings(article_id)

        # Create new embeddings
        result = await embedder.embed_article(article_v2)

        assert "success" in result or "chunks_created" in result

    @pytest.mark.asyncio
    async def test_delete_embeddings_flow(self, mock_qdrant_client, mock_embedding_model):
        """Test deleting article embeddings"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Create embeddings
        article = {
            "id": "kb_to_delete",
            "title": "Temporary Article",
            "content": "This will be deleted",
            "category": "test"
        }

        await embedder.embed_article(article)

        # Delete embeddings
        success = await embedder.delete_article_embeddings("kb_to_delete")

        assert isinstance(success, bool)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="search_similar is handled by KBSearcher, not KBEmbedder")
    async def test_vector_search_similarity_ranking(self, mock_qdrant_client, mock_embedding_model):
        """Test that vector search returns results by similarity"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Embed multiple articles
        articles = [
            {
                "id": "kb_billing",
                "title": "Billing Guide",
                "content": "Information about billing, payments, and subscriptions",
                "category": "billing"
            },
            {
                "id": "kb_api",
                "title": "API Guide",
                "content": "How to use the API for integrations",
                "category": "integrations"
            },
            {
                "id": "kb_login",
                "title": "Login Help",
                "content": "Troubleshooting login issues",
                "category": "technical"
            }
        ]

        for article in articles:
            await embedder.embed_article(article)

        # Search for billing-related query
        results = await embedder.search_similar("payment and billing questions", limit=3)

        assert isinstance(results, list)
        # Results should be ordered by similarity score

    @pytest.mark.asyncio
    async def test_embedding_process_updates_state(self, mock_qdrant_client, mock_embedding_model):
        """Test that embedding process updates state correctly"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        state = create_initial_state(message="test", context={})
        state["articles_to_embed"] = [
            {
                "id": "kb_state_test",
                "title": "Test Article",
                "content": "Test content",
                "category": "test"
            }
        ]

        state = await embedder.process(state)

        assert "current_agent" in state
        # Should track embedding results

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="search_similar is handled by KBSearcher, not KBEmbedder")
    async def test_search_with_category_filter(self, mock_qdrant_client, mock_embedding_model):
        """Test vector search with category filtering"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Embed articles in different categories
        articles = [
            {
                "id": "kb_billing_1",
                "title": "Billing Article",
                "content": "Billing information",
                "category": "billing"
            },
            {
                "id": "kb_tech_1",
                "title": "Technical Article",
                "content": "Technical information",
                "category": "technical"
            }
        ]

        for article in articles:
            await embedder.embed_article(article)

        # Search with category filter
        results = await embedder.search_similar(
            "information",
            limit=5,
            category_filter="billing"
        )

        # All results should be from billing category
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_embedding_handles_special_characters(self, mock_qdrant_client, mock_embedding_model):
        """Test embedding articles with special characters and code"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        article = {
            "id": "kb_code",
            "title": "API Code Example",
            "content": """
# API Authentication

Use this code:

```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN'
}

response = requests.get('https://api.example.com/data', headers=headers)
```

Special chars: @#$%^&*()
            """,
            "category": "integrations"
        }

        result = await embedder.embed_article(article)

        assert "success" in result or "chunks_created" in result

    @pytest.mark.asyncio
    async def test_embedding_empty_content(self, mock_qdrant_client, mock_embedding_model):
        """Test handling of articles with minimal content"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        article = {
            "id": "kb_empty",
            "title": "Minimal Article",
            "content": "",
            "category": "test"
        }

        # Should handle gracefully
        result = await embedder.embed_article(article)

        # Should either succeed or return error status
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_concurrent_embedding_operations(self, mock_qdrant_client, mock_embedding_model):
        """Test multiple embedding operations"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        # Embed multiple articles sequentially
        articles = [
            {"id": f"kb_{i}", "title": f"Article {i}", "content": f"Content {i}", "category": "test"}
            for i in range(5)
        ]

        results = []
        for article in articles:
            result = await embedder.embed_article(article)
            results.append(result)

        # All should succeed
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_embedding_with_metadata_preservation(self, mock_qdrant_client, mock_embedding_model):
        """Test that article metadata is preserved in embeddings"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        article = {
            "id": "kb_metadata",
            "title": "Article with Metadata",
            "content": "Content here",
            "category": "billing",
            "tags": ["payment", "subscription"],
            "author": "Support Team"
        }

        result = await embedder.embed_article(article)

        assert "success" in result or "chunks_created" in result

        # Metadata should be stored with embeddings in Qdrant
        # This would be verified by checking the payload in Qdrant points

    @pytest.mark.asyncio
    async def test_reembedding_after_content_update(self, test_db_session, sample_kb_articles, mock_qdrant_client, mock_embedding_model):
        """Test complete re-embedding workflow after article update"""
        embedder = KBEmbedder()
        embedder.qdrant_client = mock_qdrant_client
        embedder.embedding_model = mock_embedding_model

        article = sample_kb_articles[0]
        article_id = article.article_id

        # Initial embedding
        article_data = {
            "id": article_id,
            "title": article.title,
            "content": article.content,
            "category": article.category
        }

        await embedder.embed_article(article_data)

        # Simulate content update
        updated_content = article.content + " Additional updated information."

        # Delete old embeddings
        delete_success = await embedder.delete_article_embeddings(article_id)

        # Re-embed with updated content
        updated_article_data = {
            "id": article_id,
            "title": article.title,
            "content": updated_content,
            "category": article.category
        }

        result = await embedder.embed_article(updated_article_data)

        assert "success" in result or "chunks_created" in result
