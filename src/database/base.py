"""
Base repository with comprehensive CRUD operations
All repositories inherit from this
"""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import DeclarativeMeta
from uuid import UUID
from datetime import datetime, UTC

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with comprehensive CRUD operations
    
    Features:
    - Basic CRUD (Create, Read, Update, Delete)
    - Soft delete support with audit trail
    - Bulk operations
    - Pagination helpers
    - Existence checks
    - Query filtering
    
    Design Principles:
    - Single Responsibility: Each method does one thing well
    - Defensive Programming: Handles edge cases gracefully
    - Type Safety: Full type hints for IDE support
    - Audit Trail: Tracks who did what and when
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def create(self, created_by: Optional[UUID] = None, **kwargs) -> ModelType:
        """
        Create a new record with audit trail
        
        Args:
            created_by: UUID of user creating the record
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
        """
        if created_by and hasattr(self.model, 'created_by'):
            kwargs['created_by'] = created_by
        
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def bulk_create(
        self, 
        items: List[dict],
        created_by: Optional[UUID] = None
    ) -> List[ModelType]:
        """
        Create multiple records in one transaction
        
        Args:
            items: List of dicts with field values
            created_by: UUID of user creating the records
            
        Returns:
            List of created instances
        """
        if created_by and hasattr(self.model, 'created_by'):
            for item in items:
                item['created_by'] = created_by
        
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        
        # Refresh all instances
        for instance in instances:
            await self.session.refresh(instance)
        
        return instances
    
    async def get_by_id(
        self, 
        id: UUID,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get record by ID
        
        Args:
            id: Record UUID
            include_deleted: Include soft deleted records if True
            
        Returns:
            Model instance or None
        """
        query = select(self.model).where(self.model.id == id)
        
        # Exclude soft deleted by default
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        ascending: bool = False,
        exclude_deleted: bool = True
    ) -> List[ModelType]:
        """
        Get all records with pagination
        
        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            order_by: Field to order by
            ascending: Sort ascending if True, descending if False
            exclude_deleted: Exclude soft deleted records if True
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Exclude soft deleted
        if exclude_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        
        # Apply ordering
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if ascending:
                query = query.order_by(order_column.asc())
            else:
                query = query.order_by(order_column.desc())
        
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self, 
        id: UUID,
        updated_by: Optional[UUID] = None,
        _allow_none: bool = False,
        **kwargs
    ) -> Optional[ModelType]:
        """
        Update record by ID with audit trail
        
        Args:
            id: Record UUID
            updated_by: UUID of user updating the record
            _allow_none: If True, allows setting fields to NULL (for restoration)
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None
            
        Note:
            By default, None values are filtered out to distinguish between
            "field not provided" and "field set to NULL". Use _allow_none=True
            for operations like restore() that need to explicitly set NULL.
        """
        # Filter out None values unless explicitly allowed
        if _allow_none:
            update_data = kwargs.copy()
        else:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(id, include_deleted=True)
        
        # Add audit trail
        if updated_by and hasattr(self.model, 'updated_by'):
            update_data['updated_by'] = updated_by
        
        result = await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        
        # Check if record was found
        if result.rowcount == 0:
            return None
        
        await self.session.flush()
        
        # Include deleted records in case we're operating on soft-deleted data
        return await self.get_by_id(id, include_deleted=True)
    
    async def delete(self, id: UUID) -> bool:
        """
        Hard delete record by ID
        
        WARNING: This permanently removes the record.
        Consider using soft_delete_by_id() instead for audit trail.
        
        Args:
            id: Record UUID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def soft_delete_by_id(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None
    ) -> Optional[ModelType]:
        """
        Soft delete record (mark as deleted without removing)
        
        Args:
            id: Record UUID
            deleted_by: UUID of user deleting the record
            
        Returns:
            Updated model instance or None
            
        Raises:
            NotImplementedError: If model doesn't support soft delete
        """
        if not hasattr(self.model, 'deleted_at'):
            raise NotImplementedError(
                f"{self.model.__name__} does not support soft delete. "
                "Add deleted_at field or use delete() for hard delete."
            )
        
        update_data = {
            'deleted_at': datetime.now(UTC)
        }
        
        if deleted_by and hasattr(self.model, 'deleted_by'):
            update_data['deleted_by'] = deleted_by
        
        return await self.update(id, **update_data)
    
    async def restore(self, id: UUID) -> Optional[ModelType]:
        """
        Restore a soft deleted record by setting deleted_at and deleted_by to NULL
        
        Args:
            id: Record UUID
            
        Returns:
            Restored model instance or None if record doesn't exist
            
        Raises:
            NotImplementedError: If model doesn't support soft delete
        """
        if not hasattr(self.model, 'deleted_at'):
            raise NotImplementedError(
                f"{self.model.__name__} does not support soft delete"
            )
        
        return await self.update(
            id,
            deleted_at=None,
            deleted_by=None,
            _allow_none=True  # Explicitly allow NULL values for restoration
        )
    
    async def get_deleted(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ModelType]:
        """
        Get soft deleted records
        
        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            
        Returns:
            List of soft deleted records
        """
        if not hasattr(self.model, 'deleted_at'):
            return []
        
        query = (
            select(self.model)
            .where(self.model.deleted_at.isnot(None))
            .order_by(self.model.deleted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def exists(self, id: UUID, include_deleted: bool = False) -> bool:
        """
        Check if record exists
        
        Args:
            id: Record UUID
            include_deleted: Include soft deleted records if True
            
        Returns:
            True if exists, False otherwise
        """
        query = select(func.count()).select_from(self.model).where(self.model.id == id)
        
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    async def count(self, exclude_deleted: bool = True, **filters) -> int:
        """
        Count records with optional filters
        
        Args:
            exclude_deleted: Exclude soft deleted records if True
            **filters: Field filters (field_name=value)
            
        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model)
        
        # Exclude soft deleted
        if exclude_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def find_by(
        self,
        exclude_deleted: bool = True,
        **filters
    ) -> List[ModelType]:
        """
        Find records by field values
        
        Args:
            exclude_deleted: Exclude soft deleted records if True
            **filters: Field filters (field_name=value)
            
        Returns:
            List of matching records
        """
        query = select(self.model)
        
        # Exclude soft deleted
        if exclude_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        
        # Build WHERE conditions
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_one_by(
        self,
        exclude_deleted: bool = True,
        **filters
    ) -> Optional[ModelType]:
        """
        Find single record by field values
        
        Args:
            exclude_deleted: Exclude soft deleted records if True
            **filters: Field filters (field_name=value)
            
        Returns:
            Model instance or None
        """
        results = await self.find_by(exclude_deleted=exclude_deleted, **filters)
        return results[0] if results else None