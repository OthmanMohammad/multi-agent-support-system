# LLM Backend Abstraction Layer

This module provides a unified interface for multiple Large Language Model (LLM) backends, enabling seamless switching between providers with automatic cost tracking and metrics collection.

## Architecture

### Core Components

**UnifiedLLMClient** (`client.py`)
- Wraps LiteLLM library to provide consistent API across providers
- Handles automatic retry logic and error handling
- Tracks token usage and costs for every API call
- Supports streaming and non-streaming responses

**LiteLLMConfig** (`litellm_config.py`)
- Manages backend configurations (Anthropic, vLLM)
- Stores model mappings and parameters
- Handles backend switching logic
- Validates configuration changes

**Backend Manager** (`../services/infrastructure/backend_manager.py`)
- Orchestrates backend health checks
- Manages backend switching operations
- Monitors service availability

## Supported Backends

### Anthropic Claude
Production-ready API with three model tiers:
- **haiku**: Fast, cost-effective (claude-3-haiku-20240307)
- **sonnet**: Balanced performance (claude-3-5-sonnet-20241022)
- **opus**: Maximum capability (claude-3-opus-20240229)

Pricing: Per-token billing (input + output)

### vLLM (Self-Hosted)
Local inference server for cost optimization:
- **qwen**: Open-source model (Qwen/Qwen2.5-7B-Instruct)

Pricing: Hourly compute cost estimation

## Usage

### Basic Usage in Agents

All agents inherit from `BaseAgent` which provides access to the unified client:

```python
from src.agents.base.base_agent import BaseAgent

class MyAgent(BaseAgent):
    async def process(self, message: str) -> str:
        # Automatic backend selection based on agent config
        response = await self.call_llm(
            system_prompt="You are a helpful assistant",
            user_message=message
        )
        return response
```

The `call_llm` method automatically:
- Uses the configured backend (Anthropic or vLLM)
- Tracks token usage and costs
- Collects latency metrics
- Handles errors and retries

### Direct Client Usage

For custom implementations outside the agent framework:

```python
from src.llm.client import llm_client

async def custom_function():
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]

    response = await llm_client.chat_completion(
        messages=messages,
        model_tier="haiku",  # or "sonnet", "opus", "qwen"
        temperature=0.7,
        max_tokens=1000
    )

    return response
```

### Streaming Responses

```python
async def stream_example():
    messages = [{"role": "user", "content": "Tell me a story"}]

    async for chunk in llm_client.stream_chat_completion(
        messages=messages,
        model_tier="sonnet"
    ):
        print(chunk, end="", flush=True)
```

## Backend Switching

### Via Admin API

```bash
# Switch to vLLM
curl -X POST https://your-domain.com/api/admin/backend/switch \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"backend": "vllm", "skip_health_check": false}'

# Switch back to Anthropic
curl -X POST https://your-domain.com/api/admin/backend/switch \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"backend": "anthropic"}'
```

### Programmatically

```python
from src.services.infrastructure.backend_manager import backend_manager
from src.llm.litellm_config import LLMBackend

# Switch backend
result = await backend_manager.switch_backend(
    backend=LLMBackend.VLLM,
    skip_health_check=False
)

if result["success"]:
    print(f"Switched to {result['backend']}")
else:
    print(f"Switch failed: {result['message']}")
```

## Cost Tracking

The system automatically tracks costs for all LLM calls.

### View Current Costs

```bash
curl -X GET https://your-domain.com/api/admin/costs \
  -H "Authorization: Bearer <TOKEN>"
```

Response:
```json
{
  "anthropic": 12.45,
  "vllm": 3.20,
  "total": 15.65,
  "budget_limit": 100.0,
  "remaining": 84.35,
  "budget_used_percent": 15.65
}
```

### Budget Management

Set budget limits to prevent overruns:

```bash
curl -X POST https://your-domain.com/api/admin/budget \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"budget_limit": 150.0}'
```

Budget alerts trigger at:
- 75% (warning)
- 90% (critical warning)
- 100% (API calls blocked)

### Cost Calculation

**Anthropic**: Per-token pricing
```
cost = (input_tokens × input_price) + (output_tokens × output_price)
```

**vLLM**: Hourly compute cost
```
cost = uptime_hours × hourly_rate
```

Default vLLM rate: $0.16/hour (based on Vast.ai RTX 3090 pricing)

## Metrics Collection

The system collects detailed metrics for monitoring and optimization.

### Available Metrics

```bash
curl -X GET https://your-domain.com/api/admin/metrics \
  -H "Authorization: Bearer <TOKEN>"
```

Response includes:
- Total calls (successful/failed)
- Token usage (input/output)
- Average latency per backend/model
- Error rates
- Recent call history

### Metrics Breakdown

**Overview**:
- `total_calls`: All LLM API calls
- `successful_calls`: Completed without errors
- `failed_calls`: Errors or timeouts
- `total_tokens`: Combined input + output tokens

**By Backend**:
- Per-backend statistics (Anthropic, vLLM)
- Call counts and token usage
- Average latency

**By Model**:
- Per-model breakdown (haiku, sonnet, opus, qwen)
- Model-specific performance metrics

## Configuration

### Environment Variables

Required for Anthropic backend:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Required for vLLM backend:
```bash
VLLM_ENDPOINT=http://your-vllm-server:8000
```

Optional:
```bash
# Cost tracking budget
BUDGET_LIMIT=100.0

# vLLM hourly cost (for cost estimation)
VLLM_HOURLY_RATE=0.16
```

### vLLM Endpoint Configuration

Configure vLLM endpoint dynamically:

```bash
curl -X POST https://your-domain.com/api/admin/backend/vllm/endpoint \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"endpoint": "http://10.0.0.5:8000"}'
```

