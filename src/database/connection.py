"""
Database connection management with async connection pooling
Production-grade configuration with health checks
Uses centralized configuration management
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings
from src.utils.logging.setup import get_logger

if TYPE_CHECKING:
    from sqlalchemy.pool import Pool

# Initialize logger
logger = get_logger(__name__)

# Load settings
settings = get_settings()

# Global engine instance
_engine: AsyncEngine | None = None


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with production settings

    Returns:
        Configured async engine
    """
    engine = create_async_engine(
        str(settings.database.url),
        echo=settings.database.echo,  # Log SQL statements (disable in production)
        pool_size=settings.database.pool_size,  # Number of permanent connections
        max_overflow=settings.database.max_overflow,  # Additional connections under load
        pool_timeout=settings.database.pool_timeout,  # Seconds to wait for connection
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=settings.database.pool_recycle,  # Recycle connections after N seconds
        # Connection arguments
        connect_args={
            "server_settings": {
                "application_name": "multi_agent_support",
                "jit": "off",  # Disable JIT for faster simple queries
            }
        },
    )

    # Log connection pool events (useful for debugging)
    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.debug("database_connection_established")

    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        logger.debug("connection_checked_out_from_pool")

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
            "database_engine_created",
            environment=settings.environment,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
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
            logger.error(
                "database_session_error", error=str(e), error_type=type(e).__name__, exc_info=True
            )
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - verify connection and check table status
    Should be called on application startup

    Note: Tables should be created by running create_tables.py script
    or using Alembic migrations (alembic upgrade head).
    This function just verifies the database is accessible and reports status.
    """
    from sqlalchemy import inspect

    from src.database.models import Base

    logger.info("database_initialization_started", environment=settings.environment)
    engine = get_engine()

    # Just verify connection and report table status
    try:
        async with engine.begin() as conn:
            # Get list of existing tables
            def get_existing_tables(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())

            existing_tables = await conn.run_sync(get_existing_tables)

            # Get list of tables in our models
            model_tables = set(Base.metadata.tables.keys())

            # Find missing tables
            missing_tables = model_tables - existing_tables

            if missing_tables:
                logger.error(
                    "missing_database_tables",
                    missing_count=len(missing_tables),
                    total_expected=len(model_tables),
                    missing_tables=sorted(missing_tables)[:20],  # Log first 20
                )
                logger.error(
                    "database_not_initialized",
                    message="Run 'alembic upgrade head' to create all tables using migrations",
                )
            else:
                logger.info("database_tables_verified", table_count=len(model_tables))
    except Exception as e:
        logger.error("database_connection_failed", error=str(e), error_type=type(e).__name__)
        raise


async def close_db():
    """
    Close database connections
    Should be called on application shutdown
    """
    global _engine
    if _engine is not None:
        logger.info("database_connections_closing", environment=settings.environment)
        await _engine.dispose()
        logger.info("database_connections_closed")
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
                "total": pool.size() + pool.overflow(),
            }

            logger.debug(
                "database_health_check_passed",
                pool_size=pool_status["size"],
                checked_out=pool_status["checked_out"],
            )

            return {
                "status": "healthy",
                "database": "postgresql",
                "environment": settings.environment,
                "pool": pool_status,
            }
    except Exception as e:
        logger.error(
            "database_health_check_failed", error=str(e), error_type=type(e).__name__, exc_info=True
        )
        return {"status": "unhealthy", "error": str(e)}


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
            logger.debug("database_version_retrieved", version_info=version[:50])
            return version
    except Exception as e:
        logger.error("database_version_retrieval_failed", error=str(e), error_type=type(e).__name__)
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
        if health["status"] == "healthy":
            print(f"   Environment: {health['environment']}")
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
