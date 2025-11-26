"""
Base provider for context enrichment.

All context providers inherit from this base class, which provides
common functionality for fetching, error handling, and fallbacks.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseContextProvider(ABC):
    """
    Base class for all context providers.

    All providers must implement the `fetch` method to retrieve
    context data from their respective sources.
    """

    def __init__(self, cache_ttl: int = 300, timeout: float = 2.0):
        """
        Initialize provider.

        Args:
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
            timeout: Request timeout in seconds (default: 2 seconds)
        """
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.provider_name = self.__class__.__name__
        self.logger = logger.bind(provider=self.provider_name)

    @abstractmethod
    async def fetch(
        self, customer_id: str, conversation_id: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Fetch context from this provider.

        Args:
            customer_id: Customer ID to fetch context for
            conversation_id: Optional conversation ID for context
            **kwargs: Additional provider-specific parameters

        Returns:
            Context dictionary with provider-specific data

        Raises:
            ProviderError: If fetching fails
        """
        pass

    async def fetch_with_fallback(
        self,
        customer_id: str,
        conversation_id: str | None = None,
        fallback: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Fetch with fallback on error.

        This method wraps `fetch` and returns a fallback value
        if fetching fails, ensuring the system degrades gracefully.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            fallback: Fallback value if fetch fails (default: empty dict)
            **kwargs: Additional provider-specific parameters

        Returns:
            Context dictionary or fallback
        """
        try:
            self.logger.debug(
                "fetch_started", customer_id=customer_id, conversation_id=conversation_id
            )
            result = await self.fetch(customer_id, conversation_id, **kwargs)
            self.logger.debug("fetch_succeeded", customer_id=customer_id, keys=list(result.keys()))
            return result

        except Exception as e:
            self.logger.error(
                "fetch_failed", customer_id=customer_id, error=str(e), error_type=type(e).__name__
            )
            return fallback or {}

    def _validate_data(self, data: dict[str, Any], required_keys: list) -> bool:
        """
        Validate that fetched data contains required keys.

        Args:
            data: Data dictionary to validate
            required_keys: List of required key names

        Returns:
            True if all required keys are present
        """
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            self.logger.warning("data_validation_failed", missing_keys=missing_keys)
            return False
        return True
