# Modal vLLM Setup Guide

Complete guide for deploying vLLM on Modal.com as a serverless GPU backend.

**Migration from Vast.ai:** This implementation replaces Vast.ai's manual instance management with Modal's serverless architecture.

---

## Table of Contents

1. [Why Modal?](#why-modal)
2. [Prerequisites](#prerequisites)
3. [Modal Account Setup](#modal-account-setup)
4. [Local Installation](#local-installation)
5. [Deploy vLLM to Modal](#deploy-vllm-to-modal)
6. [Configure Application](#configure-application)
7. [Testing & Validation](#testing--validation)
8. [Cost Management](#cost-management)
9. [Troubleshooting](#troubleshooting)

---

## Why Modal?

Modal is a serverless platform that automatically manages GPU infrastructure:

| Feature | Modal (Serverless) | Vast.ai (Manual) |
|---------|-------------------|------------------|
| **Setup Time** | 5 minutes | 10+ hours (debugging) |
| **Instance Management** | Automatic | Manual search/launch/destroy |
| **Cold Start** | 10-30 seconds | 3-5 minutes |
| **Scaling** | Automatic | Manual |
| **Reliability** | 99.9% uptime | Variable (host-dependent) |
| **Pricing** | Pay-per-second | Pay-per-minute (minimum session) |
| **GPU Selection** | Automatic | Manual search across 10 configs |
| **Infrastructure Issues** | None (managed) | CDI errors, driver issues |

**Bottom Line:** Modal is production-ready, Vast.ai requires extensive debugging.

---

## Prerequisites

- **Operating System:** macOS, Linux, or Windows (WSL2)
- **Python:** 3.9+ (check: `python3 --version`)
- **Budget:** $15 USD (gives you ~36 hours of A100 usage on Starter plan)
- **Time:** 15 minutes for complete setup

---

## Modal Account Setup

### Step 1: Create Account

1. Go to [https://modal.com](https://modal.com)
2. Click "Sign Up" (top right)
3. Sign up with:
   - **GitHub** (recommended - instant auth)
   - **Google**
   - **Email**

4. Verify your email if using email signup

### Step 2: Choose Plan

Modal offers 3 plans:

#### ✅ **Starter Plan** (Recommended for $15 budget)

```
Cost: $0/month + compute usage
Included: $30/month free compute credits
GPU Concurrency: 10 concurrent requests
Perfect for: Testing, small workloads, $15 budget
```

**Your $15 budget gets:**
- ~36 hours of A100 (40GB) @ $3.00/hour
- ~24 hours of H100 (80GB) @ $4.50/hour
- Only charged when GPU is actively processing requests

#### Team Plan ($250/month + compute)

Only needed for:
- 30-day log retention
- 50+ concurrent GPU requests
- Production deployments with high traffic

#### Enterprise Plan (Custom pricing)

Only needed for:
- HIPAA compliance
- SSO
- Dedicated support

**For your use case:** Stick with **Starter Plan**. The $30 free credits cover your $15 budget entirely.

### Step 3: Add Payment Method (Optional)

1. Go to [https://modal.com/settings/billing](https://modal.com/settings/billing)
2. Click "Add payment method"
3. Enter credit card details
4. Set spending limit: **$15** (Budget enforcement)

**Note:** Modal won't charge you until you exceed the $30 free credits.

---

## Local Installation

### Step 1: Install Modal CLI

```bash
# Install Modal Python library
pip install modal

# Verify installation
modal --version
# Expected output: modal, version X.X.X
```

### Step 2: Authenticate

```bash
# Login to Modal
modal setup

# This will:
# 1. Open browser for authentication
# 2. Save token to ~/.modal.toml
# 3. Display success message
```

**Expected output:**
```
✓ Authenticated as your-username
✓ Token saved to ~/.modal.toml
```

### Step 3: Create API Token (Optional)

For programmatic access (deployment from CI/CD):

1. Go to [https://modal.com/settings/tokens](https://modal.com/settings/tokens)
2. Click "Create token"
3. Name: `multi-agent-vllm`
4. Copy the token ID and secret

**Save these for later:**
```bash
export MODAL_TOKEN_ID="ak-xxxxxxxxxxxxxxx"
export MODAL_TOKEN_SECRET="as-xxxxxxxxxxxxxxx"
```

---

## Deploy vLLM to Modal

### Step 1: Deploy vLLM Server

```bash
# Navigate to project root
cd /home/user/multi-agent-support-system

# Deploy vLLM to Modal (takes 2-3 minutes)
modal deploy src/vllm/modal_vllm.py
```

**Expected output:**
```
✓ Created objects.
├── 🔨 Created modal_vllm.serve => https://yourorg--modal-vllm-serve.modal.run
└── 🔨 Created modal_vllm.test
✓ App deployed! 🎉
```

**Save the URL:** `https://yourorg--modal-vllm-serve.modal.run`

### Step 2: Test Deployment

```bash
# Run Modal's built-in test
modal run src/vllm/modal_vllm.py::test
```

**Expected output:**
```
[Health Check] Running health check for https://...
✅ [Health Check] SUCCESS - Server is healthy

[Test 1] Sending request:
  Response: The capital of France is Paris.

[Test 2] Sending second request (tests caching):
  Response: 4

✅ [Modal vLLM Test] All tests passed!
```

### Step 3: Note Your Modal URL

The deployment creates a persistent endpoint:

```
https://yourorg--modal-vllm-serve.modal.run
```

**This URL:**
- ✅ Never changes (even after redeployments)
- ✅ Automatically scales GPUs on demand
- ✅ Returns responses in 10-30 seconds (cold start)
- ✅ Returns responses in <1 second (warm)

---

## Configure Application

### Step 1: Update Environment Variables

Add to your `.env` file:

```bash
# =============================================================================
# MODAL GPU CONFIGURATION
# =============================================================================

# Modal Web URL (from deployment - REQUIRED)
MODAL_WEB_URL=https://yourorg--modal-vllm-serve.modal.run

# Modal API Tokens (optional - only for programmatic deployment)
#MODAL_TOKEN_ID=ak-xxxxxxxxxxxxxxx
#MODAL_TOKEN_SECRET=as-xxxxxxxxxxxxxxx

# vLLM Model Configuration
MODAL_MODEL=Qwen/Qwen2.5-7B-Instruct
MODAL_GPU_TYPE=A100  # Options: A100 ($3/hr), H100 ($4.50/hr), A10G ($1/hr)
MODAL_SCALEDOWN_WINDOW_MINUTES=5  # Keep GPU warm for 5 min after last request

# Health Check Settings
MODAL_HEALTH_CHECK_TIMEOUT_SECONDS=30
MODAL_STARTUP_TIMEOUT_MINUTES=10
MODAL_MAX_RETRIES=3
MODAL_REQUEST_TIMEOUT_SECONDS=120
```

**Replace `yourorg` with your actual Modal URL!**

### Step 2: Verify Configuration

```bash
# Test that application can connect to Modal
python3 -c "
from src.core.config import get_settings
settings = get_settings()
print(f'Modal URL: {settings.modal.web_url}')
print(f'GPU Provider: Modal')
"
```

**Expected output:**
```
Modal URL: https://yourorg--modal-vllm-serve.modal.run
GPU Provider: Modal
```

---

## Testing & Validation

### Test 1: Health Check

```bash
# Test Modal orchestrator directly
python3 -m src.vllm.modal_orchestrator
```

**Expected output:**
```
[Test 1] Validate health...
✅ Health validation passed

[Test 2] Get status...
✅ Status: ready
   Endpoint: https://yourorg--modal-vllm-serve.modal.run/v1

✅ All tests passed!
```

### Test 2: Backend Manager Integration

```python
# Test via Python
python3 << EOF
import asyncio
from src.services.infrastructure.backend_manager import backend_manager

async def test():
    # Launch (configure) vLLM
    result = await backend_manager.launch_vllm_gpu()
    print(f"Launch result: {result}")

    # Get status
    status = await backend_manager.get_vllm_status()
    print(f"Status: {status}")

asyncio.run(test())
EOF
```

**Expected output:**
```
Launch result: {
  'success': True,
  'provider': 'modal',
  'status': 'ready',
  'endpoint': 'https://yourorg--modal-vllm-serve.modal.run/v1',
  'message': 'Modal vLLM endpoint configured and ready'
}

Status: {
  'provider': 'modal',
  'status': 'ready',
  'endpoint': 'https://yourorg--modal-vllm-serve.modal.run/v1',
  'uptime_hours': 0.01
}
```

### Test 3: End-to-End Request

```bash
# Make a test request via API
curl -X POST http://localhost:8000/api/admin/vllm/launch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check status
curl http://localhost:8000/api/admin/vllm/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected:**
```json
{
  "provider": "modal",
  "status": "ready",
  "endpoint": "https://yourorg--modal-vllm-serve.modal.run/v1",
  "uptime_hours": 0.5,
  "total_requests": 0
}
```

---

## Cost Management

### Pricing Breakdown

**Modal Starter Plan:**
```
Base: $0/month
Included: $30/month free compute credits
Pay-per-second of GPU usage
```

**GPU Costs (as of 2025):**

| GPU Type | VRAM | Cost/Hour | Cost/Second | Your Budget Gets |
|----------|------|-----------|-------------|------------------|
| **A100** | 40GB | $3.00 | $0.000833 | ~36 hours |
| **H100** | 80GB | $4.50 | $0.00125 | ~24 hours |
| **A10G** | 24GB | $1.00 | $0.000278 | ~108 hours |

**Recommendation:** Use A100 (good balance of performance and cost).

### Spending Limits

Set spending limits in Modal dashboard:

1. Go to [https://modal.com/settings/billing](https://modal.com/settings/billing)
2. Click "Set spending limit"
3. Enter: **$15.00**
4. Save

Modal will:
- ✅ Send email alert at 80% ($12)
- ✅ Send email alert at 100% ($15)
- ✅ Pause deployments at limit
- ✅ Never exceed your limit

### Cost Optimization Tips

1. **Use Scaledown Window:**
   ```python
   MODAL_SCALEDOWN_WINDOW_MINUTES=5
   ```
   - Keeps GPU warm for 5 minutes after last request
   - Avoids cold starts for back-to-back requests
   - Balance: Lower = cheaper, Higher = faster

2. **Monitor Usage:**
   ```bash
   # View usage in real-time
   modal app logs multi-agent-vllm-inference

   # Check spending
   # Go to: https://modal.com/settings/billing/usage
   ```

3. **Choose Right GPU:**
   - **Development:** A10G ($1/hr) - cheapest
   - **Production:** A100 ($3/hr) - best value
   - **High Performance:** H100 ($4.50/hr) - fastest

### Example Cost Calculation

**Scenario:** Support system handles 100 requests/day

```
Request pattern:
- 100 requests/day
- ~30 seconds per request
- Scaledown window: 5 minutes

Daily GPU time:
- Active inference: 100 * 30s = 3000s = 50 minutes
- Keep-alive overhead: ~2 hours (gaps between requests)
- Total: ~2.83 hours/day

Daily cost (A100 @ $3/hr):
- 2.83 hours * $3 = $8.49/day

Your $15 budget lasts:
- $15 / $8.49 = ~1.7 days of continuous operation
```

**For $15/month budget:**
- Limit to ~15-20 requests/day
- Or use A10G: ~60 requests/day

---

## Troubleshooting

### Issue: "Modal web URL not configured"

**Error:**
```
ValueError: Modal web URL not configured
```

**Fix:**
```bash
# Add to .env
MODAL_WEB_URL=https://yourorg--modal-vllm-serve.modal.run
```

### Issue: "Modal endpoint is not healthy"

**Possible Causes:**

1. **vLLM not deployed**
   ```bash
   # Deploy vLLM
   modal deploy src/vllm/modal_vllm.py
   ```

2. **Wrong URL in .env**
   ```bash
   # Check your URL matches deployment output
   modal app list
   # Copy the correct URL to .env
   ```

3. **Modal service is cold-starting**
   - Wait 30 seconds and try again
   - Cold starts take 10-30 seconds

### Issue: "Authentication failed"

**Fix:**
```bash
# Re-authenticate
modal setup

# Verify
modal app list
```

### Issue: "Spending limit reached"

**Check usage:**
```bash
# Go to: https://modal.com/settings/billing/usage
# View current spending
```

**Fix:**
1. Wait until next billing cycle (monthly reset)
2. Or increase spending limit
3. Or reduce request volume

### Issue: "ImportError: No module named 'modal'"

**Fix:**
```bash
# Install Modal
pip install modal

# Verify
modal --version
```

---

## Production Checklist

Before going live:

- [ ] ✅ Modal account created
- [ ] ✅ Payment method added
- [ ] ✅ Spending limit set to $15
- [ ] ✅ Modal CLI installed (`pip install modal`)
- [ ] ✅ Authenticated (`modal setup`)
- [ ] ✅ vLLM deployed (`modal deploy src/vllm/modal_vllm.py`)
- [ ] ✅ Deployment tested (`modal run src/vllm/modal_vllm.py::test`)
- [ ] ✅ `.env` configured with `MODAL_WEB_URL`
- [ ] ✅ Backend manager tested (health check passes)
- [ ] ✅ End-to-end API test successful
- [ ] ✅ Monitoring dashboard bookmarked (https://modal.com/apps)

---

## Next Steps

1. **Monitor Usage:**
   - Dashboard: https://modal.com/apps
   - Logs: `modal app logs multi-agent-vllm-inference`

2. **Optimize Costs:**
   - Start with A10G ($1/hr) for development
   - Switch to A100 ($3/hr) for production
   - Adjust scaledown window based on traffic pattern

3. **Scale Up:**
   - Modal automatically handles increased traffic
   - No code changes needed
   - Just monitor spending

4. **Production Hardening:**
   - Set up alerts in Modal dashboard
   - Configure backup models
   - Implement rate limiting

---

## Resources

- **Modal Documentation:** https://modal.com/docs
- **Modal vLLM Example:** https://modal.com/docs/examples/vllm_inference
- **Support:** https://modal.com/slack (join Modal Community Slack)
- **Pricing:** https://modal.com/pricing
- **Status Page:** https://status.modal.com

---

## Comparison: Modal vs Vast.ai

| Aspect | Modal (Implemented) | Vast.ai (Previous) |
|--------|-------------------|-------------------|
| **Setup Time** | 5 minutes | 10+ hours |
| **Debugging Required** | None | Extensive (CDI errors, ports, etc.) |
| **Instance Management** | Automatic | Manual (search, launch, destroy) |
| **Code Complexity** | 200 lines | 2000+ lines |
| **Reliability** | ✅ Production-ready | ❌ Host-dependent |
| **Cost Tracking** | Built-in dashboard | Manual budget enforcement |
| **Scaling** | Automatic | Manual |
| **GPU Selection** | Automatic | Manual 10-config fallback |
| **Infrastructure Issues** | None | CDI errors, driver issues |

**Result:** Modal saved 10+ hours of debugging and provides production-ready infrastructure.

---

## Support

**Questions?**
- File an issue: https://github.com/OthmanMohammad/multi-agent-support-system/issues
- Modal Community: https://modal.com/slack

**Need help?**
- Check Modal docs: https://modal.com/docs
- Review logs: `modal app logs multi-agent-vllm-inference`
- Test health: `modal run src/vllm/modal_vllm.py::test`
