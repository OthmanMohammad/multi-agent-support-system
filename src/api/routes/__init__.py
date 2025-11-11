"""
API Routes package - Domain-separated route modules

Each module contains routes for a specific domain:
- conversations: Chat conversations and messages
- customers: Customer management
- analytics: System metrics and analytics
- health: Health checks and status
"""

from fastapi import APIRouter
from api.routes import conversations, customers, analytics, health

# Create main router
api_router = APIRouter()

# Include all route modules
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(health.router, tags=["health"])

__all__ = ["api_router"]