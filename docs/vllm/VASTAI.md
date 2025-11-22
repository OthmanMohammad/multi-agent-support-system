# Vast.ai vLLM Integration (Legacy)

Status: DEPRECATED (Not Recommended for Production)
Last Updated: November 22, 2024
Migration Date: November 22, 2024

## Overview

Vast.ai provides GPU rental marketplace infrastructure for running vLLM inference. This integration was the initial implementation for GPU-accelerated language models but has been deprecated in favor of Modal.com due to infrastructure reliability issues.

This documentation is maintained for reference and troubleshooting existing deployments.

## Why Vast.ai Was Used

### Initial Requirements

The original implementation needed:
- Cost-effective GPU access for 7B parameter models
- Control over GPU selection and configuration
- Ability to search across multiple GPU types
- Pay-per-hour billing for budget predictability

Vast.ai provided a marketplace of community-hosted GPUs with competitive pricing, typically $0.12-$0.18 per hour for RTX 3090 GPUs compared to $3.00+ per hour on major cloud providers.

### GPU Selection Strategy

The implementation used a 10-tier fallback strategy to find available GPUs:

| Priority | GPU Model | VRAM | Max Price/Hour | Target Use Case |
|----------|-----------|------|----------------|-----------------|
| 1 | RTX 3090 | 24GB | $0.15 | Optimal cost/performance |
| 2 | RTX 3090 Ti | 24GB | $0.16 | Slightly faster variant |
| 3 | RTX 4090 | 24GB | $0.18 | Latest generation |
| 4 | RTX 4080 | 16GB | $0.17 | Good alternative |
| 5 | RTX A5000 | 24GB | $0.20 | Professional card |
| 6 | RTX A6000 | 48GB | $0.25 | Higher VRAM |
| 7 | A40 | 48GB | $0.30 | Datacenter GPU |
| 8 | A100 | 40GB | $0.50 | High-end option |
| 9 | V100 | 16GB | $0.35 | Older generation |
| 10 | RTX 3080 | 10GB | $0.12 | Emergency fallback |

The orchestrator would search each tier sequentially until finding an available GPU within budget constraints.

## Why Vast.ai Was Deprecated

### Infrastructure Reliability Issues

After 10+ hours of debugging, persistent issues prevented production deployment:

1. **CDI Injection Failures**: Container Device Interface errors when mounting GPUs into Docker containers
2. **Inconsistent Host Configuration**: Different hosts had varying Docker versions and NVIDIA driver setups
3. **Port Mapping Complexity**: Vast.ai uses random external port mapping, requiring dynamic endpoint discovery
4. **Startup Time Variability**: Instance startup ranged from 2-15 minutes with frequent timeouts
5. **Health Check Failures**: vLLM health endpoints often returned errors even when the service was running

### Operational Complexity

Managing Vast.ai instances required significant operational overhead:

- Manual instance lifecycle management (search, launch, monitor, destroy)
- Budget tracking scripts to prevent overspending
- Keep-alive management to automatically destroy idle instances
- Orphaned instance cleanup for failed shutdowns
- Health monitoring with circuit breaker patterns
- Error recovery and automatic retries

### Cost Comparison

While Vast.ai offered lower hourly rates, the operational costs were higher:

**Vast.ai (Active GPU Time):**
- RTX 3090: $0.14/hour
- Required: Always-on during business hours (8 hours/day)
- Monthly cost: $0.14 × 8 × 30 = $33.60

**Modal.com (Serverless):**
- L4 GPU: $0.80/hour
- Actual usage: 2-3 hours/day (auto-scales to zero when idle)
- Monthly cost: $0.80 × 2.5 × 30 = $60.00

However, Modal eliminated:
- 10+ hours of debugging time
- Ongoing operational maintenance
- Risk of orphaned instances
- Manual budget tracking

## How Vast.ai Works

### Architecture

The Vast.ai integration consists of four main components:

1. **Vast.ai API Client** (src/vllm/vastai/client.py)
   - HTTP client for Vast.ai REST API
   - Exponential backoff retry logic
   - Rate limit handling

2. **GPU Orchestrator** (src/vllm/vastai/orchestrator.py)
   - Instance lifecycle management
   - Health monitoring
   - Budget enforcement
   - Keep-alive management

3. **GPU Configurations** (src/vllm/vastai/gpu_configs.py)
   - Fallback strategy definitions
   - GPU scoring algorithm
   - Compatibility filtering

4. **Docker Configuration** (src/vllm/vastai/docker_config.py)
   - vLLM container settings
   - Port mapping configuration
   - Environment variables

### Deployment Process

The original deployment flow:

```bash
# 1. Set Vast.ai API key
export VASTAI_API_KEY="your_api_key"

# 2. Launch GPU instance via API
curl -X POST https://your-domain.com/api/admin/vllm/launch \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"keep_alive_minutes": 45, "auto_switch": true}'

# 3. Orchestrator searches for GPUs
# - Tries RTX 3090 (priority 1)
# - Falls back to RTX 4090 (priority 3)
# - Finds available instance

# 4. Launch instance
# - Vast.ai spins up host machine
# - Docker container starts
# - vLLM loads model (5-10 minutes)

# 5. Health monitoring begins
# - Checks /health every 60 seconds
# - Destroys instance after 3 failures

# 6. Keep-alive monitoring
# - Auto-destroys after 45 minutes of inactivity
```

