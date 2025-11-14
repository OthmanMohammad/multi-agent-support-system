"""
Context enrichment service - main orchestrator.

This is the main service that agents interact with to get enriched customer context.
It orchestrates all providers, handles caching, and combines data from multiple sources.
"""

from typing import Optional, List
import asyncio
from datetime import datetime
import structlog

from src.services.infrastructure.context_enrichment.models import (
    EnrichedContext,
    CustomerIntelligence,
    EngagementMetrics,
    SupportHistory,
    SubscriptionDetails,
    AccountHealth,
    CompanyEnrichment,
    ProductStatus
)
from src.services.infrastructure.context_enrichment.cache import ContextCache
from src.services.infrastructure.context_enrichment.providers.internal import (
    CustomerIntelligenceProvider,
    EngagementMetricsProvider,
    SupportHistoryProvider,
    SubscriptionDetailsProvider,
    AccountHealthProvider
)

logger = structlog.get_logger(__name__)


class ContextEnrichmentService:
    """
    Main context enrichment service.

    Orchestrates all providers, manages caching, and provides enriched context to agents.

    Usage:
        service = ContextEnrichmentService()
        context = await service.enrich_context("customer_123")
        print(context.to_prompt_context())
    """

    def __init__(
        self,
        enable_external_apis: bool = False,
        enable_caching: bool = True,
        redis_url: Optional[str] = None,
        cache_ttl: int = 300
    ):
        """
        Initialize context enrichment service.

        Args:
            enable_external_apis: Enable external API providers (default: False)
            enable_caching: Enable caching (default: True)
            redis_url: Redis URL for caching (optional, uses in-memory if not provided)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.enable_external_apis = enable_external_apis
        self.enable_caching = enable_caching

        # Initialize cache
        if enable_caching:
            self.cache = ContextCache(redis_url=redis_url, default_ttl=cache_ttl)
            logger.info("context_cache_enabled", redis=redis_url is not None)
        else:
            self.cache = None
            logger.info("context_cache_disabled")

        # Initialize internal providers
        self.customer_intelligence = CustomerIntelligenceProvider(cache_ttl=cache_ttl)
        self.engagement_metrics = EngagementMetricsProvider(cache_ttl=cache_ttl)
        self.support_history = SupportHistoryProvider(cache_ttl=cache_ttl)
        self.subscription_details = SubscriptionDetailsProvider(cache_ttl=cache_ttl)
        self.account_health = AccountHealthProvider(cache_ttl=cache_ttl)

        # External providers (optional)
        # TODO: Initialize when enable_external_apis=True
        # self.clearbit = ClearbitProvider() if enable_external_apis else None

        logger.info(
            "context_enrichment_service_initialized",
            external_apis=enable_external_apis,
            caching=enable_caching
        )

    async def enrich_context(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        force_refresh: bool = False,
        include_external: bool = None
    ) -> EnrichedContext:
        """
        Enrich context for a customer.

        This is the main method that agents call to get enriched context.
        It fetches data from all providers in parallel and combines them.

        Args:
            customer_id: Customer ID to enrich context for
            conversation_id: Optional conversation ID for additional context
            force_refresh: Skip cache and fetch fresh data (default: False)
            include_external: Override to include/exclude external APIs (default: None = use service setting)

        Returns:
            EnrichedContext with all available data

        Example:
            >>> service = ContextEnrichmentService()
            >>> context = await service.enrich_context("customer_123")
            >>> print(context.customer_intelligence.plan)
            'premium'
        """
        start_time = datetime.utcnow()
        providers_used: List[str] = []

        self.logger.info(
            "context_enrichment_started",
            customer_id=customer_id,
            conversation_id=conversation_id,
            force_refresh=force_refresh
        )

        # Check cache first (unless force_refresh)
        if self.cache and not force_refresh:
            cached_context = await self.cache.get(customer_id)
            if cached_context:
                cached_context.cache_hit = True
                self.logger.info(
                    "context_cache_hit",
                    customer_id=customer_id,
                    latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                )
                return cached_context

        # Cache miss - fetch from providers
        self.logger.debug("context_cache_miss_fetching_from_providers", customer_id=customer_id)

        # Fetch all internal providers in parallel
        tasks = [
            self.customer_intelligence.fetch_with_fallback(customer_id, conversation_id),
            self.engagement_metrics.fetch_with_fallback(customer_id, conversation_id),
            self.support_history.fetch_with_fallback(customer_id, conversation_id),
            self.subscription_details.fetch_with_fallback(customer_id, conversation_id),
            self.account_health.fetch_with_fallback(customer_id, conversation_id),
        ]

        # Execute all fetches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Track which providers were used
        providers_used.extend([
            "CustomerIntelligence",
            "EngagementMetrics",
            "SupportHistory",
            "SubscriptionDetails",
            "AccountHealth"
        ])

        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "provider_failed",
                    provider=providers_used[i],
                    error=str(result)
                )
                # Replace with empty dict
                results[i] = {}

        # Build enriched context
        try:
            context = EnrichedContext(
                customer_intelligence=CustomerIntelligence(**results[0]),
                engagement_metrics=EngagementMetrics(**results[1]),
                support_history=SupportHistory(**results[2]),
                subscription_details=SubscriptionDetails(**results[3]),
                account_health=AccountHealth(**results[4]),
                company_enrichment=None,  # External APIs not implemented yet
                product_status=ProductStatus(),  # Real-time status not implemented yet
                enriched_at=datetime.utcnow(),
                cache_hit=False,
                enrichment_latency_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
                providers_used=providers_used
            )

        except Exception as e:
            self.logger.error(
                "context_construction_failed",
                customer_id=customer_id,
                error=str(e)
            )
            # Return minimal context on error
            context = self._create_minimal_context(customer_id)

        # Cache the result
        if self.cache:
            try:
                await self.cache.set(customer_id, context)
            except Exception as e:
                self.logger.warning("cache_set_failed", error=str(e))

        self.logger.info(
            "context_enrichment_completed",
            customer_id=customer_id,
            latency_ms=context.enrichment_latency_ms,
            providers_count=len(providers_used),
            cache_hit=False
        )

        return context

    async def invalidate_cache(self, customer_id: str):
        """
        Invalidate cached context for a customer.

        Call this when customer data is updated to ensure fresh context.

        Args:
            customer_id: Customer ID
        """
        if self.cache:
            await self.cache.invalidate(customer_id)
            self.logger.info("context_cache_invalidated", customer_id=customer_id)

    async def get_context_summary(self, customer_id: str) -> dict:
        """
        Get a quick summary of customer context.

        This is lighter than full enrichment - useful for dashboards.

        Args:
            customer_id: Customer ID

        Returns:
            Dictionary with key metrics
        """
        context = await self.enrich_context(customer_id)
        return context.get_summary()

    def _create_minimal_context(self, customer_id: str) -> EnrichedContext:
        """Create minimal context on error"""
        return EnrichedContext(
            customer_intelligence=CustomerIntelligence(
                company_name=f"Customer {customer_id[:8]}"
            ),
            engagement_metrics=EngagementMetrics(),
            support_history=SupportHistory(),
            subscription_details=SubscriptionDetails(),
            account_health=AccountHealth(),
            enriched_at=datetime.utcnow(),
            cache_hit=False,
            enrichment_latency_ms=0,
            providers_used=[]
        )


# Singleton instance for easy import
_service_instance: Optional[ContextEnrichmentService] = None


def get_context_service(
    enable_caching: bool = True,
    redis_url: Optional[str] = None
) -> ContextEnrichmentService:
    """
    Get or create context enrichment service singleton.

    Args:
        enable_caching: Enable caching
        redis_url: Redis URL (optional)

    Returns:
        ContextEnrichmentService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = ContextEnrichmentService(
            enable_caching=enable_caching,
            redis_url=redis_url
        )
    return _service_instance
