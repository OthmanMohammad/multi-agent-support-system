"""
Customer Pydantic Models - Enhanced

Extended request/response models for customer endpoints with
full CRUD operations, filtering, and pagination.
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# CUSTOMER MODELS
# =============================================================================

class CustomerResponse(BaseModel):
    """Customer profile response"""

    id: UUID
    email: EmailStr
    name: Optional[str] = None
    plan: str = Field(..., description="free, starter, professional, enterprise")
    status: str = Field(default="active", description="active, inactive, suspended")
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime] = None

    # Statistics
    total_conversations: int = 0
    open_conversations: int = 0
    total_spent: float = Field(default=0.0, description="Total amount spent")

    # Metadata
    metadata: Optional[dict] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "customer@example.com",
                "name": "John Doe",
                "plan": "professional",
                "status": "active",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-11-16T12:00:00Z",
                "last_activity_at": "2025-11-16T12:00:00Z",
                "total_conversations": 25,
                "open_conversations": 2,
                "total_spent": 499.99
            }]
        }
    }


class CustomerListItem(BaseModel):
    """Customer summary for list view"""

    id: UUID
    email: EmailStr
    name: Optional[str] = None
    plan: str
    status: str
    total_conversations: int
    open_conversations: int
    created_at: datetime
    last_activity_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    """Paginated list of customers"""

    customers: List[CustomerListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "customers": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "customer@example.com",
                        "name": "John Doe",
                        "plan": "professional",
                        "status": "active",
                        "total_conversations": 25,
                        "open_conversations": 2,
                        "created_at": "2025-01-01T00:00:00Z",
                        "last_activity_at": "2025-11-16T12:00:00Z"
                    }
                ],
                "total": 1542,
                "page": 1,
                "page_size": 20,
                "total_pages": 78
            }]
        }
    }


# =============================================================================
# CUSTOMER MUTATIONS
# =============================================================================

class CustomerCreateRequest(BaseModel):
    """Create new customer"""

    email: EmailStr
    name: Optional[str] = Field(None, max_length=255)
    plan: str = Field(default="free", description="free, starter, professional, enterprise")
    metadata: Optional[dict] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "newcustomer@example.com",
                "name": "Jane Smith",
                "plan": "starter"
            }]
        }
    }


class CustomerUpdateRequest(BaseModel):
    """Update customer details"""

    name: Optional[str] = Field(None, max_length=255)
    plan: Optional[str] = Field(None, description="free, starter, professional, enterprise")
    status: Optional[str] = Field(None, description="active, inactive, suspended")
    metadata: Optional[dict] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Jane Doe",
                "plan": "professional",
                "metadata": {"notes": "VIP customer"}
            }]
        }
    }


# =============================================================================
# CUSTOMER STATISTICS
# =============================================================================

class CustomerStats(BaseModel):
    """Customer statistics"""

    total_customers: int
    active_customers: int
    inactive_customers: int
    by_plan: dict = Field(..., description="Customer count by plan")
    new_customers_today: int
    new_customers_this_week: int
    new_customers_this_month: int
    churn_rate: float = Field(..., ge=0.0, le=100.0, description="Churn rate percentage")
    average_lifetime_value: float

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_customers": 1542,
                "active_customers": 1489,
                "inactive_customers": 53,
                "by_plan": {
                    "free": 892,
                    "starter": 421,
                    "professional": 189,
                    "enterprise": 40
                },
                "new_customers_today": 12,
                "new_customers_this_week": 87,
                "new_customers_this_month": 234,
                "churn_rate": 2.5,
                "average_lifetime_value": 349.99
            }]
        }
    }
