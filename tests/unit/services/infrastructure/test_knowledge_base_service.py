"""
Unit tests for KnowledgeBaseService
"""
import pytest
from unittest.mock import MagicMock, patch

from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService
from src.core.errors import ExternalServiceError


@pytest.fixture
def mock_vector_store():
    """Create mock vector store"""
    with patch('src.services.infrastructure.knowledge_base_service.VectorStore') as mock:
        yield mock.return_value


@pytest.fixture
def service_with_mock(mock_vector_store):
    """Create service with mocked vector store"""
    service = KnowledgeBaseService()
    service.vector_store = mock_vector_store
    service.available = True
    return service


@pytest.mark.asyncio
class TestKnowledgeBaseService:
    """Test KnowledgeBaseService"""
    
    async def test_search_articles_success(self, service_with_mock, mock_vector_store):
        """Test searching articles successfully"""
        # Arrange
        mock_articles = [
            {
                "doc_id": "1",
                "title": "Test Article",
                "content": "Test content",
                "category": "technical",
                "tags": ["test"],
                "similarity_score": 0.9
            }
        ]
        mock_vector_store.search.return_value = mock_articles
        
        # Act
        result = await service_with_mock.search_articles("test query")
        
        # Assert
        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0]["title"] == "Test Article"
    
    async def test_search_articles_unavailable(self):
        """Test searching when KB unavailable"""
        # Arrange
        service = KnowledgeBaseService()
        service.available = False
        
        # Act
        result = await service.search_articles("test query")
        
        # Assert
        assert result.is_failure
        assert result.error.code == "EXTERNAL_SERVICE_ERROR"
        assert "not available" in result.error.message
    
    async def test_search_articles_error(self, service_with_mock, mock_vector_store):
        """Test search with exception"""
        # Arrange
        mock_vector_store.search.side_effect = Exception("Search failed")
        
        # Act
        result = await service_with_mock.search_articles("test query")
        
        # Assert
        assert result.is_failure
        assert result.error.code == "EXTERNAL_SERVICE_ERROR"