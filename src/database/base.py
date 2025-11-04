"""
Base repository with comprehensive CRUD operations
All repositories inherit from this
"""
from typing import TypeVar, Generic, Optional, List, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import DeclarativeMeta
from uuid import UUID
from datetime import datetime

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with comprehensive CRUD operations
    
    Features:
    - Basic CRUD (Create, Read, Update, Delete)
    - Bulk operations
    - Soft delete support
    - Pagination helpers
    - Existence checks
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
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def bulk_create(self, items: List[dict]) -> List[ModelType]:
        """
        Create multiple records in one transaction
        
        Args:
            items: List of dicts with field values
            
        Returns:
            List of created instances
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        
        # Refresh all instances
        for instance in instances:
            await self.session.refresh(instance)
        
        return instances
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get record by ID
        
        Args:
            id: Record UUID
            
        Returns:
            Model instance or None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        ascending: bool = False
    ) -> List[ModelType]:
        """
        Get all records with pagination
        
        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            order_by: Field to order by
            ascending: Sort ascending if True, descending if False
            
        Returns:
            List of model instances
        """
        query = select(self.model).limit(limit).offset(offset)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if ascending:
                query = query.order_by(order_column.asc())
            else:
                query = query.order_by(order_column.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Update record by ID
        
        Args:
            id: Record UUID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(id)
        
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        await self.session.flush()
        
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID) -> bool:
        """
        Hard delete record by ID
        
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
    
    async def soft_delete(self, id: UUID) -> Optional[ModelType]:
        """
        Soft delete record (if model has deleted_at field)
        
        Args:
            id: Record UUID
            
        Returns:
            Updated model instance or None
        """
        if not hasattr(self.model, 'deleted_at'):
            raise NotImplementedError(
                f"{self.model.__name__} does not support soft delete"
            )
        
        return await self.update(id, deleted_at=datetime.utcnow())
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if record exists
        
        Args:
            id: Record UUID
            
        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model)
            .where(self.model.id == id)
        )
        count = result.scalar()
        return count > 0
    
    async def count(self, **filters) -> int:
        """
        Count records with optional filters
        
        Args:
            **filters: Field filters (field_name=value)
            
        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def find_by(self, **filters) -> List[ModelType]:
        """
        Find records by field values
        
        Args:
            **filters: Field filters (field_name=value)
            
        Returns:
            List of matching records
        """
        query = select(self.model)
        
        # Build WHERE conditions
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_one_by(self, **filters) -> Optional[ModelType]:
        """
        Find single record by field values
        
        Args:
            **filters: Field filters (field_name=value)
            
        Returns:
            Model instance or None
        """
        results = await self.find_by(**filters)
        return results[0] if results else None