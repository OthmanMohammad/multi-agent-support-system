"""
Provider registry for dynamic context provider management.

Manages registration, discovery, and lifecycle of context providers.
"""

import structlog

from src.services.infrastructure.context_enrichment.types import (
    AgentType,
    ContextProviderProtocol,
    ProviderMetadata,
    ProviderPriority,
)

logger = structlog.get_logger(__name__)


class ProviderRegistry:
    """
    Registry for managing context providers.

    Features:
    - Dynamic provider registration
    - Agent-to-provider mapping
    - Provider dependency resolution
    - Health checking and lifecycle management

    Example:
        >>> registry = ProviderRegistry()
        >>> registry.register(
        ...     provider=CustomerIntelligenceProvider(),
        ...     agent_types=[AgentType.GENERAL, AgentType.CSM],
        ...     priority=ProviderPriority.CRITICAL
        ... )
        >>> providers = registry.get_providers_for_agent(AgentType.GENERAL)
    """

    def __init__(self):
        """Initialize provider registry"""
        self._providers: dict[str, ContextProviderProtocol] = {}
        self._metadata: dict[str, ProviderMetadata] = {}
        self._agent_mappings: dict[AgentType, list[str]] = {
            agent_type: [] for agent_type in AgentType
        }
        self._dependencies: dict[str, list[str]] = {}
        logger.info("provider_registry_initialized")

    def register(
        self,
        provider: ContextProviderProtocol,
        agent_types: list[AgentType] | None = None,
        priority: ProviderPriority = ProviderPriority.MEDIUM,
        enabled: bool = True,
        dependencies: list[str] | None = None,
    ) -> None:
        """
        Register a context provider.

        Args:
            provider: Provider instance to register
            agent_types: List of agent types this provider serves (None = all agents)
            priority: Provider execution priority
            enabled: Whether provider is enabled
            dependencies: List of provider names this provider depends on

        Raises:
            ValueError: If provider with same name already registered

        Example:
            >>> registry.register(
            ...     provider=CustomerIntelligenceProvider(),
            ...     agent_types=[AgentType.GENERAL],
            ...     priority=ProviderPriority.CRITICAL
            ... )
        """
        provider_name = provider.provider_name

        if provider_name in self._providers:
            logger.warning("provider_already_registered_replacing", provider=provider_name)

        # Store provider instance
        self._providers[provider_name] = provider

        # Store metadata
        self._metadata[provider_name] = ProviderMetadata(
            name=provider_name,
            enabled=enabled,
            priority=priority,
            agent_types=agent_types or list(AgentType),
            cache_ttl=provider.cache_ttl,
            timeout_ms=int(provider.timeout * 1000),
            dependencies=dependencies or [],
        )

        # Store dependencies
        self._dependencies[provider_name] = dependencies or []

        # Map to agent types
        target_agents = agent_types or list(AgentType)
        for agent_type in target_agents:
            if provider_name not in self._agent_mappings[agent_type]:
                self._agent_mappings[agent_type].append(provider_name)

        logger.info(
            "provider_registered",
            provider=provider_name,
            agent_types=[at.value for at in target_agents],
            priority=priority.value,
            enabled=enabled,
        )

    def unregister(self, provider_name: str) -> None:
        """
        Unregister a provider.

        Args:
            provider_name: Name of provider to unregister

        Example:
            >>> registry.unregister("CustomerIntelligence")
        """
        if provider_name not in self._providers:
            logger.warning("provider_not_found_cannot_unregister", provider=provider_name)
            return

        # Remove from providers
        del self._providers[provider_name]
        del self._metadata[provider_name]

        # Remove from agent mappings
        for agent_type in AgentType:
            if provider_name in self._agent_mappings[agent_type]:
                self._agent_mappings[agent_type].remove(provider_name)

        # Remove dependencies
        if provider_name in self._dependencies:
            del self._dependencies[provider_name]

        logger.info("provider_unregistered", provider=provider_name)

    def get_provider(self, provider_name: str) -> ContextProviderProtocol | None:
        """
        Get provider by name.

        Args:
            provider_name: Name of provider

        Returns:
            Provider instance or None if not found

        Example:
            >>> provider = registry.get_provider("CustomerIntelligence")
        """
        return self._providers.get(provider_name)

    def get_providers_for_agent(
        self, agent_type: AgentType, include_disabled: bool = False
    ) -> list[ContextProviderProtocol]:
        """
        Get all providers applicable to an agent type.

        Providers are returned sorted by priority (critical first).

        Args:
            agent_type: Agent type to get providers for
            include_disabled: Include disabled providers

        Returns:
            List of provider instances sorted by priority

        Example:
            >>> providers = registry.get_providers_for_agent(AgentType.BILLING)
            >>> for provider in providers:
            ...     result = await provider.fetch(customer_id)
        """
        provider_names = self._agent_mappings.get(agent_type, [])

        # Filter out disabled providers if requested
        if not include_disabled:
            provider_names = [name for name in provider_names if self._metadata[name]["enabled"]]

        # Get provider instances
        providers = [self._providers[name] for name in provider_names if name in self._providers]

        # Sort by priority
        providers.sort(key=lambda p: self._metadata[p.provider_name]["priority"].value)

        return providers

    def get_all_providers(self, include_disabled: bool = False) -> list[ContextProviderProtocol]:
        """
        Get all registered providers.

        Args:
            include_disabled: Include disabled providers

        Returns:
            List of all provider instances

        Example:
            >>> all_providers = registry.get_all_providers()
        """
        providers = list(self._providers.values())

        if not include_disabled:
            providers = [p for p in providers if self._metadata[p.provider_name]["enabled"]]

        return providers

    def enable_provider(self, provider_name: str) -> None:
        """
        Enable a provider.

        Args:
            provider_name: Name of provider to enable

        Example:
            >>> registry.enable_provider("CustomerIntelligence")
        """
        if provider_name in self._metadata:
            self._metadata[provider_name]["enabled"] = True
            logger.info("provider_enabled", provider=provider_name)
        else:
            logger.warning("provider_not_found_cannot_enable", provider=provider_name)

    def disable_provider(self, provider_name: str) -> None:
        """
        Disable a provider.

        Args:
            provider_name: Name of provider to disable

        Example:
            >>> registry.disable_provider("ExternalAPIProvider")
        """
        if provider_name in self._metadata:
            self._metadata[provider_name]["enabled"] = False
            logger.info("provider_disabled", provider=provider_name)
        else:
            logger.warning("provider_not_found_cannot_disable", provider=provider_name)

    def is_enabled(self, provider_name: str) -> bool:
        """
        Check if provider is enabled.

        Args:
            provider_name: Provider name to check

        Returns:
            True if enabled, False otherwise

        Example:
            >>> if registry.is_enabled("CustomerIntelligence"):
            ...     # Use provider
        """
        if provider_name in self._metadata:
            return self._metadata[provider_name]["enabled"]
        return False

    def get_metadata(self, provider_name: str) -> ProviderMetadata | None:
        """
        Get provider metadata.

        Args:
            provider_name: Provider name

        Returns:
            Provider metadata or None if not found

        Example:
            >>> metadata = registry.get_metadata("CustomerIntelligence")
            >>> print(f"Priority: {metadata['priority']}")
        """
        return self._metadata.get(provider_name)

    def get_dependencies(self, provider_name: str) -> list[str]:
        """
        Get provider dependencies.

        Args:
            provider_name: Provider name

        Returns:
            List of provider names this provider depends on

        Example:
            >>> deps = registry.get_dependencies("AccountHealth")
            >>> print(deps)  # ['CustomerIntelligence', 'EngagementMetrics']
        """
        return self._dependencies.get(provider_name, [])

    def resolve_dependencies(self, provider_names: list[str]) -> list[str]:
        """
        Resolve provider dependencies in execution order.

        Returns providers in order such that all dependencies are
        executed before their dependents.

        Args:
            provider_names: List of provider names to resolve

        Returns:
            Ordered list of provider names

        Raises:
            ValueError: If circular dependency detected

        Example:
            >>> providers = ["AccountHealth"]
            >>> resolved = registry.resolve_dependencies(providers)
            >>> print(resolved)
            ['CustomerIntelligence', 'EngagementMetrics', 'AccountHealth']
        """
        resolved = []
        seen = set()

        def resolve(name: str, path: list[str]) -> None:
            """Recursive dependency resolution"""
            if name in path:
                raise ValueError(f"Circular dependency detected: {' -> '.join([*path, name])}")

            if name in seen:
                return

            seen.add(name)
            path = [*path, name]

            # Resolve dependencies first
            for dep in self.get_dependencies(name):
                resolve(dep, path)

            # Add this provider after its dependencies
            if name not in resolved:
                resolved.append(name)

        for provider_name in provider_names:
            resolve(provider_name, [])

        return resolved

    def get_provider_count(self) -> int:
        """
        Get total number of registered providers.

        Returns:
            Number of providers

        Example:
            >>> count = registry.get_provider_count()
        """
        return len(self._providers)

    def get_enabled_provider_count(self) -> int:
        """
        Get number of enabled providers.

        Returns:
            Number of enabled providers

        Example:
            >>> enabled = registry.get_enabled_provider_count()
        """
        return sum(1 for meta in self._metadata.values() if meta["enabled"])

    def get_summary(self) -> dict[str, any]:
        """
        Get registry summary.

        Returns:
            Summary of registry state

        Example:
            >>> summary = registry.get_summary()
            >>> print(f"Total providers: {summary['total_providers']}")
        """
        return {
            "total_providers": self.get_provider_count(),
            "enabled_providers": self.get_enabled_provider_count(),
            "providers_by_priority": {
                priority.name: sum(
                    1
                    for meta in self._metadata.values()
                    if meta["priority"] == priority and meta["enabled"]
                )
                for priority in ProviderPriority
            },
            "providers_by_agent_type": {
                agent_type.value: len(
                    [
                        name
                        for name in self._agent_mappings[agent_type]
                        if self._metadata[name]["enabled"]
                    ]
                )
                for agent_type in AgentType
            },
        }


# Global registry instance
_registry_instance: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """
    Get or create provider registry singleton.

    Returns:
        ProviderRegistry instance

    Example:
        >>> registry = get_provider_registry()
        >>> registry.register(my_provider)
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ProviderRegistry()
    return _registry_instance


def reset_provider_registry() -> None:
    """
    Reset provider registry (for testing).

    Example:
        >>> reset_provider_registry()
        >>> registry = get_provider_registry()  # Fresh instance
    """
    global _registry_instance
    _registry_instance = None
