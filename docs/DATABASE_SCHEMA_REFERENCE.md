# Complete Database Schema Reference

## Quick Reference for all 30+ Tables

---

## **1. CUSTOMER DOMAIN**

### `customers` (EXPANDED)
```
id                    UUID PRIMARY KEY
email                 VARCHAR(255) UNIQUE NOT NULL
name                  VARCHAR(255)
plan                  VARCHAR(50) ['free', 'basic', 'premium', 'enterprise']
company_name          VARCHAR(255)          ← NEW
company_size          INTEGER               ← NEW
industry              VARCHAR(100)          ← NEW
mrr                   DECIMAL(10,2)         ← NEW
ltv                   DECIMAL(10,2)         ← NEW
health_score          INTEGER (0-100)       ← NEW
churn_risk            DECIMAL(3,2) (0-1)    ← NEW
nps_score             INTEGER               ← NEW
lead_source           VARCHAR(50)           ← NEW
country               VARCHAR(2)            ← NEW
timezone              VARCHAR(50)           ← NEW
language              VARCHAR(10)           ← NEW
extra_metadata        JSONB
created_at, updated_at, created_by, updated_by, deleted_at, deleted_by

Relationships:
  → conversations (1:N)
  → health_events (1:N)
  → segments (1:N)
  → notes (1:N)
  → contacts (1:N)
  → integrations (1:N)
  → subscriptions (1:N)
  → invoices (1:N)
  → payments (1:N)
  → usage_events (1:N)
  → credits (1:N)
  → deals (1:N)
  → quotes (1:N)
  → feature_usage (1:N)
  → ab_tests (1:N)
```

### `customer_health_events` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
event_type            VARCHAR(50) ['health_score_change', 'churn_risk_change', 'engagement_drop', 'usage_spike']
old_value             DECIMAL(5,2)
new_value             DECIMAL(5,2)
reason                TEXT
detected_by           VARCHAR(50)
severity              VARCHAR(20) ['low', 'medium', 'high', 'critical']
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id+created_at, severity+created_at
```

### `customer_segments` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
segment_name          VARCHAR(100)
segment_type          VARCHAR(50) ['industry', 'lifecycle', 'value', 'behavior', 'risk']
confidence_score      DECIMAL(3,2)
assigned_at           TIMESTAMP
assigned_by           VARCHAR(50)
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id, segment_name
```

### `customer_notes` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
note_type             VARCHAR(50) ['general', 'support', 'sales', 'success', 'technical']
content               TEXT
is_internal           BOOLEAN
visibility            VARCHAR(20) ['private', 'team', 'company']
author_id             UUID
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id+created_at
```

### `customer_contacts` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
email                 VARCHAR(255)
name                  VARCHAR(255)
title                 VARCHAR(100)
phone                 VARCHAR(50)
role                  VARCHAR(50) ['admin', 'billing', 'technical', 'business', 'user']
is_primary            BOOLEAN
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id, email
```

### `customer_integrations` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
integration_type      VARCHAR(50)
status                VARCHAR(20) ['active', 'paused', 'error', 'disconnected']
config                JSONB
last_sync_at          TIMESTAMP
last_sync_status      VARCHAR(20)
error_count           INTEGER
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id, integration_type
Properties: is_healthy
```

---

## **2. CONVERSATION DOMAIN**

### `conversations` (EXPANDED)
```
id                              UUID PRIMARY KEY
customer_id                     UUID → customers.id (CASCADE)
status                          VARCHAR(50) ['active', 'resolved', 'escalated']
primary_intent                  VARCHAR(100)
agents_involved                 VARCHAR[]
sentiment_avg                   FLOAT (-1 to 1)
kb_articles_used                VARCHAR[]
channel                         VARCHAR(50) ['web_chat', 'email', 'phone', 'slack', 'api', 'widget'] ← NEW
intent_confidence               DECIMAL(3,2)  ← NEW
emotion                         VARCHAR(50)   ← NEW
resolved_by_agent               VARCHAR(50)   ← NEW
first_response_time_seconds     INTEGER       ← NEW
csat_score                      INTEGER (1-5) ← NEW
last_activity_at                TIMESTAMP     ← NEW
started_at                      TIMESTAMP
ended_at                        TIMESTAMP
resolution_time_seconds         INTEGER
extra_metadata                  JSONB
timestamps + audit trail

