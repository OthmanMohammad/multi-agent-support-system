"""
Load SQL Data from JSON Files

This script loads JSON data files into the PostgreSQL database.
It handles all 20 tables with proper ordering for foreign key dependencies.

Usage:
    python scripts/load_sql_data.py [--reset] [--folder data/sql_seed]

    --reset: Delete existing data first (WARNING: Destructive!)
    --folder: Path to folder containing JSON files (default: data/sql_seed)
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Set
from decimal import Decimal
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import AsyncSessionLocal

# Import all models
from src.database.models import (
    Customer, Conversation, Message,
    Subscription, Invoice, Payment, UsageEvent, Credit,
    Employee, Lead, Deal, SalesActivity, Quote,
    FeatureUsage,
    CustomerHealthEvent, CustomerSegment, CustomerNote, CustomerContact, CustomerIntegration,
    AgentPerformance, AgentHandoff
)

# Table loading order (respects foreign key dependencies)
TABLE_ORDER = [
    # No dependencies
    "customers",
    "employees",

    # Depends on customers
    "subscriptions",
    "invoices",
    "payments",
    "credits",
    "usage_events",
    "customer_health_events",
    "customer_segments",
    "customer_notes",
    "customer_contacts",
    "customer_integrations",
    "conversations",
    "feature_usage",

    # Depends on employees/customers
    "leads",

    # Depends on leads/customers/employees
    "deals",
    "quotes",

    # Depends on deals/leads
    "sales_activities",

    # Depends on conversations
    "messages",

    # Agent-related
    "agent_performance",
    "agent_handoffs",
]

# Map table names to SQLAlchemy models
TABLE_TO_MODEL = {
    "customers": Customer,
    "employees": Employee,
    "subscriptions": Subscription,
    "invoices": Invoice,
    "payments": Payment,
    "credits": Credit,
    "usage_events": UsageEvent,
    "customer_health_events": CustomerHealthEvent,
    "customer_segments": CustomerSegment,
    "customer_notes": CustomerNote,
    "customer_contacts": CustomerContact,
    "customer_integrations": CustomerIntegration,
    "conversations": Conversation,
    "messages": Message,
    "leads": Lead,
    "deals": Deal,
    "quotes": Quote,
    "sales_activities": SalesActivity,
    "feature_usage": FeatureUsage,
    "agent_performance": AgentPerformance,
    "agent_handoffs": AgentHandoff,
}

# Unique fields per table that need deduplication
UNIQUE_FIELDS = {
    "customers": ["email", "id"],
    "employees": ["email", "id"],
    "leads": ["email", "id"],
    "quotes": ["quote_number", "id"],
    "subscriptions": ["id"],
    "invoices": ["id"],
    "payments": ["id"],
    "deals": ["id"],
    "conversations": ["id"],
    "messages": ["id"],
}

# Fields that should be converted to UUID
UUID_FIELDS = [
    "id", "customer_id", "conversation_id", "message_id", "subscription_id",
    "invoice_id", "payment_id", "lead_id", "deal_id", "employee_id",
    "assigned_to", "converted_to_customer_id", "article_id", "performed_by"
]

# Fields that should be converted to Decimal
DECIMAL_FIELDS = [
    "mrr", "arr", "value", "amount", "total_amount", "price", "balance",
    "need_score"
]

# Fields that should be converted to datetime
DATETIME_FIELDS = [
    "created_at", "updated_at", "started_at", "ended_at", "scheduled_at",
    "completed_at", "converted_at", "closed_at", "expected_close_date",
    "current_period_start", "current_period_end", "trial_start", "trial_end",
    "valid_until", "accepted_at", "last_used_at", "due_date", "paid_at",
    "last_login_at", "timestamp", "event_timestamp", "date"
]


def parse_value(key: str, value: Any) -> Any:
    """Parse a value to the correct Python type."""
    if value is None:
        return None

    # UUID fields
    if key in UUID_FIELDS:
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                return value

    # Decimal fields
    if key in DECIMAL_FIELDS:
        if isinstance(value, (int, float, str)):
            try:
                return Decimal(str(value))
            except:
                return None

    # Datetime fields
    if key in DATETIME_FIELDS:
        if isinstance(value, str):
            try:
                # Try various formats
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass

    return value


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both array and object with array property
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try common keys for data arrays
        for key in ['data', 'records', 'items']:
            if key in data and isinstance(data[key], list):
                return data[key]
        # Try first key that's a list
        for key, val in data.items():
            if isinstance(val, list):
                return val

    return []


def deduplicate_records(
    table_name: str,
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Remove duplicate records based on unique fields."""
    unique_fields = UNIQUE_FIELDS.get(table_name, ["id"])

    seen: Dict[str, Set] = {field: set() for field in unique_fields}
    deduplicated = []
    duplicates_removed = 0

    for record in records:
        is_duplicate = False

        for field in unique_fields:
            if field in record and record[field] is not None:
                value = str(record[field]).lower() if field == "email" else str(record[field])
                if value in seen[field]:
                    is_duplicate = True
                    break

        if not is_duplicate:
            # Add to seen sets
            for field in unique_fields:
                if field in record and record[field] is not None:
                    value = str(record[field]).lower() if field == "email" else str(record[field])
                    seen[field].add(value)
            deduplicated.append(record)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        print(f"   ⚠ Removed {duplicates_removed} duplicate records")

    return deduplicated


