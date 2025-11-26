"""
Knowledge Base Article models.

This module defines the KB article and usage tracking tables for the
Knowledge Base Swarm agents.
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from src.database.models.base import BaseModel


class KBArticle(BaseModel):
    """
    Knowledge Base Article.

    Stores KB articles with metadata for search and quality tracking.
    """

    __tablename__ = "kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(ARRAY(String), default=list)
    url = Column(String(500), nullable=True)

    # Quality metrics
    quality_score = Column(Float, default=None)  # 0-100
    quality_last_checked_at = Column(DateTime, default=None)

    # Usage metrics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Resolution metrics
    avg_resolution_time_seconds = Column(Float, default=None)
    resolution_count = Column(Integer, default=0)

    # CSAT metrics
    avg_csat = Column(Float, default=None)
    csat_count = Column(Integer, default=0)

    # Timestamps
    last_used_at = Column(DateTime, default=None)

    # Status
    is_active = Column(Integer, default=1)  # 1=active, 0=archived
    needs_update = Column(Integer, default=0)  # 1=needs update
    update_priority = Column(String(20), default=None)  # low, medium, high, critical

    # Relationships
    usage_records = relationship("KBUsage", back_populates="article", lazy="dynamic")
    quality_checks = relationship("KBQualityReport", back_populates="article", lazy="dynamic")
    qa_quality_checks = relationship("KBArticleQuality", back_populates="article", lazy="dynamic")

    # Indexes
    __table_args__ = (
        Index("idx_kb_articles_category", "category"),
        Index("idx_kb_articles_quality_score", "quality_score"),
        Index("idx_kb_articles_is_active", "is_active"),
        Index("idx_kb_articles_needs_update", "needs_update"),
    )

    def __repr__(self) -> str:
        return f"<KBArticle(id={self.id}, title={self.title[:50]}, category={self.category})>"


class KBUsage(BaseModel):
    """
    Knowledge Base Usage Tracking.

    Tracks article views, helpfulness votes, and resolution metrics.
    """

    __tablename__ = "kb_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True), ForeignKey("kb_articles.id"), nullable=False, index=True
    )
    event_type = Column(
        String(50), nullable=False, index=True
    )  # viewed, helpful, not_helpful, resolved_with
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True
    )
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True, index=True)

    # Resolution metrics (for resolved_with events)
    resolution_time_seconds = Column(Integer, default=None)
    csat_score = Column(Integer, default=None)  # 1-5

    # Metadata
    extra_metadata = Column(JSON, default=dict)

    # Relationships
    article = relationship("KBArticle", back_populates="usage_records")

    # Indexes
    __table_args__ = (
        Index("idx_kb_usage_article_id", "article_id"),
        Index("idx_kb_usage_event_type", "event_type"),
        Index("idx_kb_usage_conversation_id", "conversation_id"),
        Index("idx_kb_usage_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<KBUsage(id={self.id}, article_id={self.article_id}, event_type={self.event_type})>"
        )


class KBQualityReport(BaseModel):
    """
    Knowledge Base Quality Report.

    Stores quality check results for KB articles.
    """

    __tablename__ = "kb_quality_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True), ForeignKey("kb_articles.id"), nullable=False, index=True
    )

    # Relationships
    article = relationship("KBArticle", back_populates="quality_checks")

    # Overall quality score
    quality_score = Column(Integer, nullable=False)  # 0-100

    # Component scores
    completeness_score = Column(Integer, default=None)  # 0-100
    clarity_score = Column(Integer, default=None)  # 0-100
    accuracy_score = Column(Integer, default=None)  # 0-100
    examples_score = Column(Integer, default=None)  # 0-100
    formatting_score = Column(Integer, default=None)  # 0-100

    # Issues and strengths
    issues = Column(JSON, default=list)  # List of issue dicts
    strengths = Column(JSON, default=list)  # List of strengths

    # Metadata
    confidence = Column(Float, default=None)  # 0-1
    needs_update = Column(Integer, default=0)
    checked_by = Column(String(100), default="kb_quality_checker")  # Agent that performed check

    # Indexes
    __table_args__ = (
        Index("idx_kb_quality_reports_article_id", "article_id"),
        Index("idx_kb_quality_reports_quality_score", "quality_score"),
        Index("idx_kb_quality_reports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<KBQualityReport(id={self.id}, article_id={self.article_id}, quality_score={self.quality_score})>"
