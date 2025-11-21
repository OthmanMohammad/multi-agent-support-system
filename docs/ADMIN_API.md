# Admin API Documentation

This document describes the administrative API endpoints for system management, monitoring, and configuration.

## Authentication

All admin endpoints require authentication using a JWT bearer token.

### Obtaining a Token

```bash
# Register a user
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!",
    "full_name": "Admin User"
  }'

# Login to get token
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'
```

Response includes `access_token` to use in subsequent requests:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

### Using the Token

Include token in Authorization header:
```bash
curl -X GET https://your-domain.com/api/admin/backend/current \
  -H "Authorization: Bearer eyJhbGc..."
```

## Backend Management

### Get Current Backend Status

Retrieves information about the currently active LLM backend.

**Endpoint**: `GET /api/admin/backend/current`

**Response**:
```json
{
  "current_backend": "anthropic",
  "vllm_endpoint": null,
  "vllm_configured": false,
  "health_status": {
    "anthropic": true,
    "vllm": false
  },
  "last_health_check": {
    "anthropic": "2025-01-15T10:30:00Z",
    "vllm": null
  },
  "available_models": ["haiku", "sonnet", "opus"]
}
```

**Fields**:
- `current_backend`: Active backend (anthropic or vllm)
- `vllm_endpoint`: vLLM server URL if configured
- `vllm_configured`: Whether vLLM is ready to use
- `health_status`: Backend health check results
- `available_models`: Models available on current backend

### Switch Backend

Changes the active LLM backend between Anthropic and vLLM.

**Endpoint**: `POST /api/admin/backend/switch`

**Request Body**:
```json
{
  "backend": "vllm",
  "skip_health_check": false
}
```

**Parameters**:
- `backend` (required): Target backend (anthropic or vllm)
- `skip_health_check` (optional): Skip health verification before switch

**Response** (success):
```json
{
  "success": true,
  "message": "Switched to vllm",
  "backend": "vllm",
  "previous_backend": "anthropic"
}
```

**Response** (failure):
```json
{
  "success": false,
  "message": "Backend health check failed",
  "backend": "anthropic"
}
```

**Use Cases**:
- Switch to vLLM for cost savings during high-volume periods
- Fallback to Anthropic when vLLM unavailable
- Testing and development with different backends

### Configure vLLM Endpoint

Sets the vLLM server endpoint URL.

**Endpoint**: `POST /api/admin/backend/vllm/endpoint`

**Request Body**:
```json
{
  "endpoint": "http://10.0.0.5:8000"
}
```

**Response**:
```json
{
  "success": true,
  "message": "vLLM endpoint configured",
  "endpoint": "http://10.0.0.5:8000",
  "health_check_passed": true
}
```

**Requirements**:
- Endpoint must be accessible from application server
- vLLM server must be running and healthy
- URL format: `http://hostname:port` or `https://hostname:port`

### Health Checks

Monitor backend availability and response times.

**Endpoint**: `GET /api/admin/backend/health`

**Response**:
```json
{
  "anthropic": {
    "healthy": true,
    "latency_ms": 245,
    "last_check": "2025-01-15T10:35:00Z",
    "error": null
  },
  "vllm": {
    "healthy": false,
    "latency_ms": null,
    "last_check": "2025-01-15T10:35:00Z",
    "error": "Connection refused"
  }
}
```

**Check Specific Backend**:

`GET /api/admin/backend/health/anthropic`

```json
{
  "backend": "anthropic",
  "healthy": true,
  "latency_ms": 245,
  "last_check": "2025-01-15T10:35:00Z"
}
```

**Health Check Criteria**:
- Response time under 5 seconds
- Valid authentication
- Successful test completion

## Cost Management

### View Costs

Retrieves current cost breakdown and budget status.

**Endpoint**: `GET /api/admin/costs`

**Response**:
```json
{
  "anthropic": 45.67,
  "vllm": 12.30,
  "total": 57.97,
  "budget_limit": 100.0,
  "remaining": 42.03,
  "budget_used_percent": 57.97,
  "breakdown": {
    "anthropic": {
      "haiku": 12.34,
      "sonnet": 28.90,
      "opus": 4.43
    },
    "vllm": {
      "runtime_hours": 76.875,
      "hourly_rate": 0.16
    }
  }
}
```

**Cost Components**:
- `anthropic`: Total Anthropic API costs (per-token pricing)
- `vllm`: Total vLLM compute costs (hourly estimation)
- `total`: Combined costs across all backends
- `remaining`: Budget remaining before limit
- `budget_used_percent`: Percentage of budget consumed

### Update Budget

Sets the budget limit for cost tracking and alerts.

**Endpoint**: `POST /api/admin/budget`

**Request Body**:
```json
{
  "budget_limit": 150.0
}
```

**Response**:
```json
{
  "success": true,
  "budget_limit": 150.0,
  "previous_limit": 100.0,
  "current_usage": 57.97,
  "remaining": 92.03
}
```

**Budget Alerts**:

