"""
Context Injector - Inject enriched customer context into agent prompts.

Automatically fetches and formats enriched customer intelligence, account
health, support history, and activity data for agent prompts.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-110)
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@dataclass
class EnrichedContext:
    """Enriched customer context data."""
    customer_id: str
    company_name: str
    plan: str
    health_score: int
    churn_risk: float
    churn_risk_label: str
    ltv: float
    mrr: float
    team_size: int
    account_age_days: int
    last_login: Optional[str]
    last_activity: Optional[str]
    recent_activity_summary: str
    support_history_summary: str
    avg_csat: Optional[float]
    open_tickets: int
    red_flags: list
    green_flags: list


@AgentRegistry.register("context_injector", tier="essential", category="routing")
class ContextInjector(BaseAgent):
    """
    Context Injector - Enrich prompts with customer intelligence.

    Fetches and formats context from multiple sources:
    - Customer intelligence (health, churn risk, LTV)
    - Recent activity (last login, usage patterns)
    - Support history (past tickets, CSAT scores)
    - Account health (red/green flags)

    Injects formatted context into agent prompts automatically.
    Target overhead: <50ms
    """

    # Health score thresholds
    HEALTH_EXCELLENT = 80
    HEALTH_GOOD = 60
    HEALTH_FAIR = 40
    HEALTH_POOR = 40

    # Churn risk thresholds
    CHURN_LOW = 0.3
    CHURN_MEDIUM = 0.6
    CHURN_HIGH = 0.6

    def __init__(self, **kwargs):
        """Initialize Context Injector."""
        config = AgentConfig(
            name="context_injector",
            type=AgentType.UTILITY,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=100,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template="",  # Context injector doesn't use LLM
            tier="essential",
            role="context_injector"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="context_injector", agent_type="utility")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process context injection into state.

        Args:
            state: Current agent state

        Returns:
            State with enriched context
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            customer_id = state.get("customer_id")
            conversation_id = state.get("conversation_id")

            if not customer_id:
                self.logger.warning("context_injector_no_customer_id")
                return state

            # Enrich context
            enriched = await self.enrich_context(
                customer_id=customer_id,
                conversation_id=conversation_id
            )

            # Store enriched context in state
            state["enriched_context"] = enriched

            # Calculate overhead
            overhead_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["context_injection_metadata"] = {
                "overhead_ms": overhead_ms,
                "timestamp": datetime.now().isoformat(),
                "customer_id": customer_id
            }

            self.logger.info(
                "context_enriched",
                customer_id=customer_id,
                overhead_ms=overhead_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "context_enrichment_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return state

    async def inject_context(
        self,
        system_prompt: str,
        customer_id: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Inject enriched context into system prompt.

        Args:
            system_prompt: Base system prompt
            customer_id: Customer ID
            conversation_id: Optional conversation ID

        Returns:
            System prompt with injected context

        Example:
            enriched_prompt = await injector.inject_context(
                system_prompt="You are a billing specialist...",
                customer_id="cust_123"
            )
        """
        try:
            start_time = datetime.now()

            # Get enriched context
            context = await self.enrich_context(
                customer_id=customer_id,
                conversation_id=conversation_id
            )

            # Format context section
            context_section = self._format_context_section(context)

            # Inject into prompt
            enriched_prompt = f"{context_section}\n\n{system_prompt}"

            # Log overhead
            overhead_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.info(
                "context_injected",
                customer_id=customer_id,
                overhead_ms=overhead_ms
            )

            return enriched_prompt

        except Exception as e:
            self.logger.error(
                "context_injection_failed",
                error=str(e),
                customer_id=customer_id
            )
            # Return original prompt on error
            return system_prompt

    async def enrich_context(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None
    ) -> EnrichedContext:
        """
        Fetch and enrich customer context from multiple sources.

        Args:
            customer_id: Customer ID
            conversation_id: Optional conversation ID

        Returns:
            Enriched context object
        """
        # In production, this would fetch from multiple services
        # For now, we'll use mock data from customer_metadata

        # TODO: Implement actual data fetching
        # - Customer service: health score, churn risk, LTV
        # - Activity service: last login, usage patterns
        # - Support service: tickets, CSAT scores
        # - Analytics service: engagement metrics

        # Mock implementation using available data
        mock_context = EnrichedContext(
            customer_id=customer_id,
            company_name=f"Company {customer_id[-4:]}",
            plan="premium",
            health_score=75,
            churn_risk=0.25,
            churn_risk_label="low",
            ltv=12000,
            mrr=1000,
            team_size=25,
            account_age_days=180,
            last_login="2024-01-14 10:30 AM",
            last_activity="2024-01-14 2:45 PM",
            recent_activity_summary="Active user, logged in 5 times this week",
            support_history_summary="3 tickets in past 30 days, avg resolution time 4 hours",
            avg_csat=4.5,
            open_tickets=1,
            red_flags=[],
            green_flags=["high_engagement", "paying_customer", "positive_csat"]
        )

        return mock_context

    def _format_context_section(self, context: EnrichedContext) -> str:
        """
        Format enriched context for prompt injection.

        Args:
            context: Enriched context

        Returns:
            Formatted context string
        """
        # Determine health label
        health_label = self._get_health_label(context.health_score)

        # Determine churn risk label
        churn_label = self._get_churn_label(context.churn_risk)

        # Build context section
        lines = [
            "<customer_context>",
            f"Company: {context.company_name}",
            f"Plan: {context.plan.upper()}",
            f"Team Size: {context.team_size} users",
            "",
            "📊 Account Health:",
            f"  Health Score: {context.health_score}/100 ({health_label})",
            f"  Churn Risk: {int(context.churn_risk * 100)}% ({churn_label})",
            f"  Lifetime Value: ${context.ltv:,.0f}",
            f"  MRR: ${context.mrr:,.0f}",
            "",
            "📅 Activity:",
            f"  Account Age: {context.account_age_days} days",
            f"  Last Login: {context.last_login}",
            f"  Recent Activity: {context.recent_activity_summary}",
        ]

        # Add support history
        if context.support_history_summary:
            lines.extend([
                "",
                "🎫 Support History:",
                f"  {context.support_history_summary}",
                f"  Avg CSAT: {context.avg_csat if context.avg_csat else 'N/A'}/5.0",
                f"  Open Tickets: {context.open_tickets}"
            ])

        # Add red flags (warnings)
        if context.red_flags:
            lines.extend([
                "",
                "🚩 Red Flags:",
            ])
            for flag in context.red_flags:
                lines.append(f"  - {flag}")

        # Add green flags (positive signals)
        if context.green_flags:
            lines.extend([
                "",
                "✅ Positive Signals:",
            ])
            for flag in context.green_flags:
                lines.append(f"  - {flag}")

        lines.append("</customer_context>")

        return "\n".join(lines)

    def _get_health_label(self, health_score: int) -> str:
        """Get health score label."""
        if health_score >= self.HEALTH_EXCELLENT:
            return "Excellent"
        elif health_score >= self.HEALTH_GOOD:
            return "Good"
        elif health_score >= self.HEALTH_FAIR:
            return "Fair"
        else:
            return "Poor"

    def _get_churn_label(self, churn_risk: float) -> str:
        """Get churn risk label."""
        if churn_risk < self.CHURN_LOW:
            return "Low Risk"
        elif churn_risk < self.CHURN_HIGH:
            return "Medium Risk"
        else:
            return "High Risk"

    def get_context_summary(self, context: EnrichedContext) -> str:
        """
        Get human-readable context summary.

        Args:
            context: Enriched context

        Returns:
            Summary string
        """
        health_label = self._get_health_label(context.health_score)
        churn_label = self._get_churn_label(context.churn_risk)

        summary = f"""
Customer: {context.company_name} ({context.plan})
Health: {context.health_score}/100 ({health_label})
Churn Risk: {int(context.churn_risk * 100)}% ({churn_label})
MRR: ${context.mrr:,.0f} | LTV: ${context.ltv:,.0f}
Team: {context.team_size} users | Account Age: {context.account_age_days} days
Open Tickets: {context.open_tickets} | Avg CSAT: {context.avg_csat if context.avg_csat else 'N/A'}
"""
        return summary.strip()

    def extract_context_from_state(self, state: AgentState) -> Optional[EnrichedContext]:
        """
        Extract enriched context from state if available.

        Args:
            state: Agent state

        Returns:
            EnrichedContext if available, None otherwise
        """
        return state.get("enriched_context")


