"""
Database package - PostgreSQL persistence layer with async support

This package provides:
- SQLAlchemy ORM models (database/models/)
- Pydantic schemas for validation (database/schemas/)
- Repository pattern for data access (database/repositories/)
- Connection management with pooling (database/connection.py)
- Alembic migrations for schema versioning

Usage:
    # Import models
    from database.models import Customer, Conversation, Message
    
    # Import schemas
    from database.schemas import CustomerCreate, ConversationResponse
    
    # Import repositories
    from database.repositories import CustomerRepository
    
    # Get database session
    from database.connection import get_db_session
    
    async with get_db_session() as session:
        repo = CustomerRepository(session)
        customer = await repo.get_by_email("user@example.com")
"""

# Models
from database.models import (
    Base,
    BaseModel,
    Customer,
    Conversation,
    Message,
    AgentPerformance,
)

# Schemas
from database.schemas import (
    CustomerCreate,
    CustomerResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    AgentPerformanceCreate,
    AgentPerformanceResponse,
)

# Repositories
from database.repositories import (
    CustomerRepository,
    ConversationRepository,
    MessageRepository,
    AgentPerformanceRepository,
)

# Connection
from database.connection import (
    get_db_session,
    init_db,
    close_db,
    check_db_health,
    get_db_version,
)

__version__ = "2.0.0"

__all__ = [
    # Models
    "Base",
    "BaseModel",
    "Customer",
    "Conversation",
    "Message",
    "AgentPerformance",
    # Schemas
    "CustomerCreate",
    "CustomerResponse",
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
    "AgentPerformanceCreate",
    "AgentPerformanceResponse",
    # Repositories
    "CustomerRepository",
    "ConversationRepository",
    "MessageRepository",
    "AgentPerformanceRepository",
    # Connection
    "get_db_session",
    "init_db",
    "close_db",
    "check_db_health",
    "get_db_version",
]