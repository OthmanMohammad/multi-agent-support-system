"""
Enhanced base agent module with multi-agent collaboration support.

This module provides the foundation for all agents in the system,
including base classes, types, capabilities, and utilities.
"""

from src.agents.base.agent_types import (
    AgentCapability,
    AgentRole,
    AgentType,
    CSIntent,
    Domain,
    SalesIntent,
    SupportIntent,
)
from src.agents.base.base_agent import AgentConfig, BaseAgent, RoutingAgent, SpecialistAgent
from src.agents.base.capabilities import (
    CollaborationCapability,
    DatabaseWriteCapability,
    KBSearchCapability,
)
from src.agents.base.exceptions import (
    AgentError,
    AgentEscalationError,
    AgentInitializationError,
    AgentProcessingError,
    AgentRoutingError,
)

__all__ = [
    "AgentCapability",
    "AgentConfig",
    # Exceptions
    "AgentError",
    "AgentEscalationError",
    "AgentInitializationError",
    "AgentProcessingError",
    "AgentRole",
    "AgentRoutingError",
    # Types and enums
    "AgentType",
    # Base classes
    "BaseAgent",
    "CSIntent",
    "CollaborationCapability",
    "DatabaseWriteCapability",
    "Domain",
    # Capabilities
    "KBSearchCapability",
    "RoutingAgent",
    "SalesIntent",
    "SpecialistAgent",
    "SupportIntent",
]
