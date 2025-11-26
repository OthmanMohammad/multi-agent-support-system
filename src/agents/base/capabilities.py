"""
Agent capability mixins.

This module provides reusable capability mixins that agents can inherit
to gain specific functionalities like KB search, collaboration, etc.
"""

from abc import ABC
from typing import Any


class KBSearchCapability(ABC):
    """
    Mixin for agents that search knowledge base.

    Agents with this capability can search the knowledge base
    and synthesize answers from retrieved articles.
    """

    async def search_and_synthesize(
        self, query: str, category: str | None = None, limit: int = 3
    ) -> str:
        """
        Search KB and synthesize answer from results.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            Synthesized KB context string
        """
        if not hasattr(self, "search_knowledge_base"):
            return ""

        results = await self.search_knowledge_base(query, category, limit)

        if not results:
            return ""

        # Format results for LLM consumption
        kb_context = "\n\n".join(
            [f"Article: {r['title']}\n{r['content'][:500]}..." for r in results]
        )

        return kb_context

    async def get_top_article(
        self, query: str, category: str | None = None
    ) -> dict[str, Any] | None:
        """
        Get the single most relevant KB article.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            Top matching article or None
        """
        if not hasattr(self, "search_knowledge_base"):
            return None

        results = await self.search_knowledge_base(query, category, limit=1)

        return results[0] if results else None


class CollaborationCapability(ABC):
    """
    Mixin for agents that collaborate with other agents.

    Agents with this capability can request collaboration,
    coordinate with other agents, and manage handoffs.
    """

    async def request_collaboration(
        self, agent_names: list[str], pattern: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Request collaboration from other agents.

        Args:
            agent_names: List of agent names to collaborate with
            pattern: Collaboration pattern (sequential, parallel, debate, etc.)
            context: Shared context for collaboration

        Returns:
            Collaboration results
        """
        # This would interface with the coordinator service
        # For now, this is a placeholder that subclasses can override
        raise NotImplementedError(
            "Collaboration capability requires coordinator service integration"
        )

    async def handoff_to_agent(
        self, target_agent: str, context: dict[str, Any], reason: str
    ) -> dict[str, Any]:
        """
        Handoff conversation to another agent.

        Args:
            target_agent: Target agent name
            context: Context to pass to target agent
            reason: Reason for handoff

        Returns:
            Handoff confirmation
        """
        return {
            "target_agent": target_agent,
            "context": context,
            "reason": reason,
            "status": "handoff_initiated",
        }

    async def request_expert_panel(
        self, topic: str, experts: list[str], question: str
    ) -> dict[str, Any]:
        """
        Request an expert panel discussion.

        Args:
            topic: Discussion topic
            experts: List of expert agents
            question: Question for the panel

        Returns:
            Panel discussion results
        """
        return {"topic": topic, "experts": experts, "question": question, "pattern": "expert_panel"}


class DatabaseWriteCapability(ABC):
    """
    Mixin for agents that write to database.

    Agents with this capability can persist data to the database,
    including audit logs, analytics, and conversation history.
    """

    async def write_to_db(self, table: str, data: dict[str, Any]) -> bool:
        """
        Write data to database.

        Args:
            table: Target table name
            data: Data to write

        Returns:
            True if successful
        """
        # This would interface with the database service
        # For now, this is a placeholder that subclasses can override
        raise NotImplementedError("Database write capability requires database service integration")

    async def log_agent_action(self, action: str, metadata: dict[str, Any]) -> bool:
        """
        Log an agent action to audit log.

        Args:
            action: Action description
            metadata: Additional metadata

        Returns:
            True if logged successfully
        """
        if not hasattr(self, "config"):
            return False

        log_data = {"agent_name": self.config.name, "action": action, "metadata": metadata}

        return await self.write_to_db("agent_audit_log", log_data)


class ContextEnrichmentCapability(ABC):
    """
    Mixin for agents that enrich context with customer data.

    Agents with this capability can fetch and enrich context
    with customer history, preferences, and metadata.
    """

    async def enrich_customer_context(
        self, customer_id: str, include_history: bool = True, include_preferences: bool = True
    ) -> dict[str, Any]:
        """
        Enrich context with customer data.

        Args:
            customer_id: Customer identifier
            include_history: Include conversation history
            include_preferences: Include customer preferences

        Returns:
            Enriched context dictionary
        """
        if not hasattr(self, "get_enriched_context"):
            return {}

        return await self.get_enriched_context(customer_id)


class SentimentAnalysisCapability(ABC):
    """
    Mixin for agents that analyze sentiment.

    Agents with this capability can analyze message sentiment
    and emotional tone.
    """

    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis results with score and classification
        """
        # This would use an LLM or sentiment analysis service
        # For now, this is a placeholder
        return {
            "score": 0.0,  # -1 (negative) to 1 (positive)
            "classification": "neutral",
            "confidence": 0.5,
        }


class EntityExtractionCapability(ABC):
    """
    Mixin for agents that extract entities.

    Agents with this capability can extract structured entities
    from unstructured text.
    """

    async def extract_entities(self, text: str, entity_types: list[str]) -> dict[str, list[str]]:
        """
        Extract entities from text.

        Args:
            text: Text to extract from
            entity_types: Types of entities to extract
                (e.g., "plan_type", "feature", "date")

        Returns:
            Dictionary mapping entity types to extracted values
        """
        # This would use an LLM or NER service
        # For now, this is a placeholder
        return {entity_type: [] for entity_type in entity_types}
