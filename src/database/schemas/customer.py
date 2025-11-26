"""
Customer Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from src.database.schemas.conversation import ConversationInDB


class CustomerBase(BaseModel):
    """Base customer schema with common fields"""

    email: EmailStr
    name: str | None = None
    plan: str = Field(default="free", pattern="^(free|basic|premium|enterprise)$")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""

    extra_metadata: dict = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""

    name: str | None = None
    plan: str | None = Field(None, pattern="^(free|basic|premium|enterprise)$")
    extra_metadata: dict | None = None


class CustomerInDB(CustomerBase):
    """Customer as stored in database"""

    id: UUID
    extra_metadata: dict
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerResponse(CustomerInDB):
    """Customer response schema for API"""

    conversation_count: int | None = Field(default=0, description="Number of conversations")


class CustomerWithConversations(CustomerInDB):
    """Customer with related conversations"""

    conversations: list["ConversationInDB"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Update forward references after all classes are defined

CustomerWithConversations.model_rebuild()
