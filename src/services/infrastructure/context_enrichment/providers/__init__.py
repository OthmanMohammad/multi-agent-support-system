"""
Context enrichment providers.

Providers fetch context data from various sources:
- Internal: Database queries for customer data
- External: Third-party APIs (Clearbit, Crunchbase, etc.)
- Realtime: Current system status and activity
"""

from src.services.infrastructure.context_enrichment.providers.base_provider import (
    BaseContextProvider,
)

__all__ = ["BaseContextProvider"]
