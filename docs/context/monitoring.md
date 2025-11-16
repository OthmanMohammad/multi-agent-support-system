# Monitoring & Metrics

## Prometheus Metrics

### Enrichment Metrics

**`context_enrichment_requests_total{agent_type, status}`**
- Type: Counter
- Description: Total enrichment requests
- Labels:
  - `agent_type`: support, billing, success, sales
  - `status`: success, failed, timeout

**`context_enrichment_duration_seconds{agent_type}`**
- Type: Histogram
- Description: End-to-end enrichment latency
- Labels: `agent_type`
- Buckets: 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0

**`context_provider_data_points{agent_type}`**
- Type: Histogram
- Description: Number of data points returned
- Labels: `agent_type`

### Provider Metrics

**`context_provider_calls_total{provider, status}`**
- Type: Counter
- Description: Provider invocations
- Labels:
  - `provider`: customer_intelligence, subscription_details, etc.
  - `status`: success, failed, timeout

**`context_provider_latency_seconds{provider}`**
- Type: Histogram
- Description: Provider fetch latency
- Labels: `provider`

**`context_provider_errors_total{provider, error_type}`**
- Type: Counter
- Description: Provider errors by type
- Labels: `provider`, `error_type`

**`context_provider_timeouts_total{provider}`**
- Type: Counter
- Description: Provider timeouts
- Labels: `provider`

### Cache Metrics

**`context_cache_hits_total{cache_tier, agent_type}`**
- Type: Counter
- Description: Cache hits
- Labels:
  - `cache_tier`: l1, l2, l1_or_l2
  - `agent_type`

**`context_cache_misses_total{cache_tier, agent_type}`**
- Type: Counter
- Description: Cache misses
- Labels: `cache_tier`, `agent_type`

**`context_cache_size{cache_tier}`**
- Type: Gauge
- Description: Current cache size
- Labels: `cache_tier`

**`context_cache_evictions_total{cache_tier}`**
- Type: Counter
- Description: Cache evictions
- Labels: `cache_tier`

## Grafana Dashboards

### Overview Dashboard

**Panels**:
1. **Request Rate** (line graph)
   - Query: `rate(context_enrichment_requests_total[5m])`
   - Group by: `agent_type`

2. **p95 Latency** (line graph)
   - Query: `histogram_quantile(0.95, context_enrichment_duration_seconds)`
   - Threshold: 100ms (warning)

3. **Error Rate** (line graph)
   - Query: `rate(context_enrichment_requests_total{status="failed"}[5m])`
   - Threshold: 1% (warning), 5% (critical)

4. **Cache Hit Rate** (gauge)
   - Query: `rate(context_cache_hits_total[5m]) / rate(context_cache_hits_total[5m] + context_cache_misses_total[5m])`
   - Target: > 80%

### Provider Dashboard

**Panels**:
1. **Provider Latency** (heatmap)
   - Query: `context_provider_latency_seconds`
   - Group by: `provider`

2. **Provider Success Rate** (bar chart)
   - Query: `rate(context_provider_calls_total{status="success"}[5m])`

3. **Provider Errors** (table)
   - Query: `topk(10, sum by (provider, error_type) (rate(context_provider_errors_total[5m])))`

## Alerting Rules

### Critical Alerts

**High Error Rate**:
```yaml
- alert: HighContextEnrichmentErrorRate
  expr: rate(context_enrichment_requests_total{status="failed"}[5m]) > 0.05
  for: 5m
  severity: critical
  summary: Context enrichment error rate > 5%
```

**High Latency**:
```yaml
- alert: HighContextEnrichmentLatency
  expr: histogram_quantile(0.95, context_enrichment_duration_seconds) > 0.1
  for: 10m
  severity: critical
  summary: p95 latency > 100ms
```

**Cache Down**:
```yaml
- alert: CacheUnavailable
  expr: up{job="redis"} == 0
  for: 1m
  severity: critical
  summary: Redis cache unavailable
```

### Warning Alerts

**Low Cache Hit Rate**:
```yaml
- alert: LowCacheHitRate
  expr: rate(context_cache_hits_total[10m]) / rate(context_cache_hits_total[10m] + context_cache_misses_total[10m]) < 0.8
  for: 15m
  severity: warning
  summary: Cache hit rate < 80%
```

**Provider Timeouts**:
```yaml
- alert: HighProviderTimeouts
  expr: rate(context_provider_timeouts_total[5m]) > 0.01
  for: 10m
  severity: warning
  summary: Provider timeout rate > 1%
```

## Health Checks

### Endpoint

```bash
GET /api/v1/context/health
```

### Response

```json
{
  "orchestrator": "healthy",
  "cache": {
    "l1_enabled": true,
    "l1_status": "healthy",
    "l1_size": 450,
    "l2_enabled": true,
    "l2_status": "healthy",
    "redis_available": true
  },
  "providers": {
    "customer_intelligence": {"status": "healthy"},
    "subscription_details": {"status": "healthy"},
    "support_history": {"status": "healthy"}
  }
}
```

## Logging

### Structured Logging

All logs use structlog with JSON format:

```json
{
  "event": "enrichment_completed",
  "customer_id": "cust_123",
  "agent_type": "support",
  "latency_ms": 45,
  "providers_count": 5,
  "cache_hit": false,
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info"
}
```

### Key Events

- `enrichment_started`
- `enrichment_completed`
- `cache_hit` / `cache_miss`
- `provider_called`
- `provider_timeout`
- `provider_error`
- `cache_invalidated`

### Log Levels

- **DEBUG**: Detailed execution flow
- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Provider failures
- **CRITICAL**: System failures

## Performance Monitoring

### Latency Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| p50 | < 50ms | > 75ms | > 100ms |
| p95 | < 100ms | > 150ms | > 200ms |
| p99 | < 200ms | > 300ms | > 500ms |

### Throughput Targets

| Environment | Target RPS | Warning | Critical |
|-------------|------------|---------|----------|
| Dev | 100 | N/A | N/A |
| Staging | 1,000 | < 500 | < 100 |
| Production | 10,000 | < 5,000 | < 1,000 |

### Cache Targets

| Metric | Target | Warning |
|--------|--------|---------|
| L1 Hit Rate | > 50% | < 30% |
| L2 Hit Rate | > 80% | < 60% |
| Overall Hit Rate | > 80% | < 70% |
