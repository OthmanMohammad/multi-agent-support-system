---
name: 🔄 Celery Background Processing System
about: Distributed task queue for long-running workflows, scheduled tasks, and asynchronous operations
title: '[SUB-ISSUE] Implement Celery Background Processing'
labels: ['sub-issue', 'celery', 'async', 'priority:high']
assignees: []
---

# 🔄 Celery Background Processing System

> **Issue ID:** CICD-003
> **Parent Epic:** CICD-001 (CI/CD Pipeline)
> **Priority:** High
> **Estimated Effort:** 1-2 weeks
> **Team:** Backend / Infrastructure

---

## 📋 Overview

### Purpose
Implement a **production-grade distributed task queue** using Celery with Redis as the message broker. This system will handle long-running operations, scheduled tasks, and asynchronous processing that would otherwise block API responses or tie up server resources.

### Business Value
| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| **API Response Time** | Blocked by long tasks | <200ms always | **Instant responses** |
| **Task Reliability** | Lost on server restart | Persisted & retryable | **100% reliability** |
| **Concurrent Processing** | Single-threaded | Distributed workers | **10x throughput** |
| **Scheduled Tasks** | Manual/cron hacks | Automated scheduler | **Zero manual work** |
| **Observability** | No visibility | Real-time monitoring | **Full visibility** |

### Why Celery?
Your multi-agent system has **243 specialized agents** that can execute complex workflows taking **2-30 minutes**. Running these synchronously in API requests would:
- ❌ Timeout requests (30-60 second limits)
- ❌ Tie up precious worker threads
- ❌ Block other users from getting responses
- ❌ Have no retry mechanism on failure

**Celery solves all of this.** ✅

---

## 🏗️ Architecture

### System Design

```
┌───────────────────────────────────────────────────────────────┐
│                       CLIENT REQUEST                           │
│  POST /api/workflows/execute                                   │
│  {                                                             │
│    "workflow_type": "debate",                                  │
│    "query": "Should we use microservices?"                     │
│  }                                                             │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────────┐
│                      FASTAPI (Async)                           │
│  @app.post("/api/workflows/execute")                          │
│  async def execute_workflow(request: WorkflowRequest):        │
│      # Dispatch to Celery (returns immediately!)              │
│      task = execute_workflow_task.delay(                      │
│          workflow_type=request.workflow_type,                 │
│          query=request.query                                  │
│      )                                                         │
│      return {"task_id": task.id, "status": "queued"}          │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────────┐
│                    REDIS (Message Broker)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Queue:    │  │  Queue:    │  │  Queue:    │             │
│  │  high      │  │  default   │  │  low       │             │
│  │  priority  │  │  priority  │  │  priority  │             │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘             │
└─────────┼────────────────┼────────────────┼──────────────────┘
          │                │                │
          ▼                ▼                ▼
┌───────────────────────────────────────────────────────────────┐
│                    CELERY WORKERS (Pods)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Worker 1    │  │  Worker 2    │  │  Worker N    │       │
│  │  (General)   │  │  (Long tasks)│  │  (Batch)     │       │
│  │  Concurrency │  │  Concurrency │  │  Concurrency │       │
│  │  = 4         │  │  = 2         │  │  = 1         │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                   Execute long workflow
                   (2-30 minutes)
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                   RESULT BACKEND (Redis)                       │
│  Task Results (persisted for 1 hour):                         │
│  - task_id: abc123                                            │
│  - status: SUCCESS                                            │
│  - result: { ... workflow output ... }                        │
│  - execution_time: 120s                                       │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                    FLOWER (Monitoring UI)                      │
│  http://your-ip:5555                                          │
│  - Active workers                                             │
│  - Task throughput                                            │
│  - Success/failure rates                                      │
│  - Queue lengths                                              │
│  - Task execution history                                     │
└───────────────────────────────────────────────────────────────┘
```

### Task Flow Example

```python
# 1. Client sends request
POST /api/workflows/execute
{
  "workflow_type": "multi_agent_debate",
  "query": "Best database for our use case?",
  "agents": ["db_specialist", "performance_expert", "cost_analyst"]
}

# 2. FastAPI dispatches task (< 50ms)
task = execute_multi_agent_debate.delay(
    query="Best database?",
    agents=[...]
)
→ Returns: {"task_id": "abc123", "status": "queued"}

# 3. Celery worker picks up task
Worker 1: Executing task abc123...
  - Agent 1 responds (30s)
  - Agent 2 responds (45s)
  - Agent 3 responds (30s)
  - Synthesize results (15s)
→ Total: 120 seconds (2 minutes)

# 4. Result stored in Redis
task_id: abc123
status: SUCCESS
result: { "consensus": "PostgreSQL", "reasoning": "..." }

# 5. Client polls for result
GET /api/tasks/abc123
→ Returns: {"status": "SUCCESS", "result": {...}}
```

