# 🧪 Manual Testing Guide - Multi-Agent Support System

**Last Updated:** 2025-11-17
**Status:** Ready for Manual Testing

---

## 🚀 Quick Start - Test Your System!

### **Step 1: Set Up Environment Variables**

Create a `.env` file in the project root:

```bash
# Copy example and edit
cp .env.example .env
```

**Minimum Required Variables:**
```env
# Environment
ENVIRONMENT=staging

# CORS (for local testing)
API_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000"]

# Database (install PostgreSQL first)
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/support_agent

# Anthropic API (REQUIRED - get from https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Qdrant Vector Store (optional for testing, required for KB features)
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# JWT Secret (any random 32+ character string)
JWT_SECRET_KEY=change-this-to-a-long-random-string-min-32-chars

# Sentry (optional for testing)
SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/your-project

# Redis (optional - will use in-memory if not available)
REDIS_URL=redis://localhost:6379
```

---

### **Step 2: Install & Setup Database**

```bash
# Activate virtual environment
cd C:\Users\Lenovo\Desktop\multi-agent-support-system
venv\Scripts\activate

# Install PostgreSQL (if not already installed)
# Download from: https://www.postgresql.org/download/windows/

# Create database
psql -U postgres
CREATE DATABASE support_agent;
\q

# Run migrations
alembic upgrade head

# (Optional) Seed database with sample data
python seed_database.py
```

---

### **Step 3: Start the API Server**

```bash
# From project root
python src/api/main.py

# Or with uvicorn directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### **Step 4: Test API is Running**

Open browser and visit:
- **API Status:** http://localhost:8000/
- **API Docs:** http://localhost:8000/api/docs (Interactive Swagger UI)
- **Health Check:** http://localhost:8000/api/health

---

## 📝 Testing Scenarios

### **Scenario 1: Simple Billing Question (Single Agent)**

**What happens:** Customer asks billing question → Billing specialist agent responds

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"test@example.com\",
    \"message\": \"How do I update my payment method?\"
  }"
```

**Expected Response:**
```json
{
  "conversation_id": "uuid-here",
  "message": "Here's how to update your payment method...",
  "agent_used": "payment_method_updater",
  "status": "resolved",
  "confidence": 0.9
}
```

**What to Check:**
- ✅ Conversation created successfully
- ✅ Agent detected the billing intent
- ✅ Response is helpful and accurate
- ✅ Status is "resolved"

---

### **Scenario 2: Technical Issue (Agent Routing)**

**What happens:** Technical question → Router → Technical specialist

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"tech-user@example.com\",
    \"message\": \"I can't log in, I forgot my password\"
  }"
```

**Expected:**
- Router agent analyzes the message
- Routes to `login_specialist` agent
- Login specialist provides password reset steps

**What to Check:**
- ✅ Correct agent was selected (login_specialist)
- ✅ Response includes password reset instructions
- ✅ Agent history shows routing path

---

### **Scenario 3: Complex Query (Multi-Agent Collaboration)**

**What happens:** Complex question → Coordinator → Multiple agents collaborate

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/workflows/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"pattern\": \"expert_panel\",
    \"message\": \"I want to upgrade my plan and also need help with API integration\",
    \"agents\": [\"plan_upgrade\", \"technical_support\", \"api_specialist\"],
    \"customer_id\": \"power-user@example.com\"
  }"
```

**Expected:**
- Coordinator orchestrates multiple agents
- plan_upgrade agent discusses upgrade options
- technical_support helps with setup
- api_specialist provides integration guidance
- Final synthesized response from all agents

**What to Check:**
- ✅ Multiple agents executed
- ✅ Each agent contributed their expertise
- ✅ Final response is coherent and complete
- ✅ Agent history shows all agents involved

---

### **Scenario 4: Escalation Flow**

**What happens:** Complex issue → Agent can't handle → Escalates

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"enterprise@company.com\",
    \"message\": \"I need a 50% discount for our nonprofit organization\"
  }"
```

**Expected:**
- Discount negotiator agent processes request
- Realizes 50% is above approval limit (30%)
- Escalates to human sales team
- Provides escalation reason

**What to Check:**
- ✅ Status is "escalated"
- ✅ Escalation reason is provided
- ✅ Next_agent is set to human team
- ✅ Should_escalate flag is true

---

### **Scenario 5: Knowledge Base Search**

**What happens:** Question that needs KB lookup → KB search → Answer with citations

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"curious@example.com\",
    \"message\": \"What are the features of the Pro plan?\"
  }"
```

**Expected:**
- Agent searches knowledge base
- Finds relevant articles about Pro plan
- Returns answer with KB citations
- Includes links to help articles

**What to Check:**
- ✅ kb_results array has entries
- ✅ Response includes plan features
- ✅ Citations/links included
- ✅ Confidence score indicates KB match

---

