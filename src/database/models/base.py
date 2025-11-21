"""
Base SQLAlchemy model
"""
from sqlalchemy import Column, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, declared_attr
from datetime import datetime, UTC
from typing import Optional
import uuid

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class AuditMixin:
    """
    Mixin for audit trail tracking
    Tracks who created, updated, and deleted records
    """
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None):
        """Mark record as deleted"""
        self.deleted_at = datetime.now(UTC)
        self.deleted_by = deleted_by
    
    def restore(self):
        """Restore soft deleted record"""
        self.deleted_at = None
        self.deleted_by = None


class BaseModel(Base, TimestampMixin, AuditMixin):
    """
    Base model with common functionality
    All models should inherit from this

    Features:
    - UUID primary key (id)
    - Automatic timestamps (created_at, updated_at)
    - Audit trail (created_by, updated_by, deleted_by)
    - Soft delete support (deleted_at)
    - Automatic table naming
    - to_dict() helper method
    """
    __abstract__ = True

    # Primary key (UUID)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key (UUID)"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name"""
        # Convert CamelCase to snake_case and pluralize
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return name + 's'
    
    @declared_attr
    def __table_args__(cls):
        """Add index for soft delete queries on all tables"""
        table_name = cls.__tablename__ if hasattr(cls, '__tablename__') else None
        if table_name:
            return (
                Index(
                    f'idx_{table_name}_not_deleted',
                    'deleted_at',
                    postgresql_where=text('deleted_at IS NULL')
                ),
            )
        return tuple()
    
    def to_dict(self, exclude_deleted: bool = True) -> dict:
        """
        Convert model to dictionary
        
        Args:
            exclude_deleted: Exclude audit fields if True
            
        Returns:
            Dictionary representation of model
        """
        data = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        
        if exclude_deleted:
            # Remove audit fields from output
            data.pop('deleted_at', None)
            data.pop('deleted_by', None)
        
        return data
    
    def __repr__(self) -> str:
        """String representation"""
        id_val = getattr(self, 'id', None)
        deleted = " [DELETED]" if self.is_deleted else ""
        return f"<{self.__class__.__name__}(id={id_val}){deleted}>"