# Database Migrations Guide

Complete guide for managing database migrations in the multi-agent support system.

## Table of Contents
- [Overview](#overview)
- [Migration Chain](#migration-chain)
- [Quick Start](#quick-start)
- [Testing Migrations](#testing-migrations)
- [Common Issues](#common-issues)
- [Best Practices](#best-practices)

---

## Overview

This project uses **Alembic** for database migrations with **PostgreSQL**.

**Database Schema:**
- 63 tables total
- 4 migration files
- Organized by feature/tier

**Tools:**
- Alembic (migration management)
- SQLAlchemy 2.0 (ORM)
- asyncpg (async PostgreSQL driver)

---

## Migration Chain

The migrations **must** be applied in this order:

```
efaa6e584823 (Initial schema)
    ↓
20251114120000 (Complete schema expansion)
    ↓
20251116000000 (Tier 3: Operational excellence)
    ↓
20251116120000 (Authentication system)
    ↓
20251117000000 (Tier 4: Advanced capabilities)
```

**Verification:**
```bash
alembic history
```

Should show:
```
20251117000000 -> head
20251116120000
20251116000000
20251114120000
efaa6e584823
```

---

## Quick Start

### 1. Check Current State

```bash
# View migration history
alembic history

# Check current revision
alembic current

# Show what's pending
alembic show
```

### 2. Apply All Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Or apply one by one
alembic upgrade +1
```

### 3. Verify Tables Created

```bash
# Using our test script
python scripts/test_migrations.py

# Or manually
psql -d your_database -c "\dt"
```

---

## Testing Migrations

### Automated Test Script

We provide a comprehensive test script:

```bash
# Test current state
python scripts/test_migrations.py

# Reset database (DESTRUCTIVE!)
python scripts/test_migrations.py --reset
```

**What it tests:**
1. ✓ Migration chain validity
2. ✓ Current database revision
3. ✓ Table count
4. ✓ All models have tables
5. ✓ Database connectivity

### Manual Testing

#### Test 1: Clean Database Setup

```bash
# 1. Drop all tables (if needed)
python scripts/test_migrations.py --reset

# 2. Apply migrations
alembic upgrade head

# 3. Verify
python scripts/test_migrations.py
```

Expected output:
```
✓ All tests passed!
  Current revision: 20251117000000
  Tables in database: 63
  Expected tables: 63
```

#### Test 2: Incremental Migrations

```bash
# Start from scratch
alembic downgrade base

# Apply one at a time
alembic upgrade +1  # efaa6e584823
alembic upgrade +1  # 20251114120000
alembic upgrade +1  # 20251116000000
alembic upgrade +1  # 20251116120000
alembic upgrade +1  # 20251117000000

# Verify at each step
alembic current
```

#### Test 3: Downgrade & Upgrade

```bash
# Downgrade one step
alembic downgrade -1

# Check state
alembic current

# Upgrade back
alembic upgrade +1
```

---

## Common Issues

### Issue 1: "No such revision"

**Symptom:**
```
Can't locate revision identified by '20251116120000'
```

**Cause:** Migration chain is broken (circular dependency)

**Fix:**
Check `down_revision` in each migration file:
- `20251116120000` should point to `20251116000000` ✓
- `20251117000000` should point to `20251116120000` ✓

### Issue 2: "Table already exists"

**Symptom:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "customers" already exists
```

**Cause:** Tables exist but alembic_version doesn't match

**Fix:**
```bash
# Option 1: Stamp current revision (if tables are correct)
alembic stamp head

# Option 2: Drop and recreate
python scripts/test_migrations.py --reset
alembic upgrade head
```

### Issue 3: Missing Tables

**Symptom:**
```
⚠ Missing 28 tables
```

**Cause:** Migrations not fully applied

**Fix:**
```bash
# Check what's missing
python scripts/test_migrations.py

# Apply remaining migrations
alembic upgrade head
```

### Issue 4: "Multiple head revisions"

**Symptom:**
```
Error: Multiple head revisions are present
```

**Cause:** Branching in migration chain

**Fix:**
```bash
# Merge heads
alembic merge heads -m "merge branches"

# Then upgrade
alembic upgrade head
```

---

## Best Practices

### Creating New Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add new feature"

# Manual migration
alembic revision -m "custom migration"
```

**Review before applying:**
1. Check `upgrade()` function
2. Check `downgrade()` function
3. Test on development database first

### Migration Naming Convention

```
YYYYMMDDHHMMSS_description.py
```

Examples:
- `20251118120000_add_user_preferences.py`
- `20251118150000_add_notification_tables.py`

### Safe Migration Workflow

1. **Development:**
   ```bash
   # Create migration
   alembic revision --autogenerate -m "description"

   # Test locally
   alembic upgrade head
   python scripts/test_migrations.py
   ```

2. **Staging:**
   ```bash
   # Apply and verify
   alembic upgrade head
   python scripts/test_migrations.py

   # Test application
   python -m pytest
   ```

3. **Production:**
   ```bash
   # Backup database first!
   pg_dump your_database > backup.sql

   # Apply migration
   alembic upgrade head

   # Verify
   python scripts/test_migrations.py
   ```

### Rollback Strategy

```bash
# Immediate rollback (if just applied)
alembic downgrade -1

# Restore from backup (if issues persist)
psql your_database < backup.sql
```

---

## Database Setup from Scratch

### Option 1: Using Migrations (Recommended)

```bash
# 1. Ensure database exists
createdb your_database_name

# 2. Configure environment
cp .env.example .env
# Edit DATABASE_URL in .env

# 3. Apply migrations
alembic upgrade head

# 4. Verify
python scripts/test_migrations.py
```

### Option 2: Using Models Directly

```bash
# Only for development!
python scripts/fix_missing_tables.py
```

**Note:** This bypasses migrations and creates tables directly from models. Use only for development or emergency recovery.

---

## Troubleshooting

### Check Migration Status

```bash
# Current revision
alembic current

# Pending migrations
alembic show head

# Full history
alembic history --verbose
```

### Verify Table Creation

```bash
# Count tables
psql -d your_database -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# List all tables
psql -d your_database -c "\dt"

# Check specific table
psql -d your_database -c "\d customers"
```

### Check Logs

```bash
# Enable SQL logging in .env
DATABASE_ECHO=true

# Run migration with verbose output
alembic upgrade head --sql > migration.sql
```

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Need Help?

1. Run the test script: `python scripts/test_migrations.py`
2. Check the logs
3. Review this guide
4. Check Alembic documentation

For emergency recovery:
```bash
python scripts/test_migrations.py --reset
alembic upgrade head
```