"""
Enhanced base agent module with multi-agent collaboration support.

This module provides the foundation for all agents in the system,
including base classes, types, capabilities, and utilities.
"""

from src.agents.base.base_agent import (
    BaseAgent,
    RoutingAgent,
    SpecialistAgent,
    AgentConfig
)
from src.agents.base.agent_types import (
    AgentType,
    AgentCapability,
    Domain,
    SupportIntent,
    SalesIntent,
    CSIntent,
    AgentRole
)
from src.agents.base.capabilities import (
    KBSearchCapability,
    CollaborationCapability,
    DatabaseWriteCapability
)
from src.agents.base.exceptions import (
    AgentError,
    AgentInitializationError,
    AgentProcessingError,
    AgentRoutingError,
    AgentEscalationError
)

__all__ = [
    # Base classes
    "BaseAgent",
    "RoutingAgent",
    "SpecialistAgent",
    "AgentConfig",
    # Types and enums
    "AgentType",
    "AgentCapability",
    "Domain",
    "SupportIntent",
    "SalesIntent",
    "CSIntent",
    "AgentRole",
    # Capabilities
    "KBSearchCapability",
    "CollaborationCapability",
    "DatabaseWriteCapability",
    # Exceptions
    "AgentError",
    "AgentInitializationError",
    "AgentProcessingError",
    "AgentRoutingError",
    "AgentEscalationError",
]
