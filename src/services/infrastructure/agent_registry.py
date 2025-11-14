"""
Agent registry for dynamic agent discovery and instantiation.

This module provides a centralized registry for all agents in the system,
enabling dynamic discovery, instantiation, and management of agents.
"""

from typing import Dict, Type, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """
    Registry for all agents in the system.

    Enables dynamic agent discovery and instantiation.
    Agents self-register using the @AgentRegistry.register decorator.
    """

    _agents: Dict[str, Type] = {}
    _metadata: Dict[str, Dict] = {}

    @classmethod
    def register(
        cls,
        name: str,
        tier: Optional[str] = None,
        category: Optional[str] = None
    ):
        """
        Decorator to register an agent.

        Args:
            name: Agent name (unique identifier)
            tier: Agent tier (essential, revenue, etc.)
            category: Agent category (routing, billing, technical, etc.)

        Example:
            @AgentRegistry.register("meta_router", tier="essential", category="routing")
            class MetaRouterAgent(BaseAgent):
                ...
        """
        def decorator(agent_class: Type):
            if name in cls._agents:
                logger.warning(
                    "agent_already_registered",
                    name=name,
                    existing_class=cls._agents[name].__name__,
                    new_class=agent_class.__name__
                )

            cls._agents[name] = agent_class
            cls._metadata[name] = {
                "tier": tier,
                "category": category,
                "class_name": agent_class.__name__,
                "module": agent_class.__module__
            }

            logger.debug(
                "agent_registered",
                name=name,
                tier=tier,
                category=category,
                class_name=agent_class.__name__
            )

            return agent_class
        return decorator

    @classmethod
    def get_agent(cls, name: str) -> Optional[Type]:
        """
        Get agent class by name.

        Args:
            name: Agent name

        Returns:
            Agent class or None if not found
        """
        agent_class = cls._agents.get(name)

        if agent_class is None:
            logger.warning("agent_not_found", name=name)

        return agent_class

    @classmethod
    def get_all_agents(cls) -> Dict[str, Type]:
        """
        Get all registered agents.

        Returns:
            Dictionary mapping agent names to agent classes
        """
        return cls._agents.copy()

    @classmethod
    def get_agents_by_tier(cls, tier: str) -> List[str]:
        """
        Get agents by tier.

        Args:
            tier: Tier name (essential, revenue, etc.)

        Returns:
            List of agent names in the tier
        """
        return [
            name for name, metadata in cls._metadata.items()
            if metadata.get("tier") == tier
        ]

    @classmethod
    def get_agents_by_category(cls, category: str) -> List[str]:
        """
        Get agents by category.

        Args:
            category: Category name (routing, billing, technical, etc.)

        Returns:
            List of agent names in the category
        """
        return [
            name for name, metadata in cls._metadata.items()
            if metadata.get("category") == category
        ]

    @classmethod
    def get_agent_metadata(cls, name: str) -> Optional[Dict]:
        """
        Get agent metadata.

        Args:
            name: Agent name

        Returns:
            Agent metadata dictionary or None if not found
        """
        return cls._metadata.get(name)

    @classmethod
    def list_agents(cls) -> List[Dict]:
        """
        List all registered agents with metadata.

        Returns:
            List of dictionaries with agent information
        """
        return [
            {
                "name": name,
                "class": agent_class.__name__,
                **cls._metadata.get(name, {})
            }
            for name, agent_class in cls._agents.items()
        ]

    @classmethod
    def clear(cls):
        """
        Clear all registered agents.

        Useful for testing.
        """
        cls._agents.clear()
        cls._metadata.clear()
        logger.info("agent_registry_cleared")

    @classmethod
    def get_tier_summary(cls) -> Dict[str, int]:
        """
        Get summary of agents by tier.

        Returns:
            Dictionary mapping tier names to agent counts
        """
        summary = {}
        for metadata in cls._metadata.values():
            tier = metadata.get("tier", "unknown")
            summary[tier] = summary.get(tier, 0) + 1
        return summary

    @classmethod
    def get_category_summary(cls) -> Dict[str, int]:
        """
        Get summary of agents by category.

        Returns:
            Dictionary mapping category names to agent counts
        """
        summary = {}
        for metadata in cls._metadata.values():
            category = metadata.get("category", "unknown")
            summary[category] = summary.get(category, 0) + 1
        return summary


# Example usage:
# @AgentRegistry.register("meta_router", tier="essential", category="routing")
# class MetaRouterAgent(BaseAgent):
#     tier = "essential"
#     category = "routing"
#     ...