Indexes: customer_id, status, started_at, channel, emotion, last_activity_at
Relationships: → customer, → messages, → handoffs, → collaborations, → tags, → ab_tests
```

### `messages` (EXPANDED)
```
id                    UUID PRIMARY KEY
conversation_id       UUID → conversations.id (CASCADE)
role                  VARCHAR(20) ['user', 'assistant', 'system']
content               TEXT
agent_name            VARCHAR(50)
intent                VARCHAR(100)
sentiment             FLOAT (-1 to 1)
confidence            FLOAT (0 to 1)
tokens_used           INTEGER
agent_confidence      DECIMAL(3,2)  ← NEW
urgency               VARCHAR(20) ['low', 'medium', 'high', 'critical'] ← NEW
model_used            VARCHAR(100)  ← NEW
tokens_used           INTEGER       ← NEW (duplicate column name - check migration)
created_at            TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Indexes: conversation_id+created_at, agent_name+created_at
```

### `agent_handoffs` (NEW)
```
id                    UUID PRIMARY KEY
conversation_id       UUID → conversations.id (CASCADE)
from_agent            VARCHAR(50)
to_agent              VARCHAR(50)
handoff_reason        TEXT
state_transferred     JSONB
confidence_before     DECIMAL(3,2)
timestamp             TIMESTAMP
latency_ms            INTEGER
extra_metadata        JSONB
timestamps + audit trail

Constraint: from_agent != to_agent
Indexes: conversation_id+timestamp, from_agent+to_agent
Properties: handoff_duration_seconds
```

### `agent_collaborations` (NEW)
```
id                    UUID PRIMARY KEY
conversation_id       UUID → conversations.id (CASCADE)
collaboration_type    VARCHAR(50) ['sequential', 'parallel', 'debate', 'verification', 'expert_panel']
agents_involved       VARCHAR[]
coordinator_agent     VARCHAR(50)
start_time            TIMESTAMP
end_time              TIMESTAMP
duration_ms           INTEGER
outcome               TEXT
consensus_reached     BOOLEAN
extra_metadata        JSONB
timestamps + audit trail

Indexes: conversation_id, collaboration_type
Properties: agent_count, duration_seconds, is_complete
```

### `conversation_tags` (NEW)
```
id                    UUID PRIMARY KEY
conversation_id       UUID → conversations.id (CASCADE)
tag                   VARCHAR(50)
tag_category          VARCHAR(50)
confidence            DECIMAL(3,2)
tagged_by             VARCHAR(50)
extra_metadata        JSONB
timestamps + audit trail

Indexes: conversation_id, tag
```

---

## **3. SUBSCRIPTION & BILLING DOMAIN**

### `subscriptions` (NEW)
```
id                       UUID PRIMARY KEY
customer_id              UUID → customers.id (CASCADE)
plan                     VARCHAR(50) ['free', 'basic', 'premium', 'enterprise']
billing_cycle            VARCHAR(20) ['monthly', 'annual']
mrr                      DECIMAL(10,2)
arr                      DECIMAL(10,2)
seats_total              INTEGER
seats_used               INTEGER
status                   VARCHAR(20) ['active', 'past_due', 'canceled', 'unpaid', 'trialing']
current_period_start     TIMESTAMP
current_period_end       TIMESTAMP
cancel_at_period_end     BOOLEAN
canceled_at              TIMESTAMP
trial_start              TIMESTAMP
trial_end                TIMESTAMP
extra_metadata           JSONB
timestamps + audit trail

