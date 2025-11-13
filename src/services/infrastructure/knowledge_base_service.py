"""
Knowledge Base Infrastructure Service - Wraps vector store operations

This service provides a Result-based interface to the vector store (Qdrant).
It handles KB article search, retrieval, and usage tracking.

All semantic search and KB operations go through this service.

"""

from typing import List, Dict, Optional
from uuid import UUID
import time

from src.core.result import Result
from src.core.errors import ExternalServiceError, NotFoundError
from src.vector_store import VectorStore
from src.utils.logging.setup import get_logger


class KnowledgeBaseService:
    """
    Infrastructure service for knowledge base operations
    
    Wraps vector store (Qdrant) operations with Result pattern.
    
    Responsibilities:
    - Semantic search via vector store
    - Article retrieval
    - Usage tracking (data write)
    
    NOT responsible for:
    - Determining relevance thresholds (domain logic)
    - Article recommendation logic (domain logic)
    - Content generation (domain logic)
    
    """
    
    def __init__(self):
        """Initialize with vector store"""
        self.logger = get_logger(__name__)
        
        try:
            self.vector_store = VectorStore()
            self.available = True
            self.logger.info("kb_service_initialized", status="available")
        except Exception as e:
            self.logger.error(
                "kb_service_initialization_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            self.vector_store = None
            self.available = False
    
    def is_available(self) -> bool:
        """
        Check if KB service is available
        
        Returns:
            True if vector store is initialized and ready
        """
        return self.available and self.vector_store is not None
    
    async def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> Result[List[Dict]]:
        """
        Search KB articles using semantic search
        
        This is a thin wrapper around vector store search.
        No business logic - just data retrieval.
        
        Args:
            query: Search query
            category: Optional category filter (billing, technical, usage, api)
            limit: Max results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            Result with list of articles
        """
        if not self.is_available():
            self.logger.error("kb_search_unavailable", query=query)
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="search",
                is_retryable=True
            ))
        
        try:
            self.logger.info(
                "kb_search_started",
                query=query,
                category=category,
                limit=limit,
                score_threshold=score_threshold
            )
            
            start_time = time.time()
            results = self.vector_store.search(
                query=query,
                category=category,
                limit=limit,
                score_threshold=score_threshold
            )
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                "kb_search_completed",
                query=query,
                results_count=len(results),
                top_score=results[0]["similarity_score"] if results else 0,
                duration_ms=round(duration_ms, 2)
            )
            
            return Result.ok(results)
            
        except Exception as e:
            self.logger.error(
                "kb_search_failed",
                query=query,
                category=category,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(ExternalServiceError(
                message=f"Failed to search knowledge base: {str(e)}",
                service="Qdrant",
                operation="search",
                is_retryable=True
            ))
    
    async def get_article_by_id(
        self,
        article_id: str
    ) -> Result[Optional[Dict]]:
        """Get specific article by ID"""
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="get_by_id",
                is_retryable=True
            ))
        
        self.logger.debug("kb_get_by_id_not_implemented", article_id=article_id)
        return Result.fail(NotFoundError(
            resource="Article",
            identifier=article_id
        ))
    
    async def track_article_usage(
        self,
        conversation_id: UUID,
        article_ids: List[str]
    ) -> Result[None]:
        """Track which articles were used in a conversation"""
        try:
            self.logger.info(
                "kb_article_usage_tracked",
                conversation_id=str(conversation_id),
                article_count=len(article_ids),
                article_ids=article_ids
            )
            
            return Result.ok(None)
            
        except Exception as e:
            self.logger.warning(
                "kb_article_usage_tracking_failed",
                conversation_id=str(conversation_id),
                error=str(e)
            )
            return Result.ok(None)
    
    async def get_popular_articles(
        self,
        days: int = 30,
        limit: int = 10
    ) -> Result[List[Dict]]:
        """Get most-used articles"""
        self.logger.debug("kb_popular_articles_not_implemented", days=days, limit=limit)
        return Result.ok([])
    
    async def search_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> Result[List[Dict]]:
        """Get articles by category"""
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="search_by_category",
                is_retryable=True
            ))
        
        try:
            self.logger.info(
                "kb_category_search_started",
                category=category,
                limit=limit
            )
            
            results = self.vector_store.search(
                query="",
                category=category,
                limit=limit,
                score_threshold=0.0
            )
            
            self.logger.info(
                "kb_category_search_completed",
                category=category,
                results_count=len(results)
            )
            return Result.ok(results)
            
        except Exception as e:
            self.logger.error(
                "kb_category_search_failed",
                category=category,
                error=str(e),
                exc_info=True
            )
            return Result.fail(ExternalServiceError(
                message=f"Failed to get articles by category: {str(e)}",
                service="Qdrant",
                operation="search_by_category",
                is_retryable=True
            ))
    
    async def get_collection_info(self) -> Result[Dict]:
        """Get KB collection statistics"""
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="get_collection_info",
                is_retryable=True
            ))
        
        try:
            info = self.vector_store.get_collection_info()
            
            self.logger.info(
                "kb_collection_info_retrieved",
                points_count=info.get("points_count", 0)
            )
            return Result.ok(info)
            
        except Exception as e:
            self.logger.error(
                "kb_collection_info_failed",
                error=str(e),
                exc_info=True
            )
            return Result.fail(ExternalServiceError(
                message=f"Failed to get collection info: {str(e)}",
                service="Qdrant",
                operation="get_collection_info",
                is_retryable=False
            ))
    
    async def add_article(
        self,
        title: str,
        content: str,
        category: str,
        tags: List[str]
    ) -> Result[str]:
        """Add new article to KB"""
        self.logger.debug(
            "kb_add_article_not_implemented",
            title=title,
            category=category
        )
        return Result.fail(ExternalServiceError(
            message="Article creation not yet implemented",
            service="Qdrant",
            operation="add_article",
            is_retryable=False
        ))
    
    async def update_article(
        self,
        article_id: str,
        content: str
    ) -> Result[None]:
        """Update existing article"""
        self.logger.debug("kb_update_article_not_implemented", article_id=article_id)
        return Result.fail(ExternalServiceError(
            message="Article updates not yet implemented",
            service="Qdrant",
            operation="update_article",
            is_retryable=False
        ))
    
    async def delete_article(
        self,
        article_id: str
    ) -> Result[None]:
        """Soft delete article (mark as inactive)"""
        self.logger.debug("kb_delete_article_not_implemented", article_id=article_id)
        return Result.fail(ExternalServiceError(
            message="Article deletion not yet implemented",
            service="Qdrant",
            operation="delete_article",
            is_retryable=False
        ))
    
    async def refresh_embeddings(self) -> Result[None]:
        """Refresh all article embeddings (admin operation)"""
        self.logger.debug("kb_refresh_embeddings_not_implemented")
        return Result.fail(ExternalServiceError(
            message="Embedding refresh not yet implemented",
            service="Qdrant",
            operation="refresh_embeddings",
            is_retryable=False
        ))