---

## 📦 Components

### 1. Celery Application
**File:** `src/celery/celery_app.py`

**Configuration:**
```python
- Broker: Redis (DB 1)
- Result Backend: Redis (DB 2)
- Task Serializer: JSON
- Result Expires: 3600 seconds (1 hour)
- Task Acks Late: True (safer - acknowledge after execution)
- Worker Prefetch Multiplier: 1 (fair distribution)
- Retry Backoff: True (exponential backoff)
- Max Retries: 3
```

**Queues:**
```python
1. high_priority (priority=10)
   - Urgent customer requests
   - Critical system tasks
   - SLA: <30 seconds

2. default (priority=5)
   - Normal agent workflows
   - Regular operations
   - SLA: <5 minutes

3. low_priority (priority=1)
   - Batch processing
   - Analytics generation
   - Cleanup tasks
   - SLA: <1 hour
```

### 2. Task Modules

#### Agent Tasks (`src/celery/tasks/agent_tasks.py`)
```python
Tasks:
- execute_workflow(workflow_type, query, context)
  → Run multi-agent workflows (sequential, parallel, debate, etc.)
  → Execution time: 2-30 minutes
  → Queue: default
  → Retry: 3 times with exponential backoff

- execute_urgent_agent(agent_name, query, context)
  → Single agent execution for urgent requests
  → Execution time: 5-30 seconds
  → Queue: high_priority
  → Retry: 2 times

- batch_execute_agents(agent_configs[])
  → Parallel execution of multiple agents
  → Execution time: 5-15 minutes
  → Queue: low_priority
  → Retry: 1 time
```

#### Analytics Tasks (`src/celery/tasks/analytics_tasks.py`)
```python
Tasks:
- generate_daily_report()
  → Aggregate previous day's metrics
  → Schedule: Daily at 9 AM (Celery Beat)
  → Execution time: 2-5 minutes

- calculate_usage_costs()
  → Calculate LLM usage costs for all customers
  → Schedule: Hourly
  → Execution time: 1-3 minutes

- generate_customer_insights(customer_id)
  → Deep analysis of customer usage patterns
  → Trigger: On-demand or weekly
  → Execution time: 5-10 minutes
```

#### Maintenance Tasks (`src/celery/tasks/maintenance_tasks.py`)
```python
Tasks:
- cleanup_expired_conversations()
  → Delete conversations older than 30 days
  → Schedule: Daily at 3 AM
  → Execution time: 1-5 minutes

- rebuild_vector_embeddings()
  → Re-embed entire knowledge base
  → Schedule: Weekly (Sundays at 2 AM)
  → Execution time: 30-60 minutes

- optimize_database()
  → Run VACUUM, ANALYZE, reindex
  → Schedule: Weekly (Saturdays at 4 AM)
  → Execution time: 10-30 minutes
```

#### Notification Tasks (`src/celery/tasks/notification_tasks.py`)
```python
Tasks:
- send_email(to, subject, body, html)
  → Send email via SMTP
  → Retry: 5 times (SMTP can be flaky)
  → Execution time: 1-5 seconds

- send_slack_message(channel, message)
  → Post message to Slack
  → Retry: 3 times
  → Execution time: <1 second

- send_critical_alert(message, recipients)
  → High-priority alert (PagerDuty, Slack, email)
  → Queue: high_priority
  → Retry: 5 times with immediate retries
```

---

### 3. Celery Workers (Kubernetes Pods)

#### Worker Deployment
**File:** `k8s/celery-worker-deployment.yaml`

```yaml
Replicas: 2 (can scale to 10)
Resources:
  - CPU: 500m (1 core max)
  - Memory: 1GB (2GB max)

Concurrency: 4 workers per pod
Queues: high_priority, default, low_priority

Health Checks:
  - Liveness: celery inspect ping
  - Readiness: celery inspect active

Autoscaling:
  - Min: 2 pods
  - Max: 10 pods
  - Metric: Queue length > 100 tasks
```

### 4. Celery Beat (Scheduler)

#### Beat Deployment
**File:** `k8s/celery-beat-deployment.yaml`

```yaml
Replicas: 1 (only one scheduler needed!)
Resources:
  - CPU: 100m
  - Memory: 256MB

Schedule Storage: /tmp/celerybeat-schedule (persistent volume)

Schedules:
  - cleanup_expired_conversations: Daily @ 3 AM
  - generate_daily_report: Daily @ 9 AM
  - calculate_usage_costs: Hourly
  - rebuild_vector_embeddings: Weekly (Sunday @ 2 AM)
  - optimize_database: Weekly (Saturday @ 4 AM)
```

