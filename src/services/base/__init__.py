"""
Base service classes and utilities

This package provides the foundation for all service classes in the application.

Usage:
    from src.services.base import BaseService, handle_exceptions

    class CustomerService(BaseService):
        @handle_exceptions("create_customer")
        async def create_customer(self, email: str) -> Result[Customer]:
            # Service implementation
            pass
"""

from src.services.base.base_service import BaseService, handle_exceptions

__version__ = "1.0.0"

__all__ = ["BaseService", "handle_exceptions"]