### Instance Lifecycle

```
┌─────────────────────────────────────────────────┐
│                    IDLE                         │
│              No GPU Running                     │
└─────────────┬───────────────────────────────────┘
              │
        Launch Request
              │
              v
┌─────────────────────────────────────────────────┐
│                 SEARCHING                       │
│         Try 10 GPU Configurations               │
└─────────────┬───────────────────────────────────┘
              │
        GPU Found
              │
              v
┌─────────────────────────────────────────────────┐
│                LAUNCHING                        │
│     Create Instance on Vast.ai Host             │
└─────────────┬───────────────────────────────────┘
              │
      Instance Created
              │
              v
┌─────────────────────────────────────────────────┐
│                 BOOTING                         │
│        Wait for Instance Running                │
└─────────────┬───────────────────────────────────┘
              │
     Instance Running
              │
              v
┌─────────────────────────────────────────────────┐
│            STARTING_VLLM                        │
│       Wait for Health Check (10 min)            │
└─────────────┬───────────────────────────────────┘
              │
    Health Check Passes
              │
              v
┌─────────────────────────────────────────────────┐
│                  READY                          │
│         Process Requests (45 min)               │
└─────────────┬───────────────────────────────────┘
              │
   Keep-Alive Expires or Health Failure
              │
              v
┌─────────────────────────────────────────────────┐
│                DESTROYING                       │
│        Destroy Instance, Stop Billing           │
└─────────────┬───────────────────────────────────┘
              │
              v
           IDLE (cycle repeats)
```

### Budget Enforcement

The implementation included four budget checkpoints:

**Checkpoint 1: Before Search**
```python
total_spent = cost_tracker.get_total_cost()
if total_spent >= VASTAI_BUDGET_LIMIT:
    raise RuntimeError("Budget exceeded")
```

**Checkpoint 2: After Launch**
```python
estimated_cost = (keep_alive_minutes / 60) * price_per_hour
if estimated_cost > VASTAI_SESSION_BUDGET_LIMIT:
    raise RuntimeError("Session would exceed budget")
```

**Checkpoint 3: During Runtime**
```python
# Background monitor checks every 5 minutes
current_cost = calculate_runtime_cost()
if current_cost > session_budget:
    await destroy_instance()
```

**Checkpoint 4: On Extension**
```python
new_cost = (additional_minutes / 60) * price_per_hour
if current_cost + new_cost > session_budget:
    raise RuntimeError("Extension would exceed budget")
```

## What We Were Doing

### Implementation Details

The Vast.ai integration provided:

1. **Intelligent GPU Search**: Multi-factor scoring algorithm considering price, reliability, network speed, CUDA version, and disk space

2. **Automatic Instance Management**: Complete lifecycle from search to destruction with error recovery

3. **Health Monitoring**: Circuit breaker pattern with automatic destruction after 3 consecutive health check failures

4. **Cost Tracking**: Real-time cost calculation and budget enforcement

5. **Safety Mechanisms**: Orphaned instance cleanup, automatic destruction on shutdown, and budget limits

### Code Organization

```
src/vllm/vastai/
├── __init__.py          # Package exports
├── client.py            # Vast.ai API client
├── orchestrator.py      # GPU lifecycle management
├── gpu_configs.py       # Fallback configurations
└── docker_config.py     # vLLM container settings

scripts/vastai/
├── check_budget.py          # Budget monitoring script
└── cleanup_orphaned_gpus.py # Orphaned instance cleanup
```

### Admin API Endpoints

The system exposed Vast.ai-specific endpoints:

```bash
# Launch GPU instance
POST /api/admin/vllm/launch
{
  "keep_alive_minutes": 45,
  "auto_switch": true
}

# Get instance status
GET /api/admin/vllm/status

# Extend keep-alive time
POST /api/admin/vllm/extend
{
  "additional_minutes": 15
}

# Destroy instance
POST /api/admin/vllm/destroy
```

### Integration with Backend Manager

The backend manager included Vast.ai provider detection:

```python
# src/services/infrastructure/backend_manager.py

if settings.vastai.api_key:
    # Initialize orchestrator
    await gpu_orchestrator._init_client()
    provider = "vastai"
```

Provider priority: Modal > Vast.ai > Anthropic

## Migration Guide

### Migrating to Modal.com

To migrate from Vast.ai to Modal:

**Step 1: Deploy Modal Endpoint**
```bash
modal deploy src/vllm/modal/deployment.py
```

**Step 2: Update Environment Variables**
```bash
# Add Modal configuration
export MODAL_WEB_URL="https://yourorg--multi-agent-vllm-inference-serve.modal.run"

# Remove Vast.ai configuration (optional)
unset VASTAI_API_KEY
```

**Step 3: Restart Application**
```bash
docker compose restart fastapi
```