Constraint: seats_used <= seats_total
Indexes: customer_id, status
Properties: is_active, is_trial, days_until_renewal, seat_utilization
```

### `invoices` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
subscription_id       UUID → subscriptions.id (SET NULL)
invoice_number        VARCHAR(50) UNIQUE
amount                DECIMAL(10,2)
currency              VARCHAR(3)
status                VARCHAR(20) ['draft', 'open', 'paid', 'void', 'uncollectible']
issued_at             TIMESTAMP
due_at                TIMESTAMP
paid_at               TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id, invoice_number (unique), status
Properties: is_paid, is_overdue
```

### `payments` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
invoice_id            UUID → invoices.id (SET NULL)
amount                DECIMAL(10,2)
currency              VARCHAR(3)
status                VARCHAR(20) ['pending', 'succeeded', 'failed', 'canceled', 'refunded']
payment_method        VARCHAR(50)
transaction_id        VARCHAR(255)
processed_at          TIMESTAMP
failed_reason         TEXT
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id, invoice_id, status
Properties: is_successful
```

### `usage_events` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
event_type            VARCHAR(50)
quantity              INTEGER
unit                  VARCHAR(50)
timestamp             TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Indexes: customer_id+timestamp, event_type
```

### `credits` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
amount                DECIMAL(10,2)
currency              VARCHAR(3)
credit_type           VARCHAR(50) ['promotional', 'refund', 'goodwill', 'migration']
reason                TEXT
expires_at            TIMESTAMP
used_amount           DECIMAL(10,2)
status                VARCHAR(20) ['active', 'used', 'expired', 'canceled']
extra_metadata        JSONB
timestamps + audit trail

Constraint: used_amount <= amount
Indexes: customer_id, status
Properties: remaining_amount, is_expired
```

---

## **4. SALES & LEADS DOMAIN**

### `employees` (NEW)
```
id                    UUID PRIMARY KEY
email                 VARCHAR(255) UNIQUE
name                  VARCHAR(255)
role                  VARCHAR(50)
department            VARCHAR(50)
is_active             BOOLEAN
extra_metadata        JSONB
timestamps + audit trail

Indexes: email (unique), role
```

### `leads` (NEW)
```
id                          UUID PRIMARY KEY
email                       VARCHAR(255)
name                        VARCHAR(255)
company                     VARCHAR(255)
title                       VARCHAR(255)
phone                       VARCHAR(50)
budget                      VARCHAR(50)
authority                   VARCHAR(50)
need_score                  DECIMAL(3,2) (0-1)
timeline                    VARCHAR(50)
lead_score                  INTEGER (0-100)
qualification_status        VARCHAR(50) ['new', 'mql', 'sql', 'qualified', 'disqualified', 'converted']
source                      VARCHAR(50)
assigned_to                 UUID → employees.id (SET NULL)
converted_to_customer_id    UUID → customers.id (SET NULL)
converted_at                TIMESTAMP
extra_metadata              JSONB
timestamps + audit trail

Indexes: email, qualification_status, lead_score, assigned_to
Properties: is_qualified, is_converted
```

### `deals` (NEW)
```
id                      UUID PRIMARY KEY
lead_id                 UUID → leads.id (SET NULL)
customer_id             UUID → customers.id (SET NULL)
name                    VARCHAR(255)
value                   DECIMAL(10,2)
currency                VARCHAR(3)
stage                   VARCHAR(50) ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
probability             INTEGER (0-100)
expected_close_date     TIMESTAMP
closed_at               TIMESTAMP
lost_reason             TEXT
assigned_to             UUID → employees.id (SET NULL)
extra_metadata          JSONB
timestamps + audit trail