Automatic alerts at thresholds:
- **75%**: Warning logged, continue operations
- **90%**: Critical warning, consider action
- **100%**: API calls blocked until budget increased

Alert example:
```json
{
  "event": "budget_alert",
  "level": "warning",
  "threshold": "75%",
  "current_usage": 75.0,
  "budget_limit": 100.0,
  "message": "Budget usage at 75%"
}
```

### Reset Costs

Resets cost tracking counters (useful for monthly billing cycles).

**Endpoint**: `POST /api/admin/costs/reset`

**Response**:
```json
{
  "success": true,
  "message": "Cost counters reset",
  "previous_costs": {
    "anthropic": 45.67,
    "vllm": 12.30,
    "total": 57.97
  }
}
```

**Warning**: This operation resets all cost counters. Historical data is not recoverable.

## Metrics and Monitoring

### Get Metrics

Retrieves detailed usage metrics for monitoring and optimization.

**Endpoint**: `GET /api/admin/metrics`

**Response**:
```json
{
  "overview": {
    "total_calls": 15234,
    "successful_calls": 15180,
    "failed_calls": 54,
    "total_tokens": 28456789,
    "backends_active": 1,
    "models_used": 3
  },
  "by_backend": {
    "anthropic": {
      "calls": 15234,
      "success_rate": 99.65,
      "total_input_tokens": 12345678,
      "total_output_tokens": 16111111,
      "avg_latency_ms": 1250,
      "total_cost": 45.67
    }
  },
  "by_model": {
    "haiku": {
      "calls": 12500,
      "avg_latency_ms": 850,
      "total_tokens": 18000000,
      "cost": 12.34
    },
    "sonnet": {
      "calls": 2500,
      "avg_latency_ms": 2100,
      "total_tokens": 9500000,
      "cost": 28.90
    },
    "opus": {
      "calls": 234,
      "avg_latency_ms": 3500,
      "total_tokens": 956789,
      "cost": 4.43
    }
  },
  "recent_calls": 150
}
```

**Metrics Breakdown**:

**Overview**:
- `total_calls`: All LLM API requests
- `successful_calls`: Completed without errors
- `failed_calls`: Errors, timeouts, or retries exhausted
- `total_tokens`: Combined input and output tokens

**Per Backend**:
- Call counts and success rates
- Token usage (input/output split)
- Average latency
- Cumulative costs

**Per Model**:
- Model-specific performance
- Usage patterns
- Cost attribution

### Export Metrics

Export metrics in various formats for external analysis.

**Endpoint**: `GET /api/admin/metrics/export`

**Query Parameters**:
- `format`: Export format (json, csv, prometheus)
- `start_date`: Start of date range (ISO 8601)
- `end_date`: End of date range (ISO 8601)

**Example**:
```bash
curl -X GET "https://your-domain.com/api/admin/metrics/export?format=csv&start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z" \
  -H "Authorization: Bearer <TOKEN>"
```

**CSV Response**:
```csv
timestamp,backend,model,calls,tokens,cost,latency_ms
2025-01-15T00:00:00Z,anthropic,haiku,1250,180000,1.23,850
2025-01-15T00:00:00Z,anthropic,sonnet,250,95000,2.89,2100
```

**Prometheus Format**:
```
# HELP llm_calls_total Total LLM API calls
# TYPE llm_calls_total counter
llm_calls_total{backend="anthropic",model="haiku"} 12500

# HELP llm_latency_ms Average latency in milliseconds
# TYPE llm_latency_ms gauge
llm_latency_ms{backend="anthropic",model="haiku"} 850
```

## System Configuration

### View Configuration

Retrieves current system configuration.

**Endpoint**: `GET /api/admin/config`

**Response**:
```json
{
  "backend": {
    "current": "anthropic",
    "auto_fallback": true,
    "health_check_interval": 300
  },
  "costs": {
    "budget_limit": 100.0,
    "alert_thresholds": [75, 90, 100],
    "vllm_hourly_rate": 0.16
  },
  "rate_limits": {
    "enabled": true,
    "max_requests_per_hour": 10000,
    "max_tokens_per_minute": 100000
  }
}
```

### Update Configuration

Modifies system configuration parameters.

**Endpoint**: `PUT /api/admin/config`

**Request Body**:
```json
{
  "backend": {
    "auto_fallback": true,
    "health_check_interval": 600
  },
  "rate_limits": {
    "max_requests_per_hour": 15000
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Configuration updated",
  "updated_fields": ["backend.auto_fallback", "backend.health_check_interval", "rate_limits.max_requests_per_hour"]
}
```

## Error Responses

All endpoints follow consistent error response format.

### Standard Error Response

```json
{
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "details": {
    "error_type": "ValueError",
    "field": "budget_limit"
  }
}
```

### HTTP Status Codes

