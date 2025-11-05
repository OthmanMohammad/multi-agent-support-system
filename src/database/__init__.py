"""
Database package - PostgreSQL persistence layer with async support

This package provides:
- SQLAlchemy ORM models (database/models/)
- Pydantic schemas for validation (database/schemas/)
- Repository pattern for data access (database/repositories/)
- Unit of Work for transaction management (database/unit_of_work.py)
- Connection management with pooling (database/connection.py)
- Alembic migrations for schema versioning

Usage:
    # Import models
    from database.models import Customer, Conversation, Message
    
    # Import schemas
    from database.schemas import CustomerCreate, ConversationResponse
    
    # Import repositories
    from database.repositories import CustomerRepository
    
    # Import Unit of Work (RECOMMENDED)
    from database import get_unit_of_work
    
    async with get_unit_of_work() as uow:
        customer = await uow.customers.create(...)
        conversation = await uow.conversations.create(...)
        # Transaction commits automatically
    
    # Legacy: Get database session
    from database.connection import get_db_session
    
    async with get_db_session() as session:
        repo = CustomerRepository(session)
        customer = await repo.get_by_email("user@example.com")
"""

# Models
from database.models import (
    Base,
    BaseModel,
    TimestampMixin,
    AuditMixin,
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

# Unit of Work (NEW - RECOMMENDED)
from database.unit_of_work import (
    UnitOfWork,
    get_unit_of_work,
    get_uow,
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
    "TimestampMixin",
    "AuditMixin",
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
    # Unit of Work (NEW)
    "UnitOfWork",
    "get_unit_of_work",
    "get_uow",
    # Connection
    "get_db_session",
    "init_db",
    "close_db",
    "check_db_health",
    "get_db_version",
]