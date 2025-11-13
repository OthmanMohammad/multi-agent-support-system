"""
Database models - SQLAlchemy ORM models
DEPRECATED: Individual models moved to database/models/ directory
This file maintained for backward compatibility
"""
# Import all models for backward compatibility
from src.database.models.base import Base, BaseModel, TimestampMixin
from src.database.models.customer import Customer
from src.database.models.conversation import Conversation
from src.database.models.message import Message
from src.database.models.agent_performance import AgentPerformance

# Re-export everything
__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "Customer",
    "Conversation",
    "Message",
    "AgentPerformance",
]

# Note: This file exists for backward compatibility with existing imports.
# New code should import from database.models directly:
#   from database.models import Customer, Conversation, Message