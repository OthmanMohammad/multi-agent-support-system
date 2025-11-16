# Troubleshooting Guide

## Common Issues

### High Latency

**Symptoms**:
- p95 latency > 100ms
- Slow response times
- Timeout errors

**Diagnosis**:
```bash
# Check provider latencies
python scripts/benchmark_providers.py --verbose

# Check cache hit rate
curl http://localhost:8000/api/v1/context/cache/stats
```

**Solutions**:

1. **Low Cache Hit Rate**:
   ```bash
   # Warm cache for high-value customers
   python scripts/warm_cache.py --customers enterprise
   
   # Increase TTL
   # Edit config: l1_cache_ttl = 60, l2_cache_ttl = 600
   ```

2. **Slow Providers**:
   ```bash
   # Identify slow providers
   python scripts/benchmark_providers.py
   
   # Check database connections
   # Check external API status
   # Optimize database queries
   ```

3. **Database Connection Pool Exhausted**:
   ```python
   # Increase pool size in config
   database_pool_size = 20
   database_max_overflow = 10
   ```

---

### Cache Not Working

**Symptoms**:
- 100% cache miss rate
- Every request hits providers
- High database load

**Diagnosis**:
```bash
# Check cache health
curl http://localhost:8000/api/v1/context/health

# Check Redis connectivity
redis-cli ping

# Check cache stats
curl http://localhost:8000/api/v1/context/cache/stats
```

**Solutions**:

1. **Redis Not Available**:
   ```bash
   # Check Redis status
   systemctl status redis
   
   # Start Redis
   systemctl start redis
   
   # Check connection
   redis-cli -h localhost -p 6379 ping
   ```

2. **Cache Disabled in Config**:
   ```python
   # Check config
   enable_l1_cache = True
   enable_l2_cache = True
   enable_caching = True
   ```

3. **TTL Too Short**:
   ```python
   # Increase TTL
   l1_cache_ttl = 30  # seconds
   l2_cache_ttl = 300  # seconds
   ```

---

### Provider Failures

**Symptoms**:
- Enrichment requests fail
- Partial data returned
- Error logs

**Diagnosis**:
```bash
# Check provider health
curl http://localhost:8000/api/v1/context/health | jq '.providers'

# Check logs
grep "provider_error" logs/app.log | tail -20

# Benchmark specific provider
python scripts/benchmark_providers.py --provider customer_intelligence
```

**Solutions**:

1. **Database Connection Issues**:
   ```bash
   # Check database connectivity
   psql -h localhost -U user -d database
   
   # Check connection pool
   # Verify pool_size and max_overflow settings
   ```

2. **Slow Queries**:
   ```sql
   -- Find slow queries
   SELECT * FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   
   -- Add indexes if needed
   CREATE INDEX idx_customer_id ON conversations(customer_id);
   ```

3. **Provider Timeout**:
   ```python
   # Increase timeout
   provider_timeout_ms = 1000  # was 500
   ```

---

### Memory Issues

**Symptoms**:
- High memory usage
- OOM errors
- Slow performance

**Diagnosis**:
```bash
# Check L1 cache size
curl http://localhost:8000/api/v1/context/cache/stats | jq '.l1_size'

# Monitor memory
top -p $(pgrep -f "python")

# Check cache evictions
# High evictions indicate cache too small
```

**Solutions**:

1. **L1 Cache Too Large**:
   ```python
   # Reduce L1 cache size
   l1_cache_max_size = 500  # was 5000
   ```

2. **Memory Leak**:
   ```bash
   # Monitor over time
   # Check for growing object counts
   # Review code for circular references
   ```

3. **Too Many Concurrent Requests**:
   ```python
   # Limit concurrency
   max_concurrent_requests = 100
   ```

---

### Incorrect Data

**Symptoms**:
- Stale data returned
- Missing fields
- Wrong customer data

**Diagnosis**:
```bash
# Check cache age
# Look for old enriched_at timestamps

# Force refresh
curl -X POST http://localhost:8000/api/v1/context/enrich \
  -d '{"customer_id": "cust_123", "force_refresh": true}'
```

**Solutions**:

1. **Stale Cache**:
   ```bash
   # Invalidate cache
   python scripts/invalidate_cache.py --customer cust_123
   
   # Or invalidate all
   python scripts/invalidate_cache.py --all
   ```

2. **Provider Returning Old Data**:
   ```bash
   # Check database for latest data
   psql -c "SELECT * FROM customers WHERE id = 'cust_123'"
   
   # Verify provider query logic
   # Check for caching within provider
   ```

3. **Wrong Customer ID**:
   ```bash
   # Verify customer ID format
   # Check UUID vs string handling
   # Review request parameters
   ```

---

### High Error Rate

**Symptoms**:
- Many failed enrichment requests
- Error logs
- Alert notifications

**Diagnosis**:
```bash
# Check error rate
curl http://localhost:8000/metrics | grep enrichment_requests_total

# Check specific errors
grep "ERROR" logs/app.log | tail -50

# Check provider errors
curl http://localhost:8000/api/v1/context/health
```

**Solutions**:

1. **Circuit Breaker Opened**:
   ```bash
   # Wait for recovery timeout
   # Or manually reset circuit breaker
   # Check underlying provider health
   ```

2. **Rate Limiting**:
   ```bash
   # Check rate limit settings
   # Increase limits if appropriate
   # Distribute load
   ```

3. **Database Issues**:
   ```bash
   # Check database health
   # Check connection pool
   # Review slow query log
   ```

## Debugging Tools

### Health Check

```bash
curl http://localhost:8000/api/v1/context/health | jq
```

### Cache Stats

```bash
curl http://localhost:8000/api/v1/context/cache/stats | jq
```

### Benchmark Providers

```bash
# All providers
python scripts/benchmark_providers.py --verbose

# Specific provider
python scripts/benchmark_providers.py --provider customer_intelligence --iterations 100

# Concurrent load test
python scripts/benchmark_providers.py --concurrent --concurrency 10 --duration 30
```

### Cache Management

```bash
# Warm cache
python scripts/warm_cache.py --customers enterprise --verbose

# Invalidate specific customer
python scripts/invalidate_cache.py --customer cust_123 --verbose

# Invalidate all
python scripts/invalidate_cache.py --all
```

### Logs

```bash
# Tail logs
tail -f logs/app.log | grep context_enrichment

# Search for errors
grep "ERROR" logs/app.log | grep context

# Search for specific customer
grep "cust_123" logs/app.log
```

## Performance Tuning Checklist

- [ ] Cache hit rate > 80%
- [ ] p95 latency < 100ms
- [ ] Provider latencies < 50ms
- [ ] Database connections pooled
- [ ] Indexes on frequently queried fields
- [ ] Redis available and connected
- [ ] L1 cache sized appropriately
- [ ] Timeouts configured correctly
- [ ] Circuit breakers enabled
- [ ] Monitoring and alerts active

## Getting Help

1. **Check Logs**: Review application logs for errors
2. **Run Health Check**: Verify system health
3. **Benchmark Providers**: Identify slow components
4. **Review Metrics**: Check Grafana dashboards
5. **Check Documentation**: Review architecture and caching docs
6. **Contact Team**: Reach out to platform team with:
   - Logs
   - Health check output
   - Benchmark results
   - Grafana dashboard links
