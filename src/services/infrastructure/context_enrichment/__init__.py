"""
Context Enrichment System.

Provides rich customer intelligence to agents by gathering data from multiple sources:
- Internal: Database queries for customer data, engagement, support history
- External: Third-party APIs (Clearbit, etc.) - optional
- Real-time: Current system status and activity

Usage:
    from src.services.infrastructure.context_enrichment import get_context_service

    service = get_context_service()
    context = await service.enrich_context("customer_123")
    prompt_context = context.to_prompt_context()
"""

from src.services.infrastructure.context_enrichment.service import (
    ContextEnrichmentService,
    get_context_service
)
from src.services.infrastructure.context_enrichment.models import (
    EnrichedContext,
    CustomerIntelligence,
    EngagementMetrics,
    SupportHistory,
    SubscriptionDetails,
    AccountHealth,
    CompanyEnrichment,
    ProductStatus,
    ChurnRiskLevel,
    HealthScoreLevel
)
from src.services.infrastructure.context_enrichment.exceptions import (
    ContextEnrichmentError,
    ProviderError,
    CacheError
)

__all__ = [
    # Main service
    "ContextEnrichmentService",
    "get_context_service",
    # Models
    "EnrichedContext",
    "CustomerIntelligence",
    "EngagementMetrics",
    "SupportHistory",
    "SubscriptionDetails",
    "AccountHealth",
    "CompanyEnrichment",
    "ProductStatus",
    "ChurnRiskLevel",
    "HealthScoreLevel",
    # Exceptions
    "ContextEnrichmentError",
    "ProviderError",
    "CacheError",
]
