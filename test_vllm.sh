#!/bin/bash

set -e

API_URL="https://129.159.141.19"
EMAIL="vllm-test@example.com"
PASSWORD="TestPass123!"

echo "========================================="
echo "vLLM GPU Orchestration Test Suite"
echo "========================================="
echo ""

# 1. Register/Login
echo "=== Step 1: Authentication ==="
RESPONSE=$(curl -k -s -X POST ${API_URL}/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\",
    \"full_name\": \"vLLM Tester\"
  }")

TOKEN=$(echo $RESPONSE | jq -r '.access_token')

# If registration fails, try login
if [ "$TOKEN" == "null" ]; then
  echo "User exists, logging in..."
  RESPONSE=$(curl -k -s -X POST ${API_URL}/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"${EMAIL}\",
      \"password\": \"${PASSWORD}\"
    }")

  TOKEN=$(echo $RESPONSE | jq -r '.access_token')
fi

if [ "$TOKEN" == "null" ]; then
  echo "❌ Authentication failed!"
  echo $RESPONSE | jq
  exit 1
fi

echo "✅ Authenticated successfully"
echo "Token: ${TOKEN:0:20}..."
echo ""

# 2. Check initial vLLM status
echo "=== Step 2: Check Initial vLLM Status ==="
curl -k -s ${API_URL}/api/admin/vllm/status \
  -H "Authorization: Bearer $TOKEN" | jq '{
    status: .status,
    instance_id: .instance.instance_id,
    gpu: .instance.gpu_name,
    endpoint: .instance.endpoint
  }'
echo ""

# 3. Launch GPU instance
echo "=== Step 3: Launching GPU Instance ==="
echo "This will search for the best GPU offer and launch vLLM..."
LAUNCH_RESPONSE=$(curl -k -s -X POST ${API_URL}/api/admin/vllm/launch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keep_alive_minutes": 15,
    "auto_switch": true
  }')

echo $LAUNCH_RESPONSE | jq
echo ""

# Extract instance ID
INSTANCE_ID=$(echo $LAUNCH_RESPONSE | jq -r '.instance.instance_id')

if [ "$INSTANCE_ID" == "null" ]; then
  echo "❌ Failed to launch GPU instance"
  exit 1
fi

echo "✅ GPU instance launched: $INSTANCE_ID"
echo ""

# 4. Monitor status (check every 20 seconds for up to 8 minutes)
echo "=== Step 4: Monitoring Launch Progress ==="
echo "Waiting for vLLM to be ready (this can take 3-5 minutes)..."
echo ""

MAX_ATTEMPTS=24
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))

  STATUS=$(curl -k -s ${API_URL}/api/admin/vllm/status \
    -H "Authorization: Bearer $TOKEN")

  CURRENT_STATUS=$(echo $STATUS | jq -r '.status')
  GPU_NAME=$(echo $STATUS | jq -r '.instance.gpu_name')
  ENDPOINT=$(echo $STATUS | jq -r '.instance.endpoint')
  RUNTIME=$(echo $STATUS | jq -r '.runtime_minutes')
  COST=$(echo $STATUS | jq -r '.estimated_cost')

  echo "[$ATTEMPT/$MAX_ATTEMPTS] Status: $CURRENT_STATUS | GPU: $GPU_NAME | Runtime: ${RUNTIME}min | Cost: \$${COST}"

  # Check if running
  if [ "$CURRENT_STATUS" == "running" ] && [ "$ENDPOINT" != "null" ]; then
    echo ""
    echo "✅ vLLM is ready!"
    echo "   Endpoint: $ENDPOINT"
    echo "   GPU: $GPU_NAME"
    echo "   Runtime: ${RUNTIME} minutes"
    echo "   Estimated Cost: \$${COST}"
    echo ""
    break
  fi

  # Check if failed
  if [ "$CURRENT_STATUS" == "failed" ] || [ "$CURRENT_STATUS" == "error" ]; then
    echo ""
    echo "❌ Launch failed!"
    echo $STATUS | jq
    exit 1
  fi

  sleep 20
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo ""
  echo "⚠️  Timeout waiting for vLLM to be ready"
  echo "Current status:"
  echo $STATUS | jq
  exit 1
fi

# 5. Test conversation with vLLM
echo "=== Step 5: Testing AI Conversation ==="
CONV_RESPONSE=$(curl -k -s -X POST ${API_URL}/api/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "message": "Hello! Can you help me with a product question?"
  }')

echo $CONV_RESPONSE | jq '{
  conversation_id: .conversation_id,
  customer_email: .customer_email,
  response: .response,
  model_used: .metadata.model,
  response_time_ms: .metadata.response_time_ms
}'
echo ""

# 6. Check detailed costs
echo "=== Step 6: Cost Tracking ==="
COSTS=$(curl -k -s ${API_URL}/api/admin/costs \
  -H "Authorization: Bearer $TOKEN")

echo $COSTS | jq '{
  gpu_orchestration: {
    total: .gpu_orchestration.total,
    current_instance: .gpu_orchestration.current_instance,
    total_instances: .gpu_orchestration.total_instances_launched,
    total_runtime: .gpu_orchestration.total_runtime_minutes
  },
  llm_api_calls: {
    total: .llm_api_calls.total,
    total_calls: .llm_api_calls.total_calls
  },
  grand_total: .total
}'
echo ""

# 7. Test keep-alive extension
echo "=== Step 7: Testing Keep-Alive Extension ==="
EXTEND_RESPONSE=$(curl -k -s -X POST ${API_URL}/api/admin/vllm/extend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_minutes": 10
  }')

echo $EXTEND_RESPONSE | jq
echo ""

# 8. Final status check
echo "=== Step 8: Final Status Check ==="
curl -k -s ${API_URL}/api/admin/vllm/status \
  -H "Authorization: Bearer $TOKEN" | jq '{
    status: .status,
    instance_id: .instance.instance_id,
    gpu: .instance.gpu_name,
    endpoint: .instance.endpoint,
    runtime_minutes: .runtime_minutes,
    cost_per_hour: .instance.cost_per_hour,
    estimated_total_cost: .estimated_cost,
    keep_alive_until: .keep_alive_until
  }'
echo ""

# 9. Optional: Destroy instance (uncomment to auto-destroy)
# echo "=== Step 9: Destroying GPU Instance ==="
# curl -k -s -X POST ${API_URL}/api/admin/vllm/destroy \
#   -H "Authorization: Bearer $TOKEN" | jq
# echo ""

echo "========================================="
echo "✅ Test Suite Completed Successfully!"
echo "========================================="
echo ""
echo "Instance $INSTANCE_ID is still running."
echo "To manually destroy it, run:"
echo ""
echo "curl -k -X POST ${API_URL}/api/admin/vllm/destroy \\"
echo "  -H \"Authorization: Bearer $TOKEN\""
echo ""
