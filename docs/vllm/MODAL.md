# Modal.com vLLM Integration

Status: ACTIVE (Production)
Last Updated: November 22, 2024

## Overview

Modal.com provides serverless GPU infrastructure for running vLLM (Vector Language Model) inference. This integration enables the multi-agent support system to use open-source language models with automatic scaling and pay-per-second billing.

## Why Modal.com

### Cost Efficiency
Modal uses a pay-per-second billing model. You only pay for GPU time when actively processing requests. When idle, the cost is zero. This contrasts with traditional GPU rentals where you pay for the entire rental period regardless of usage.

For a $30 monthly budget:
- L4 GPU: 37.5 hours of compute time at $0.80/hour
- A100 GPU: 10 hours of compute time at $3.00/hour

### Automatic Scaling
Modal handles GPU provisioning automatically. When a request arrives, Modal spins up a GPU instance. After a configurable idle period (default: 5 minutes), the instance scales down to zero.

This eliminates the need for:
- Manual instance management
- Keep-alive monitoring
- Budget tracking scripts
- Orphaned instance cleanup

### Infrastructure Reliability
Modal manages the entire container and GPU lifecycle. There are no CDI (Container Device Interface) injection failures, no manual Docker configuration, and no networking issues to debug.

Cold start time ranges from 10-30 seconds for initial GPU provisioning. Subsequent requests while the instance is warm complete in under 1 second.

## How Modal Works

### Architecture

1. Deployment: You deploy a vLLM server as a Modal function
2. Web URL: Modal provides a permanent HTTPS endpoint
3. Auto-scaling: Modal monitors incoming requests and provisions GPUs as needed
4. Billing: You are charged only for the seconds the GPU is actively running

### Deployment Process

Deploy the vLLM server to Modal:

```bash
modal deploy src/vllm/modal/deployment.py
```

This command:
- Builds a container image with CUDA 12.8, Python 3.12, and vLLM 0.11.2
- Downloads the Qwen 2.5 7B Instruct model (24GB fits in L4 GPU memory)
- Creates persistent volumes for model caching
- Exposes an OpenAI-compatible API endpoint

After deployment, Modal returns a web URL:
```
https://yourorg--multi-agent-vllm-inference-serve.modal.run
```

This URL remains permanent across redeploys.

### Configuration

Configure the system by setting environment variables:

```bash
MODAL_WEB_URL=https://yourorg--multi-agent-vllm-inference-serve.modal.run
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret
MODAL_MODEL=Qwen/Qwen2.5-7B-Instruct
MODAL_GPU_TYPE=L4
MODAL_SCALEDOWN_WINDOW_MINUTES=5
```

The token credentials are optional and only needed for programmatic deployment. For manual deployment, use the Modal CLI with `modal token new`.

### GPU Options

Modal supports multiple GPU types:

| GPU Type | VRAM | Cost per Hour | Use Case |
|----------|------|---------------|----------|
| L4 | 24GB | $0.80 | Recommended for 7B models |
| A10G | 24GB | $1.10 | Alternative to L4 |
| A100 | 40GB | $3.00 | Larger models or higher throughput |
| H100 | 80GB | $4.50 | Maximum performance |

The default L4 GPU provides the best balance of cost and performance for the Qwen 2.5 7B model.

### Integration with Backend Manager

The backend manager automatically detects Modal configuration on startup:

```python
# src/services/infrastructure/backend_manager.py

if settings.modal.web_url:
    init_modal_orchestrator(settings.modal.web_url)
    provider = "modal"
```

When Modal is configured, it takes priority over other providers in the fallback chain:
1. Modal (serverless)
2. Vast.ai (legacy)
3. Anthropic (fallback)

### API Endpoints

The Modal vLLM server exposes OpenAI-compatible endpoints:

**Health Check**
```bash
GET /health
```

**List Models**
```bash
GET /v1/models
```

**Chat Completion**
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Streaming Support**
```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [...],
  "stream": true
}
```

### Cost Management

Set spending limits in the Modal dashboard to prevent unexpected charges:

1. Visit https://modal.com/settings/billing
2. Set a monthly spending limit (e.g., $30)
3. Modal will stop processing requests when the limit is reached

Monitor usage in real-time:
```bash
# Check Modal dashboard
https://modal.com/settings/billing/usage

# View application logs
modal app logs multi-agent-vllm-inference
```

## What We Are Doing

### Current Implementation

The multi-agent support system uses Modal for:

1. **AI-Powered Responses**: Customer support conversations use vLLM through Modal
2. **Cost Optimization**: Serverless billing reduces costs compared to always-on GPU instances
3. **Automatic Scaling**: System handles variable load without manual intervention
4. **Fallback Strategy**: If Modal is unavailable, the system falls back to Anthropic

### Code Organization

```
src/vllm/modal/
├── __init__.py          # Package exports
├── client.py            # HTTP client for Modal endpoint
├── orchestrator.py      # High-level orchestration
└── deployment.py        # Modal deployment configuration
```

