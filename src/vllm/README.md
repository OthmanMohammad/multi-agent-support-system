# vLLM Multi-Provider Integration

Version: 2.0.0
Status: Production
Last Updated: November 22, 2024

## Overview

This package provides GPU-accelerated language model inference for the multi-agent support system using vLLM (Vector Language Model). The implementation supports multiple GPU providers with automatic fallback and cost optimization.

## Supported Providers

### Modal.com (Recommended)

Status: ACTIVE
Documentation: docs/vllm/MODAL.md

Modal.com provides serverless GPU infrastructure with pay-per-second billing and automatic scaling. This is the recommended provider for production deployments.

Key Features:
- Serverless architecture (zero cost when idle)
- Automatic GPU provisioning and scaling
- L4 GPU at $0.80/hour
- 10-30 second cold start time
- No instance management required
- 99.9% uptime SLA

Typical Monthly Cost:
- Low traffic: $10-20 (2-3 hours actual GPU time per day)
- Medium traffic: $30-40 (4-5 hours actual GPU time per day)
- High traffic: $50-60 (7-8 hours actual GPU time per day)

### Vast.ai (Legacy)

Status: DEPRECATED
Documentation: docs/vllm/VASTAI.md

Vast.ai provided GPU marketplace access for the initial implementation but has been deprecated due to infrastructure reliability issues. The code is maintained for reference but is not recommended for new deployments.

Migration from Vast.ai to Modal is straightforward and requires only environment variable changes.

## Architecture

### Provider Priority

The backend manager automatically selects providers in priority order:

1. **Modal.com** (if MODAL_WEB_URL is configured)
2. **Vast.ai** (if VASTAI_API_KEY is configured)
3. **Anthropic** (fallback if no GPU provider available)

This ensures the system always has a functioning language model backend while preferring cost-effective GPU options when available.

### Directory Structure

```
src/vllm/
├── __init__.py              # Package exports
├── README.md                # This file
├── modal/                   # Modal.com integration (ACTIVE)
│   ├── __init__.py
│   ├── client.py           # HTTP client for Modal endpoint
│   ├── orchestrator.py     # High-level orchestration
│   └── deployment.py       # Modal deployment configuration
└── vastai/                  # Vast.ai integration (LEGACY)
    ├── __init__.py
    ├── client.py           # Vast.ai API client
    ├── orchestrator.py     # GPU lifecycle management
    ├── gpu_configs.py      # Fallback configurations
    └── docker_config.py    # vLLM container settings
```

### Package Exports

The package exports Modal integration components for use throughout the application:

```python
from src.vllm import (
    ModalVLLMClient,           # HTTP client for Modal endpoint
    ModalOrchestrator,         # Orchestrator class
    modal_orchestrator,        # Global orchestrator instance
    init_modal_orchestrator,   # Initialize orchestrator
    get_modal_orchestrator,    # Get orchestrator instance
    is_modal_configured,       # Check if Modal is configured
)
```

Vast.ai components are available but deprecated:

```python
from src.vllm.vastai import (
    VastAIClient,              # Vast.ai API client (deprecated)
    GPUOrchestrator,           # GPU lifecycle manager (deprecated)
    gpu_orchestrator,          # Global orchestrator (deprecated)
)
```

## Configuration

### Modal.com Configuration

Required environment variables:

```bash
# Modal endpoint URL (from deployment)
MODAL_WEB_URL=https://yourorg--multi-agent-vllm-inference-serve.modal.run

# Optional: Modal API credentials (only needed for programmatic deployment)
MODAL_TOKEN_ID=your_token_id
MODAL_TOKEN_SECRET=your_token_secret

# Optional: Model and GPU configuration
MODAL_MODEL=Qwen/Qwen2.5-7B-Instruct
MODAL_GPU_TYPE=L4
MODAL_SCALEDOWN_WINDOW_MINUTES=5
```

### Vast.ai Configuration (Legacy)

Vast.ai configuration is deprecated but still functional:

```bash
# Vast.ai API key (deprecated)
VASTAI_API_KEY=your_api_key

# Optional budget limits (deprecated)
VASTAI_BUDGET_LIMIT=15.0
VASTAI_SESSION_BUDGET_LIMIT=2.0
```

For new deployments, use Modal.com instead.

## Quick Start

### Deploying Modal.com

