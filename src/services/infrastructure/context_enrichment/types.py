"""
Type definitions for context enrichment system.

Comprehensive type hints and protocols for context enrichment components.
"""

from enum import Enum
from typing import Any, Protocol, TypedDict, runtime_checkable
from uuid import UUID


class AgentType(str, Enum):
    """Agent type enumeration for provider selection"""

    GENERAL = "general"
    TECHNICAL_SUPPORT = "technical_support"
    BILLING = "billing"
    SALES = "sales"
    CSM = "customer_success"
    ESCALATION = "escalation"
    ANALYTICS = "analytics"
    SECURITY = "security"


class ProviderPriority(int, Enum):
    """Provider execution priority"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OPTIONAL = 5


class PIIFilterLevel(str, Enum):
    """PII filtering sensitivity level"""

    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class ProviderStatus(str, Enum):
    """Provider execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DISABLED = "disabled"


class ProviderExecutionResult(TypedDict, total=False):
    """Provider execution result"""

    provider_name: str
    status: ProviderStatus
    data: dict[str, Any]
    error: str | None
    execution_time_ms: float
    from_cache: bool
    relevance_score: float


class EnrichmentRequest(TypedDict, total=False):
    """Context enrichment request"""

    customer_id: UUID
    conversation_id: UUID | None
    agent_type: AgentType
    required_providers: list[str] | None
    optional_providers: list[str] | None
    timeout_ms: int
    force_refresh: bool
    include_external: bool
    pii_filter_level: PIIFilterLevel


class ProviderMetadata(TypedDict):
    """Provider metadata for registry"""

    name: str
    enabled: bool
    priority: ProviderPriority
    agent_types: list[AgentType]
    cache_ttl: int
    timeout_ms: int
    dependencies: list[str]


class RelevanceScoreComponents(TypedDict):
    """Relevance score breakdown"""

    recency_score: float
    completeness_score: float
    agent_relevance_score: float
    data_quality_score: float


class CacheMetrics(TypedDict):
    """Cache performance metrics"""

    l1_hits: int
    l1_misses: int
    l2_hits: int
    l2_misses: int
    hit_rate: float
    avg_latency_ms: float


class ProviderMetrics(TypedDict):
    """Provider performance metrics"""

    total_calls: int
    successful_calls: int
    failed_calls: int
    timeout_calls: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float


@runtime_checkable
class ContextProviderProtocol(Protocol):
    """Protocol for context providers"""

    provider_name: str
    cache_ttl: int
    timeout: float

    async def fetch(
        self, customer_id: str, conversation_id: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Fetch context data"""
        ...

    async def fetch_with_fallback(
        self,
        customer_id: str,
        conversation_id: str | None = None,
        fallback: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Fetch with fallback on error"""
        ...


@runtime_checkable
class RelevanceScorerProtocol(Protocol):
    """Protocol for relevance scorers"""

    def score(self, context: dict[str, Any], agent_type: AgentType, **kwargs) -> float:
        """Calculate relevance score (0-1)"""
        ...

    def score_with_breakdown(
        self, context: dict[str, Any], agent_type: AgentType, **kwargs
    ) -> RelevanceScoreComponents:
        """Calculate score with component breakdown"""
        ...


@runtime_checkable
class PIIFilterProtocol(Protocol):
    """Protocol for PII filters"""

    def filter(
        self, data: dict[str, Any], level: PIIFilterLevel = PIIFilterLevel.PARTIAL
    ) -> dict[str, Any]:
        """Filter PII from data"""
        ...

    def mask_value(
        self, value: str, value_type: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL
    ) -> str:
        """Mask individual PII value"""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations"""

    async def get(self, key: str) -> Any | None:
        """Get value from cache"""
        ...

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL"""
        ...

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        ...

    async def clear(self) -> None:
        """Clear all cache"""
        ...


# Type aliases for better readability
CustomerId = UUID
ConversationId = UUID
ProviderName = str
CacheKey = str
RelevanceScore = float
ExecutionTimeMs = float
