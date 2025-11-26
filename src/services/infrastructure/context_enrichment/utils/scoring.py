"""
Relevance scoring for context data.

Calculates relevance scores for context data based on recency, completeness,
agent type relevance, and data quality.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from src.services.infrastructure.context_enrichment.types import AgentType, RelevanceScoreComponents

logger = structlog.get_logger(__name__)


class RelevanceScorer:
    """
    Calculate relevance scores for context data.

    Relevance is calculated based on:
    - Recency: How fresh is the data?
    - Completeness: How complete is the data?
    - Agent relevance: How relevant for the requesting agent type?
    - Data quality: Are there missing/invalid values?

    Example:
        >>> scorer = RelevanceScorer()
        >>> score = scorer.score(context_data, AgentType.BILLING)
        >>> assert 0 <= score <= 1
    """

    # Agent-specific field weights
    AGENT_FIELD_WEIGHTS = {
        AgentType.GENERAL: {
            "company_name": 1.0,
            "plan": 0.9,
            "health_score": 0.8,
            "last_login": 0.7,
        },
        AgentType.BILLING: {
            "mrr": 1.0,
            "plan": 1.0,
            "payment_method_valid": 1.0,
            "billing_cycle": 0.9,
            "seats_total": 0.8,
        },
        AgentType.TECHNICAL_SUPPORT: {
            "last_conversation": 1.0,
            "open_tickets": 1.0,
            "avg_csat": 0.9,
            "most_common_issues": 0.8,
            "last_login": 0.7,
        },
        AgentType.SALES: {
            "churn_risk": 1.0,
            "ltv": 1.0,
            "mrr": 1.0,
            "health_score": 0.9,
            "company_size": 0.8,
        },
        AgentType.CSM: {
            "health_score": 1.0,
            "churn_risk": 1.0,
            "nps_score": 0.9,
            "login_count_30d": 0.8,
            "avg_csat": 0.8,
        },
    }

    def __init__(self):
        """Initialize relevance scorer"""
        self.logger = logger.bind(component="relevance_scorer")

    def score(self, context: dict[str, Any], agent_type: AgentType, **kwargs) -> float:
        """
        Calculate overall relevance score (0-1).

        Args:
            context: Context data to score
            agent_type: Agent type requesting the context
            **kwargs: Additional parameters

        Returns:
            Relevance score between 0 and 1

        Example:
            >>> scorer = RelevanceScorer()
            >>> score = scorer.score(
            ...     {"company_name": "Acme", "plan": "enterprise"},
            ...     AgentType.GENERAL
            ... )
            >>> assert 0 <= score <= 1
        """
        components = self.score_with_breakdown(context, agent_type, **kwargs)

        # Weighted average of components
        score = (
            components["recency_score"] * 0.3
            + components["completeness_score"] * 0.3
            + components["agent_relevance_score"] * 0.3
            + components["data_quality_score"] * 0.1
        )

        self.logger.debug(
            "relevance_score_calculated", score=score, agent_type=agent_type.value, **components
        )

        return min(1.0, max(0.0, score))

    def score_with_breakdown(
        self, context: dict[str, Any], agent_type: AgentType, **kwargs
    ) -> RelevanceScoreComponents:
        """
        Calculate relevance score with component breakdown.

        Args:
            context: Context data to score
            agent_type: Agent type requesting the context
            **kwargs: Additional parameters

        Returns:
            RelevanceScoreComponents with individual scores

        Example:
            >>> scorer = RelevanceScorer()
            >>> components = scorer.score_with_breakdown(data, AgentType.BILLING)
            >>> print(f"Recency: {components['recency_score']}")
        """
        return RelevanceScoreComponents(
            recency_score=self._score_recency(context),
            completeness_score=self._score_completeness(context, agent_type),
            agent_relevance_score=self._score_agent_relevance(context, agent_type),
            data_quality_score=self._score_data_quality(context),
        )

    def _score_recency(self, context: dict[str, Any]) -> float:
        """
        Score data recency.

        More recent data gets higher scores.
        Uses exponential decay with 30-day half-life.

        Args:
            context: Context data

        Returns:
            Recency score (0-1)
        """
        # Check for timestamp fields
        timestamp_fields = ["enriched_at", "last_login", "last_conversation", "customer_since"]

        most_recent = None
        for field in timestamp_fields:
            value = context.get(field)
            if value and isinstance(value, datetime):
                if most_recent is None or value > most_recent:
                    most_recent = value

        if most_recent is None:
            # No timestamp found - assume stale
            return 0.5

        # Calculate age in days
        age_days = (datetime.now(UTC) - most_recent).days

        # Exponential decay with 30-day half-life
        # After 30 days, score is 0.5; after 60 days, 0.25; etc.
        score = 2 ** (-age_days / 30)

        return min(1.0, score)

    def _score_completeness(self, context: dict[str, Any], agent_type: AgentType) -> float:
        """
        Score data completeness for agent type.

        Checks how many relevant fields are populated.

        Args:
            context: Context data
            agent_type: Agent type

        Returns:
            Completeness score (0-1)
        """
        relevant_fields = self.AGENT_FIELD_WEIGHTS.get(
            agent_type, self.AGENT_FIELD_WEIGHTS[AgentType.GENERAL]
        )

        if not relevant_fields:
            return 1.0

        filled_weight = 0.0
        total_weight = 0.0

        for field, weight in relevant_fields.items():
            total_weight += weight
            value = context.get(field)

            # Check if field is filled with meaningful data
            if value is not None:
                if isinstance(value, (list, dict)):
                    if len(value) > 0:
                        filled_weight += weight
                elif isinstance(value, str):
                    if value.strip():
                        filled_weight += weight
                else:
                    filled_weight += weight

        if total_weight == 0:
            return 1.0

        return filled_weight / total_weight

    def _score_agent_relevance(self, context: dict[str, Any], agent_type: AgentType) -> float:
        """
        Score how relevant the data is for the agent type.

        Checks for presence of agent-specific critical fields.

        Args:
            context: Context data
            agent_type: Agent type

        Returns:
            Agent relevance score (0-1)
        """
        relevant_fields = self.AGENT_FIELD_WEIGHTS.get(
            agent_type, self.AGENT_FIELD_WEIGHTS[AgentType.GENERAL]
        )

        if not relevant_fields:
            return 1.0

        # Get top 3 most important fields for this agent
        top_fields = sorted(relevant_fields.items(), key=lambda x: x[1], reverse=True)[:3]

        if not top_fields:
            return 1.0

        # Score based on presence of top fields
        score = sum(
            1.0 if context.get(field) is not None else 0.0 for field, _ in top_fields
        ) / len(top_fields)

        return score

    def _score_data_quality(self, context: dict[str, Any]) -> float:
        """
        Score data quality.

        Checks for:
        - Missing required fields
        - Invalid values (negative numbers where inappropriate)
        - Placeholder/dummy values

        Args:
            context: Context data

        Returns:
            Data quality score (0-1)
        """
        issues = 0
        checks = 0

        # Check for required fields
        required_fields = ["company_name"]
        for field in required_fields:
            checks += 1
            if not context.get(field):
                issues += 1

        # Check for invalid numeric values
        numeric_fields = ["mrr", "ltv", "health_score", "login_count_30d"]
        for field in numeric_fields:
            value = context.get(field)
            if value is not None:
                checks += 1
                if isinstance(value, (int, float)):
                    if value < 0:
                        issues += 1
                    # Health score should be 0-100
                    if field == "health_score" and (value < 0 or value > 100):
                        issues += 1

        # Check for placeholder values
        placeholder_patterns = ["test", "example", "placeholder", "todo", "unknown"]
        for _key, value in context.items():
            if isinstance(value, str):
                checks += 1
                if any(pattern in value.lower() for pattern in placeholder_patterns):
                    issues += 1

        if checks == 0:
            return 1.0

        # Quality score based on issues found
        quality = 1.0 - (issues / checks)
        return max(0.0, quality)


# Convenience functions
_scorer_instance: RelevanceScorer | None = None


def _get_scorer() -> RelevanceScorer:
    """Get or create scorer instance"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RelevanceScorer()
    return _scorer_instance


def score_context(context: dict[str, Any], agent_type: AgentType, **kwargs) -> float:
    """
    Convenience function to score context.

    Args:
        context: Context data
        agent_type: Agent type
        **kwargs: Additional parameters

    Returns:
        Relevance score (0-1)

    Example:
        >>> score = score_context(data, AgentType.BILLING)
    """
    return _get_scorer().score(context, agent_type, **kwargs)


def score_with_breakdown(
    context: dict[str, Any], agent_type: AgentType, **kwargs
) -> RelevanceScoreComponents:
    """
    Convenience function to score with breakdown.

    Args:
        context: Context data
        agent_type: Agent type
        **kwargs: Additional parameters

    Returns:
        Score components

    Example:
        >>> components = score_with_breakdown(data, AgentType.BILLING)
    """
    return _get_scorer().score_with_breakdown(context, agent_type, **kwargs)
