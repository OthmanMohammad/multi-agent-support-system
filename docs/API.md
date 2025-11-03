# Multi-Agent Support API Documentation

## Overview

REST API for intelligent customer support with multi-agent routing.

**Base URL**: `http://localhost:8000`
**Documentation**: `http://localhost:8000/docs` (Swagger UI)

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if API is healthy.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agents_loaded": ["router", "billing", "technical", "usage", "escalation"],
  "qdrant_connected": true,
  "timestamp": "2025-01-15T10:30:00"
}
```

---

### 2. Chat (Non-Streaming)

**POST** `/chat`

Send a message and get immediate response.

**Request:**
```json
{
  "message": "I want to upgrade to premium",
  "conversation_id": "optional-conv-id",
  "customer_id": "user123",
  "stream": false
}
```

**Response:**
```json
{
  "conversation_id": "abc-123-def",
  "message": "Great! I'd be happy to help you upgrade...",
  "intent": "billing_upgrade",
  "confidence": 0.95,
  "agent_path": ["router", "billing"],
  "kb_articles_used": ["How to Upgrade Your Plan"],
  "status": "resolved",
  "timestamp": "2025-01-15T10:30:00"
}
```

---

### 3. Chat (Streaming)

**POST** `/chat/stream`

Send message and get streaming response (Server-Sent Events).

**Request:** Same as `/chat`

**Response:** SSE stream
```
event: conversation_id
data: abc-123-def

event: thinking
data: Processing your request...

event: intent
data: billing_upgrade

event: agent_path
data: router → billing

event: message
data: Great! I'd be happy to help...

event: done
data: complete
```

**Client Example (JavaScript):**
```javascript
const eventSource = new EventSource('/chat/stream');

eventSource.addEventListener('message', (e) => {
  console.log('Chunk:', e.data);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});
```

---

### 4. Get Conversation

**GET** `/conversations/{conversation_id}`

Get full conversation history.

**Response:**
```json
{
  "conversation_id": "abc-123-def",
  "customer_id": "user123",
  "messages": [
    {
      "role": "user",
      "content": "I want to upgrade",
      "timestamp": "2025-01-15T10:30:00",
      "agent_name": null
    },
    {
      "role": "assistant",
      "content": "Great! I'd be happy...",
      "timestamp": "2025-01-15T10:30:05",
      "agent_name": "billing"
    }
  ],
  "agent_history": ["router", "billing"],
  "status": "resolved",
  "started_at": "2025-01-15T10:30:00",
  "last_updated": "2025-01-15T10:30:05"
}
```

---

### 5. List Conversations

**GET** `/conversations?customer_id=user123&limit=50`

List recent conversations.

**Query Parameters:**
- `customer_id` (optional): Filter by customer
- `limit` (optional): Max results (default: 50)

**Response:** Array of conversations

---

### 6. Metrics

**GET** `/metrics`

Get system metrics.

**Response:**
```json
{
  "total_conversations": 145,
  "total_messages": 423,
  "intent_distribution": {
    "billing_upgrade": 45,
    "technical_sync": 32
  },
  "agent_usage": {
    "router": 145,
    "billing": 78,
    "technical": 45
  },
  "avg_confidence": 0.87,
  "uptime_seconds": 86400
}
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "detail": "Validation error message"
}
```

**404 Not Found:**
```json
{
  "detail": "Conversation not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error message"
}
```

---

## Usage Examples

### Python (requests)
```python
import requests

# Chat
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "I want to upgrade to premium"}
)

data = response.json()
print(data['message'])
```

### cURL
```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to upgrade to premium"}'

# Health
curl http://localhost:8000/health
```

### JavaScript (fetch)
```javascript
// Chat
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'I want to upgrade'})
});

const data = await response.json();
console.log(data.message);
```

---

## Rate Limiting

Currently: **No rate limiting** (development)

Production TODO:
- 100 requests/minute per IP
- 1000 requests/hour per customer

---

## Authentication

Currently: **None** (development)

Production TODO:
- API keys
- JWT tokens
- OAuth 2.0

---

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start API
python src/api/main.py

# Or with uvicorn
uvicorn src.api.main:app --reload --port 8000
```

### Production (Docker)
```bash
# Build image
docker build -t support-api .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-xxx \
  -e QDRANT_URL=https://xxx.qdrant.io \
  -e QDRANT_API_KEY=xxx \
  support-api
```

---

## Next Steps

- [ ] Add PostgreSQL for persistence
- [ ] Add Redis for caching
- [ ] Add authentication
- [ ] Add rate limiting
- [ ] Add monitoring (Prometheus)
- [ ] Add CI/CD pipeline