```bash
# 1. Install Modal CLI
pip install modal

# 2. Authenticate with Modal
modal token new

# 3. Deploy vLLM server
modal deploy src/vllm/modal/deployment.py

# 4. Copy the web URL from deployment output
# Example: https://yourorg--multi-agent-vllm-inference-serve.modal.run

# 5. Configure environment
export MODAL_WEB_URL="<your-web-url>"

# 6. Restart application
docker compose restart fastapi
```

### Verifying Deployment

```bash
# Check Modal endpoint health
curl https://yourorg--multi-agent-vllm-inference-serve.modal.run/health

# Check application status
curl -X GET https://your-domain.com/api/admin/vllm/status \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Expected response:
# {
#   "status": "ready",
#   "endpoint": "https://yourorg--multi-agent-vllm-inference-serve.modal.run/v1",
#   "provider": "modal"
# }
```

## Usage

### Backend Manager Integration

The vLLM integration is accessed through the backend manager:

```python
from src.services.infrastructure.backend_manager import backend_manager

# Check current provider
provider = backend_manager.get_current_provider()
# Returns: "modal", "vastai", or "anthropic"

# Get vLLM status
status = await backend_manager.get_vllm_status()
# Returns: {"status": "ready", "endpoint": "...", ...}

# Make chat completion request
response = await backend_manager.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)
```

The backend manager automatically routes requests to the appropriate provider based on availability and configuration.

### Direct Modal Client Usage

For advanced use cases, the Modal client can be used directly:

```python
from src.vllm.modal import get_modal_orchestrator

# Get orchestrator
orchestrator = get_modal_orchestrator()

# Get endpoint URL
endpoint = orchestrator.get_endpoint()
# Returns: "https://yourorg--multi-agent-vllm-inference-serve.modal.run/v1"

# Check health
status = await orchestrator.get_status()
# Returns: {"status": "ready", "endpoint": "...", ...}

# Make chat completion
response = await orchestrator.chat_completion(
    messages=[...],
    temperature=0.7,
    max_tokens=2048
)
```

## API Endpoints

### Admin Endpoints

The application exposes admin endpoints for vLLM management:

```bash
# Get vLLM status
GET /api/admin/vllm/status

# Launch GPU instance (Vast.ai only - deprecated)
POST /api/admin/vllm/launch

# Destroy GPU instance (Vast.ai only - deprecated)
POST /api/admin/vllm/destroy
```

Modal.com does not require launch/destroy endpoints as it scales automatically.

### vLLM OpenAI-Compatible Endpoints

The vLLM server exposes standard OpenAI-compatible endpoints:

```bash
# Health check
GET /health

# List available models
GET /v1/models

# Chat completion
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

## Cost Management

### Modal.com Costs

Modal bills per second of actual GPU usage:

```bash
# L4 GPU pricing
$0.80/hour = $0.000222/second

# Example: 30 minutes of GPU time
30 minutes × 60 seconds × $0.000222 = $0.40

# Monthly estimate (2 hours/day average)
2 hours/day × 30 days × $0.80 = $48.00
```

Set spending limits in the Modal dashboard to prevent unexpected charges:
https://modal.com/settings/billing

### Vast.ai Costs (Legacy)

Vast.ai bills per hour of instance runtime:

```bash
# RTX 3090 pricing (typical)
$0.14/hour

# Example: 45 minutes keep-alive
45 minutes = 0.75 hours × $0.14 = $0.105

# Monthly estimate (8 hours/day active)
8 hours/day × 30 days × $0.14 = $33.60
```

Note: Vast.ai charges for the entire instance runtime regardless of actual request volume, making it less cost-effective for variable workloads.

## Monitoring

### Health Checks

The system automatically monitors vLLM health:

```python
# Health check runs every 60 seconds
health = await orchestrator.client.health_check()

if not health["healthy"]:
    # Log warning and fall back to Anthropic
    logger.warning("vllm_health_check_failed")
```

### Logging

All vLLM operations are logged with structured context:

```json
{
  "event": "modal_orchestrator_initialized",
  "modal_web_url": "https://...",
  "timestamp": "2024-11-22T10:00:00Z"
}

