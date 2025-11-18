"""
Fix Migration State

This script fixes the issue where tables exist but alembic_version is out of sync.
This happens when tables are created by fix_missing_tables.py instead of migrations.

Usage:
    python scripts/fix_migration_state.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from src.database.connection import get_engine, close_db
from src.database.models import Base
from src.utils.logging.setup import setup_logging, get_logger


async def check_tables_exist():
    """Check which tables exist in database"""
    print("\n[1/3] Checking which tables exist...")

    engine = get_engine()

    async with engine.connect() as conn:
        def get_tables(sync_conn):
            inspector = inspect(sync_conn)
            return set(inspector.get_table_names())

        existing_tables = await conn.run_sync(get_tables)

    # Tables from each migration
    tier4_tables = [
        'ml_predictions', 'churn_predictions', 'ltv_predictions',
        'prediction_explanations', 'prediction_features',
        'personalization_rules', 'content_recommendations', 'recommendation_feedback',
        'competitor_mentions', 'competitive_analysis', 'market_trends',
        'sentiment_analysis', 'content_library', 'content_performance',
        'learning_events', 'model_performance', 'feedback_analysis'
    ]

    auth_tables = ['users', 'api_keys', 'sessions']

    tier3_tables = [
        'ab_tests', 'ab_test_experiments', 'ab_test_results',
        'automated_tasks', 'automation_workflow_executions', 'automation_triggers',
        'test_runs', 'test_cases', 'bug_reports', 'performance_metrics',
        'security_alerts', 'access_control_logs', 'compliance_reports', 'anomaly_detections'
    ]

    has_tier4 = any(t in existing_tables for t in tier4_tables)
    has_auth = any(t in existing_tables for t in auth_tables)
    has_tier3 = any(t in existing_tables for t in tier3_tables)

    print(f"  Tier 4 (Advanced) tables: {'✓ Present' if has_tier4 else '✗ Missing'}")
    print(f"  Auth tables: {'✓ Present' if has_auth else '✗ Missing'}")
    print(f"  Tier 3 (Operational) tables: {'✓ Present' if has_tier3 else '✗ Missing'}")
    print(f"  Total tables: {len(existing_tables)}")

    # Determine which revision we should be at
    if has_tier4:
        target_revision = '20251117000000'
        print(f"\n  → Should be at: {target_revision} (Tier 4)")
    elif has_auth:
        target_revision = '20251116120000'
        print(f"\n  → Should be at: {target_revision} (Auth)")
    elif has_tier3:
        target_revision = '20251116000000'
        print(f"\n  → Should be at: {target_revision} (Tier 3)")
    else:
        target_revision = '20251114120000'
        print(f"\n  → Should be at: {target_revision} (Schema Expansion)")

    return target_revision


async def get_current_revision():
    """Get current alembic revision"""
    print("\n[2/3] Checking alembic version...")

    engine = get_engine()

    async with engine.connect() as conn:
        # Check if alembic_version exists
        def has_table(sync_conn):
            inspector = inspect(sync_conn)
            return 'alembic_version' in inspector.get_table_names()

        if not await conn.run_sync(has_table):
            print("  ⚠ No alembic_version table")
            return None

        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()

        if version:
            print(f"  Current revision: {version}")
        else:
            print("  ⚠ No revision recorded")

        return version


async def stamp_revision(target_revision: str):
    """Stamp database with correct revision"""
    print(f"\n[3/3] Stamping database with revision: {target_revision}")

    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "stamp", target_revision],
            capture_output=True,
            text=True,
            check=True
        )

        print("  ✓ Database stamped successfully")
        print(f"\n  Output: {result.stdout}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to stamp: {e.stderr}")
        return False
    except FileNotFoundError:
        print("  ✗ Alembic not found")
        return False


async def main():
    """Main function"""
    setup_logging()

    print("=" * 70)
    print("FIX MIGRATION STATE")
    print("=" * 70)
    print()
    print("This script will synchronize alembic_version with actual table state.")
    print("Use this when tables exist but alembic is out of sync.")
    print()

    # Step 1: Check which tables exist
    target_revision = await check_tables_exist()

    # Step 2: Check current revision
    current_revision = await get_current_revision()

    # Step 3: Stamp if needed
    if current_revision == target_revision:
        print("\n" + "=" * 70)
        print("✓ Already at correct revision!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("ACTION REQUIRED")
        print("=" * 70)
        print(f"\nCurrent: {current_revision or 'None'}")
        print(f"Target:  {target_revision}")
        print()
        print("This will update alembic_version without running migrations.")
        print("Only do this if tables already exist!")
        print()

        response = input("Stamp database with correct revision? [y/N]: ")

        if response.lower() == 'y':
            success = await stamp_revision(target_revision)

            if success:
                print("\n" + "=" * 70)
                print("✓ Migration state fixed!")
                print("=" * 70)
                print()
                print("Next steps:")
                print("  1. Verify: alembic current")
                print("  2. Test: python scripts/test_migrations.py")
            else:
                print("\n✗ Failed to fix migration state")
                sys.exit(1)
        else:
            print("\nCancelled.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(main())