### Client Implementation

The Modal client (src/vllm/modal/client.py) provides:
- Async HTTP requests to the Modal endpoint
- Exponential backoff retry logic
- Health check monitoring
- OpenAI-compatible request format

### Orchestrator Implementation

The Modal orchestrator (src/vllm/modal/orchestrator.py) provides:
- Endpoint URL management
- Status reporting
- Health validation
- Request tracking

Unlike the Vast.ai orchestrator, Modal requires no instance management code. The orchestrator simply wraps the client and provides status endpoints.

### Startup Initialization

On application startup, the backend manager initializes the Modal orchestrator:

```python
# src/api/main.py

@app.on_event("startup")
async def startup_event():
    if settings.modal.web_url:
        orchestrator = init_modal_orchestrator(settings.modal.web_url)
        await orchestrator.validate_health()
```

### Health Monitoring

The system periodically checks Modal health:

```python
# Every API call validates endpoint health
health = await orchestrator.client.health_check()
if not health["healthy"]:
    # Log warning and fall back to Anthropic
    logger.warning("modal_health_check_failed")
```

### Request Flow

1. User sends a support message
2. Backend manager checks current provider (Modal)
3. System formats OpenAI-compatible request
4. Modal provisions GPU if needed (cold start: 10-30s)
5. vLLM processes the request
6. Response streams back to the user
7. After 5 minutes of inactivity, Modal scales to zero

## Deployment Guide

### Prerequisites

1. Modal account (https://modal.com)
2. Modal CLI installed: `pip install modal`
3. Modal authentication: `modal token new`

### Initial Setup

```bash
# 1. Install Modal SDK
pip install modal

# 2. Authenticate
modal token new

# 3. Deploy vLLM server
modal deploy src/vllm/modal/deployment.py

# 4. Copy the web URL from output
# Example: https://yourorg--multi-agent-vllm-inference-serve.modal.run

# 5. Configure environment
export MODAL_WEB_URL="https://yourorg--multi-agent-vllm-inference-serve.modal.run"

# 6. Restart application
docker compose restart fastapi
```

### Testing Deployment

```bash
# Test Modal endpoint directly
curl https://yourorg--multi-agent-vllm-inference-serve.modal.run/health

# Test via application API
curl -X GET https://your-domain.com/api/admin/vllm/status \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### Monitoring

View logs in real-time:
```bash
modal app logs multi-agent-vllm-inference
```

View recent requests:
```bash
modal app list
```

Check spending:
```bash
# Visit Modal dashboard
https://modal.com/settings/billing/usage
```

## Troubleshooting

### Cold Start Latency

Symptom: First request takes 30-60 seconds
Cause: GPU provisioning time
Solution: This is expected behavior. Subsequent requests are fast.

### 503 Service Unavailable

Symptom: Modal returns 503 errors
Cause: GPU quota exceeded or cold start timeout
Solution: Check Modal dashboard for quota limits. Increase timeout in nginx configuration if needed.

### Model Not Found Error

Symptom: Modal returns "model not found"
Cause: Model name mismatch
Solution: Verify MODAL_MODEL matches the deployed model (default: Qwen/Qwen2.5-7B-Instruct)

### Unexpected Charges

Symptom: Modal bill higher than expected
Cause: Instance stayed warm longer than expected
Solution: Verify MODAL_SCALEDOWN_WINDOW_MINUTES is set correctly (default: 5). Set spending limit in Modal dashboard.

## Migration from Vast.ai

If migrating from Vast.ai to Modal:

1. Deploy Modal endpoint (see Deployment Guide)
2. Set MODAL_WEB_URL environment variable
3. Restart application
4. Backend manager will automatically prefer Modal
5. Remove Vast.ai configuration (optional)

No code changes are required. The backend manager handles provider detection automatically.

## Performance Characteristics

### Latency

- Cold start: 10-30 seconds (first request after idle period)
- Warm request: <1 second (while instance is active)
- Model inference: 20-50 tokens/second (L4 GPU)

### Throughput

- Concurrent requests: 32 (configurable via MAX_CONCURRENT_REQUESTS)
- Model supports: 4096 token context window
- Recommended: <10 concurrent users per instance

### Reliability

- Modal uptime: 99.9% (per Modal SLA)
- Auto-restart: Yes (Modal handles container failures)
- Health monitoring: Every 60 seconds

## Security

### Network Security

- Modal provides HTTPS endpoints by default
- TLS 1.2+ encryption for all traffic
- No public IP exposure required

### Authentication

- No authentication required for deployed endpoints
- Implement application-layer authentication in backend manager
- Use environment variables for sensitive configuration

### Data Privacy

- Requests are processed in Modal's cloud infrastructure
- No data persistence (stateless processing)
- Model weights cached in Modal volumes (encrypted at rest)

## Support and Resources

Modal Documentation: https://modal.com/docs
Modal Community: https://modal.com/community
Modal Status: https://status.modal.com

For issues specific to this integration, check application logs:
```bash
docker compose logs -f fastapi
```
