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
from src.llm.client import llm_client

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
            anthropic_client: Optional Anthropic client (deprecated, kept for compatibility)
            kb_service: Optional knowledge base service
            context_service: Optional context enrichment service
        """
        self.config = config
        self.logger = logger.bind(agent=config.name, agent_type=config.type.value)

        # Legacy Anthropic client (kept for backward compatibility)
        settings = get_settings()
        self.client = anthropic_client or Anthropic(api_key=settings.anthropic.api_key)

        # NEW: Unified LLM client (LiteLLM abstraction)
        self.llm_client = llm_client

        # Map model names to tiers for LiteLLM
        self._model_tier_map = {
            "claude-3-haiku-20240307": "haiku",
            "claude-3-5-sonnet-20241022": "sonnet",
            "claude-3-5-sonnet-20240620": "sonnet",
            "claude-3-opus-20240229": "opus",
        }

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
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Call LLM via unified client with error handling and logging.

        NOW USES: LiteLLM abstraction for multi-backend support (Anthropic/vLLM)

        This method is backend-agnostic - it works with any configured backend
        (Anthropic Claude API or vLLM) without code changes.

        Args:
            system_prompt: System instructions
            user_message: User message (current message)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            conversation_history: Optional list of previous messages for multi-turn context.
                                 Each message should have 'role' and 'content' keys.

        Returns:
            LLM response text

        Raises:
            AgentLLMError: If LLM call fails
        """
        try:
            # Get model tier from config model name
            model_tier = self._model_tier_map.get(self.config.model, "haiku")

            # Build messages list with proper multi-turn format
            messages = []

            # Add system prompt as the first message context
            system_context = system_prompt

            # If conversation history is provided, format it for context
            if conversation_history and len(conversation_history) > 0:
                # Build conversation context string for the system prompt
                history_text = self._format_conversation_history(conversation_history)
                system_context = f"{system_prompt}\n\n## Previous Conversation History:\n{history_text}"

            # Format as single user message with system context
            # (LiteLLM/Anthropic work best with this format)
            messages = [
                {"role": "user", "content": f"{system_context}\n\n## Current Message:\n{user_message}"}
            ]

            # Call unified LLM client (automatically uses current backend)
            content = await self.llm_client.chat_completion(
                messages=messages,
                model_tier=model_tier,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
            )

            # Note: Metrics and cost tracking are handled inside llm_client.chat_completion()
            # No need to log here - llm_client already logs everything

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

    def _format_conversation_history(
        self,
        history: List[Dict[str, Any]],
        max_messages: int = 10
    ) -> str:
        """
        Format conversation history for inclusion in LLM prompt.

        Args:
            history: List of message dictionaries with 'role' and 'content'
            max_messages: Maximum number of recent messages to include (prevents token overflow)

        Returns:
            Formatted string representation of conversation history
        """
        if not history:
            return ""

        # Take only the most recent messages to prevent token overflow
        recent_history = history[-max_messages:] if len(history) > max_messages else history

        formatted_parts = []
        for msg in recent_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            agent_name = msg.get("agent_name")

            # Format role label
            if role == "user":
                role_label = "Customer"
            elif role == "assistant":
                role_label = f"Agent ({agent_name})" if agent_name else "Agent"
            else:
                role_label = role.capitalize()

            # Truncate very long messages to prevent token overflow
            if len(content) > 500:
                content = content[:500] + "..."

            formatted_parts.append(f"{role_label}: {content}")

        return "\n\n".join(formatted_parts)

    def get_conversation_context(self, state: AgentState) -> List[Dict[str, Any]]:
        """
        Extract conversation history from agent state for LLM context.

        This method should be called by agents to get properly formatted
        conversation history for multi-turn context.

        Args:
            state: Current agent state containing messages

        Returns:
            List of message dictionaries ready for LLM context
        """
        messages = state.get("messages", [])

        # Convert Message TypedDicts to plain dicts
        history = []
        for msg in messages[:-1]:  # Exclude current message (it's handled separately)
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "agent_name": msg.get("agent_name")
            })

        return history

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