### 5. Flower (Monitoring UI)

#### Flower Deployment
**File:** `k8s/flower-deployment.yaml`

```yaml
Replicas: 1
Resources:
  - CPU: 250m
  - Memory: 512MB

Port: 5555
Authentication: Basic auth (username/password)

Features:
  - Real-time task monitoring
  - Worker status
  - Task history (last 1000 tasks)
  - Queue length graphs
  - Success/failure rates
  - Task execution time histograms
```

---

## 🎯 Use Cases

### Use Case 1: Long-Running Agent Workflows
```python
# BEFORE (Synchronous - blocks for 5 minutes!)
@app.post("/api/workflows/debate")
async def run_debate(query: str):
    result = await debate_workflow.execute(query)  # 5 minutes!
    return result  # User waits 5 minutes 😡

# AFTER (Asynchronous - returns immediately!)
@app.post("/api/workflows/debate")
async def run_debate(query: str):
    task = execute_debate_workflow.delay(query)
    return {
        "task_id": task.id,
        "status_url": f"/api/tasks/{task.id}",
        "estimated_time": "5 minutes"
    }  # Returns in <50ms 😊
```

### Use Case 2: Scheduled Reports
```python
# Automatically generates daily reports
# No cron jobs needed!
@celery_app.task
def generate_daily_report():
    report = {
        "date": datetime.now().date(),
        "total_conversations": db.count_conversations(),
        "total_agents_executed": db.count_agent_executions(),
        "avg_response_time": db.avg_response_time(),
        "top_agents": db.top_agents(limit=10)
    }

    # Send to stakeholders
    send_email.delay(
        to="team@company.com",
        subject=f"Daily Report - {report['date']}",
        body=render_template("daily_report.html", report=report)
    )

# Scheduled in celery_app.py:
beat_schedule = {
    'daily-report': {
        'task': 'src.celery.tasks.analytics_tasks.generate_daily_report',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    }
}
```

### Use Case 3: Batch Processing
```python
# Import 10,000 customers from CSV
@celery_app.task
def import_customers_from_csv(file_path: str):
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            customer = Customer(
                name=row['name'],
                email=row['email'],
                company=row['company']
            )
            db.session.add(customer)

        db.session.commit()

    # Send notification when done
    send_slack_message.delay(
        channel="#ops",
        message=f"Imported {reader.line_num} customers"
    )
```

### Use Case 4: Email Notifications (Non-blocking)
```python
# BEFORE (Synchronous - blocks for 2 seconds)
@app.post("/api/conversations")
async def create_conversation(data: ConversationCreate):
    conversation = db.create_conversation(data)
    send_email_to_user(conversation)  # Blocks for 2s!
    return conversation

# AFTER (Asynchronous - instant response)
@app.post("/api/conversations")
async def create_conversation(data: ConversationCreate):
    conversation = db.create_conversation(data)

    # Send email in background
    send_email.delay(
        to=conversation.user_email,
        subject="Conversation Created",
        body=f"Your conversation #{conversation.id} has been created"
    )

    return conversation  # Returns immediately!
```

---

## 📋 Detailed Implementation

### Step 1: Install Dependencies
```bash
# Add to requirements.txt
celery[redis]==5.4.0
flower==2.0.1
redis==5.1.1
```

### Step 2: Configure Celery Application
**File:** `src/celery/celery_app.py`

```python
from celery import Celery
from celery.schedules import crontab
from src.core.config import settings

celery_app = Celery(
    'multi_agent_tasks',
    broker=settings.celery_broker_url,  # redis://redis:6379/1
    backend=settings.celery_result_backend,  # redis://redis:6379/2
    include=[
        'src.celery.tasks.agent_tasks',
        'src.celery.tasks.analytics_tasks',
        'src.celery.tasks.maintenance_tasks',
        'src.celery.tasks.notification_tasks',
    ]
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,

    # Queues
    task_queues={
        'high_priority': {'priority': 10},
        'default': {'priority': 5},
        'low_priority': {'priority': 1},
    },

    # Scheduled tasks
    beat_schedule={
        'cleanup-expired-conversations': {
            'task': 'src.celery.tasks.maintenance_tasks.cleanup_expired_conversations',
            'schedule': crontab(hour=3, minute=0),
        },
        'generate-daily-report': {
            'task': 'src.celery.tasks.analytics_tasks.generate_daily_report',
            'schedule': crontab(hour=9, minute=0),
        },
        'calculate-usage-costs': {
            'task': 'src.celery.tasks.analytics_tasks.calculate_usage_costs',
            'schedule': crontab(minute=0),  # Every hour
        },
    }
)
```

