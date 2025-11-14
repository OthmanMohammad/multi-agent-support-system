# Context Enrichment System

Advanced context enrichment system that provides agents with rich customer intelligence before responding.

## Overview

The Context Enrichment System gathers customer data from multiple sources and combines them into a comprehensive context that agents can use to provide hyper-personalized responses.

### Data Sources

**Internal Providers** (Implemented):
- `CustomerIntelligenceProvider`: Company profile, plan, revenue, health score, churn risk
- `EngagementMetricsProvider`: Login activity, feature usage, engagement patterns
- `SupportHistoryProvider`: Conversation history, CSAT scores, common issues
- `SubscriptionDetailsProvider`: Seats, billing cycle, renewal dates, trial status
- `AccountHealthProvider`: Red/yellow/green flags, health indicators

**External Providers** (Planned):
- `ClearbitProvider`: Company enrichment data
- `CrunchbaseProvider`: Funding information
- `NewsAPIProvider`: Recent company news

**Real-time Providers** (Planned):
- `ProductStatusProvider`: System status, incidents
- `CurrentActivityProvider`: Live user activity
- `AgentPerformanceProvider`: Real-time agent metrics

## Quick Start

### Basic Usage

```python
from src.services.infrastructure.context_enrichment import get_context_service

# Get the service
service = get_context_service()

# Enrich context for a customer
context = await service.enrich_context("customer_123")

# Use in agent prompt
prompt_context = context.to_prompt_context()
print(prompt_context)
```

### Integration with Agents

```python
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.workflow.state import AgentState

class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            type=AgentType.SPECIALIST,
            capabilities=[AgentCapability.CONTEXT_AWARE]  # Enable context
        )
        super().__init__(config)

    async def process(self, state: AgentState) -> AgentState:
        customer_id = state.get("customer_id")

        # Get enriched context
        context = await self.get_enriched_context(customer_id)

        # Inject into prompt
        system_prompt = "You are a helpful support agent."
        enriched_prompt = await self.inject_context_into_prompt(
            system_prompt,
            customer_id
        )

        # Use enriched prompt with LLM
        response = await self.call_llm(enriched_prompt, state["current_message"])

        state["agent_response"] = response
        return state
```

## Architecture

```
┌─────────────────────────────────────────┐
│   ContextEnrichmentService              │
│   (Main Orchestrator)                   │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐ ┌──▼───┐ ┌─▼────┐
│Cache │ │Providers│ │Models│
└──────┘ └────────┘ └──────┘
```

### Components

1. **Service** (`service.py`): Main orchestrator that coordinates all providers
2. **Cache** (`cache.py`): Redis + in-memory caching with TTL
3. **Models** (`models.py`): Data structures for enriched context
4. **Providers** (`providers/`): Fetch data from various sources
5. **Exceptions** (`exceptions.py`): Custom error types

## Data Models

### EnrichedContext

Complete enriched context combining all data sources:

```python
@dataclass
class EnrichedContext:
    customer_intelligence: CustomerIntelligence
    engagement_metrics: EngagementMetrics
    support_history: SupportHistory
    subscription_details: SubscriptionDetails
    account_health: AccountHealth
    company_enrichment: Optional[CompanyEnrichment]
    product_status: ProductStatus
    enriched_at: datetime
    cache_hit: bool
    enrichment_latency_ms: float
```

### Key Metrics

```python
# Customer Intelligence
- company_name: str
- plan: str
- mrr: float
- health_score: int (0-100)
- churn_risk: float (0-1)

# Engagement
- login_count_30d: int
- most_used_features: List[str]
- feature_adoption_score: float (0-1)

# Support History
- total_conversations: int
- avg_csat: float (1-5)
- open_tickets: int

# Account Health
- red_flags: List[str]  # Critical issues
- yellow_flags: List[str]  # Warnings
- green_flags: List[str]  # Opportunities
```

## Caching

The system uses a two-tier caching strategy:

1. **Redis Cache** (if available): Distributed cache shared across instances
2. **In-Memory Cache** (fallback): Local cache when Redis is unavailable

### Cache Configuration

```python
# With Redis
service = ContextEnrichmentService(
    enable_caching=True,
    redis_url="redis://localhost:6379",
    cache_ttl=300  # 5 minutes
)

# Without Redis (in-memory only)
service = ContextEnrichmentService(
    enable_caching=True,
    cache_ttl=300
)

# No caching
service = ContextEnrichmentService(
    enable_caching=False
)
```

### Cache Invalidation

```python
# Invalidate when customer data changes
await service.invalidate_cache("customer_123")

# Force refresh (skip cache)
context = await service.enrich_context(
    "customer_123",
    force_refresh=True
)
```