def process_record(record: Dict[str, Any], model_class) -> Dict[str, Any]:
    """Process a record, converting types as needed."""
    processed = {}

    for key, value in record.items():
        # Skip unknown fields
        if not hasattr(model_class, key):
            continue

        processed[key] = parse_value(key, value)

    return processed


async def clear_tables(session: AsyncSession):
    """Clear all tables in reverse order (to handle FK constraints)."""
    print("\n⚠️  Clearing existing data...")

    # Use a separate transaction for clearing
    try:
        # Disable FK checks temporarily and truncate all at once
        await session.execute(text("SET session_replication_role = 'replica'"))

        for table_name in reversed(TABLE_ORDER):
            if table_name in TABLE_TO_MODEL:
                try:
                    await session.execute(text(f"DELETE FROM {table_name}"))
                    print(f"  ✓ Cleared {table_name}")
                except Exception as e:
                    print(f"  ⚠ Could not clear {table_name}: {e}")

        # Re-enable FK checks
        await session.execute(text("SET session_replication_role = 'origin'"))
        await session.commit()
        print("✅ All tables cleared")

    except Exception as e:
        print(f"  ❌ Error during clear: {e}")
        await session.rollback()
        raise


async def load_table_data(
    session: AsyncSession,
    table_name: str,
    data: List[Dict[str, Any]]
) -> tuple[int, int]:
    """Load data into a specific table. Returns (loaded, skipped)."""
    if table_name not in TABLE_TO_MODEL:
        print(f"  ⚠ Unknown table: {table_name}, skipping")
        return 0, 0

    model_class = TABLE_TO_MODEL[table_name]
    loaded = 0
    skipped = 0
    errors = []

    for i, record in enumerate(data):
        try:
            # Process the record
            processed = process_record(record, model_class)

            if not processed:
                skipped += 1
                continue

            # Create model instance
            instance = model_class(**processed)
            session.add(instance)
            loaded += 1

            # Commit every 50 records to catch errors early and not lose all progress
            if loaded % 50 == 0:
                try:
                    await session.commit()
                except Exception as flush_error:
                    await session.rollback()
                    # Try to identify problematic record
                    errors.append(f"Batch ending at record {i}: {str(flush_error)[:80]}")
                    skipped += 1
                    loaded -= 1

        except Exception as e:
            errors.append(f"Record {i}: {str(e)[:80]}")
            skipped += 1

    # Final commit for remaining records
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        errors.append(f"Final commit: {str(e)[:80]}")

    if errors:
        print(f"  ⚠ {len(errors)} errors:")
        for error in errors[:3]:
            print(f"    - {error}")
        if len(errors) > 3:
            print(f"    ... and {len(errors) - 3} more")

    return loaded, skipped