# Helper function to create instance
def create_context_injector(**kwargs) -> ContextInjector:
    """
    Create ContextInjector instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured ContextInjector instance
    """
    return ContextInjector(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio

    async def test_context_injector():
        """Test Context Injector with sample data."""
        print("=" * 60)
        print("TESTING CONTEXT INJECTOR")
        print("=" * 60)

        injector = ContextInjector()

        # Test 1: Enrich context
        print("\n" + "="*60)
        print("TEST 1: Enrich Context")
        print("="*60)

        context = await injector.enrich_context(
            customer_id="cust_abc123",
            conversation_id="conv_xyz789"
        )

        print("\n✓ Context enriched:")
        print(injector.get_context_summary(context))

        # Test 2: Inject context into prompt
        print("\n" + "="*60)
        print("TEST 2: Inject Context into Prompt")
        print("="*60)

        base_prompt = """You are a billing specialist. Help the customer with billing inquiries.
Be professional, empathetic, and solution-oriented."""

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_abc123"
        )

        print("\n✓ Prompt with injected context:")
        print("-" * 60)
        print(enriched_prompt)
        print("-" * 60)

        # Test 3: Context formatting
        print("\n" + "="*60)
        print("TEST 3: Context Formatting")
        print("="*60)

        formatted = injector._format_context_section(context)
        print("\n✓ Formatted context section:")
        print(formatted)

    # Run tests
    asyncio.run(test_context_injector())
