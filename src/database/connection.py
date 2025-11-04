"""
Database connection management with async connection pooling
Production-grade configuration with health checks
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy import text, event
from sqlalchemy.pool import Pool
import os
import logging

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in environment. "
        "Please set it in your .env file"
    )

# Database connection settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# Global engine instance
_engine: Optional[AsyncEngine] = None


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with production settings
    
    Returns:
        Configured async engine
    """
    engine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO,  # Log SQL statements (disable in production)
        pool_size=DB_POOL_SIZE,  # Number of permanent connections
        max_overflow=DB_MAX_OVERFLOW,  # Additional connections under load
        pool_timeout=DB_POOL_TIMEOUT,  # Seconds to wait for connection
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=DB_POOL_RECYCLE,  # Recycle connections after N seconds
        # Connection arguments
        connect_args={
            "server_settings": {
                "application_name": "multi_agent_support",
                "jit": "off",  # Disable JIT for faster simple queries
            }
        }
    )
    
    # Log connection pool events (useful for debugging)
    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.debug("Database connection established")
    
    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.debug("Connection checked out from pool")
    
    return engine


def get_engine() -> AsyncEngine:
    """
    Get or create global engine instance
    
    Returns:
        Async engine
    """
    global _engine
    if _engine is None:
        _engine = create_engine()
        logger.info(
            f"Database engine created: "
            f"pool_size={DB_POOL_SIZE}, "
            f"max_overflow={DB_MAX_OVERFLOW}"
        )
    return _engine


# Create session factory
def create_session_factory() -> async_sessionmaker:
    """
    Create session factory with engine
    
    Returns:
        Session factory
    """
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Don't expire objects after commit
        autocommit=False,
        autoflush=False,
    )


# Global session factory
AsyncSessionLocal = create_session_factory()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with automatic commit/rollback
    
    Usage:
        async with get_db_session() as session:
            result = await session.execute(query)
            # Session automatically committed/rolled back
    
    Yields:
        Async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables
    Should be called on application startup
    """
    from database.models import Base
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")


async def close_db():
    """
    Close database connections
    Should be called on application shutdown
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database connections closed")
        _engine = None


async def check_db_health() -> dict:
    """
    Check database connection health
    
    Returns:
        Dict with health status
    """
    try:
        engine = get_engine()
        
        async with engine.connect() as conn:
            # Test query
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
            
            # Get pool status
            pool: Pool = engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow()
            }
            
            return {
                "status": "healthy",
                "database": "postgresql",
                "pool": pool_status
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def get_db_version() -> str:
    """
    Get PostgreSQL version
    
    Returns:
        Version string
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            return version
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return "unknown"


if __name__ == "__main__":
    import asyncio
    
    async def test():
        """Test database connection"""
        print("=" * 60)
        print("Testing Database Connection")
        print("=" * 60)
        
        # Test connection
        print("\n1. Testing connection...")
        health = await check_db_health()
        print(f"   Status: {health['status']}")
        if health['status'] == 'healthy':
            print(f"   Pool size: {health['pool']['size']}")
            print(f"   Checked out: {health['pool']['checked_out']}")
        
        # Get version
        print("\n2. Getting PostgreSQL version...")
        version = await get_db_version()
        print(f"   {version}")
        
        # Test session
        print("\n3. Testing session creation...")
        async with get_db_session() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"   Connected to database: {db_name}")
        
        print("\n✓ All tests passed!")
        
        # Cleanup
        await close_db()
    
    asyncio.run(test())