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

from src.services.infrastructure.context_enrichment.exceptions import (
    CacheError,
    ContextEnrichmentError,
    ProviderError,
)
from src.services.infrastructure.context_enrichment.models import (
    AccountHealth,
    ChurnRiskLevel,
    CompanyEnrichment,
    CustomerIntelligence,
    EngagementMetrics,
    EnrichedContext,
    HealthScoreLevel,
    ProductStatus,
    SubscriptionDetails,
    SupportHistory,
)
from src.services.infrastructure.context_enrichment.service import (
    ContextEnrichmentService,
    get_context_service,
)

__all__ = [
    "AccountHealth",
    "CacheError",
    "ChurnRiskLevel",
    "CompanyEnrichment",
    # Exceptions
    "ContextEnrichmentError",
    # Main service
    "ContextEnrichmentService",
    "CustomerIntelligence",
    "EngagementMetrics",
    # Models
    "EnrichedContext",
    "HealthScoreLevel",
    "ProductStatus",
    "ProviderError",
    "SubscriptionDetails",
    "SupportHistory",
    "get_context_service",
]