**Step 4: Destroy Existing Vast.ai Instances**
```bash
# Via API
curl -X POST https://your-domain.com/api/admin/vllm/destroy \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Or run cleanup script
python scripts/vastai/cleanup_orphaned_gpus.py
```

**Step 5: Verify Modal Backend**
```bash
curl https://your-domain.com/api/admin/vllm/status
```

Response should show provider as "modal".

### Configuration Removal

After migration, remove Vast.ai-specific environment variables:

```bash
# Required
VASTAI_API_KEY

# Optional (can be removed)
VASTAI_BUDGET_LIMIT
VASTAI_SESSION_BUDGET_LIMIT
VASTAI_DEFAULT_KEEP_ALIVE_MINUTES
VASTAI_MAX_STARTUP_TIME_MINUTES
VASTAI_AUTO_DESTROY_ON_ERROR
VASTAI_AUTO_DESTROY_ON_SHUTDOWN
VASTAI_HEALTH_CHECK_INTERVAL_SECONDS
VASTAI_SEARCH_TIMEOUT_SECONDS
VASTAI_MAX_SEARCH_RETRIES
```

### Cleanup Scripts

Remove cron jobs for Vast.ai maintenance:

```bash
# Remove budget monitoring
crontab -e
# Delete line: 0 */6 * * * python scripts/vastai/check_budget.py

# Remove orphaned instance cleanup
# Delete line: 0 4 * * * python scripts/vastai/cleanup_orphaned_gpus.py
```

## Troubleshooting Legacy Deployments

### CDI Injection Errors

Symptom: Container fails with "failed to inject CDI devices"
Cause: Incompatible NVIDIA driver or Docker version on host
Solution: No reliable fix. Migrate to Modal.

### Instance Stuck in Loading State

Symptom: Instance shows "loading" status for 10+ minutes
Cause: Host machine failed to start or Docker container crashed
Solution: Destroy instance and retry. If persistent, migrate to Modal.

### Health Check Failures

Symptom: vLLM health endpoint returns 404 or 500 errors
Cause: Port mapping issues or vLLM startup failure
Solution: Check instance logs via SSH. Verify port mapping in instance details.

### Orphaned Instances

Symptom: Vast.ai shows running instances but application shows no active instance
Cause: Application crashed before cleanup
Solution: Run cleanup script:
```bash
python scripts/vastai/cleanup_orphaned_gpus.py
```

### Budget Exceeded Errors

Symptom: Launch fails with "budget exceeded" error
Cause: Total spending reached VASTAI_BUDGET_LIMIT
Solution: Increase budget limit or wait for next billing period:
```bash
export VASTAI_BUDGET_LIMIT=30.0
```

## Performance Characteristics

### Latency

- Instance search: 5-15 seconds (varies by availability)
- Instance boot: 2-5 minutes (host startup)
- vLLM load: 5-10 minutes (model download and initialization)
- Total cold start: 7-15 minutes
- Warm request: <1 second (once running)

### Reliability

- Search success rate: 60-80% (depends on GPU availability)
- Instance boot success rate: 70-90% (varies by host reliability)
- Health check success rate: 85-95% (after successful boot)
- Overall launch success rate: 50-70%

### Costs

- RTX 3090: $0.14/hour (typical)
- RTX 4090: $0.18/hour (typical)
- A100: $0.50/hour (typical)
- Additional: Disk storage ($0.02/GB/month)

## Known Issues

### Issue: CDI Device Injection Failures

Status: UNRESOLVED (Critical)
Impact: Prevents GPU access in Docker containers
Workaround: None reliable
Resolution: Migrate to Modal.com

### Issue: Random Port Mapping

Status: DOCUMENTED (Minor)
Impact: Requires dynamic endpoint discovery
Workaround: Parse port mapping from instance API
Resolution: Modal uses fixed ports

### Issue: Inconsistent Startup Times

Status: DOCUMENTED (Moderate)
Impact: Unpredictable user experience
Workaround: Increase timeout to 15 minutes
Resolution: Modal cold start is consistent (10-30 seconds)

### Issue: Health Check Endpoint Mismatch

Status: RESOLVED
Impact: False-positive health failures
Workaround: Use /v1/models instead of /health
Resolution: Fixed in orchestrator.py line 505

## Reference Documentation

Vast.ai API Documentation: https://vast.ai/docs/api
Vast.ai Console: https://vast.ai/console
Vast.ai Marketplace: https://vast.ai/marketplace

## Support

For issues with legacy Vast.ai deployments, refer to application logs:
```bash
docker compose logs -f fastapi
```

For new deployments, use Modal.com instead (see docs/vllm/MODAL.md).

## Deprecation Timeline

- November 22, 2024: Vast.ai marked as deprecated
- November 22, 2024: Modal.com becomes recommended provider
- December 22, 2024: Vast.ai code moved to legacy package
- Future: Vast.ai code may be removed in a future release

Existing Vast.ai deployments will continue to function, but no new features or bug fixes will be implemented for Vast.ai. All development effort is now focused on Modal.com integration.
