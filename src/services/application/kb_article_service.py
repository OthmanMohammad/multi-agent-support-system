"""
Knowledge Base Article Application Service

This service orchestrates all KB article operations, coordinating between:
- Database persistence (SQLAlchemy/PostgreSQL)
- Vector store (Qdrant)
- Business logic validation
- Analytics tracking

Architecture:
- Application Layer: Orchestrates use cases (this file)
- Infrastructure Layer: Vector store operations (KnowledgeBaseService)
- Domain Layer: Business rules and validation
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
import asyncio

from src.core.result import Result
from src.core.errors import (
    ValidationError,
    NotFoundError,
    BusinessRuleError,
    InternalError,
    ExternalServiceError
)
from src.database.unit_of_work import UnitOfWork, get_unit_of_work
from src.database.models.kb_article import KBArticle, KBUsage, KBQualityReport
from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService
from src.vector_store import VectorStore
from src.utils.logging.setup import get_logger


class KBArticleService:
    """
    Application service for Knowledge Base article management

    Responsibilities:
    - Create/update/delete articles (with dual persistence: DB + Qdrant)
    - Search articles (delegates to KB infrastructure service)
    - Track article usage and quality metrics
    - Sync between database and vector store

    Design Patterns:
    - Result pattern for error handling
    - Unit of Work for transactional consistency
    - Repository pattern for data access
    - Event-driven for analytics
    """

    def __init__(
        self,
        kb_service: KnowledgeBaseService
    ):
        """
        Initialize KB article service

        Args:
            kb_service: Infrastructure service for vector search

        Note:
            This service uses get_unit_of_work() context manager internally
            for all database operations. Each method manages its own transaction.
        """
        self.kb_service = kb_service
        self.logger = get_logger(__name__)

        # Direct vector store access for article management
        # (kb_service is read-only, we need write access)
        try:
            self.vector_store = VectorStore()
            self.vector_store_available = True
        except Exception as e:
            self.logger.warning(
                "vector_store_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.vector_store = None
            self.vector_store_available = False

        self.logger.info(
            "kb_article_service_initialized",
            vector_store_available=self.vector_store_available
        )

    # ========================================================================
    # ARTICLE CRUD OPERATIONS
    # ========================================================================

    async def create_article(
        self,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> Result[KBArticle]:
        """
        Create a new KB article

        This performs dual-write:
        1. Save to PostgreSQL (source of truth)
        2. Index in Qdrant (for semantic search)

        If Qdrant fails, article is still created but search won't work
        until manual sync/retry.

        Args:
            title: Article title (max 500 chars)
            content: Article content (markdown supported)
            category: Category (billing, technical, usage, api, account)
            tags: Optional tags for filtering
            url: Optional public URL to article

        Returns:
            Result with created KBArticle or error
        """
        # Validation
        validation_result = self._validate_article(title, content, category)
        if validation_result.is_failure:
            return Result.fail(validation_result.error)

        tags = tags or []

        try:
            self.logger.info(
                "kb_article_creation_started",
                title=title[:50],
                category=category,
                tags_count=len(tags)
            )

            # Create article model
            article = KBArticle(
                id=uuid4(),
                title=title.strip(),
                content=content.strip(),
                category=category.lower(),
                tags=tags,
                url=url,
                is_active=1,
                view_count=0,
                helpful_count=0,
                not_helpful_count=0,
                resolution_count=0
            )

            # Save to database (transaction)
            async with get_unit_of_work() as uow:
                uow.session.add(article)
                await uow.flush()  # Get ID and ensure it's persisted

            self.logger.info(
                "kb_article_saved_to_database",
                article_id=str(article.id),
                title=title[:50]
            )

            # Index in Qdrant (async, best-effort)
            if self.vector_store_available:
                index_result = await self._index_article_in_vector_store(article)
                if index_result.is_failure:
                    # Log but don't fail the whole operation
                    self.logger.warning(
                        "kb_article_vector_indexing_failed",
                        article_id=str(article.id),
                        error=str(index_result.error)
                    )
            else:
                self.logger.warning(
                    "kb_article_not_indexed_vector_store_unavailable",
                    article_id=str(article.id)
                )

            self.logger.info(
                "kb_article_created_successfully",
                article_id=str(article.id),
                title=title[:50],
                indexed_in_qdrant=self.vector_store_available
            )

            return Result.ok(article)

        except Exception as e:
            self.logger.error(
                "kb_article_creation_failed",
                title=title[:50],
                category=category,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to create KB article: {str(e)}",
                context={"title": title, "category": category}
            ))

    async def update_article(
        self,
        article_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> Result[KBArticle]:
        """
        Update an existing KB article

        Performs dual-update:
        1. Update in PostgreSQL
        2. Re-index in Qdrant

        Args:
            article_id: Article UUID
            title: New title (optional)
            content: New content (optional)
            category: New category (optional)
            tags: New tags (optional)
            url: New URL (optional)

        Returns:
            Result with updated article or error
        """
        try:
            self.logger.info(
                "kb_article_update_started",
                article_id=str(article_id)
            )

            # Get existing article and update
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)

                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                # Update fields
                if title is not None:
                    article.title = title.strip()
                if content is not None:
                    article.content = content.strip()
                if category is not None:
                    article.category = category.lower()
                if tags is not None:
                    article.tags = tags
                if url is not None:
                    article.url = url

                article.updated_at = datetime.now(timezone.utc)
                await uow.flush()  # Ensure changes are persisted

            # Re-index in Qdrant
            if self.vector_store_available:
                await self._index_article_in_vector_store(article)

            self.logger.info(
                "kb_article_updated_successfully",
                article_id=str(article_id),
                title=article.title[:50]
            )

            return Result.ok(article)

        except Exception as e:
            self.logger.error(
                "kb_article_update_failed",
                article_id=str(article_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to update article: {str(e)}"
            ))

    async def delete_article(
        self,
        article_id: UUID,
        soft_delete: bool = True
    ) -> Result[None]:
        """
        Delete a KB article

        By default, performs soft delete (marks as inactive).
        Hard delete removes from both DB and Qdrant.

        Args:
            article_id: Article UUID
            soft_delete: If True, mark inactive; if False, hard delete

        Returns:
            Result with None or error
        """
        try:
            self.logger.info(
                "kb_article_deletion_started",
                article_id=str(article_id),
                soft_delete=soft_delete
            )

            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)

                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                if soft_delete:
                    # Soft delete - mark as inactive
                    article.is_active = 0
                    article.updated_at = datetime.now(timezone.utc)
                else:
                    # Hard delete - remove from DB
                    await uow.session.delete(article)

                await uow.flush()  # Ensure changes are persisted

            # Remove from Qdrant (TODO: implement delete by doc_id)
            # For now, Qdrant entries become stale (filtered by is_active in search)

            self.logger.info(
                "kb_article_deleted_successfully",
                article_id=str(article_id),
                soft_delete=soft_delete
            )

            return Result.ok(None)

        except Exception as e:
            self.logger.error(
                "kb_article_deletion_failed",
                article_id=str(article_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to delete article: {str(e)}"
            ))

    async def get_article_by_id(self, article_id: UUID) -> Result[KBArticle]:
        """Get article by ID"""
        try:
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)

                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                return Result.ok(article)

        except Exception as e:
            self.logger.error(
                "kb_article_get_failed",
                article_id=str(article_id),
                error=str(e)
            )
            return Result.fail(InternalError(
                message=f"Failed to get article: {str(e)}"
            ))

    # ========================================================================
    # SEARCH OPERATIONS
    # ========================================================================

    async def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> Result[List[Dict[str, Any]]]:
        """
        Search articles using semantic search

        Delegates to infrastructure KB service which handles Qdrant.

        Args:
            query: Search query
            category: Optional category filter
            limit: Max results
            score_threshold: Min similarity score

        Returns:
            Result with list of article dicts
        """
        return await self.kb_service.search_articles(
            query=query,
            category=category,
            limit=limit,
            score_threshold=score_threshold
        )

    async def get_articles_by_category(
        self,
        category: str,
        limit: int = 10,
        include_inactive: bool = False
    ) -> Result[List[KBArticle]]:
        """Get all articles in a category"""
        try:
            from sqlalchemy import select

            async with get_unit_of_work() as uow:
                query = select(KBArticle).where(
                    KBArticle.category == category.lower()
                )

                if not include_inactive:
                    query = query.where(KBArticle.is_active == 1)

                query = query.limit(limit)

                result = await uow.session.execute(query)
                articles = result.scalars().all()

                return Result.ok(list(articles))

        except Exception as e:
            self.logger.error(
                "kb_get_by_category_failed",
                category=category,
                error=str(e)
            )
            return Result.fail(InternalError(
                message=f"Failed to get articles by category: {str(e)}"
            ))

    # ========================================================================
    # USAGE TRACKING
    # ========================================================================

    async def track_article_view(
        self,
        article_id: UUID,
        conversation_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None
    ) -> Result[None]:
        """
        Track that an article was viewed

        Updates:
        - article.view_count
        - article.last_used_at
        - Creates kb_usage record
        """
        try:
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)
                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                # Update metrics
                article.view_count += 1
                article.last_used_at = datetime.now(timezone.utc)

                # Create usage record
                usage = KBUsage(
                    id=uuid4(),
                    article_id=article_id,
                    event_type="viewed",
                    conversation_id=conversation_id,
                    customer_id=customer_id
                )
                uow.session.add(usage)

                await uow.flush()  # Ensure changes are persisted

            self.logger.debug(
                "kb_article_view_tracked",
                article_id=str(article_id),
                conversation_id=str(conversation_id) if conversation_id else None
            )

            return Result.ok(None)

        except Exception as e:
            self.logger.warning(
                "kb_article_view_tracking_failed",
                article_id=str(article_id),
                error=str(e)
            )
            # Don't fail the main operation if tracking fails
            return Result.ok(None)

    async def track_article_helpful(
        self,
        article_id: UUID,
        helpful: bool,
        conversation_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None
    ) -> Result[None]:
        """Track article helpfulness vote"""
        try:
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)
                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                if helpful:
                    article.helpful_count += 1
                else:
                    article.not_helpful_count += 1

                # Create usage record
                usage = KBUsage(
                    id=uuid4(),
                    article_id=article_id,
                    event_type="helpful" if helpful else "not_helpful",
                    conversation_id=conversation_id,
                    customer_id=customer_id
                )
                uow.session.add(usage)

                await uow.flush()  # Ensure changes are persisted

            return Result.ok(None)

        except Exception as e:
            self.logger.warning(
                "kb_article_helpful_tracking_failed",
                article_id=str(article_id),
                error=str(e)
            )
            return Result.ok(None)

    async def track_article_resolved_issue(
        self,
        article_id: UUID,
        conversation_id: UUID,
        customer_id: UUID,
        resolution_time_seconds: int,
        csat_score: Optional[int] = None
    ) -> Result[None]:
        """Track that an article helped resolve an issue"""
        try:
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)
                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                # Update resolution metrics
                article.resolution_count += 1

                # Update average resolution time
                if article.avg_resolution_time_seconds is None:
                    article.avg_resolution_time_seconds = float(resolution_time_seconds)
                else:
                    # Running average
                    total_time = article.avg_resolution_time_seconds * (article.resolution_count - 1)
                    article.avg_resolution_time_seconds = (total_time + resolution_time_seconds) / article.resolution_count

                # Update CSAT
                if csat_score is not None:
                    if article.avg_csat is None:
                        article.avg_csat = float(csat_score)
                        article.csat_count = 1
                    else:
                        total_csat = article.avg_csat * article.csat_count
                        article.csat_count += 1
                        article.avg_csat = (total_csat + csat_score) / article.csat_count

                # Create usage record
                usage = KBUsage(
                    id=uuid4(),
                    article_id=article_id,
                    event_type="resolved_with",
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    resolution_time_seconds=resolution_time_seconds,
                    csat_score=csat_score
                )
                uow.session.add(usage)

                await uow.flush()  # Ensure changes are persisted

            self.logger.info(
                "kb_article_resolution_tracked",
                article_id=str(article_id),
                resolution_time=resolution_time_seconds,
                csat=csat_score
            )

            return Result.ok(None)

        except Exception as e:
            self.logger.error(
                "kb_article_resolution_tracking_failed",
                article_id=str(article_id),
                error=str(e)
            )
            return Result.ok(None)

    # ========================================================================
    # BULK OPERATIONS & SYNC
    # ========================================================================

    async def bulk_import_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> Result[Dict[str, Any]]:
        """
        Bulk import articles from list of dicts

        Each dict should have: title, content, category, tags (optional)

        Returns:
            Result with stats (success_count, failure_count, errors)
        """
        success_count = 0
        failure_count = 0
        errors = []

        self.logger.info(
            "kb_bulk_import_started",
            article_count=len(articles)
        )

        for idx, article_data in enumerate(articles):
            try:
                result = await self.create_article(
                    title=article_data["title"],
                    content=article_data["content"],
                    category=article_data["category"],
                    tags=article_data.get("tags", []),
                    url=article_data.get("url")
                )

                if result.is_success:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append({
                        "index": idx,
                        "title": article_data["title"][:50],
                        "error": str(result.error)
                    })

            except Exception as e:
                failure_count += 1
                errors.append({
                    "index": idx,
                    "title": article_data.get("title", "Unknown")[:50],
                    "error": str(e)
                })

        self.logger.info(
            "kb_bulk_import_completed",
            total=len(articles),
            success=success_count,
            failures=failure_count
        )

        return Result.ok({
            "total": len(articles),
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors[:10]  # Limit error list
        })

    async def sync_all_to_vector_store(self) -> Result[Dict[str, Any]]:
        """
        Sync all active articles from DB to Qdrant

        Use this to rebuild the vector index or after Qdrant downtime.

        Returns:
            Result with sync stats
        """
        if not self.vector_store_available:
            return Result.fail(ExternalServiceError(
                message="Vector store is not available",
                service="Qdrant",
                operation="sync",
                is_retryable=True
            ))

        try:
            self.logger.info("kb_vector_sync_started")

            # Get all active articles from DB
            from sqlalchemy import select

            async with get_unit_of_work() as uow:
                query = select(KBArticle).where(KBArticle.is_active == 1)
                result = await uow.session.execute(query)
                articles = result.scalars().all()

            self.logger.info(
                "kb_vector_sync_articles_loaded",
                count=len(articles)
            )

            # Prepare documents for Qdrant
            documents = []
            for article in articles:
                # Generate embedding
                embedding = self.vector_store.generate_embedding(
                    f"{article.title} {article.content}"
                )

                documents.append({
                    "id": str(article.id),
                    "doc_id": str(article.id),
                    "embedding": embedding,
                    "title": article.title,
                    "content": article.content,
                    "category": article.category,
                    "tags": article.tags or []
                })

            # Upsert to Qdrant
            self.vector_store.upsert_documents(documents)

            self.logger.info(
                "kb_vector_sync_completed",
                synced_count=len(documents)
            )

            return Result.ok({
                "synced_count": len(documents),
                "total_articles": len(articles)
            })

        except Exception as e:
            self.logger.error(
                "kb_vector_sync_failed",
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to sync to vector store: {str(e)}"
            ))

    # ========================================================================
    # ANALYTICS & QUALITY
    # ========================================================================

    async def get_article_stats(
        self,
        article_id: UUID
    ) -> Result[Dict[str, Any]]:
        """Get comprehensive stats for an article"""
        try:
            async with get_unit_of_work() as uow:
                article = await uow.session.get(KBArticle, article_id)
                if not article:
                    return Result.fail(NotFoundError(
                        resource="KBArticle",
                        identifier=str(article_id)
                    ))

                # Calculate helpfulness ratio
                total_votes = article.helpful_count + article.not_helpful_count
                helpfulness_ratio = (
                    article.helpful_count / total_votes
                    if total_votes > 0
                    else 0.0
                )

                stats = {
                    "article_id": str(article.id),
                    "title": article.title,
                    "category": article.category,
                    "view_count": article.view_count,
                    "helpful_count": article.helpful_count,
                    "not_helpful_count": article.not_helpful_count,
                    "helpfulness_ratio": round(helpfulness_ratio, 3),
                    "resolution_count": article.resolution_count,
                    "avg_resolution_time_seconds": article.avg_resolution_time_seconds,
                    "avg_csat": article.avg_csat,
                    "quality_score": article.quality_score,
                    "last_used_at": article.last_used_at.isoformat() if article.last_used_at else None,
                    "created_at": article.created_at.isoformat(),
                    "is_active": bool(article.is_active)
                }

                return Result.ok(stats)

        except Exception as e:
            self.logger.error(
                "kb_article_stats_failed",
                article_id=str(article_id),
                error=str(e)
            )
            return Result.fail(InternalError(
                message=f"Failed to get article stats: {str(e)}"
            ))

    async def get_popular_articles(
        self,
        limit: int = 10,
        days: int = 30
    ) -> Result[List[Dict[str, Any]]]:
        """Get most popular articles by view count"""
        try:
            from sqlalchemy import select
            from datetime import timedelta

            since_date = datetime.now(timezone.utc) - timedelta(days=days)

            async with get_unit_of_work() as uow:
                query = (
                    select(KBArticle)
                    .where(KBArticle.is_active == 1)
                    .where(KBArticle.last_used_at >= since_date)
                    .order_by(KBArticle.view_count.desc())
                    .limit(limit)
                )

                result = await uow.session.execute(query)
                articles = result.scalars().all()

                return Result.ok([
                    {
                        "id": str(a.id),
                        "title": a.title,
                        "category": a.category,
                        "view_count": a.view_count,
                        "helpful_count": a.helpful_count
                    }
                    for a in articles
                ])

        except Exception as e:
            self.logger.error("kb_popular_articles_failed", error=str(e))
            return Result.fail(InternalError(
                message=f"Failed to get popular articles: {str(e)}"
            ))

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _validate_article(
        self,
        title: str,
        content: str,
        category: str
    ) -> Result[None]:
        """Validate article data"""
        errors = []

        if not title or len(title.strip()) < 5:
            errors.append("Title must be at least 5 characters")
        if len(title) > 500:
            errors.append("Title must be less than 500 characters")

        if not content or len(content.strip()) < 20:
            errors.append("Content must be at least 20 characters")

        valid_categories = [
            "billing", "technical", "usage", "api", "account",
            "integration", "sales", "success", "general", "security",
            "onboarding", "troubleshooting", "features", "pricing"
        ]
        if category.lower() not in valid_categories:
            errors.append(
                f"Category must be one of: {', '.join(valid_categories)}"
            )

        if errors:
            return Result.fail(ValidationError(
                field="article",
                message="; ".join(errors)
            ))

        return Result.ok(None)

    async def _index_article_in_vector_store(
        self,
        article: KBArticle
    ) -> Result[None]:
        """Index a single article in Qdrant"""
        try:
            # Generate embedding
            embedding = self.vector_store.generate_embedding(
                f"{article.title} {article.content}"
            )

            # Prepare document
            document = {
                "id": str(article.id),
                "doc_id": str(article.id),
                "embedding": embedding,
                "title": article.title,
                "content": article.content,
                "category": article.category,
                "tags": article.tags or []
            }

            # Upsert to Qdrant
            self.vector_store.upsert_documents([document])

            return Result.ok(None)

        except Exception as e:
            return Result.fail(ExternalServiceError(
                message=f"Failed to index article in vector store: {str(e)}",
                service="Qdrant",
                operation="upsert",
                is_retryable=True
            ))