"""
Enhanced BaseAgent with multi-agent collaboration support.

This module provides the foundation for all agents in the system,
including advanced capabilities for collaboration, context enrichment,
and knowledge base integration.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from anthropic import Anthropic
import structlog

from src.core.config import get_settings
from src.workflow.state import AgentState
from src.agents.base.agent_types import AgentType, AgentCapability
from src.agents.base.exceptions import (
    AgentError,
    AgentProcessingError,
    AgentLLMError,
    AgentKnowledgeBaseError
)

logger = structlog.get_logger(__name__)


@dataclass
class AgentConfig:
    """
    Configuration for an agent.

    Attributes:
        name: Agent name (unique identifier)
        type: Agent type (router, specialist, coordinator, etc.)
        model: Claude model to use
        temperature: LLM temperature (0-1)
        max_tokens: Maximum tokens for LLM response
        capabilities: List of agent capabilities
        system_prompt_template: System prompt template with placeholders
        kb_category: Default knowledge base category to search
        tier: Agent tier (essential, revenue, operational, advanced)
        role: Specific role within the system
    """
    name: str
    type: AgentType
    model: str = "claude-3-haiku-20240307"
    temperature: float = 0.3
    max_tokens: int = 1000
    capabilities: List[AgentCapability] = field(default_factory=list)
    system_prompt_template: str = ""
    kb_category: Optional[str] = None
    tier: str = "essential"
    role: Optional[str] = None


class BaseAgent(ABC):
    """
    Enhanced base agent with advanced capabilities.

    All agents inherit from this base class. Provides core functionality:
    - LLM interaction with error handling
    - Knowledge base search
    - Context enrichment
    - State management
    - Escalation logic
    - Logging and monitoring

    Subclasses must implement the `process` method.
    """

    def __init__(
        self,
        config: AgentConfig,
        anthropic_client: Optional[Anthropic] = None,
        kb_service: Optional[Any] = None,
        context_service: Optional[Any] = None
    ):
        """
        Initialize base agent.

        Args:
            config: Agent configuration
            anthropic_client: Optional Anthropic client (created if not provided)
            kb_service: Optional knowledge base service
            context_service: Optional context enrichment service
        """
        self.config = config
        self.logger = logger.bind(agent=config.name, agent_type=config.type.value)

        # Initialize Anthropic client
        settings = get_settings()
        self.client = anthropic_client or Anthropic(api_key=settings.anthropic.api_key)

        # Optional services
        self.kb_service = kb_service
        self.context_service = context_service

        self.logger.info(
            "agent_initialized",
            model=config.model,
            capabilities=[c.value for c in config.capabilities]
        )

    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state.

        This is the main method each agent must implement.

        Args:
            state: Current agent state

        Returns:
            Updated agent state

        Raises:
            AgentProcessingError: If processing fails
        """
        pass

    async def call_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call Claude API with error handling and logging.

        Args:
            system_prompt: System instructions
            user_message: User message
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLM response text

        Raises:
            AgentLLMError: If LLM call fails
        """
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            content = response.content[0].text

            # Log usage
            self.logger.info(
                "llm_call_success",
                model=self.config.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            )

            return content

        except Exception as e:
            self.logger.error(
                "llm_call_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise AgentLLMError(
                message=f"LLM call failed: {str(e)}",
                agent_name=self.config.name,
                details={"error_type": type(e).__name__}
            ) from e

    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant articles.

        Args:
            query: Search query
            category: Filter by category (optional)
            limit: Number of results

        Returns:
            List of KB articles with scores

        Raises:
            AgentKnowledgeBaseError: If KB search fails critically
        """
        # Check if capability is enabled
        if AgentCapability.KB_SEARCH not in self.config.capabilities:
            self.logger.warning(
                "kb_search_not_enabled",
                agent=self.config.name
            )
            return []

        # Check if KB service is available
        if not self.kb_service:
            self.logger.warning("kb_service_not_available")
            # Try using the legacy search_articles function
            try:
                from src.knowledge_base import search_articles
                category = category or self.config.kb_category
                results = search_articles(query=query, category=category, limit=limit)
                self.logger.info(
                    "kb_search_success_legacy",
                    query=query,
                    category=category,
                    results_count=len(results)
                )
                return results
            except Exception as e:
                self.logger.error(
                    "kb_search_failed_legacy",
                    error=str(e)
                )
                return []

        try:
            category = category or self.config.kb_category
            results = await self.kb_service.search(
                query=query,
                category=category,
                limit=limit
            )

            self.logger.info(
                "kb_search_success",
                query=query,
                category=category,
                results_count=len(results)
            )

            return results

        except Exception as e:
            self.logger.error(
                "kb_search_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Don't raise - just return empty results
            return []

    async def get_enriched_context(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get enriched customer context.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)

        Returns:
            EnrichedContext object or None if not available
        """
        # Check if capability is enabled
        if AgentCapability.CONTEXT_AWARE not in self.config.capabilities:
            return None

        if not self.context_service:
            # Try to get context service from global singleton
            try:
                from src.services.infrastructure.context_enrichment import get_context_service
                self.context_service = get_context_service()
            except Exception as e:
                self.logger.warning("context_service_not_available", error=str(e))
                return None

        try:
            context = await self.context_service.enrich_context(
                customer_id=customer_id,
                conversation_id=conversation_id
            )

            self.logger.info(
                "context_enrichment_success",
                customer_id=customer_id,
                latency_ms=context.enrichment_latency_ms,
                cache_hit=context.cache_hit
            )
            return context

        except Exception as e:
            self.logger.error(
                "context_enrichment_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return None

    async def inject_context_into_prompt(
        self,
        system_prompt: str,
        customer_id: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Inject enriched context into system prompt.

        This automatically fetches and injects customer context into the system prompt,
        making agents context-aware without extra code.

        Args:
            system_prompt: Original system prompt
            customer_id: Customer ID
            conversation_id: Optional conversation ID

        Returns:
            System prompt with injected context

        Example:
            >>> prompt = "You are a helpful billing specialist."
            >>> enriched_prompt = await self.inject_context_into_prompt(prompt, "customer_123")
            >>> # enriched_prompt now contains customer intelligence
        """
        context = await self.get_enriched_context(customer_id, conversation_id)

        if context:
            # Inject context before the main prompt
            context_section = context.to_prompt_context()
            return f"{context_section}\n\n{system_prompt}"

        return system_prompt

    def build_system_prompt(self, **kwargs) -> str:
        """
        Build system prompt from template with context injection.

        Args:
            **kwargs: Variables to inject into template

        Returns:
            Formatted system prompt
        """
        if not self.config.system_prompt_template:
            return ""

        try:
            return self.config.system_prompt_template.format(**kwargs)
        except KeyError as e:
            self.logger.warning(
                "system_prompt_template_missing_key",
                missing_key=str(e)
            )
            return self.config.system_prompt_template

    def update_state(self, state: AgentState, **updates) -> AgentState:
        """
        Update agent state with new values.

        Args:
            state: Current state
            **updates: Key-value pairs to update

        Returns:
            Updated state
        """
        # Add this agent to history
        if "agent_history" not in state:
            state["agent_history"] = []
        if self.config.name not in state["agent_history"]:
            state["agent_history"].append(self.config.name)

        # Set current agent
        state["current_agent"] = self.config.name

        # Increment turn count
        state["turn_count"] = state.get("turn_count", 0) + 1

        # Update with provided values
        state.update(updates)

        return state

    def should_escalate(self, state: AgentState) -> bool:
        """
        Check if conversation should be escalated.

        Args:
            state: Current state

        Returns:
            True if should escalate
        """
        # Too many turns
        if state.get("turn_count", 0) > state.get("max_turns", 5):
            self.logger.info(
                "escalation_triggered",
                reason="max_turns_exceeded",
                turn_count=state.get("turn_count")
            )
            return True

        # Very low confidence
        if state.get("response_confidence", 1.0) < 0.4:
            self.logger.info(
                "escalation_triggered",
                reason="low_confidence",
                confidence=state.get("response_confidence")
            )
            return True

        # Very negative sentiment
        if state.get("sentiment", 0) < -0.7:
            self.logger.info(
                "escalation_triggered",
                reason="negative_sentiment",
                sentiment=state.get("sentiment")
            )
            return True

        # Explicit escalation flag
        if state.get("should_escalate", False):
            self.logger.info(
                "escalation_triggered",
                reason="explicit_flag",
                escalation_reason=state.get("escalation_reason", "unknown")
            )
            return True

        return False

    def add_to_history(self, state: AgentState) -> AgentState:
        """
        Add current agent to agent_history.

        Deprecated: Use update_state instead.

        Args:
            state: Current state

        Returns:
            Updated state with agent in history
        """
        agent_history = state.get("agent_history", [])
        if self.config.name not in agent_history:
            agent_history.append(self.config.name)

        state["agent_history"] = agent_history
        state["current_agent"] = self.config.name

        return state


class RoutingAgent(BaseAgent):
    """
    Base class for routing agents.

    Routing agents classify intent and route to appropriate specialists.
    """

    async def classify_and_route(self, state: AgentState) -> AgentState:
        """
        Classification logic for routers.

        Args:
            state: Current state

        Returns:
            Updated state with routing decision
        """
        raise NotImplementedError("Subclasses must implement classify_and_route")


class SpecialistAgent(BaseAgent):
    """
    Base class for specialist agents.

    Specialist agents resolve specific types of queries
    (billing, technical, usage, etc.)
    """

    async def resolve_query(self, state: AgentState) -> AgentState:
        """
        Resolution logic for specialists.

        Args:
            state: Current state

        Returns:
            Updated state with resolution
        """
        raise NotImplementedError("Subclasses must implement resolve_query")