## 🔍 Testing with Swagger UI (Easier!)

**Go to:** http://localhost:8000/api/docs

### **Step-by-Step:**

1. **Create a conversation:**
   - Click `/api/conversations` → `POST`
   - Click "Try it out"
   - Fill in the request body:
     ```json
     {
       "customer_id": "test@example.com",
       "message": "How much does the Pro plan cost?"
     }
     ```
   - Click "Execute"
   - See the response!

2. **Get conversation history:**
   - Copy the `conversation_id` from the response
   - Click `/api/conversations/{conversation_id}` → `GET`
   - Click "Try it out"
   - Paste the conversation_id
   - Click "Execute"
   - See all messages in the conversation!

3. **List all agents:**
   - Click `/api/agents` → `GET`
   - Click "Try it out"
   - Click "Execute"
   - See all 224 available agents!

4. **Execute specific agent:**
   - Click `/api/agents/{agent_name}/execute` → `POST`
   - Try agent_name: `pricing_explainer`
   - Message: "Compare Basic and Pro plans"
   - Click "Execute"

---

## 🎯 What to Look For During Testing

### **✅ Success Indicators:**

1. **Agent Selection:**
   - Correct agent chosen for query type
   - Agent history shows routing path
   - Intent detection is accurate

2. **Response Quality:**
   - Answers are helpful and accurate
   - Tone is professional
   - Includes actionable next steps
   - Cites sources when appropriate

3. **Multi-Agent Collaboration:**
   - Multiple agents work together seamlessly
   - Each contributes their expertise
   - Final response is synthesized well
   - No contradictions between agents

4. **Escalation Logic:**
   - Escalates when appropriate
   - Provides clear escalation reason
   - Sets correct next_agent
   - Maintains conversation context

5. **Performance:**
   - Responses in < 5 seconds
   - No timeouts
   - Database queries efficient
   - LLM calls complete successfully

---

## 🐛 Common Issues & Solutions

### **Issue: "Database connection failed"**
**Solution:**
- Check PostgreSQL is running: `pg_ctl status`
- Verify DATABASE_URL in .env
- Run migrations: `alembic upgrade head`

### **Issue: "ANTHROPIC_API_KEY invalid"**
**Solution:**
- Get valid key from https://console.anthropic.com/
- Make sure no extra spaces in .env file
- Key should start with `sk-ant-`

### **Issue: "Agent not found"**
**Solution:**
- Check agent name spelling
- List available agents: `GET /api/agents`
- Some agents may not be registered yet

### **Issue: "CORS error in browser"**
**Solution:**
- Add your frontend URL to API_CORS_ORIGINS
- Must be JSON array format: `["http://localhost:3000"]`
- Restart API server after changing .env

### **Issue: "Rate limit exceeded"**
**Solution:**
- Wait 60 seconds
- Or disable rate limiting in .env: `API_RATE_LIMIT_ENABLED=false`
- Or increase limit: `API_RATE_LIMIT_REQUESTS=1000`

---

## 📊 Monitoring Your Tests

### **Check Logs:**
```bash
# Logs are in stdout
# Watch for these events:
# - agent_execution_started
# - agent_execution_completed
# - llm_call_made
# - kb_search_performed
# - escalation_triggered
```

### **Database Queries:**
```sql
-- Check conversations created
SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;

-- Check messages
SELECT * FROM messages ORDER BY created_at DESC LIMIT 20;

-- Check agent usage
SELECT agent_name, COUNT(*) as usage_count
FROM agent_executions
GROUP BY agent_name
ORDER BY usage_count DESC;
```

---

## 🎉 Success Criteria

Your system is working if:

✅ **API starts without errors**
✅ **Health endpoint returns 200**
✅ **Can create conversations**
✅ **Agents respond to messages**
✅ **Correct agents are selected for queries**
✅ **Multi-agent workflows execute**
✅ **Escalation logic works**
✅ **Database records are created**
✅ **LLM calls succeed (no 404 errors)**
✅ **Responses are helpful and accurate**

---

## 🚀 Next: Build a Frontend!

Once API testing works, you can:

1. **Build a React/Next.js frontend**
2. **Connect via REST API**
3. **Show conversation UI**
4. **Display agent responses**
5. **Show agent collaboration in real-time**

**Example Frontend Flow:**
```javascript
// Create conversation
const response = await fetch('http://localhost:8000/api/conversations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    customer_id: 'user@example.com',
    message: 'How do I upgrade my plan?'
  })
});

const data = await response.json();
console.log('Agent response:', data.message);
console.log('Agent used:', data.agent_used);
```

---

## 📞 Need Help?

If you encounter issues:
1. Check the logs in console
2. Verify all environment variables are set
3. Ensure database is running
4. Check API_CORS_ORIGINS includes your frontend URL
5. Review the error message carefully

---

**Happy Testing! 🎉**