Indexes: lead_id, customer_id, stage, assigned_to
Properties: is_won, is_lost, is_closed, weighted_value
```

### `sales_activities` (NEW)
```
id                    UUID PRIMARY KEY
deal_id               UUID → deals.id (CASCADE)
lead_id               UUID → leads.id (CASCADE)
activity_type         VARCHAR(50) ['call', 'email', 'meeting', 'demo', 'proposal', 'follow_up']
subject               VARCHAR(255)
description           TEXT
outcome               VARCHAR(50)
scheduled_at          TIMESTAMP
completed_at          TIMESTAMP
performed_by          UUID → employees.id (SET NULL)
extra_metadata        JSONB
timestamps + audit trail

Indexes: deal_id, lead_id, activity_type
Properties: is_completed
```

### `quotes` (NEW)
```
id                    UUID PRIMARY KEY
deal_id               UUID → deals.id (SET NULL)
customer_id           UUID → customers.id (SET NULL)
quote_number          VARCHAR(50) UNIQUE
total_amount          DECIMAL(10,2)
currency              VARCHAR(3)
status                VARCHAR(20) ['draft', 'sent', 'accepted', 'declined', 'expired']
valid_until           TIMESTAMP
accepted_at           TIMESTAMP
line_items            JSONB
extra_metadata        JSONB
timestamps + audit trail

Indexes: deal_id, customer_id, quote_number (unique)
Properties: is_accepted
```

---

## **5. ANALYTICS DOMAIN**

### `conversation_analytics` (NEW)
```
id                              UUID PRIMARY KEY
date                            TIMESTAMP
channel                         VARCHAR(50)
total_conversations             INTEGER
resolved_conversations          INTEGER
escalated_conversations         INTEGER
avg_resolution_time_seconds     INTEGER
avg_sentiment                   FLOAT
avg_csat                        FLOAT
extra_metadata                  JSONB
timestamps + audit trail

Indexes: date, channel+date
Properties: resolution_rate, escalation_rate
```

### `feature_usage` (NEW)
```
id                    UUID PRIMARY KEY
customer_id           UUID → customers.id (CASCADE)
feature_name          VARCHAR(100)
usage_count           INTEGER
last_used_at          TIMESTAMP
date                  TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Unique: customer_id + feature_name + date
Indexes: customer_id+date, feature_name
```

### `ab_tests` (NEW)
```
id                    UUID PRIMARY KEY
test_name             VARCHAR(100)
variant               VARCHAR(50)
customer_id           UUID → customers.id (CASCADE)
conversation_id       UUID → conversations.id (CASCADE)
outcome               VARCHAR(50)
metric_value          FLOAT
timestamp             TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Indexes: test_name, variant
```

### `agent_performance` (EXISTING)
```
id                      UUID PRIMARY KEY
agent_name              VARCHAR(50)
date                    TIMESTAMP
total_interactions      INTEGER
successful_resolutions  INTEGER
escalations             INTEGER
avg_confidence          FLOAT
avg_sentiment           FLOAT
avg_response_time_ms    INTEGER
extra_metadata          JSONB
timestamps + audit trail

Unique: agent_name + date
Properties: success_rate
```

---

## **6. WORKFLOW AUTOMATION DOMAIN**

### `workflows` (NEW)
```
id                    UUID PRIMARY KEY
name                  VARCHAR(255)
trigger_type          VARCHAR(50) ['time_based', 'event_based', 'condition_based', 'manual']
trigger_config        JSONB
actions               JSONB
is_active             BOOLEAN
extra_metadata        JSONB
timestamps + audit trail

Indexes: name, is_active
Properties: action_count
```

### `workflow_executions` (NEW)
```
id                    UUID PRIMARY KEY
workflow_id           UUID → workflows.id (CASCADE)
status                VARCHAR(20) ['running', 'completed', 'failed', 'canceled']
started_at            TIMESTAMP
completed_at          TIMESTAMP
error_message         TEXT
execution_log         JSONB
extra_metadata        JSONB
timestamps + audit trail

