"""
Fix missing database tables by creating them directly from SQLAlchemy models.

This is a quick fix for when Alembic thinks migrations are applied but tables don't exist.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, text
from src.database.models import Base
from src.core.config import get_settings


async def create_missing_tables():
    """Create only the missing tables"""
    settings = get_settings()

    print("=" * 80)
    print("FIXING MISSING DATABASE TABLES")
    print("=" * 80)
    print(f"\nEnvironment: {settings.environment}")
    print(f"Database: {str(settings.database.url).split('@')[1] if '@' in str(settings.database.url) else 'localhost'}")

    # Create engine
    engine = create_async_engine(
        str(settings.database.url),
        echo=True  # Show SQL statements
    )

    try:
        # Check what tables exist
        async with engine.begin() as conn:
            def get_existing_tables(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())

            existing_tables = await conn.run_sync(get_existing_tables)

        # Get list of tables in our models
        model_tables = set(Base.metadata.tables.keys())

        # Find missing tables
        missing_tables = model_tables - existing_tables

        print(f"\n{'='*80}")
        print(f"ANALYSIS:")
        print(f"{'='*80}")
        print(f"Total expected tables: {len(model_tables)}")
        print(f"Existing tables: {len(existing_tables)}")
        print(f"Missing tables: {len(missing_tables)}")

        if missing_tables:
            print(f"\nMissing tables:")
            for table in sorted(missing_tables):
                print(f"  - {table}")

            print(f"\n{'='*80}")
            print("CREATING MISSING TABLES...")
            print(f"{'='*80}\n")

            # Create tables one by one, each in its own transaction
            created_count = 0
            skipped_count = 0
            error_count = 0

            for table_name in sorted(missing_tables):
                table = Base.metadata.tables[table_name]
                try:
                    # Create each table in its own transaction
                    async with engine.begin() as table_conn:
                        def create_single_table(sync_conn):
                            table.create(sync_conn, checkfirst=True)

                        await table_conn.run_sync(create_single_table)

                    print(f"  ✓ Created: {table_name}")
                    created_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if "already exists" in error_msg.lower():
                        print(f"  ⊘ Skipped (already exists): {table_name}")
                        skipped_count += 1
                    else:
                        print(f"  ✗ Error creating {table_name}: {error_msg[:150]}")
                        error_count += 1

            print(f"\n{'='*80}")
            print(f"SUMMARY:")
            print(f"  Created: {created_count} tables")
            print(f"  Skipped: {skipped_count} tables (already existed)")
            print(f"  Errors: {error_count} tables")
            print(f"{'='*80}")

            if created_count > 0 or skipped_count > 0:
                print("✓ Database setup complete!")
            else:
                print("⚠ No tables were created - check errors above")
        else:
            print(f"\n✓ No missing tables - database is complete!")

    finally:
        await engine.dispose()

    print("\nYou can now start your application:")
    print("python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000\n")


if __name__ == "__main__":
    asyncio.run(create_missing_tables())