async def load_sql_data(folder: str = "data/sql_seed", reset: bool = False):
    """Main function to load all SQL data from JSON files."""
    print("=" * 70)
    print("📥 LOADING SQL DATA FROM JSON FILES")
    print("=" * 70)
    print(f"\nSource folder: {folder}")

    folder_path = project_root / folder

    if not folder_path.exists():
        print(f"\n❌ Folder not found: {folder_path}")
        print("\nCreate the folder and add your JSON files:")
        print(f"  mkdir -p {folder}")
        print(f"  # Add your JSON files: customers.json, conversations.json, etc.")
        sys.exit(1)

    # Find all JSON files
    json_files = list(folder_path.glob("*.json"))

    if not json_files:
        print(f"\n❌ No JSON files found in {folder_path}")
        print("\nExpected files (one per table):")
        for table in TABLE_ORDER:
            print(f"  - {table}.json")
        sys.exit(1)

    print(f"\nFound {len(json_files)} JSON files:")
    for f in sorted(json_files):
        print(f"  • {f.name}")

    # Optionally clear existing data (separate session)
    if reset:
        async with AsyncSessionLocal() as clear_session:
            await clear_tables(clear_session)

    # Process files in the correct order
    total_loaded = 0
    total_skipped = 0
    stats = {}

    print("\n" + "-" * 70)
    print("LOADING DATA")
    print("-" * 70)

    # Process each table in a separate session to avoid transaction issues
    for table_name in TABLE_ORDER:
        # Find the matching file (try different naming conventions)
        possible_names = [
            f"{table_name}.json",
            f"{table_name}s.json",
            f"{table_name.replace('_', '-')}.json",
        ]

        file_path = None
        for name in possible_names:
            candidate = folder_path / name
            if candidate.exists():
                file_path = candidate
                break

        if not file_path:
            continue

        print(f"\n📄 Loading {table_name} from {file_path.name}...")

        try:
            data = load_json_file(file_path)
            print(f"   Found {len(data)} records in file")

            if data:
                # Deduplicate before loading
                data = deduplicate_records(table_name, data)
                print(f"   {len(data)} records after deduplication")

                # Use a fresh session for each table
                async with AsyncSessionLocal() as session:
                    loaded, skipped = await load_table_data(session, table_name, data)
                    stats[table_name] = loaded
                    total_loaded += loaded
                    total_skipped += skipped
                    print(f"   ✓ Loaded {loaded} records" + (f" (skipped {skipped})" if skipped else ""))

        except Exception as e:
            print(f"   ❌ Error: {e}")
            stats[table_name] = f"Error: {str(e)[:50]}"

    # Also check for any files that weren't in TABLE_ORDER
    processed_names = set(TABLE_ORDER)
    for json_file in json_files:
        table_name = json_file.stem.lower().replace('-', '_').rstrip('s')
        # Try singular form too
        if table_name not in processed_names and f"{table_name}s" not in processed_names:
            print(f"\n⚠️  Unknown file: {json_file.name} (not in TABLE_ORDER)")

    # Summary
    print("\n" + "=" * 70)
    print("✅ SQL DATA LOAD COMPLETE!")
    print("=" * 70)
    print(f"\nTotal records loaded: {total_loaded}")
    if total_skipped > 0:
        print(f"Total records skipped: {total_skipped}")
    print("\nBy table:")
    for table, count in sorted(stats.items()):
        if isinstance(count, int):
            print(f"  • {table}: {count:,} records")
        else:
            print(f"  • {table}: {count}")

    print("\n🎉 Your database is now populated with data!")
    print("\nNext steps:")
    print("  1. Load KB articles: python scripts/init_knowledge_base.py")
    print("  2. Start the API: python -m uvicorn src.api.main:app --reload")


def main():
    """Main entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load SQL data from JSON files into PostgreSQL database"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Clear existing data before loading (WARNING: Destructive!)'
    )
    parser.add_argument(
        '--folder',
        type=str,
        default='data/sql_seed',
        help='Path to folder containing JSON files (default: data/sql_seed)'
    )

    args = parser.parse_args()

    if args.reset:
        print("\n" + "!" * 70)
        print("WARNING: This will DELETE all existing data!")
        print("!" * 70)
        response = input("\nType 'YES' to confirm: ")
        if response != "YES":
            print("Cancelled.")
            sys.exit(0)

    asyncio.run(load_sql_data(folder=args.folder, reset=args.reset))


if __name__ == "__main__":
    main()