**200 OK**: Request successful
**400 Bad Request**: Invalid request parameters
**401 Unauthorized**: Missing or invalid authentication token
**403 Forbidden**: Insufficient permissions
**404 Not Found**: Resource does not exist
**429 Too Many Requests**: Rate limit exceeded
**500 Internal Server Error**: Server-side error
**503 Service Unavailable**: Backend unavailable

### Common Error Codes

**AUTHENTICATION_REQUIRED**
```json
{
  "code": "AUTHENTICATION_REQUIRED",
  "message": "Not authenticated"
}
```
Solution: Provide valid JWT token in Authorization header

**BACKEND_UNAVAILABLE**
```json
{
  "code": "BACKEND_UNAVAILABLE",
  "message": "Backend health check failed",
  "details": {"backend": "vllm", "error": "Connection refused"}
}
```
Solution: Verify backend is running and accessible

**BUDGET_EXCEEDED**
```json
{
  "code": "BUDGET_EXCEEDED",
  "message": "Budget limit reached",
  "details": {
    "limit": 100.0,
    "current": 100.0,
    "requested_cost": 0.50
  }
}
```
Solution: Increase budget limit via POST /api/admin/budget

**INVALID_BACKEND**
```json
{
  "code": "INVALID_BACKEND",
  "message": "Invalid backend specified",
  "details": {"backend": "invalid", "valid_options": ["anthropic", "vllm"]}
}
```
Solution: Use valid backend name (anthropic or vllm)

## Rate Limiting

Admin endpoints have separate rate limits from user endpoints.

**Limits**:
- 1000 requests per hour per user
- 100 configuration changes per hour
- 10 backend switches per hour

**Rate Limit Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1621234567
```

**Rate Limit Exceeded Response**:
```json
{
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded",
  "details": {
    "limit": 1000,
    "reset_in_seconds": 2345
  }
}
```

## Best Practices

### Security

1. **Token Management**
   - Rotate tokens regularly
   - Use short expiration times
   - Store tokens securely (never in code or logs)

2. **Access Control**
   - Limit admin access to authorized users
   - Use separate accounts for different environments
   - Audit admin actions regularly

3. **Network Security**
   - Use HTTPS for all requests
   - Restrict admin endpoint access by IP if possible
   - Monitor for unusual access patterns

### Performance

1. **Caching**
   - Cache health check results (5 minute TTL)
   - Cache metrics for dashboards
   - Avoid polling endpoints frequently

2. **Monitoring**
   - Set up alerts for budget thresholds
   - Monitor backend health continuously
   - Track metric trends over time

3. **Cost Optimization**
   - Use haiku model for simple tasks
   - Switch to vLLM for high-volume workloads
   - Review metrics to identify optimization opportunities

### Operations

1. **Deployment**
   - Test backend switches in staging first
   - Verify health checks before production switches
   - Have rollback plan ready

2. **Maintenance**
   - Schedule configuration changes during low-traffic periods
   - Export metrics before reset operations
   - Document all configuration changes

3. **Troubleshooting**
   - Check health endpoints first
   - Review recent metrics for anomalies
   - Examine logs for error details

## Examples

### Complete Workflow

```bash
# 1. Get authentication token
TOKEN=$(curl -s -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"SecurePassword123!"}' \
  | jq -r '.access_token')

# 2. Check current backend status
curl -X GET https://your-domain.com/api/admin/backend/current \
  -H "Authorization: Bearer $TOKEN"

# 3. View current costs
curl -X GET https://your-domain.com/api/admin/costs \
  -H "Authorization: Bearer $TOKEN"

# 4. Check backend health
curl -X GET https://your-domain.com/api/admin/backend/health \
  -H "Authorization: Bearer $TOKEN"

# 5. Switch to vLLM if healthy
curl -X POST https://your-domain.com/api/admin/backend/switch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backend":"vllm"}'

# 6. Monitor metrics
curl -X GET https://your-domain.com/api/admin/metrics \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Monitoring Script

```bash
#!/bin/bash

TOKEN="your-token-here"
API_URL="https://your-domain.com/api/admin"

# Check costs and alert if over 75%
costs=$(curl -s -X GET "$API_URL/costs" -H "Authorization: Bearer $TOKEN")
used=$(echo $costs | jq -r '.budget_used_percent')

if (( $(echo "$used > 75" | bc -l) )); then
  echo "WARNING: Budget at ${used}%"
  # Send alert
fi

# Check backend health
health=$(curl -s -X GET "$API_URL/backend/health" -H "Authorization: Bearer $TOKEN")
anthropic_healthy=$(echo $health | jq -r '.anthropic.healthy')

if [ "$anthropic_healthy" != "true" ]; then
  echo "ERROR: Anthropic backend unhealthy"
  # Send alert
fi
```

## Support

For issues or questions:

1. Check endpoint response error messages
2. Verify authentication token validity
3. Review application logs
4. Test with curl examples above

Log queries:
```bash
# Admin API access logs
docker compose logs fastapi | grep "/api/admin"

# Backend switch events
docker compose logs fastapi | grep "backend_switched"

# Cost alerts
docker compose logs fastapi | grep "budget_alert"
```