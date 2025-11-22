# vLLM GPU Orchestration - Quick Reference

## Quick Start

Run the full test suite:
```bash
./test_vllm.sh
```

Or use individual commands below:

---

## 1. Authentication

### Register User
```bash
curl -k -X POST https://129.159.141.19/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vllm-test@example.com",
    "password": "TestPass123!",
    "full_name": "vLLM Tester"
  }' | jq
```

### Login (if already registered)
```bash
TOKEN=$(curl -k -s -X POST https://129.159.141.19/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vllm-test@example.com",
    "password": "TestPass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

## 2. vLLM Instance Management

### Check Status
```bash
curl -k https://129.159.141.19/api/admin/vllm/status \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response (when idle):**
```json
{
  "status": "idle",
  "instance": null,
  "runtime_minutes": 0,
  "estimated_cost": 0,
  "keep_alive_until": null
}
```

**Expected Response (when running):**
```json
{
  "status": "running",
  "instance": {
    "instance_id": 28109876,
    "gpu_name": "RTX 3090",
    "cost_per_hour": 0.15,
    "endpoint": "http://216.155.221.130:45123"
  },
  "runtime_minutes": 5.2,
  "estimated_cost": 0.013,
  "keep_alive_until": "2025-11-22T15:30:00Z"
}
```

### Launch GPU Instance
```bash
curl -k -X POST https://129.159.141.19/api/admin/vllm/launch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keep_alive_minutes": 15,
    "auto_switch": true
  }' | jq
```

**Parameters:**
- `keep_alive_minutes`: How long to keep instance alive (default: 10)
- `auto_switch`: Automatically switch from LiteLLM to vLLM when ready (default: true)

**Expected Response:**
```json
{
  "message": "GPU instance launching",
  "instance": {
    "instance_id": 28109876,
    "gpu_name": "RTX 3090",
    "cost_per_hour": 0.15
  },
  "estimated_startup_time_seconds": 180
}
```

### Monitor Launch Progress
```bash
# Run every 20 seconds until status == "running"
watch -n 20 'curl -k -s https://129.159.141.19/api/admin/vllm/status \
  -H "Authorization: Bearer $TOKEN" | jq "{status, gpu: .instance.gpu_name, endpoint: .instance.endpoint}"'
```

### Extend Keep-Alive
```bash
curl -k -X POST https://129.159.141.19/api/admin/vllm/extend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_minutes": 10
  }' | jq
```

### Destroy Instance
```bash
curl -k -X POST https://129.159.141.19/api/admin/vllm/destroy \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "message": "GPU instance destroyed",
  "instance_id": 28109876,
  "final_runtime_minutes": 12.5,
  "total_cost": 0.03125
}
```

---

## 3. Test AI Conversation

### Send Message (will auto-launch GPU if needed)
```bash
curl -k -X POST https://129.159.141.19/api/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "message": "What are your business hours?"
  }' | jq
```

**Expected Response:**
```json
{
  "conversation_id": "conv_123456",
  "customer_email": "customer@example.com",
  "message": "What are your business hours?",
  "response": "Our business hours are Monday through Friday...",
  "metadata": {
    "model": "vllm-vast-ai",
    "response_time_ms": 450,
    "cost": 0.00012
  }
}
```

### List Conversations
```bash
curl -k https://129.159.141.19/api/conversations \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 4. Cost Tracking

### Get Detailed Costs
```bash
curl -k https://129.159.141.19/api/admin/costs \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "gpu_orchestration": {
    "total": 0.125,
    "current_instance": 0.0325,
    "total_instances_launched": 3,
    "total_runtime_minutes": 47.5
  },
  "llm_api_calls": {
    "total": 0.0045,
    "total_calls": 15
  },
  "total": 0.1295
}
```

---

## 5. Direct vLLM API Access

Once the instance is running, you can access vLLM directly:

### Get Endpoint
```bash
ENDPOINT=$(curl -k -s https://129.159.141.19/api/admin/vllm/status \
  -H "Authorization: Bearer $TOKEN" | jq -r '.instance.endpoint')

echo "vLLM Endpoint: $ENDPOINT"
```

### List Available Models
```bash
curl -s ${ENDPOINT}/v1/models | jq
```

### Chat Completion
```bash
curl -s -X POST ${ENDPOINT}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [
      {"role": "user", "content": "Hello! How are you?"}
    ],
    "max_tokens": 100
  }' | jq
```

---

## 6. Troubleshooting

### Check Backend Logs
```bash
doppler run -- docker compose logs -f backend
```

### Check Database
```bash
doppler run -- docker compose exec backend python -c "
from src.database import get_db
from src.models import User, Conversation, CostTracking
from sqlalchemy import func

db = next(get_db())
print('Users:', db.query(func.count(User.id)).scalar())
print('Conversations:', db.query(func.count(Conversation.id)).scalar())
print('Cost Records:', db.query(func.count(CostTracking.id)).scalar())
"
```

### Check Vast.ai Connection
```bash
doppler run -- docker compose exec backend python -c "
import asyncio
from src.vllm.vastai_client import VastAIClient
import os

async def test():
    client = VastAIClient(os.getenv('VASTAI_API_KEY'))
    instances = await client.get_instances()
    print(f'Active instances: {len(instances)}')
    for inst in instances:
        print(f'  - ID: {inst[\"id\"]}, Status: {inst.get(\"actual_status\")}')

asyncio.run(test())
"
```

### Manually Destroy Stuck Instance
```bash
doppler run -- docker compose exec backend python -c "
import asyncio
from src.vllm.vastai_client import VastAIClient
import os

async def destroy(instance_id):
    client = VastAIClient(os.getenv('VASTAI_API_KEY'))
    await client.destroy_instance(instance_id)
    print(f'Destroyed instance {instance_id}')

asyncio.run(destroy(28109576))  # Replace with your instance ID
"
```

---

## Expected Workflow

1. **Launch GPU** → Takes 3-5 minutes
   - Searches 10 GPU types (RTX 3090 → RTX 3080)
   - Scores offers by price, reliability, network speed
   - Launches best offer
   - Waits for vLLM to be ready

2. **Use vLLM** → Instant responses
   - Send messages via `/api/conversations`
   - Costs ~$0.001-0.003 per message
   - Keep-alive timer resets on each use

3. **Auto-Destroy** → After idle timeout
   - No activity for X minutes
   - Instance destroyed automatically
   - Total cost tracked in database

---

## Budget Limits

Current limits (configured in code):
- **Per instance**: $5.00
- **Daily total**: $50.00
- **Monthly total**: $500.00

Launches blocked if budget would be exceeded.
