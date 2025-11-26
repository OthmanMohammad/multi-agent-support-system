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
    from src.database.models import Customer, Conversation, Message

    # Import schemas
    from src.database.schemas import CustomerCreate, ConversationResponse

    # Import repositories
    from src.database.repositories import CustomerRepository

    # Import Unit of Work (RECOMMENDED)
    from database import get_unit_of_work

    async with get_unit_of_work() as uow:
        customer = await uow.customers.create(...)
        conversation = await uow.conversations.create(...)
        # Transaction commits automatically

    # Legacy: Get database session
    from src.database.connection import get_db_session

    async with get_db_session() as session:
        repo = CustomerRepository(session)
        customer = await repo.get_by_email("user@example.com")
"""

# Models
# Connection
from src.database.connection import (
    check_db_health,
    close_db,
    get_db_session,
    get_db_version,
    init_db,
)
from src.database.models import (
    AgentPerformance,
    AuditMixin,
    Base,
    BaseModel,
    Conversation,
    Customer,
    Message,
    TimestampMixin,
)

# Repositories
from src.database.repositories import (
    AgentPerformanceRepository,
    ConversationRepository,
    CustomerRepository,
    MessageRepository,
)

# Schemas
from src.database.schemas import (
    AgentPerformanceCreate,
    AgentPerformanceResponse,
    ConversationCreate,
    ConversationResponse,
    CustomerCreate,
    CustomerResponse,
    MessageCreate,
    MessageResponse,
)

# Unit of Work (NEW - RECOMMENDED)
from src.database.unit_of_work import (
    UnitOfWork,
    get_unit_of_work,
    get_uow,
)

__version__ = "2.0.0"

__all__ = [
    "AgentPerformance",
    "AgentPerformanceCreate",
    "AgentPerformanceRepository",
    "AgentPerformanceResponse",
    "AuditMixin",
    # Models
    "Base",
    "BaseModel",
    "Conversation",
    "ConversationCreate",
    "ConversationRepository",
    "ConversationResponse",
    "Customer",
    # Schemas
    "CustomerCreate",
    # Repositories
    "CustomerRepository",
    "CustomerResponse",
    "Message",
    "MessageCreate",
    "MessageRepository",
    "MessageResponse",
    "TimestampMixin",
    # Unit of Work (NEW)
    "UnitOfWork",
    "check_db_health",
    "close_db",
    # Connection
    "get_db_session",
    "get_db_version",
    "get_unit_of_work",
    "get_uow",
    "init_db",
]
