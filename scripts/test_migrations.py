"""
Test Database Migrations

This script verifies that Alembic migrations work correctly and create all expected tables.

Usage:
    python scripts/test_migrations.py [--reset]

    --reset: Drop all tables and recreate from scratch (WARNING: Destructive)
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


async def check_migration_chain():
    """
    Check if Alembic migration chain is correct

    Returns:
        True if chain is valid, False otherwise
    """
    print("\n[1/5] Checking Alembic migration chain...")

    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "history"],
            capture_output=True,
            text=True,
            check=True
        )

        # Check if there are any issues
        if "head" not in result.stdout:
            print("✗ Migration chain issue detected")
            print(result.stdout)
            return False

        print("✓ Migration chain is valid")

        # Show the chain
        print("\nMigration chain:")
        for line in result.stdout.split('\n')[:10]:  # Show first 10 lines
            if line.strip():
                print(f"  {line}")

        return True

    except FileNotFoundError:
        print("✗ Alembic not found. Install with: pip install alembic")
        return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Alembic error: {e.stderr}")
        return False


async def get_current_revision():
    """Get current database revision"""
    print("\n[2/5] Checking current database revision...")

    engine = get_engine()

    try:
        async with engine.connect() as conn:
            # Check if alembic_version table exists
            def check_table(sync_conn):
                inspector = inspect(sync_conn)
                return 'alembic_version' in inspector.get_table_names()

            has_version_table = await conn.run_sync(check_table)

            if not has_version_table:
                print("⚠ No alembic_version table - database not initialized")
                return None

            # Get current version
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()

            if version:
                print(f"✓ Current revision: {version}")
            else:
                print("⚠ No revision applied yet")

            return version

    except Exception as e:
        print(f"✗ Error checking revision: {e}")
        return None


async def count_tables():
    """Count tables in database"""
    print("\n[3/5] Counting database tables...")

    engine = get_engine()

    try:
        async with engine.connect() as conn:
            def get_table_count(sync_conn):
                inspector = inspect(sync_conn)
                tables = inspector.get_table_names()
                return len(tables), tables

            count, tables = await conn.run_sync(get_table_count)

            print(f"✓ Found {count} tables in database")

            # Show first 10 tables
            if tables:
                print("\n  Sample tables:")
                for table in sorted(tables)[:10]:
                    print(f"    - {table}")
                if count > 10:
                    print(f"    ... and {count - 10} more")

            return count, tables

    except Exception as e:
        print(f"✗ Error counting tables: {e}")
        return 0, []


async def verify_models_vs_db():
    """Verify that all models have corresponding tables"""
    print("\n[4/5] Verifying models vs database...")

    engine = get_engine()

    try:
        async with engine.connect() as conn:
            def check_models(sync_conn):
                inspector = inspect(sync_conn)
                existing_tables = set(inspector.get_table_names())
                model_tables = set(Base.metadata.tables.keys())

                missing = model_tables - existing_tables
                extra = existing_tables - model_tables

                return {
                    'existing': existing_tables,
                    'expected': model_tables,
                    'missing': missing,
                    'extra': extra
                }

            result = await conn.run_sync(check_models)

            print(f"  Expected tables (from models): {len(result['expected'])}")
            print(f"  Existing tables (in database): {len(result['existing'])}")

            if result['missing']:
                print(f"\n⚠ Missing {len(result['missing'])} tables:")
                for table in sorted(list(result['missing']))[:20]:
                    print(f"    - {table}")
                if len(result['missing']) > 20:
                    print(f"    ... and {len(result['missing']) - 20} more")
                return False

            if result['extra']:
                print(f"\n✓ Found {len(result['extra'])} extra tables (e.g., alembic_version, indexes)")

            print("\n✓ All model tables exist in database")
            return True

    except Exception as e:
        print(f"✗ Error verifying models: {e}")
        return False


async def run_test_query():
    """Run a simple test query"""
    print("\n[5/5] Running test query...")

    engine = get_engine()

    try:
        async with engine.connect() as conn:
            # Test a simple query
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' LIMIT 5"
            ))
            tables = [row[0] for row in result]

            print(f"✓ Successfully queried database")
            print(f"  Sample tables: {', '.join(tables)}")

            return True

    except Exception as e:
        print(f"✗ Error running query: {e}")
        return False


async def reset_database():
    """
    Reset database by dropping all tables (WARNING: Destructive!)

    This is useful for testing migrations from scratch.
    """
    print("\n" + "!" * 70)
    print("WARNING: This will DROP ALL TABLES in the database!")
    print("!" * 70)

    response = input("\nType 'DELETE EVERYTHING' to confirm: ")
    if response != "DELETE EVERYTHING":
        print("\nCancelled.")
        return False

    print("\nDropping all tables...")

    engine = get_engine()

    try:
        async with engine.begin() as conn:
            # Get all table names in the public schema
            result = await conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]

            if tables:
                print(f"  Found {len(tables)} tables to drop")

                # Drop all tables with CASCADE to handle dependencies
                for table in tables:
                    print(f"    Dropping {table}...")
                    await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

                print("✓ All tables dropped")
            else:
                print("  No tables to drop")

            return True

    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return False


async def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test database migrations")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (drop all tables)'
    )

    args = parser.parse_args()

    setup_logging()

    print("=" * 70)
    print("DATABASE MIGRATION TEST")
    print("=" * 70)

    if args.reset:
        if not await reset_database():
            sys.exit(1)

        print("\n" + "=" * 70)
        print("Now run: alembic upgrade head")
        print("=" * 70)
        await close_db()
        return

    # Run tests
    tests_passed = True

    # Test 1: Check migration chain
    if not await check_migration_chain():
        tests_passed = False

    # Test 2: Check current revision
    current_revision = await get_current_revision()

    # Test 3: Count tables
    count, tables = await count_tables()

    # Test 4: Verify models vs DB
    if not await verify_models_vs_db():
        tests_passed = False

    # Test 5: Run test query
    if not await run_test_query():
        tests_passed = False

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if tests_passed:
        print("\n✓ All tests passed!")
        print(f"\n  Current revision: {current_revision or 'None'}")
        print(f"  Tables in database: {count}")
        print(f"  Expected tables: {len(Base.metadata.tables)}")

        if count < len(Base.metadata.tables):
            print("\n⚠ Some tables are missing. Run:")
            print("  alembic upgrade head")
    else:
        print("\n✗ Some tests failed!")
        print("\nTo fix:")
        print("  1. Check migration chain: alembic history")
        print("  2. Apply migrations: alembic upgrade head")
        print("  3. Or reset and reapply: python scripts/test_migrations.py --reset")
        print("                          alembic upgrade head")

    print()

    await close_db()

    return 0 if tests_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)