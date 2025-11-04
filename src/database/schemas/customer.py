"""
Customer Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from database.schemas.conversation import ConversationInDB


class CustomerBase(BaseModel):
    """Base customer schema with common fields"""
    email: EmailStr
    name: Optional[str] = None
    plan: str = Field(default="free", pattern="^(free|basic|premium|enterprise)$")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    extra_metadata: dict = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    name: Optional[str] = None
    plan: Optional[str] = Field(None, pattern="^(free|basic|premium|enterprise)$")
    extra_metadata: Optional[dict] = None


class CustomerInDB(CustomerBase):
    """Customer as stored in database"""
    id: UUID
    extra_metadata: dict
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class CustomerResponse(CustomerInDB):
    """Customer response schema for API"""
    conversation_count: Optional[int] = Field(default=0, description="Number of conversations")


class CustomerWithConversations(CustomerInDB):
    """Customer with related conversations"""
    conversations: list['ConversationInDB'] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references after all classes are defined
from database.schemas.conversation import ConversationInDB
CustomerWithConversations.model_rebuild()