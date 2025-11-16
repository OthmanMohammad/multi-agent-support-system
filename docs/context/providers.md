# Context Providers

## Overview

Providers fetch specific types of customer data from various sources. Each provider is independent, allowing for parallel execution and graceful failure handling.

## Available Providers

### 1. CustomerIntelligenceProvider

**Purpose**: Core customer profile and business metrics

**Data Provided**:
- Company information (name, industry, size)
- Plan and revenue metrics (MRR, ARR, LTV)
- Health score and churn risk
- NPS score
- Customer tenure
- Segments
- Key notes from CSMs

**Database Queries**:
- `Customer` table
- `CustomerSegment` table
- `CustomerHealthEvent` table
- `CustomerNote` table
- `CustomerContact` table
- `Subscription` table

**Latency**: ~20-30ms

---

### 2. SubscriptionDetailsProvider

**Purpose**: Billing and subscription information

**Data Provided**:
- Current subscription (status, plan, billing cycle)
- Seats (total, used, utilization)
- Billing information (MRR, ARR, next invoice)
- Payment health (failed payments, overdue invoices)
- Credit balance

**Database Queries**:
- `Subscription` table
- `Invoice` table
- `Payment` table
- `Credit` table

**Latency**: ~15-25ms

---

### 3. SupportHistoryProvider

**Purpose**: Customer support interaction history

**Data Provided**:
- Total conversations and tickets
- Open tickets
- Resolution times
- CSAT scores
- Common issues
- Escalations
- Agent performance

**Database Queries**:
- `Conversation` table
- `Message` table
- `AgentPerformance` table

**Latency**: ~20-30ms

---

### 4. EngagementMetricsProvider

**Purpose**: Product usage and engagement data

**Data Provided**:
- Login frequency
- Session duration
- Feature adoption
- Usage patterns
- Unused premium features
- Engagement trend

**Database Queries**:
- `UsageEvent` table (last 30 days)
- `FeatureUsage` table

**Latency**: ~25-35ms

---

### 5. AccountHealthProvider

**Purpose**: Aggregated account health analysis

**Data Provided**:
- Red flags (critical issues)
- Yellow flags (warnings)
- Green flags (positive signals)
- Expansion opportunities

**Dependencies**:
- Aggregates data from other providers
- No direct database queries

**Latency**: ~5-10ms (aggregation only)

---

### 6. SalesPipelineProvider

**Purpose**: Sales opportunities and pipeline

**Data Provided**:
- Open deals
- Pipeline value
- Deal stages
- Recent sales activities
- Pending quotes

**Database Queries**:
- `Deal` table
- `SalesActivity` table
- `Quote` table

**Latency**: ~15-25ms

---

### 7. FeatureUsageProvider

**Purpose**: Detailed feature usage analysis

**Data Provided**:
- Daily/weekly active features
- Power user identification
- Adoption opportunities
- Feature utilization trends

**Database Queries**:
- `FeatureUsage` table (last 90 days)

**Latency**: ~20-30ms

---

### 8. SecurityContextProvider

**Purpose**: Security posture and compliance

**Data Provided**:
- Failed login attempts
- MFA/SSO status
- Suspicious activities
- Compliance score
- Last security audit

**Database Queries**:
- `AuditLog` table (last 30 days)

**Latency**: ~15-25ms

## Creating Custom Providers

### Step 1: Create Provider Class

```python
from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider

class MyCustomProvider(BaseContextProvider):
    """My custom data provider"""
    
    async def fetch(
        self,
        customer_id: str,
        conversation_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch custom data"""
        # Your implementation
        return {"custom_data": "value"}
```

### Step 2: Register Provider

```python
from src.services.infrastructure.context_enrichment.registry import get_registry

registry = get_registry()
registry.register("my_custom", MyCustomProvider())
```

### Step 3: Configure for Agent Types

```python
from src.services.infrastructure.context_enrichment.types import AgentType

registry.configure_agent(
    AgentType.SUPPORT,
    ["customer_intelligence", "my_custom"]
)
```

## Provider Best Practices

1. **Keep Queries Fast**: Target < 50ms per provider
2. **Handle Failures Gracefully**: Return fallback data
3. **Log Errors**: Use structured logging
4. **Implement Health Checks**: Override `health_check()` method
5. **Use Connection Pooling**: Reuse database connections
6. **Cache Expensive Operations**: Use Redis for slow external calls
7. **Return Consistent Schema**: Always return expected fields
8. **Document Data Sources**: Comment which tables/APIs used