### Step 3: Create Task Modules
Tasks already created in earlier work - just need to organize properly.

### Step 4: Add to docker-compose.yml
```yaml
services:
  celery-worker:
    build: .
    command: celery -A src.celery.celery_app worker --loglevel=info --concurrency=4
    environment:
      <<: *common-env
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  celery-beat:
    build: .
    command: celery -A src.celery.celery_app beat --loglevel=info
    environment:
      <<: *common-env
    depends_on:
      - redis
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  flower:
    build: .
    command: celery -A src.celery.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      <<: *common-env
    depends_on:
      - redis
```

### Step 5: Integrate with FastAPI
```python
# src/api/routes/workflows.py
from fastapi import APIRouter
from src.celery.tasks.agent_tasks import execute_workflow

router = APIRouter()

@router.post("/workflows/execute")
async def execute_workflow_async(request: WorkflowRequest):
    """Execute multi-agent workflow asynchronously"""
    task = execute_workflow.delay(
        workflow_type=request.workflow_type,
        query=request.query,
        context=request.context or {}
    )

    return {
        "task_id": task.id,
        "status": "queued",
        "status_url": f"/api/tasks/{task.id}",
        "estimated_time": estimate_workflow_time(request.workflow_type)
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of asynchronous task"""
    task = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task.status,  # PENDING, STARTED, SUCCESS, FAILURE
        "result": task.result if task.ready() else None,
        "error": str(task.info) if task.failed() else None
    }
```

---

## ✅ Acceptance Criteria

### Infrastructure
- [ ] Celery installed and configured
- [ ] Redis configured with 3 databases (cache=0, broker=1, results=2)
- [ ] Celery worker deployed to Kubernetes (2 pods minimum)
- [ ] Celery Beat deployed (1 pod, with persistent volume)
- [ ] Flower deployed and accessible at http://your-ip:5555

### Task Implementation
- [ ] Agent tasks module created with 3 tasks
- [ ] Analytics tasks module created with 3 tasks
- [ ] Maintenance tasks module created with 3 tasks
- [ ] Notification tasks module created with 3 tasks
- [ ] All tasks have proper error handling and retry logic

### Scheduled Tasks
- [ ] Daily cleanup task scheduled and tested
- [ ] Daily report task scheduled and tested
- [ ] Hourly cost calculation scheduled and tested
- [ ] Weekly KB update scheduled and tested

### Integration
- [ ] FastAPI endpoints created for task submission
- [ ] FastAPI endpoints created for task status checking
- [ ] Tasks can be triggered from API
- [ ] Task results can be retrieved from API

### Monitoring
- [ ] Flower UI accessible and showing workers
- [ ] Task execution visible in Flower
- [ ] Queue lengths visible in Flower
- [ ] Worker health checks passing

### Testing
- [ ] Unit tests for all task modules (>80% coverage)
- [ ] Integration tests for task execution
- [ ] Load test: 100 concurrent tasks handled successfully
- [ ] Failure test: Tasks retry on failure

### Documentation
- [ ] Celery architecture documented
- [ ] Task modules documented
- [ ] API endpoints documented
- [ ] Monitoring guide created

---

## 📊 Success Metrics

```yaml
Task Throughput:
  Target: 1000+ tasks per day
  Measured: ___

Average Task Duration:
  Target: <2 minutes (for standard workflows)
  Measured: ___

Task Success Rate:
  Target: >99%
  Measured: ___

Worker Utilization:
  Target: 40-70% average
  Measured: ___

Queue Length:
  Target: <50 pending tasks (average)
  Measured: ___
```

---

## 🗺️ Implementation Timeline

### Week 1: Core Setup
**Days 1-2:** Infrastructure
- Install Celery dependencies
- Configure celery_app.py
- Set up Redis databases

**Days 3-5:** Task Development
- Create all task modules
- Implement error handling
- Add retry logic

### Week 2: Deployment & Integration
**Days 1-2:** Kubernetes Deployment
- Deploy worker pods
- Deploy Beat pod
- Deploy Flower

**Days 3-4:** API Integration
- Create FastAPI endpoints
- Test task submission
- Test status checking

**Day 5:** Testing & Documentation
- Run integration tests
- Load testing
- Write documentation

---

## 📚 Related Issues

- **CICD-001:** Main CI/CD Pipeline (Parent)
- **CICD-004:** Monitoring & Observability
- **CICD-002:** Docker Infrastructure

---

## 🔗 Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Flower Documentation](https://flower.readthedocs.io/)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)

---

**Issue Author:** Backend Team
**Created:** 2025-01-15
**Last Updated:** 2025-01-15
