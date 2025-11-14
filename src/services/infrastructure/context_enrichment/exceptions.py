"""
Context enrichment exceptions.

Custom exceptions for the context enrichment system.
"""

from typing import Optional


class ContextEnrichmentError(Exception):
    """Base exception for context enrichment errors"""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        customer_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.message = message
        self.provider = provider
        self.customer_id = customer_id
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.provider:
            return f"[{self.provider}] {self.message}"
        return self.message


class ProviderError(ContextEnrichmentError):
    """Raised when a provider fails to fetch data"""
    pass


class CacheError(ContextEnrichmentError):
    """Raised when cache operations fail"""
    pass


class DataValidationError(ContextEnrichmentError):
    """Raised when data validation fails"""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when a provider times out"""
    pass


class ProviderNotConfiguredError(ProviderError):
    """Raised when a provider is not properly configured"""
    pass
