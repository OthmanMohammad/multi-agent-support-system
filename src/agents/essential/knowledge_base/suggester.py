"""
KB Suggester Agent.

Suggests new KB articles based on patterns from gap detection, support tickets,
feature requests, and product changes.

Part of: STORY-002 Knowledge Base Swarm (TASK-208)
"""

from typing import List, Dict, Optional
from collections import Counter
from datetime import datetime, timedelta, UTC
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.database.connection import get_db_session
from src.database.models import Conversation
from src.utils.logging.setup import get_logger


class KBSuggester(BaseAgent):
    """
    KB Suggester Agent.

    Suggests new KB articles based on multiple data sources:
    - KB gaps (from gap detector)
    - Recent support ticket trends
    - Product releases
    - Common support topics
    """

    def __init__(self):
        """Initialize KB Suggester agent."""
        config = AgentConfig(
            name="kb_suggester",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=512,
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info("kb_suggester_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and generate article suggestions.

        Args:
            state: AgentState

        Returns:
            Updated state with suggestions
        """
        kb_gaps = state.get("kb_gaps", [])
        days = state.get("suggestion_days", 30)
        limit = state.get("suggestion_limit", 10)

        self.logger.info(
            "kb_suggestion_generation_started",
            gaps_count=len(kb_gaps),
            days=days,
            limit=limit
        )

        # Generate suggestions
        suggestions = await self.generate_suggestions(
            kb_gaps=kb_gaps,
            days=days,
            limit=limit
        )

        # Update state
        state = self.update_state(
            state,
            kb_suggestions=suggestions,
            suggestions_count=len(suggestions)
        )

        self.logger.info(
            "kb_suggestion_generation_completed",
            suggestions_count=len(suggestions)
        )

        return state

    async def generate_suggestions(
        self,
        kb_gaps: List[Dict] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict]:
        """
        Generate KB article suggestions.

        Args:
            kb_gaps: Output from gap detector
            days: Look back period
            limit: Max suggestions

        Returns:
            List of article suggestions
        """
        suggestions = []

        # Source 1: KB gaps (highest priority)
        if kb_gaps:
            for gap in kb_gaps[:5]:  # Top 5 gaps
                suggestions.append({
                    "title": gap["suggested_article_title"],
                    "category": gap["category"],
                    "reason": f"Frequently asked ({gap['frequency']} times)",
                    "priority": self._map_gap_priority(gap["priority_score"]),
                    "target_audience": "all_users",
                    "estimated_length": "medium",
                    "should_include": gap.get("key_questions", []),
                    "source": "gap_detection"
                })

        # Source 2: High-volume ticket topics
        ticket_suggestions = await self._suggest_from_tickets(days)
        suggestions.extend(ticket_suggestions)

        # Deduplicate and prioritize
        suggestions = self._deduplicate_suggestions(suggestions)
        suggestions = self._prioritize_suggestions(suggestions)

        return suggestions[:limit]

    async def _suggest_from_tickets(self, days: int) -> List[Dict]:
        """
        Suggest articles based on support ticket patterns.

        Args:
            days: Look back period

        Returns:
            List of suggestions
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        try:
            async with get_db_session() as session:
                # Get conversations
                result = await session.execute(
                    select(Conversation).where(
                        Conversation.created_at >= cutoff
                    )
                )
                convos = result.scalars().all()

                # Count primary intents
                intent_counts = Counter([
                    c.primary_intent
                    for c in convos
                    if c.primary_intent
                ])

                # Top 3 most common intents
                top_intents = intent_counts.most_common(3)

                suggestions = []
                for intent, count in top_intents:
                    if count >= 10:  # Significant volume
                        suggestions.append({
                            "title": self._intent_to_title(intent),
                            "category": self._intent_to_category(intent),
                            "reason": f"Common support topic ({count} tickets)",
                            "priority": "medium",
                            "target_audience": "all_users",
                            "estimated_length": "short",
                            "should_include": ["Quick steps", "Common issues"],
                            "source": "support_tickets"
                        })

                self.logger.info(
                    "ticket_suggestions_generated",
                    suggestions_count=len(suggestions)
                )

                return suggestions

        except SQLAlchemyError as e:
            self.logger.error(
                "ticket_suggestions_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    def _intent_to_title(self, intent: str) -> str:
        """
        Convert intent to article title.

        Args:
            intent: User intent string

        Returns:
            Article title
        """
        intent_titles = {
            "billing_upgrade": "How to Upgrade Your Plan",
            "billing_downgrade": "How to Downgrade Your Plan",
            "billing_refund": "Refund Policy and Process",
            "billing_invoice": "Accessing Your Invoices",
            "technical_bug": "Troubleshooting Common Issues",
            "technical_sync": "Fixing Sync Problems",
            "technical_performance": "Improving Performance",
            "feature_create": "Creating Your First Project",
            "feature_edit": "Editing and Managing Projects",
            "feature_invite": "Inviting Team Members",
            "feature_export": "Exporting Your Data",
            "integration_api": "API Integration Guide",
            "integration_webhook": "Setting Up Webhooks",
            "account_login": "Login and Authentication Help"
        }
        return intent_titles.get(
            intent,
            f"Guide to {intent.replace('_', ' ').title()}"
        )

    def _intent_to_category(self, intent: str) -> str:
        """
        Map intent to category.

        Args:
            intent: User intent

        Returns:
            Category string
        """
        if intent.startswith("billing"):
            return "billing"
        elif intent.startswith("technical"):
            return "technical"
        elif intent.startswith("integration"):
            return "integrations"
        elif intent.startswith("account"):
            return "account"
        else:
            return "usage"

    def _map_gap_priority(self, priority_score: float) -> str:
        """
        Map numeric priority to level.

        Args:
            priority_score: Numeric score (0-100)

        Returns:
            Priority level string
        """
        if priority_score >= 80:
            return "critical"
        elif priority_score >= 60:
            return "high"
        elif priority_score >= 40:
            return "medium"
        else:
            return "low"

    def _deduplicate_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """
        Remove duplicate suggestions.

        Args:
            suggestions: List of suggestions

        Returns:
            Deduplicated list
        """
        seen_titles = set()
        unique = []

        for suggestion in suggestions:
            if suggestion["title"] not in seen_titles:
                seen_titles.add(suggestion["title"])
                unique.append(suggestion)

        return unique

    def _prioritize_suggestions(self, suggestions: List[Dict]) -> List[Dict]:
        """
        Sort suggestions by priority.

        Args:
            suggestions: List of suggestions

        Returns:
            Sorted list
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 3),
                x.get("source", "z")  # Prefer gap_detection over others
            )
        )

        return suggestions


if __name__ == "__main__":
    # Test KB Suggester
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB SUGGESTER")
        print("=" * 60)

        suggester = KBSuggester()

        # Test gaps
        test_gaps = [
            {
                "suggested_article_title": "API Authentication Guide",
                "category": "api",
                "frequency": 25,
                "priority_score": 85,
                "key_questions": ["How to authenticate?", "API key setup?"]
            },
            {
                "suggested_article_title": "Data Export Tutorial",
                "category": "usage",
                "frequency": 15,
                "priority_score": 65,
                "key_questions": ["How to export?", "Export formats?"]
            }
        ]

        print("\nTest 1: Generate suggestions from gaps")
        suggestions = await suggester.generate_suggestions(
            kb_gaps=test_gaps,
            days=30,
            limit=5
        )

        print(f"Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['title']}")
            print(f"   Category: {suggestion['category']}")
            print(f"   Priority: {suggestion['priority']}")
            print(f"   Reason: {suggestion['reason']}")
            print(f"   Source: {suggestion['source']}")

        print("\nTest 2: Process with state")
        state = create_initial_state(message="test", context={})
        state["kb_gaps"] = test_gaps
        state = await suggester.process(state)
        print(f"Suggestions generated: {state.get('suggestions_count', 0)}")

        print("\n✓ KB Suggester tests completed!")

    asyncio.run(test())