## Health Checks

Monitor backend availability:

```bash
# Check all backends
curl -X GET https://your-domain.com/api/admin/backend/health \
  -H "Authorization: Bearer <TOKEN>"

# Check specific backend
curl -X GET https://your-domain.com/api/admin/backend/health/anthropic \
  -H "Authorization: Bearer <TOKEN>"
```

Health checks verify:
- API endpoint reachability
- Authentication validity
- Response time within acceptable range

## Error Handling

The system implements comprehensive error handling:

### Automatic Retries

Failed requests retry with exponential backoff:
- Initial delay: 1 second
- Maximum retries: 3
- Backoff multiplier: 2x

### Error Types

**Rate Limiting (429)**:
- Automatic retry after delay
- Logged for monitoring

**Authentication (401)**:
- No retry (requires config fix)
- Alert logged

**Service Unavailable (503)**:
- Retry with backoff
- Consider backend switch

**Timeout**:
- Configurable timeout per request
- Default: 60 seconds

### Error Logging

All errors logged with context:
```json
{
  "event": "llm_call_failed",
  "backend": "anthropic",
  "model": "claude-3-haiku-20240307",
  "error_type": "RateLimitError",
  "error_message": "Rate limit exceeded",
  "retry_count": 2
}
```

## Performance Optimization

### Model Selection

Choose models based on use case:

**Haiku**: Simple tasks, high volume
- Customer support responses
- Data extraction
- Classification

**Sonnet**: Complex reasoning
- Code generation
- Analysis
- Multi-step workflows

**Opus**: Maximum capability
- Creative writing
- Complex problem solving
- Critical decisions

**Qwen (vLLM)**: Cost optimization
- High-volume tasks
- Development/testing
- Non-critical workloads

### Caching

The system does not implement response caching by default. Consider implementing at the application layer for frequently requested content.

### Request Batching

For multiple independent requests, use concurrent execution:

```python
import asyncio

async def batch_requests():
    tasks = [
        llm_client.chat_completion(messages=msg, model_tier="haiku")
        for msg in message_list
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## Migration Guide

### Migrating Existing Agents

Existing agents automatically use the new backend abstraction. No code changes required.

The `BaseAgent.call_llm()` method internally uses the unified client:

**Before** (direct Anthropic client):
```python
response = self.client.messages.create(
    model=self.config.model,
    max_tokens=self.config.max_tokens,
    messages=[{"role": "user", "content": message}]
)
```

**After** (unified client - automatic):
```python
response = await self.call_llm(
    system_prompt=system_prompt,
    user_message=message
)
```

Both work. The new method provides automatic cost tracking and metrics.

## Troubleshooting

### Backend Switch Fails

**Symptom**: Backend switch returns `success: false`

**Solutions**:
1. Check backend health: `GET /api/admin/backend/health`
2. Verify configuration (API keys, endpoints)
3. Use `skip_health_check: true` to force switch
4. Check logs for specific error messages

### High Costs

**Symptom**: Budget alerts or unexpected costs

**Actions**:
1. Review metrics: `GET /api/admin/metrics`
2. Identify high-usage models/agents
3. Consider switching to Haiku for simple tasks
4. Enable vLLM for non-critical workloads
5. Implement request filtering/validation

### Slow Response Times

**Symptom**: High latency in metrics

**Solutions**:
1. Check backend health and response times
2. Consider using faster model (Haiku vs Sonnet)
3. Reduce max_tokens if possible
4. Implement request timeout limits
5. Monitor network connectivity

### Missing Metrics

**Symptom**: Metrics show zero or incomplete data

**Causes**:
1. Metrics collection not initialized
2. Redis connection issues
3. Recent deployment/restart

**Fix**: Metrics reset on restart. Historical data not persisted.

## API Reference

### UnifiedLLMClient Methods

**chat_completion(messages, model_tier, **kwargs)**
- Synchronous completion
- Returns full response text

**stream_chat_completion(messages, model_tier, **kwargs)**
- Async generator for streaming
- Yields text chunks

**get_available_models()**
- Returns list of available models for current backend

### Admin Endpoints

**GET /api/admin/backend/current**
- Current backend status

**POST /api/admin/backend/switch**
- Switch between backends

**GET /api/admin/costs**
- Cost breakdown and budget status

**POST /api/admin/budget**
- Update budget limit

**GET /api/admin/metrics**
- Usage metrics and statistics

**GET /api/admin/backend/health**
- Health check all backends

**POST /api/admin/backend/vllm/endpoint**
- Configure vLLM endpoint

See `src/api/routes/admin.py` for complete API documentation.

## Security Considerations

### API Key Management

- Store API keys in environment variables or secrets manager
- Never commit keys to version control
- Rotate keys regularly
- Use separate keys for development and production

### Access Control

Admin endpoints require authentication:
- JWT token with admin role
- API key with admin scope

Configure role-based access in `src/api/dependencies/auth_dependencies.py`

### Rate Limiting

The application implements rate limiting:
- Per-user request limits
- Backend-specific quotas
- Budget-based throttling

### Audit Logging

All admin actions logged:
- Backend switches
- Budget changes
- Configuration updates

Logs include user ID, timestamp, and action details.

## Support

For issues or questions:
1. Check logs: `docker compose logs fastapi`
2. Verify configuration: environment variables and secrets
3. Test health endpoints
4. Review error messages in structured logs

Common log queries:
```bash
# LLM errors
docker compose logs fastapi | grep "llm_call_failed"

# Cost tracking
docker compose logs fastapi | grep "cost_tracked"

# Backend switches
docker compose logs fastapi | grep "backend_switched"
```