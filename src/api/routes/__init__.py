"""
API Routes package - Domain-separated route modules

Each module contains routes for a specific domain:
- auth: Authentication and user management
- agents: Agent execution and management
- workflows: Multi-agent workflow orchestration
- conversations: Chat conversations and messages
- customers: Customer management
- analytics: System metrics and analytics
- health: Health checks and status
"""

from fastapi import APIRouter
from src.api.routes import auth, agents, workflows, conversations, customers, analytics, health

# Create main router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

__all__ = ["api_router"]