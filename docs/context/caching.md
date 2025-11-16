# Caching Strategy

## Two-Tier Architecture

### L1 Cache (In-Memory LRU)

**Purpose**: Ultra-fast local cache for hot data

**Characteristics**:
- **Storage**: In-memory (process RAM)
- **Eviction**: LRU (Least Recently Used)
- **Capacity**: 1,000 items (configurable)
- **TTL**: 30 seconds
- **Latency**: Sub-10ms
- **Scope**: Per-process

**Use Cases**:
- Repeated requests for same customer
- High-frequency agent interactions
- Burst traffic handling

**Configuration**:
```python
# In core/config.py
enable_l1_cache: bool = True
l1_cache_ttl: int = 30  # seconds
l1_cache_max_size: int = 1000
```

---

### L2 Cache (Redis)

**Purpose**: Distributed cache shared across all processes

**Characteristics**:
- **Storage**: Redis
- **Eviction**: TTL-based
- **Capacity**: Unlimited (Redis memory)
- **TTL**: 5 minutes
- **Latency**: ~20ms
- **Scope**: Global (all processes)

**Use Cases**:
- Cache sharing across instances
- Longer-lived data
- Distributed deployments

**Configuration**:
```python
# In core/config.py
enable_l2_cache: bool = True
l2_cache_ttl: int = 300  # seconds
redis_url: str = "redis://localhost:6379"
```

## Cache Flow

### Read Path

```
Request ??? L1 Check ??? L2 Check ??? Providers ??? Store L1+L2 ??? Return
          ???          ???
         Hit?      Hit? ??? Promote to L1
          ???
        Return
```

### Write Path

```
Data ??? Store in L1 ??? Store in L2 ??? Complete
       (30s TTL)     (5min TTL)
```

## Cache Keys

### Format

```
context:{customer_id}:{agent_type}[:{conversation_id}]
```

### Examples

```
context:cust_123:support
context:cust_123:billing
context:cust_123:support:conv_456
```

## Cache Invalidation

### When to Invalidate

1. **Customer Data Changes**
   - Profile updates
   - Plan changes
   - Subscription modifications

2. **Support Ticket Created**
   - Invalidate support history cache

3. **Payment Received**
   - Invalidate billing cache

4. **Manual Request**
   - Admin invalidation
   - Data correction

### Invalidation Methods

**Single Customer**:
```python
await orchestrator.invalidate_cache(
    customer_id="cust_123",
    agent_type=AgentType.SUPPORT
)
```

**All Agent Types**:
```python
await orchestrator.invalidate_cache(
    customer_id="cust_123"
)
```

**Entire Cache**:
```python
cache = get_cache()
await cache.clear()
```

**Pattern-Based** (Redis only):
```bash
python scripts/invalidate_cache.py --pattern "context:*:support"
```

## Cache Warming

### Purpose

Pre-populate cache for high-value customers to ensure fast initial responses.

### Strategies

**Enterprise Customers**:
```bash
python scripts/warm_cache.py --customers enterprise
```

**High-Value Customers**:
```bash
python scripts/warm_cache.py --customers high_value
```

**Custom List**:
```bash
python scripts/warm_cache.py --file customers.txt
```

### Scheduling

Recommend warming cache:
- Daily at low-traffic hours (e.g., 2 AM)
- After major data imports
- Before expected high-traffic periods

### Monitoring

```bash
# Get cache statistics
curl http://localhost:8000/api/v1/context/cache/stats

{
  "l1_hits": 850,
  "l1_misses": 150,
  "l1_hit_rate": 85.0,
  "l2_hits": 100,
  "l2_misses": 50,
  "l2_hit_rate": 66.7,
  "overall_hit_rate": 87.0
}
```

## Performance Tuning

### L1 Cache Size

**Too Small**: High eviction rate, poor hit rate
**Too Large**: Memory pressure, slower lookups

**Recommendation**: 
- Dev: 100-500 items
- Staging: 500-1000 items
- Production: 1000-5000 items

### TTL Tuning

**L1 TTL** (30s default):
- Shorter: Fresher data, higher provider load
- Longer: Stale data risk, lower provider load

**L2 TTL** (5min default):
- Shorter: More database queries
- Longer: Potential data staleness

## Best Practices

1. **Monitor Hit Rates**: Target > 80%
2. **Invalidate Proactively**: On data changes
3. **Warm Strategic Caches**: High-value customers
4. **Use Conversation Context**: Different cache keys
5. **Handle Cache Failures**: Graceful degradation
6. **Size L1 Appropriately**: Based on memory
7. **Distribute Load**: Use Redis for scaling
8. **Test Invalidation**: Verify in staging
