"""
Agent-specific exceptions.

This module defines custom exceptions for agent operations,
enabling better error handling and debugging.
"""


class AgentError(Exception):
    """Base exception for all agent errors"""

    def __init__(self, message: str, agent_name: str | None = None, details: dict | None = None):
        self.message = message
        self.agent_name = agent_name
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.agent_name:
            return f"[{self.agent_name}] {self.message}"
        return self.message


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize properly"""

    pass


class AgentProcessingError(AgentError):
    """Raised when an agent fails to process a request"""

    pass


class AgentRoutingError(AgentError):
    """Raised when routing decisions fail"""

    pass


class AgentEscalationError(AgentError):
    """Raised when escalation logic fails"""

    pass


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid"""

    pass


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out"""

    pass


class AgentLLMError(AgentError):
    """Raised when LLM calls fail"""

    pass


class AgentKnowledgeBaseError(AgentError):
    """Raised when knowledge base operations fail"""

    pass


class AgentCollaborationError(AgentError):
    """Raised when agent collaboration fails"""

    pass
