"""
Base service classes and utilities

This package provides the foundation for all service classes in the application.

Usage:
    from services.base import BaseService
    
    class CustomerService(BaseService):
        def create_customer(self, email: str) -> Result[Customer]:
            # Service implementation
            pass
"""

from services.base.base_service import BaseService

__version__ = "1.0.0"

__all__ = ["BaseService"]