## Performance

### Benchmarks

- **Internal providers only**: ~50-100ms
- **With cache hit**: ~5-10ms
- **With external APIs**: ~200-500ms

### Optimization Tips

1. **Enable caching**: Reduces latency by 95% for repeat requests
2. **Use appropriate TTL**: Balance freshness vs performance
   - High-traffic: 300s (5 min)
   - Medium-traffic: 600s (10 min)
   - Low-traffic: 1800s (30 min)
3. **Selective external APIs**: Only call for high-value customers
4. **Parallel fetching**: All providers execute in parallel

## Error Handling

The system degrades gracefully:

1. **Provider failures**: Individual providers can fail without affecting others
2. **Cache failures**: Falls back to direct fetching
3. **Complete failure**: Returns minimal context with defaults

```python
try:
    context = await service.enrich_context("customer_123")
except ContextEnrichmentError as e:
    # Service-level error
    logger.error(f"Enrichment failed: {e}")
    context = None
```

## Example Output

### Context Summary

```python
summary = await service.get_context_summary("customer_123")
# {
#     "company_name": "Acme Corp",
#     "plan": "premium",
#     "health_score": 85,
#     "churn_risk": 0.15,
#     "churn_risk_level": "low",
#     "login_count_30d": 45,
#     "open_tickets": 1,
#     "days_to_renewal": 28,
#     "has_critical_issues": False,
#     "has_opportunities": True,
#     "cache_hit": True
# }
```

### Prompt Context

```python
prompt_context = context.to_prompt_context()
# <customer_context>
# Company: Acme Corp
# Industry: Technology
# Plan: PREMIUM
# MRR: $250.00
# Health Score: 85/100 (Good)
# Churn Risk: Low (15%)
# Customer Since: 2024-06-15 (152 days)
#
# Recent Activity:
# - Last login: 2024-11-13 14:32
# - Login frequency: 45 times (last 30 days)
# - Most used features: Projects, Tasks, Reports
#
# Support History:
# - Total conversations: 12
# - Average CSAT: 4.5/5
#
# Subscription:
# - Plan: PREMIUM
# - Seats: 8/10
# - Renewal: 28 days
#
# ✅ OPPORTUNITIES:
# - High engagement - upsell opportunity
# - High CSAT scores - ask for referral
# </customer_context>
```

## Testing

### Unit Tests

```bash
pytest tests/services/infrastructure/context_enrichment/
```

### Manual Testing

```python
# Test basic enrichment
from src.services.infrastructure.context_enrichment import get_context_service
import asyncio

async def test():
    service = get_context_service()
    context = await service.enrich_context("test_customer_123")
    print(context.to_prompt_context())

asyncio.run(test())
```

## Future Enhancements

1. **External API Integration**: Clearbit, Crunchbase, etc.
2. **Real-time Providers**: Live activity tracking
3. **ML-based Insights**: Predictive churn, next-best-action
4. **Custom Provider Framework**: Easy to add new data sources
5. **Context Versioning**: Track context changes over time
6. **A/B Testing**: Different context strategies
7. **Performance Monitoring**: Detailed metrics and dashboards

## Troubleshooting

### Common Issues

**Issue**: Context enrichment is slow
- **Solution**: Enable caching, check cache hit rate

**Issue**: Cache not working
- **Solution**: Verify Redis connection, check logs for errors

**Issue**: Missing data in context
- **Solution**: Check provider logs, verify database queries

**Issue**: Memory usage high
- **Solution**: Reduce cache TTL, limit cache size, use Redis

### Debug Mode

```python
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)

service = ContextEnrichmentService()
context = await service.enrich_context("customer_123")
# Check logs for detailed execution trace
```

## Configuration

### Environment Variables

```bash
# Redis (optional)
REDIS_URL=redis://localhost:6379

# Cache settings
CONTEXT_CACHE_ENABLED=true
CONTEXT_CACHE_TTL=300

# External APIs (optional)
CLEARBIT_API_KEY=sk_xxx
CRUNCHBASE_API_KEY=xxx
```

### Code Configuration

```python
from src.services.infrastructure.context_enrichment import ContextEnrichmentService

service = ContextEnrichmentService(
    enable_external_apis=False,  # Disable for MVP
    enable_caching=True,
    redis_url=None,  # Use in-memory cache
    cache_ttl=300  # 5 minutes
)
```

## Support

For questions or issues:
1. Check logs for detailed error messages
2. Review provider implementations
3. Test with minimal configuration
4. File an issue with reproduction steps