Indexes: workflow_id, status
Properties: is_running, is_successful, duration_seconds
```

### `scheduled_tasks` (NEW)
```
id                    UUID PRIMARY KEY
task_name             VARCHAR(100)
task_type             VARCHAR(50)
schedule              VARCHAR(100)
parameters            JSONB
is_active             BOOLEAN
last_run_at           TIMESTAMP
next_run_at           TIMESTAMP
extra_metadata        JSONB
timestamps + audit trail

Indexes: task_name, is_active, next_run_at
Properties: is_overdue
```

---

## **7. SECURITY & COMPLIANCE DOMAIN**

### `audit_logs` (NEW - IMMUTABLE)
```
id                    UUID PRIMARY KEY
entity_type           VARCHAR(50)
entity_id             UUID
action                VARCHAR(50) ['create', 'read', 'update', 'delete', 'login', 'logout', 'export']
actor_type            VARCHAR(50) ['user', 'agent', 'system', 'api']
actor_id              UUID
changes               JSONB
ip_address            VARCHAR(45)
user_agent            TEXT
timestamp             TIMESTAMP
extra_metadata        JSONB

NOTE: No soft delete (immutable logs)
Indexes: entity_type+entity_id, actor_type+actor_id, timestamp, action
```

---

## **STATISTICS**

### **Tables**
- **Total Tables:** 30
- **New Tables:** 26
- **Expanded Tables:** 3 (customers, conversations, messages)
- **Existing Tables:** 4 (customers, conversations, messages, agent_performance)

### **Columns**
- **Total New Columns:** 400+
- **Expanded Table Columns:** 23 new columns

### **Relationships**
- **1:N (One-to-Many):** 70+
- **N:1 (Many-to-One):** 20+
- **1:1 (One-to-One):** 1

### **Indexes**
- **Primary Key Indexes:** 30
- **Unique Indexes:** 6
- **Foreign Key Indexes:** 30+
- **Composite Indexes:** 15+
- **Partial Indexes:** 2

### **Constraints**
- **Check Constraints:** 30+
- **Foreign Key Constraints:** 30+
- **Unique Constraints:** 6+

---

## **COMMON QUERY PATTERNS**

### **Get Customer with All Data**
```python
customer = session.query(Customer).options(
    selectinload(Customer.subscriptions),
    selectinload(Customer.health_events),
    selectinload(Customer.deals)
).filter(Customer.email == 'user@example.com').first()
```

### **Find At-Risk Customers**
```python
at_risk = session.query(Customer).filter(
    Customer.health_score < 50,
    Customer.churn_risk > 0.7
).all()
```

### **Get Active Subscriptions Ending Soon**
```python
from datetime import datetime, timedelta

ending_soon = session.query(Subscription).filter(
    Subscription.status == 'active',
    Subscription.current_period_end < datetime.utcnow() + timedelta(days=7)
).all()
```

### **Track Agent Handoffs**
```python
handoffs = session.query(AgentHandoff).join(Conversation).filter(
    Conversation.customer_id == customer_id,
    AgentHandoff.timestamp >= datetime.utcnow() - timedelta(days=30)
).order_by(AgentHandoff.timestamp.desc()).all()
```

---

## **🔗 KEY RELATIONSHIPS**

```
Customer
  ├── conversations (1:N)
  ├── subscriptions (1:N)
  ├── health_events (1:N)
  ├── leads (1:1) ← converted_from
  ├── deals (1:N)
  ├── invoices (1:N)
  ├── payments (1:N)
  └── feature_usage (1:N)

Conversation
  ├── customer (N:1)
  ├── messages (1:N)
  ├── handoffs (1:N)
  ├── collaborations (1:N)
  ├── tags (1:N)
  └── ab_tests (1:N)

Subscription
  ├── customer (N:1)
  └── invoices (1:N)

Lead
  ├── assigned_to → Employee (N:1)
  ├── converted_to → Customer (N:1)
  ├── deals (1:N)
  └── activities (1:N)

Deal
  ├── lead (N:1)
  ├── customer (N:1)
  ├── assigned_to → Employee (N:1)
  ├── activities (1:N)
  └── quotes (1:N)
```

---