{
  "event": "modal_chat_completion",
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "tokens": 150,
  "total_requests": 42,
  "timestamp": "2024-11-22T10:05:00Z"
}
```

### Metrics

The orchestrator tracks key metrics:

- Total requests processed
- Response time (health checks)
- Uptime hours
- Current status (ready/degraded/unhealthy)

Access metrics via the status endpoint:

```bash
GET /api/admin/vllm/status
```

## Troubleshooting

### Modal.com Issues

**Cold Start Latency**
Symptom: First request takes 30 seconds
Cause: GPU provisioning time (expected behavior)
Solution: Subsequent requests are fast while instance is warm

**503 Service Unavailable**
Symptom: Modal returns 503 errors
Cause: GPU quota exceeded or cold start timeout
Solution: Check Modal dashboard for quota limits

**Model Not Found**
Symptom: Modal returns "model not found"
Cause: Model name mismatch
Solution: Verify MODAL_MODEL matches deployed model

### Vast.ai Issues (Legacy)

**CDI Injection Failures**
Symptom: Container fails with "failed to inject CDI devices"
Cause: Infrastructure compatibility issues
Solution: Migrate to Modal.com

**Instance Timeout**
Symptom: Instance stuck in "loading" for 10+ minutes
Cause: Host startup failure
Solution: Destroy instance and retry, or migrate to Modal.com

See docs/vllm/VASTAI.md for detailed Vast.ai troubleshooting.

## Migration from Vast.ai

To migrate from Vast.ai to Modal:

```bash
# 1. Deploy Modal endpoint
modal deploy src/vllm/modal/deployment.py

# 2. Update environment
export MODAL_WEB_URL="<your-modal-url>"
unset VASTAI_API_KEY

# 3. Restart application
docker compose restart fastapi

# 4. Destroy any running Vast.ai instances
python scripts/vastai/cleanup_orphaned_gpus.py
```

The backend manager will automatically detect Modal and prioritize it over Vast.ai.

## Performance

### Modal.com Performance

- Cold start: 10-30 seconds (first request after idle)
- Warm request: <1 second (while instance is active)
- Inference speed: 20-50 tokens/second (L4 GPU)
- Concurrent requests: Up to 32 simultaneous
- Context window: 4096 tokens

### Vast.ai Performance (Legacy)

- Cold start: 7-15 minutes (instance boot + model load)
- Warm request: <1 second (once running)
- Inference speed: 25-55 tokens/second (RTX 3090)
- Concurrent requests: Up to 32 simultaneous
- Context window: 4096 tokens

## Security

### Network Security

- Modal provides HTTPS endpoints by default (TLS 1.2+)
- No public IP exposure required
- Encrypted traffic for all requests

### Authentication

- No authentication at the vLLM endpoint level
- Application-layer authentication in backend manager
- Admin API requires bearer token authorization

### Data Privacy

- Requests processed in provider cloud infrastructure
- No persistent data storage (stateless processing)
- Model weights cached in encrypted volumes

## Development

### Running Tests

```bash
# Test Modal integration
pytest tests/test_modal_vllm.py -v

# Test backend manager
pytest tests/test_backend_manager.py -v
```

### Adding a New Provider

To add a new GPU provider:

1. Create new package: `src/vllm/provider_name/`
2. Implement client: `src/vllm/provider_name/client.py`
3. Implement orchestrator: `src/vllm/provider_name/orchestrator.py`
4. Update backend manager: `src/services/infrastructure/backend_manager.py`
5. Update priority chain in backend manager
6. Add environment configuration: `src/core/config.py`
7. Document provider: `docs/vllm/PROVIDER_NAME.md`

## Resources

### Documentation

- Modal Integration: docs/vllm/MODAL.md
- Vast.ai Legacy: docs/vllm/VASTAI.md
- Backend Manager: src/services/infrastructure/README.md

### External Links

- vLLM Documentation: https://docs.vllm.ai
- Modal Documentation: https://modal.com/docs
- Vast.ai Documentation: https://vast.ai/docs (legacy)

### Support

For issues or questions:

1. Check application logs: `docker compose logs -f fastapi`
2. Verify configuration: `curl .../api/admin/vllm/status`
3. Review provider documentation
4. Check provider status pages

## Changelog

### Version 2.0.0 (November 22, 2024)

- Added Modal.com serverless integration
- Deprecated Vast.ai integration
- Reorganized package structure (modal/ and vastai/ subpackages)
- Updated imports to use full paths (production style)
- Added comprehensive documentation for each provider
- Implemented automatic provider detection and fallback

### Version 1.0.0 (November 22, 2024)

- Initial Vast.ai integration
- 10-tier GPU fallback strategy
- Budget enforcement and cost tracking
- Health monitoring with circuit breaker
- Automatic instance cleanup
