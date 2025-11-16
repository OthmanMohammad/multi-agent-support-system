"""
Context enrichment orchestrator.

Coordinates multiple providers to gather and enrich customer context data.
Implements parallel execution, timeout handling, caching, and result aggregation.
"""

from typing import Dict, Any, Optional, List, Set
import asyncio
from datetime import datetime
import structlog
from uuid import UUID

from src.services.infrastructure.context_enrichment.types import (
    EnrichedContext,
    ProviderResult,
    AgentType,
    ProviderPriority,
    PIIFilterLevel,
    ProviderStatus
)
from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
from src.services.infrastructure.context_enrichment.cache import ContextCache
from src.services.infrastructure.context_enrichment.utils.scoring import RelevanceScorer
from src.services.infrastructure.context_enrichment.utils.filtering import PIIFilter
from src.services.infrastructure.context_enrichment.utils.monitoring import ContextMetrics, MetricsTimer
from src.services.infrastructure.context_enrichment.utils.aggregation import ResultAggregator
from src.core.config import get_settings

logger = structlog.get_logger(__name__)


class ContextOrchestrator:
    """
    Orchestrates context enrichment from multiple providers.

    Features:
    - Parallel provider execution with timeout handling
    - Two-tier caching (L1 in-memory + L2 Redis)
    - Relevance scoring and filtering
    - PII filtering based on agent type
    - Comprehensive metrics and monitoring
    - Graceful degradation on provider failures

    Example:
        >>> orchestrator = ContextOrchestrator()
        >>> context = await orchestrator.enrich(
        ...     customer_id="cust_123",
        ...     agent_type=AgentType.SUPPORT,
        ...     conversation_id="conv_456"
        ... )
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        cache: Optional[ContextCache] = None,
        scorer: Optional[RelevanceScorer] = None,
        pii_filter: Optional[PIIFilter] = None,
        metrics: Optional[ContextMetrics] = None,
        aggregator: Optional[ResultAggregator] = None
    ):
        """
        Initialize orchestrator.

        Args:
            registry: Provider registry (uses default if None)
            cache: Context cache (uses default if None)
            scorer: Relevance scorer (uses default if None)
            pii_filter: PII filter (uses default if None)
            metrics: Metrics collector (uses default if None)
            aggregator: Result aggregator (uses default if None)
        """
        self.settings = get_settings()
        self.config = self.settings.context_enrichment

        self.registry = registry or ProviderRegistry()
        self.cache = cache or ContextCache()
        self.scorer = scorer or RelevanceScorer()
        self.pii_filter = pii_filter or PIIFilter()
        self.metrics = metrics or ContextMetrics()
        self.aggregator = aggregator or ResultAggregator()

        self.logger = logger.bind(component="orchestrator")

    async def enrich(
        self,
        customer_id: str,
        agent_type: AgentType,
        conversation_id: Optional[str] = None,
        force_refresh: bool = False,
        timeout_ms: Optional[int] = None,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> EnrichedContext:
        """
        Enrich customer context for an agent.

        Args:
            customer_id: Customer ID to enrich
            agent_type: Type of agent requesting context
            conversation_id: Optional conversation ID
            force_refresh: Skip cache and fetch fresh data
            timeout_ms: Override default timeout
            providers: Specific providers to use (uses all if None)
            **kwargs: Additional parameters passed to providers

        Returns:
            Enriched context with data from all providers

        Example:
            >>> context = await orchestrator.enrich(
            ...     customer_id="cust_123",
            ...     agent_type=AgentType.SUPPORT,
            ...     conversation_id="conv_456",
            ...     timeout_ms=1000
            ... )
        """
        with MetricsTimer(self.metrics.enrichment_duration, {"agent_type": agent_type.value}):
            start_time = datetime.utcnow()

            self.logger.info(
                "enrichment_started",
                customer_id=customer_id,
                agent_type=agent_type.value,
                conversation_id=conversation_id,
                force_refresh=force_refresh
            )

            # Check cache first (unless force_refresh)
            if not force_refresh and self.config.enable_caching:
                cached = await self._get_from_cache(customer_id, agent_type, conversation_id)
                if cached:
                    self.metrics.cache_hits.labels(
                        cache_tier="l1_or_l2",
                        agent_type=agent_type.value
                    ).inc()

                    self.logger.info(
                        "enrichment_cache_hit",
                        customer_id=customer_id,
                        agent_type=agent_type.value
                    )
                    return cached

                self.metrics.cache_misses.labels(
                    cache_tier="l1_or_l2",
                    agent_type=agent_type.value
                ).inc()

            # Determine which providers to use
            provider_names = providers or self.registry.get_providers_for_agent(agent_type)

            if not provider_names:
                self.logger.warning(
                    "no_providers_for_agent",
                    agent_type=agent_type.value
                )
                return self._create_empty_context(customer_id, agent_type, conversation_id)

            # Execute providers in parallel
            timeout = timeout_ms or self.config.provider_timeout_ms
            results = await self._execute_providers(
                customer_id=customer_id,
                conversation_id=conversation_id,
                provider_names=provider_names,
                timeout_ms=timeout,
                **kwargs
            )

            # Aggregate results
            aggregated_data = await self.aggregator.aggregate(results, agent_type)

            # Calculate relevance scores
            scored_data = await self._score_data(
                aggregated_data,
                agent_type,
                conversation_id
            )

            # Apply PII filtering
            filtered_data = await self._filter_pii(scored_data, agent_type)

            # Build enriched context
            context = EnrichedContext(
                customer_id=customer_id,
                agent_type=agent_type,
                conversation_id=conversation_id,
                data=filtered_data,
                provider_results=results,
                enriched_at=datetime.utcnow(),
                cache_hit=False,
                relevance_score=self._calculate_overall_score(scored_data),
                latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )

            # Store in cache
            if self.config.enable_caching:
                await self._store_in_cache(context)

            # Record metrics
            self.metrics.enrichment_requests.labels(
                agent_type=agent_type.value,
                status="success"
            ).inc()

            self.metrics.provider_data_points.labels(
                agent_type=agent_type.value
            ).observe(len(filtered_data))

            self.logger.info(
                "enrichment_completed",
                customer_id=customer_id,
                agent_type=agent_type.value,
                latency_ms=context.latency_ms,
                providers_count=len(results),
                data_points=len(filtered_data)
            )

            return context

    async def _execute_providers(
        self,
        customer_id: str,
        conversation_id: Optional[str],
        provider_names: List[str],
        timeout_ms: int,
        **kwargs
    ) -> List[ProviderResult]:
        """
        Execute multiple providers in parallel with timeout.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID
            provider_names: Provider names to execute
            timeout_ms: Timeout in milliseconds
            **kwargs: Additional parameters

        Returns:
            List of provider results
        """
        # Group providers by priority
        critical_providers = []
        high_providers = []
        normal_providers = []
        low_providers = []

        for name in provider_names:
            provider = self.registry.get_provider(name)
            if not provider:
                continue

            priority = getattr(provider, 'priority', ProviderPriority.NORMAL)

            if priority == ProviderPriority.CRITICAL:
                critical_providers.append(name)
            elif priority == ProviderPriority.HIGH:
                high_providers.append(name)
            elif priority == ProviderPriority.LOW:
                low_providers.append(name)
            else:
                normal_providers.append(name)

        # Execute in priority order with timeouts
        all_results = []

        # Critical providers: full timeout, wait for all
        if critical_providers:
            critical_results = await self._execute_provider_group(
                critical_providers,
                customer_id,
                conversation_id,
                timeout_ms,
                wait_for_all=True,
                **kwargs
            )
            all_results.extend(critical_results)

        # High priority: 80% of remaining timeout
        remaining_timeout = timeout_ms - sum(r.latency_ms for r in all_results)
        if high_providers and remaining_timeout > 0:
            high_results = await self._execute_provider_group(
                high_providers,
                customer_id,
                conversation_id,
                int(remaining_timeout * 0.8),
                wait_for_all=False,
                **kwargs
            )
            all_results.extend(high_results)

        # Normal priority: 50% of remaining timeout
        remaining_timeout = timeout_ms - sum(r.latency_ms for r in all_results)
        if normal_providers and remaining_timeout > 0:
            normal_results = await self._execute_provider_group(
                normal_providers,
                customer_id,
                conversation_id,
                int(remaining_timeout * 0.5),
                wait_for_all=False,
                **kwargs
            )
            all_results.extend(normal_results)

        # Low priority: remaining timeout
        remaining_timeout = timeout_ms - sum(r.latency_ms for r in all_results)
        if low_providers and remaining_timeout > 0:
            low_results = await self._execute_provider_group(
                low_providers,
                customer_id,
                conversation_id,
                remaining_timeout,
                wait_for_all=False,
                **kwargs
            )
            all_results.extend(low_results)

        return all_results

    async def _execute_provider_group(
        self,
        provider_names: List[str],
        customer_id: str,
        conversation_id: Optional[str],
        timeout_ms: int,
        wait_for_all: bool = False,
        **kwargs
    ) -> List[ProviderResult]:
        """
        Execute a group of providers in parallel.

        Args:
            provider_names: Provider names to execute
            customer_id: Customer ID
            conversation_id: Conversation ID
            timeout_ms: Timeout in milliseconds
            wait_for_all: Wait for all providers or return on first completion
            **kwargs: Additional parameters

        Returns:
            List of provider results
        """
        tasks = []
        for name in provider_names:
            task = self._execute_single_provider(
                name,
                customer_id,
                conversation_id,
                timeout_ms,
                **kwargs
            )
            tasks.append(task)

        if not tasks:
            return []

        # Execute all tasks in parallel
        if wait_for_all:
            # Wait for all providers to complete (or timeout)
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Return as soon as possible, don't wait for slow providers
            done, pending = await asyncio.wait(
                tasks,
                timeout=timeout_ms / 1000.0,
                return_when=asyncio.ALL_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            results = [task.result() for task in done if not task.cancelled()]

        # Filter out exceptions and failed results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(
                    "provider_exception",
                    error=str(result),
                    error_type=type(result).__name__
                )
                continue

            if isinstance(result, ProviderResult):
                valid_results.append(result)

        return valid_results

    async def _execute_single_provider(
        self,
        provider_name: str,
        customer_id: str,
        conversation_id: Optional[str],
        timeout_ms: int,
        **kwargs
    ) -> ProviderResult:
        """
        Execute a single provider with timeout and error handling.

        Args:
            provider_name: Provider name
            customer_id: Customer ID
            conversation_id: Conversation ID
            timeout_ms: Timeout in milliseconds
            **kwargs: Additional parameters

        Returns:
            Provider result
        """
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return ProviderResult(
                provider_name=provider_name,
                status=ProviderStatus.FAILED,
                data={},
                error="Provider not found",
                latency_ms=0,
                fetched_at=datetime.utcnow()
            )

        start_time = datetime.utcnow()

        try:
            # Execute with timeout
            data = await asyncio.wait_for(
                provider.fetch(
                    customer_id=customer_id,
                    conversation_id=conversation_id,
                    **kwargs
                ),
                timeout=timeout_ms / 1000.0
            )

            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record metrics
            self.metrics.provider_calls.labels(
                provider=provider_name,
                status="success"
            ).inc()

            self.metrics.provider_latency.labels(
                provider=provider_name
            ).observe(latency_ms)

            return ProviderResult(
                provider_name=provider_name,
                status=ProviderStatus.SUCCESS,
                data=data,
                error=None,
                latency_ms=latency_ms,
                fetched_at=datetime.utcnow()
            )

        except asyncio.TimeoutError:
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.logger.warning(
                "provider_timeout",
                provider=provider_name,
                customer_id=customer_id,
                timeout_ms=timeout_ms,
                latency_ms=latency_ms
            )

            self.metrics.provider_calls.labels(
                provider=provider_name,
                status="timeout"
            ).inc()

            self.metrics.provider_timeouts.labels(
                provider=provider_name
            ).inc()

            return ProviderResult(
                provider_name=provider_name,
                status=ProviderStatus.TIMEOUT,
                data={},
                error=f"Timeout after {timeout_ms}ms",
                latency_ms=latency_ms,
                fetched_at=datetime.utcnow()
            )

        except Exception as e:
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.logger.error(
                "provider_error",
                provider=provider_name,
                customer_id=customer_id,
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=latency_ms
            )

            self.metrics.provider_calls.labels(
                provider=provider_name,
                status="error"
            ).inc()

            self.metrics.provider_errors.labels(
                provider=provider_name,
                error_type=type(e).__name__
            ).inc()

            return ProviderResult(
                provider_name=provider_name,
                status=ProviderStatus.FAILED,
                data={},
                error=str(e),
                latency_ms=latency_ms,
                fetched_at=datetime.utcnow()
            )

    async def _get_from_cache(
        self,
        customer_id: str,
        agent_type: AgentType,
        conversation_id: Optional[str]
    ) -> Optional[EnrichedContext]:
        """Get enriched context from cache"""
        cache_key = self._build_cache_key(customer_id, agent_type, conversation_id)

        cached = await self.cache.get(cache_key)
        if cached:
            cached.cache_hit = True
            return cached

        return None

    async def _store_in_cache(self, context: EnrichedContext):
        """Store enriched context in cache"""
        cache_key = self._build_cache_key(
            context.customer_id,
            context.agent_type,
            context.conversation_id
        )

        await self.cache.set(cache_key, context)

    def _build_cache_key(
        self,
        customer_id: str,
        agent_type: AgentType,
        conversation_id: Optional[str]
    ) -> str:
        """Build cache key from parameters"""
        if conversation_id:
            return f"context:{customer_id}:{agent_type.value}:{conversation_id}"
        return f"context:{customer_id}:{agent_type.value}"

    async def _score_data(
        self,
        data: Dict[str, Any],
        agent_type: AgentType,
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Score and rank data by relevance"""
        return await self.scorer.score(data, agent_type, conversation_id)

    async def _filter_pii(
        self,
        data: Dict[str, Any],
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """Apply PII filtering based on agent type"""
        # Determine filter level based on agent type
        filter_level = self._get_filter_level_for_agent(agent_type)

        return await self.pii_filter.filter(data, filter_level)

    def _get_filter_level_for_agent(self, agent_type: AgentType) -> PIIFilterLevel:
        """Get PII filter level for agent type"""
        # Agents with higher privileges see more PII
        if agent_type in [AgentType.BILLING, AgentType.LEGAL]:
            return PIIFilterLevel.NONE
        elif agent_type in [AgentType.SUPPORT, AgentType.SUCCESS]:
            return PIIFilterLevel.PARTIAL
        else:
            return PIIFilterLevel.FULL

    def _calculate_overall_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall relevance score from scored data"""
        if not data:
            return 0.0

        # Extract scores from scored data
        scores = []
        for value in data.values():
            if isinstance(value, dict) and '_score' in value:
                scores.append(value['_score'])

        if not scores:
            return 0.0

        # Return average score
        return sum(scores) / len(scores)

    def _create_empty_context(
        self,
        customer_id: str,
        agent_type: AgentType,
        conversation_id: Optional[str]
    ) -> EnrichedContext:
        """Create empty context when no providers available"""
        return EnrichedContext(
            customer_id=customer_id,
            agent_type=agent_type,
            conversation_id=conversation_id,
            data={},
            provider_results=[],
            enriched_at=datetime.utcnow(),
            cache_hit=False,
            relevance_score=0.0,
            latency_ms=0
        )

    async def invalidate_cache(
        self,
        customer_id: str,
        agent_type: Optional[AgentType] = None,
        conversation_id: Optional[str] = None
    ):
        """
        Invalidate cache for customer.

        Args:
            customer_id: Customer ID
            agent_type: Optional agent type (invalidates all if None)
            conversation_id: Optional conversation ID
        """
        if agent_type:
            cache_key = self._build_cache_key(customer_id, agent_type, conversation_id)
            await self.cache.delete(cache_key)
        else:
            # Invalidate all agent types
            for at in AgentType:
                cache_key = self._build_cache_key(customer_id, at, conversation_id)
                await self.cache.delete(cache_key)

        self.logger.info(
            "cache_invalidated",
            customer_id=customer_id,
            agent_type=agent_type.value if agent_type else "all"
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of orchestrator and all providers.

        Returns:
            Health check results
        """
        health = {
            "orchestrator": "healthy",
            "cache": await self.cache.health_check(),
            "providers": {}
        }

        # Check all registered providers
        for name in self.registry.list_providers():
            provider = self.registry.get_provider(name)
            if provider and hasattr(provider, 'health_check'):
                try:
                    provider_health = await provider.health_check()
                    health["providers"][name] = provider_health
                except Exception as e:
                    health["providers"][name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
            else:
                health["providers"][name] = {"status": "unknown"}

        return health

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.

        Returns:
            Current metrics
        """
        return await self.metrics.get_current_metrics()


# Global orchestrator instance
_orchestrator: Optional[ContextOrchestrator] = None


def get_orchestrator() -> ContextOrchestrator:
    """
    Get or create global orchestrator instance.

    Returns:
        Global orchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ContextOrchestrator()
    return _orchestrator
