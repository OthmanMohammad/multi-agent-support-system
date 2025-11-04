"""
Customer model - User accounts
"""
from sqlalchemy import Column, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from database.models.base import BaseModel, TimestampMixin


class Customer(BaseModel, TimestampMixin):
    """Customer/User account"""
    
    __tablename__ = "customers"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core Fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    plan = Column(String(50), default="free", nullable=False, index=True)
    
    # Flexible metadata for additional customer info
    extra_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'basic', 'premium', 'enterprise')",
            name="check_customer_plan_values"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, email={self.email}, plan={self.plan})>"