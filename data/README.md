# Data Directory - Complete Guide

This directory contains all seed data, configuration, and documentation for populating the Multi-Agent Support System's databases.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Databases Used](#databases-used)
3. [Directory Structure](#directory-structure)
4. [PostgreSQL Database](#postgresql-database)
5. [Qdrant Vector Database](#qdrant-vector-database)
6. [Data Schemas](#data-schemas)
7. [Scripts Reference](#scripts-reference)
8. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The Multi-Agent Support System uses a **dual-database architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Support System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │   PostgreSQL        │         │   Qdrant Cloud      │        │
│  │   (SQL Database)    │         │   (Vector Database) │        │
│  ├─────────────────────┤         ├─────────────────────┤        │
│  │ • Customers         │         │ • KB Article        │        │
│  │ • Conversations     │         │   Embeddings        │        │
│  │ • Messages          │         │ • Semantic Search   │        │
│  │ • Subscriptions     │         │   Vectors           │        │
│  │ • Invoices          │         │                     │        │
│  │ • Leads & Deals     │         │ Model: all-MiniLM   │        │
│  │ • KB Articles       │◄────────┤ Dimensions: 384     │        │
│  │ • Usage Events      │  Sync   │ Distance: Cosine    │        │
│  │ • And 15+ more...   │         │                     │        │
│  └─────────────────────┘         └─────────────────────┘        │
│           │                               │                      │
│           ▼                               ▼                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   AI Agents (243 total)                  │    │
│  │  • Query customer data from PostgreSQL                   │    │
│  │  • Semantic search KB articles via Qdrant                │    │
│  │  • Provide informed, context-aware responses             │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Databases Used

### 1. PostgreSQL (Relational Database)

**What it is:** A traditional SQL database that stores structured data with relationships.

**Why we use it:**
- Stores all business data (customers, subscriptions, conversations, etc.)
- Supports complex queries and joins
- ACID compliance for data integrity
- Stores KB articles as source of truth (Qdrant is just for search)

**Connection:** Configured via environment variables or Doppler:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

### 2. Qdrant Cloud (Vector Database)

**What it is:** A specialized database for storing and searching high-dimensional vectors (embeddings).

**Why we use it:**
- Enables **semantic search** - find articles by meaning, not just keywords
- "How do I upgrade?" finds articles about "plan changes" even without exact match
- Fast similarity search across thousands of articles
- Filters by category for targeted results

**Connection:** Configured via environment variables or Doppler:
```
QDRANT__URL=https://your-cluster.aws.cloud.qdrant.io:6333
QDRANT__API_KEY=your-api-key
```

**How it works:**
1. Each KB article's text is converted to a 384-dimensional vector using `all-MiniLM-L6-v2`
2. Vectors are stored in Qdrant with metadata (title, category, tags)
3. When a user asks a question, the query is also converted to a vector
4. Qdrant finds articles with the most similar vectors (cosine similarity)

---

## Directory Structure

```
data/
├── README.md                    # This file
├── kb_articles/
│   └── seed_articles.json       # KB articles for vector database
├── sql_seed/
│   ├── customers.json           # Customer records
│   ├── employees.json           # Employee/agent records
│   ├── subscriptions.json       # Subscription data
│   ├── invoices.json            # Invoice records
│   ├── payments.json            # Payment history
│   ├── credits.json             # Account credits
│   ├── conversations.json       # Chat conversations
│   ├── messages.json            # Individual messages
│   ├── leads.json               # Sales leads
│   ├── deals.json               # Sales deals/opportunities
│   ├── quotes.json              # Price quotes
│   ├── sales_activities.json    # Sales activity log
│   ├── usage_events.json        # Product usage events
│   ├── feature_usage.json       # Feature adoption metrics
│   ├── customer_health_events.json
│   ├── customer_segments.json
│   ├── customer_notes.json
│   ├── customer_contacts.json
│   ├── customer_integrations.json
│   └── agent_performance.json   # Agent metrics
└── conversations/               # Sample conversation exports
```

---

## PostgreSQL Database

### Tables Overview (20+ tables)

| Table | Description | Key Fields |
|-------|-------------|------------|
| `customers` | Customer accounts | id, email, name, plan |
| `employees` | Internal team members | id, email, name, role, department |
| `subscriptions` | Active subscriptions | customer_id, plan, mrr, status |
| `invoices` | Billing invoices | customer_id, amount, status, due_date |
| `payments` | Payment records | invoice_id, amount, method, status |
| `credits` | Account credits | customer_id, amount, reason |
| `conversations` | Chat sessions | customer_id, status, agents_involved |
| `messages` | Chat messages | conversation_id, role, content, agent_name |
| `leads` | Sales prospects | email, company, lead_score, status |
| `deals` | Sales opportunities | lead_id, value, stage, probability |
| `quotes` | Price quotes | deal_id, total_amount, status |
| `sales_activities` | Sales actions | deal_id, activity_type, outcome |
| `usage_events` | Product usage | customer_id, event_type, quantity |
| `feature_usage` | Feature adoption | customer_id, feature_name, usage_count |
| `kb_articles` | Knowledge base | title, content, category, tags |
| `customer_health_events` | Health signals | customer_id, event_type, score_change |
| `customer_segments` | Segmentation | customer_id, segment_name |
| `agent_performance` | Agent metrics | agent_name, conversations_handled, avg_resolution_time |

### Loading Order (Foreign Key Dependencies)

Tables must be loaded in this order to respect foreign key constraints:

```
1. customers, employees           # No dependencies
2. subscriptions                  # Depends on customers
3. invoices                       # Depends on customers
4. payments                       # Depends on invoices
5. credits                        # Depends on customers
6. usage_events                   # Depends on customers
7. customer_health_events         # Depends on customers
8. customer_segments              # Depends on customers
9. customer_notes                 # Depends on customers
10. customer_contacts             # Depends on customers
11. customer_integrations         # Depends on customers
12. conversations                 # Depends on customers
13. feature_usage                 # Depends on customers
14. leads                         # Depends on employees (optional)
15. deals                         # Depends on leads, customers
16. quotes                        # Depends on deals
17. sales_activities              # Depends on deals, leads
18. messages                      # Depends on conversations
19. agent_performance             # No dependencies
```

---

## Qdrant Vector Database

### Collection: `kb_articles`

**Vector Configuration:**
- **Dimensions:** 384 (from `all-MiniLM-L6-v2` model)
- **Distance Metric:** Cosine similarity
- **Index:** HNSW (Hierarchical Navigable Small World)

**Payload Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | string (UUID) | Article ID (matches PostgreSQL) |
| `title` | string | Article title |
| `content` | string | Full article content |
| `category` | keyword | Category for filtering |
| `tags` | array | Tags for additional filtering |

**Valid Categories:**
- `billing` - Payment, invoices, subscriptions
- `technical` - Bugs, troubleshooting, errors
- `usage` - How-to guides, features
- `api` - API documentation, webhooks
- `account` - Account management, settings
- `integration` - Third-party integrations
- `sales` - Pricing, plans, upgrades
- `success` - Best practices, tips
- `general` - General information
- `security` - Security features, compliance
- `onboarding` - Getting started guides
- `troubleshooting` - Problem resolution
- `features` - Feature documentation
- `pricing` - Pricing information

---

## Data Schemas

### KB Article (seed_articles.json)

```json
{
  "records": [
    {
      "id": "uuid-string",
      "title": "Article Title (5-500 chars)",
      "content": "Full markdown content (min 20 chars)...",
      "category": "billing",
      "tags": ["tag1", "tag2"],
      "url": "https://docs.example.com/article",
      "quality_score": 85.5,
      "is_active": 1
    }
  ]
}
```

**Alternative formats supported:**
```json
{"articles": [...]}
{"records": [...]}
{"data": [...]}
[...]  // Direct array
```

### Customer (customers.json)

```json
[
  {
    "id": "uuid-string",
    "email": "customer@example.com",
    "name": "Customer Name",
    "plan": "free|basic|premium|enterprise",
    "extra_metadata": {
      "company": "Company Name",
      "company_size": "1-10|11-50|51-200|201-500|500+",
      "industry": "technology|healthcare|finance|...",
      "title": "Job Title",
      "timezone": "America/New_York",
      "signup_source": "organic|referral|google|demo",
      "phone": "+1-555-123-4567"
    },
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Subscription (subscriptions.json)

```json
[
  {
    "id": "uuid-string",
    "customer_id": "customer-uuid",
    "plan": "basic|premium|enterprise",
    "billing_cycle": "monthly|annual",
    "mrr": 99.00,
    "arr": 1188.00,
    "seats_total": 10,
    "seats_used": 7,
    "status": "active|past_due|canceled|trialing",
    "current_period_start": "2024-01-01T00:00:00Z",
    "current_period_end": "2024-02-01T00:00:00Z",
    "cancel_at_period_end": false
  }
]
```

### Conversation (conversations.json)

```json
[
  {
    "id": "uuid-string",
    "customer_id": "customer-uuid",
    "status": "active|resolved|escalated",
    "primary_intent": "billing_question|technical_support|upgrade_request|...",
    "agents_involved": ["agent_support_1", "agent_billing_2"],
    "sentiment_avg": 0.75,
    "kb_articles_used": ["article-uuid-1", "article-uuid-2"],
    "started_at": "2024-01-15T10:30:00Z",
    "ended_at": "2024-01-15T10:45:00Z",
    "resolution_time_seconds": 900
  }
]
```

### Message (messages.json)

```json
[
  {
    "id": "uuid-string",
    "conversation_id": "conversation-uuid",
    "role": "user|assistant",
    "content": "Message content...",
    "agent_name": "closer",
    "sentiment": 0.8,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Lead (leads.json)

```json
[
  {
    "id": "uuid-string",
    "email": "lead@company.com",
    "name": "Lead Name",
    "company": "Company Name",
    "title": "Job Title",
    "phone": "+1-555-123-4567",
    "lead_score": 75,
    "qualification_status": "new|mql|sql|qualified|disqualified|converted",
    "source": "website|referral|cold_outreach|event|partner",
    "assigned_to": "employee-uuid",
    "converted_to_customer_id": "customer-uuid",
    "converted_at": "2024-01-20T15:00:00Z",
    "extra_metadata": {
      "industry": "technology",
      "company_size": 150,
      "budget": "$10k-50k",
      "timeline": "Q1 2024"
    }
  }
]
```

### Deal (deals.json)

```json
[
  {
    "id": "uuid-string",
    "lead_id": "lead-uuid",
    "customer_id": "customer-uuid",
    "name": "Enterprise Deal - Acme Corp",
    "value": 50000.00,
    "currency": "USD",
    "stage": "prospecting|qualification|proposal|negotiation|closed_won|closed_lost",
    "probability": 60,
    "expected_close_date": "2024-03-15T00:00:00Z",
    "assigned_to": "employee-uuid",
    "extra_metadata": {
      "deal_type": "new_business|renewal|upsell|expansion",
      "competitor": "CompetitorA"
    }
  }
]
```

---

## Scripts Reference

### 1. Load SQL Data

**Script:** `scripts/load_sql_data.py`

**Purpose:** Loads JSON files from `data/sql_seed/` into PostgreSQL.

**Usage:**
```bash
# Load data (keeps existing data)
python scripts/load_sql_data.py

# Clear existing data first, then load
python scripts/load_sql_data.py --reset

# Load from a different folder
python scripts/load_sql_data.py --folder data/my_custom_seed
```

**What it does:**
1. Reads all JSON files from `data/sql_seed/`
2. Automatically deduplicates records (by email, id)
3. Converts data types (UUID, Decimal, DateTime)
4. Inserts records in correct order (respecting foreign keys)
5. Reports success/failure counts

**Output example:**
```
📄 Loading customers from customers.json...
   Found 500 records in file
   ⚠ Removed 23 duplicate records
   477 records after deduplication
   ✓ Loaded 477 records

✅ SQL DATA LOAD COMPLETE!
Total records loaded: 2,770
```

### 2. Initialize Knowledge Base

**Script:** `scripts/init_knowledge_base.py`

**Purpose:** Loads KB articles into both PostgreSQL AND Qdrant (with vector embeddings).

**Usage:**
```bash
# Load articles (keeps existing)
python scripts/init_knowledge_base.py

# Clear and reload everything
python scripts/init_knowledge_base.py --reset
```

**What it does:**
1. Connects to Qdrant Cloud
2. Creates/recreates the `kb_articles` collection
3. Loads articles from `data/kb_articles/seed_articles.json`
4. For each article:
   - Saves to PostgreSQL (source of truth)
   - Generates 384-dim embedding using `all-MiniLM-L6-v2`
   - Stores embedding + metadata in Qdrant
5. Runs verification tests (search queries)

**Output example:**
```
[3/5] Loading seed articles...
✓ Loaded 297 articles from seed data

  Category breakdown:
    - billing: 45 articles
    - technical: 52 articles
    - usage: 38 articles
    ...

[5/5] Importing articles into database and vector store...
✓ Import completed:
  - Total: 297
  - Success: 297
  - Failures: 0

[Test 1] Testing vector search...
✓ Vector search working! Query: 'how do I upgrade my plan?'
  Found 3 results:
    1. How to Upgrade Your ProjectFlow Plan (score: 0.545)
```

### 3. Seed Database (Random Data)

**Script:** `scripts/seed_database.py`

**Purpose:** Generates random test data programmatically (not from JSON files).

**Usage:**
```bash
python scripts/seed_database.py
```

**What it does:**
- Creates ~100 random customers
- Generates subscriptions, conversations, messages
- Creates usage events and feature usage data
- Populates sales pipeline (leads, deals)

**When to use:** Only for quick testing when you don't have real/custom data.

### 4. Embed Articles (Standalone)

**Script:** `scripts/embed_articles.py`

**Purpose:** Generates embeddings for articles and saves to file (for inspection/debugging).

**Usage:**
```bash
# Process all article files
python scripts/embed_articles.py --all

# Process single file
python scripts/embed_articles.py --input data/articles.json --output data/articles_embedded.json
```

---

## Step-by-Step Setup Guide

### Initial Setup (First Time)

```bash
# 1. Make sure PostgreSQL and Qdrant are configured
#    Check your .env or Doppler for:
#    - DATABASE_URL
#    - QDRANT__URL
#    - QDRANT__API_KEY

# 2. Run database migrations (if not already done)
alembic upgrade head

# 3. Prepare your data files
#    - Place KB articles in: data/kb_articles/seed_articles.json
#    - Place SQL data in: data/sql_seed/*.json

# 4. Load SQL data into PostgreSQL
python scripts/load_sql_data.py --reset

# 5. Load KB articles into PostgreSQL + Qdrant
python scripts/init_knowledge_base.py --reset

# 6. Verify everything worked
python scripts/init_knowledge_base.py  # Should show vector count

# 7. Start the application
python -m uvicorn src.api.main:app --reload
```

### Adding New Data

```bash
# Add new SQL data:
# 1. Add/update JSON files in data/sql_seed/
# 2. Run without --reset to append:
python scripts/load_sql_data.py

# Add new KB articles:
# 1. Add articles to data/kb_articles/seed_articles.json
# 2. Run without --reset to append:
python scripts/init_knowledge_base.py
```

### Resetting Everything

```bash
# WARNING: This deletes all data!

# Reset SQL database
python scripts/load_sql_data.py --reset

# Reset KB + Qdrant vectors
python scripts/init_knowledge_base.py --reset
```

### Syncing Qdrant with PostgreSQL

If Qdrant gets out of sync with PostgreSQL (e.g., after manual DB edits):

```python
# In Python:
from src.services.application.kb_article_service import KBArticleService
from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService

kb_service = KnowledgeBaseService()
article_service = KBArticleService(kb_service)

# This re-indexes all active articles from DB to Qdrant
result = await article_service.sync_all_to_vector_store()
print(result.value)  # {'synced_count': 297, 'total_articles': 297}
```

---

## Troubleshooting

### "Duplicate key value violates unique constraint"

**Cause:** Your data has duplicate emails or IDs.

**Solution:** The `load_sql_data.py` script automatically deduplicates, but if you still see errors:
1. Check your JSON files for duplicate `email` or `id` fields
2. Use `--reset` to clear existing data first

### "Vector search returned no results"

**Causes & Solutions:**

1. **No vectors in Qdrant:**
   ```bash
   python scripts/init_knowledge_base.py --reset
   ```

2. **Articles exist but not indexed:**
   - Check `Total vectors` in the output - should match article count
   - If mismatch, run `--reset` to reindex

3. **Category mismatch:**
   - Search filters by category - make sure category exists in data
   - Valid categories: billing, technical, usage, api, account, integration, sales, success, general, security, onboarding, troubleshooting, features, pricing

### "Seed file not found"

**Cause:** The script looks for `data/kb_articles/seed_articles.json`

**Solution:**
```bash
# Rename your file
mv "data/kb_articles/kb articles.json" "data/kb_articles/seed_articles.json"
```

### "Could not find articles array in JSON file"

**Cause:** Your JSON format isn't recognized.

**Solution:** Use one of these formats:
```json
{"articles": [...]}
{"records": [...]}
{"data": [...]}
[...]  // Direct array
```

### "Foreign key constraint violation"

**Cause:** Trying to insert data that references non-existent records.

**Solution:**
1. Make sure IDs in your data are consistent
2. Load tables in the correct order (customers before subscriptions, etc.)
3. Use `--reset` to start fresh

### "Vector store is not available"

**Cause:** Can't connect to Qdrant.

**Solution:**
1. Check your Qdrant URL and API key in environment variables
2. Verify your Qdrant Cloud cluster is running
3. Check network connectivity

---

## Data Quality Tips

### For KB Articles

1. **Minimum content length:** 20 characters (enforced)
2. **Title length:** 5-500 characters
3. **Use specific categories:** Helps with filtered search
4. **Include relevant tags:** Improves search relevance
5. **Use markdown:** Content supports full markdown formatting

### For SQL Data

1. **Use valid UUIDs:** Format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
2. **Consistent references:** If `subscription.customer_id` = X, customer X must exist
3. **Valid enums:**
   - `plan`: free, basic, premium, enterprise
   - `status`: active, past_due, canceled, trialing
   - `stage`: prospecting, qualification, proposal, negotiation, closed_won, closed_lost

### Generating Test Data

If you need to generate test data, consider:
1. Using an LLM with the schemas above as a prompt
2. Using Faker library for realistic fake data
3. Exporting from a staging environment

---

## Quick Reference

| Task | Command |
|------|---------|
| Load SQL data | `python scripts/load_sql_data.py` |
| Load SQL data (fresh) | `python scripts/load_sql_data.py --reset` |
| Load KB articles | `python scripts/init_knowledge_base.py` |
| Load KB articles (fresh) | `python scripts/init_knowledge_base.py --reset` |
| Start API server | `python -m uvicorn src.api.main:app --reload` |
| Check Qdrant status | Visit your Qdrant Cloud dashboard |

---

## Support

For issues with data loading:
1. Check the troubleshooting section above
2. Review script output for specific error messages
3. Verify your environment variables are set correctly

For data schema questions:
1. Check the database models in `src/database/models/`
2. Review the schemas section in this document