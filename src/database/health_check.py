"""
Database health check utility
Run this to verify database connection and pool status
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import (
    check_db_health,
    get_db_version,
    get_db_session,
    close_db
)
from src.database.models import Customer, Conversation, Message, AgentPerformance
from sqlalchemy import text, func


async def run_health_check():
    """Run comprehensive database health check"""
    
    print("=" * 70)
    print("DATABASE HEALTH CHECK")
    print("=" * 70)
    
    # 1. Connection test
    print("\n1. Testing database connection...")
    health = await check_db_health()
    
    if health['status'] == 'healthy':
        print(f"   ✓ Status: {health['status']}")
        print(f"   ✓ Database: {health['database']}")
        print(f"   Pool Status:")
        for key, value in health['pool'].items():
            print(f"      - {key}: {value}")
    else:
        print(f"   ✗ Status: {health['status']}")
        print(f"   ✗ Error: {health.get('error', 'Unknown')}")
        return False
    
    # 2. Version check
    print("\n2. PostgreSQL version...")
    version = await get_db_version()
    print(f"   {version}")
    
    # 3. Table existence check
    print("\n3. Checking tables...")
    async with get_db_session() as session:
        tables = {
            'customers': Customer,
            'conversations': Conversation,
            'messages': Message,
            'agent_performance': AgentPerformance
        }
        
        for table_name, model in tables.items():
            try:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = result.scalar()
                print(f"   ✓ {table_name}: {count} records")
            except Exception as e:
                print(f"   ✗ {table_name}: Error - {e}")
    
    # 4. Index check
    print("\n4. Checking indexes...")
    async with get_db_session() as session:
        result = await session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """))
        
        indexes = result.fetchall()
        print(f"   Found {len(indexes)} indexes:")
        
        current_table = None
        for schema, table, index in indexes:
            if table != current_table:
                print(f"\n   {table}:")
                current_table = table
            print(f"      - {index}")
    
    # 5. Performance test
    print("\n5. Testing query performance...")
    async with get_db_session() as session:
        import time
        
        # Simple query
        start = time.time()
        await session.execute(text("SELECT 1"))
        simple_time = (time.time() - start) * 1000
        print(f"   Simple query: {simple_time:.2f}ms")
        
        # Count query
        start = time.time()
        result = await session.execute(
            text("SELECT COUNT(*) FROM conversations")
        )
        result.scalar()
        count_time = (time.time() - start) * 1000
        print(f"   Count query: {count_time:.2f}ms")
    
    print("\n" + "=" * 70)
    print("✓ HEALTH CHECK COMPLETE")
    print("=" * 70)
    
    return True


async def main():
    """Main function"""
    try:
        success = await run_health_check()
        
        # Cleanup
        await close_db()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        import traceback
        traceback.print_exc()
        
        await close_db()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())