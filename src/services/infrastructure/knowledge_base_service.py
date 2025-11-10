"""
Knowledge Base Infrastructure Service - Wraps vector store operations

This service provides a Result-based interface to the vector store (Qdrant).
It handles KB article search, retrieval, and usage tracking.

All semantic search and KB operations go through this service.
"""

from typing import List, Dict, Optional
from uuid import UUID

from core.result import Result
from core.errors import ExternalServiceError, NotFoundError
from vector_store import VectorStore


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
        try:
            self.vector_store = VectorStore()
            self.available = True
        except Exception as e:
            print(f"Warning: Could not initialize vector store: {e}")
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
            Result with list of articles, each containing:
                - doc_id: Article ID
                - title: Article title
                - content: Article content
                - category: Article category
                - tags: List of tags
                - similarity_score: Relevance score (0-1)
        """
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="search",
                is_retryable=True
            ))
        
        try:
            results = self.vector_store.search(
                query=query,
                category=category,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return Result.ok(results)
            
        except Exception as e:
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
        """
        Get specific article by ID
        
        NOTE: VectorStore doesn't currently support get_by_id.
        This would need to be implemented in vector_store.py.
        For now, returns NOT_IMPLEMENTED.
        
        Args:
            article_id: Article ID
            
        Returns:
            Result with article dict or None
        """
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="get_by_id",
                is_retryable=True
            ))
        
        # TODO: Implement get_by_id in VectorStore
        return Result.fail(NotFoundError(
            resource="Article",
            identifier=article_id
        ))
    
    async def track_article_usage(
        self,
        conversation_id: UUID,
        article_ids: List[str]
    ) -> Result[None]:
        """
        Track which articles were used in a conversation
        
        This is for analytics - writes to a tracking table/log.
        Pure data write, no business logic.
        
        Args:
            conversation_id: Conversation UUID
            article_ids: List of article IDs used
            
        Returns:
            Result with None on success
        """
        try:
            # TODO: Implement article usage tracking
            # Could write to:
            # - Separate article_usage table
            # - Analytics service
            # - Log file
            # For now, just log to stdout
            print(f"[KB_USAGE] conversation={conversation_id}, articles={article_ids}")
            
            return Result.ok(None)
            
        except Exception as e:
            # Don't fail on tracking errors - this is non-critical
            print(f"Warning: Failed to track article usage: {e}")
            return Result.ok(None)
    
    async def get_popular_articles(
        self,
        days: int = 30,
        limit: int = 10
    ) -> Result[List[Dict]]:
        """
        Get most-used articles
        
        NOTE: Requires article usage tracking to be implemented.
        For now, returns NOT_IMPLEMENTED.
        
        Args:
            days: Number of days to analyze
            limit: Max articles to return
            
        Returns:
            Result with list of popular articles
        """
        # TODO: Implement after article usage tracking is in place
        # Would query article_usage table and aggregate
        return Result.ok([])
    
    async def search_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> Result[List[Dict]]:
        """
        Get articles by category
        
        This is essentially a search with category filter and no query.
        Useful for browsing KB by category.
        
        Args:
            category: Category name (billing, technical, usage, api)
            limit: Max articles to return
            
        Returns:
            Result with list of articles in category
        """
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="search_by_category",
                is_retryable=True
            ))
        
        try:
            # Search with empty query to get all in category
            # Vector store will return by relevance
            results = self.vector_store.search(
                query="",  # Empty query
                category=category,
                limit=limit,
                score_threshold=0.0  # Accept all
            )
            
            return Result.ok(results)
            
        except Exception as e:
            return Result.fail(ExternalServiceError(
                message=f"Failed to get articles by category: {str(e)}",
                service="Qdrant",
                operation="search_by_category",
                is_retryable=True
            ))
    
    async def get_collection_info(self) -> Result[Dict]:
        """
        Get KB collection statistics
        
        Useful for health checks and monitoring.
        
        Returns:
            Result with collection info:
                - name: Collection name
                - vector_size: Embedding dimensions
                - points_count: Number of articles
                - status: Collection status
        """
        if not self.is_available():
            return Result.fail(ExternalServiceError(
                message="Knowledge base is not available",
                service="Qdrant",
                operation="get_collection_info",
                is_retryable=True
            ))
        
        try:
            info = self.vector_store.get_collection_info()
            return Result.ok(info)
            
        except Exception as e:
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
        """
        Add new article to KB
        
        NOTE: This would require implementing upsert in VectorStore.
        For now, returns NOT_IMPLEMENTED.
        
        Args:
            title: Article title
            content: Article content
            category: Category (billing, technical, usage, api)
            tags: List of tags
            
        Returns:
            Result with article ID
        """
        # TODO: Implement article creation in VectorStore
        # Would need to:
        # 1. Generate embedding for content
        # 2. Create point with metadata
        # 3. Upsert to collection
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
        """
        Update existing article
        
        NOTE: Requires get_by_id and update in VectorStore.
        For now, returns NOT_IMPLEMENTED.
        
        Args:
            article_id: Article ID
            content: New content
            
        Returns:
            Result with None on success
        """
        # TODO: Implement after get_by_id and upsert are available
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
        """
        Soft delete article (mark as inactive)
        
        NOTE: Requires metadata update in VectorStore.
        For now, returns NOT_IMPLEMENTED.
        
        Args:
            article_id: Article ID
            
        Returns:
            Result with None on success
        """
        # TODO: Implement soft delete via metadata flag
        return Result.fail(ExternalServiceError(
            message="Article deletion not yet implemented",
            service="Qdrant",
            operation="delete_article",
            is_retryable=False
        ))
    
    async def refresh_embeddings(self) -> Result[None]:
        """
        Refresh all article embeddings (admin operation)
        
        This would regenerate embeddings for all articles.
        Useful after model upgrades.
        
        NOTE: Expensive operation, should be run in background.
        
        Returns:
            Result with None on success
        """
        # TODO: Implement batch embedding refresh
        # Would need to:
        # 1. Get all articles
        # 2. Regenerate embeddings
        # 3. Batch update collection
        return Result.fail(ExternalServiceError(
            message="Embedding refresh not yet implemented",
            service="Qdrant",
            operation="refresh_embeddings",
            is_retryable=False
        ))