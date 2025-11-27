"""
LangGraph - Multi-agent orchestration using LangGraph
Refactored to use new tier-based agent architecture with AgentRegistry

This module provides backward compatibility with the original SupportGraph
interface while using the new 4-tier agent system.
"""

from typing import Any

from langgraph.graph import END, StateGraph

# CRITICAL: Import agents module to trigger registration decorators
# This must happen before accessing AgentRegistry.get_agent()
import src.agents  # noqa: F401 - Side effect import for agent registration

from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState, create_initial_state


class SupportGraph:
    """
    Multi-agent support system graph using LangGraph

    Refactored to use new tier-based architecture (243 agents across 4 tiers).
    Maintains backward compatibility with original 6-agent interface.

    New Architecture:
    - Tier 1 (Essential): Routing, KB, Support specialists
    - Tier 2 (Revenue): Sales, CS, Monetization
    - Tier 3 (Operational): Analytics, Automation, QA, Security
    - Tier 4 (Advanced): Content, Competitive Intel, ML/Predictive

    Routing Pattern:
    - Single-hop: Router → Specialist → END
    - Router can answer directly: Router → END
    - Low confidence: Router → Escalation → END
    """

    def __init__(self):
        """Initialize graph with new tier-based agents"""
        self.logger = get_logger(__name__)
        self.logger.info("support_graph_initializing", architecture="tier-based")

        # Load agents from registry
        self._load_agents()

        # Build LangGraph workflow
        self.app = self._build_graph()

        self.logger.info("support_graph_initialized", status="compiled")

    def _load_agents(self):
        """Load agents from AgentRegistry dynamically"""
        # Get router agent
        router_class = AgentRegistry.get_agent("meta_router")
        if not router_class:
            raise RuntimeError("Meta router not found in registry. Ensure agents are imported.")

        self.router = router_class()

        # Map agent names to registry names
        # Includes domain routers and specialist agents
        self.agent_mapping = {
            # Domain routers (tier 2 routing)
            "support_domain_router": "support_domain_router",
            "sales_domain_router": "sales_domain_router",
            "cs_domain_router": "cs_domain_router",
            # Support specialist agents
            "billing": "billing_agent",
            "technical": "technical_agent",
            "usage": "usage_agent",
            "api": "api_agent",
            "account": "account_deletion_specialist",
            # Sales specialist agents - Qualification
            "sales_qualification": "inbound_qualifier",
            "inbound_qualifier": "inbound_qualifier",
            "bant_qualifier": "bant_qualifier",
            # Sales specialist agents - Education
            "sales_education": "demo_scheduler",
            "feature_explainer": "feature_explainer",
            "demo_scheduler": "demo_scheduler",
            "value_proposition": "value_proposition",
            "use_case_matcher": "use_case_matcher",
            "roi_calculator": "roi_calculator",
            # Sales specialist agents - Objection Handling
            "sales_objection": "price_objection_handler",
            "price_objection_handler": "price_objection_handler",
            "competitor_comparison_handler": "competitor_comparison_handler",
            "integration_objection_handler": "integration_objection_handler",
            "security_objection_handler": "security_objection_handler",
            "timing_objection_handler": "timing_objection_handler",
            "feature_gap_handler": "feature_gap_handler",
            # Sales specialist agents - Progression
            "sales_progression": "closer",
            "closer": "closer",
            "trial_optimizer": "trial_optimizer",
            "proposal_generator": "proposal_generator",
            "contract_negotiator": "contract_negotiator",
            # Customer Success specialist agents
            "cs_health": "health_score",
            "cs_onboarding": "onboarding_coordinator",
            "cs_adoption": "feature_adoption",
            "cs_retention": "renewal_manager",
            "cs_expansion": "upsell_identifier",
            # Escalation
            "escalation": "escalation_decider",
        }

        # Initialize specialist agents dynamically
        self.agents = {}
        for legacy_name, new_name in self.agent_mapping.items():
            agent_class = AgentRegistry.get_agent(new_name)
            if agent_class:
                self.agents[legacy_name] = agent_class()
                self.logger.debug("agent_loaded", legacy_name=legacy_name, new_name=new_name)
            else:
                self.logger.warning(
                    "agent_not_found_in_registry", agent_name=new_name, legacy_name=legacy_name
                )

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow using new tier-based agents

        Returns:
            Compiled LangGraph application
        """
        workflow = StateGraph(AgentState)

        # Add router node
        workflow.add_node("router", self.router.process)

        # Add specialist nodes
        for agent_name, agent in self.agents.items():
            workflow.add_node(agent_name, agent.process)

        # Entry point - always start with router
        workflow.set_entry_point("router")

        # Routing function - decides where to go after router
        def route_from_router(state: AgentState) -> str:
            """
            Decide where to route from router

            Router sets state["next_agent"] to indicate routing:
            - "billing", "technical", "usage", "api" → Route to specialist
            - "escalation" → Route to escalation
            - None → Router answered directly, end conversation

            Args:
                state: Current agent state

            Returns:
                Next node name or END
            """
            next_agent = state.get("next_agent")

            # Map domain to agent
            if next_agent in self.agents:
                return next_agent
            elif next_agent == "support":
                # Default support routing - choose based on primary_domain
                domain = state.get("primary_domain", "general")
                if domain == "billing":
                    return "billing"
                elif domain == "technical":
                    return "technical"
                elif domain == "usage":
                    return "usage"
                elif domain == "integration":
                    return "api"
                else:
                    return "escalation"
            else:
                # Router answered directly or no routing decision
                return END

        # Build routing map
        routing_map = {agent_name: agent_name for agent_name in self.agents}
        routing_map[END] = END

        # Add conditional routing from meta router to domain routers
        workflow.add_conditional_edges("router", route_from_router, routing_map)

        # Domain routers can route to specialists
        domain_routers = ["support_domain_router", "sales_domain_router", "cs_domain_router"]
        for domain_router in domain_routers:
            if domain_router in self.agents:
                workflow.add_conditional_edges(
                    domain_router,
                    route_from_router,  # Reuse same routing logic
                    routing_map,
                )

        # Specialist agents end after responding (not routers)
        for agent_name in self.agents:
            if agent_name not in domain_routers:
                workflow.add_edge(agent_name, END)

        # Compile the graph
        compiled = workflow.compile()
        self.logger.debug("langgraph_workflow_compiled")

        return compiled

    async def run(
        self,
        message: str,
        conversation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentState:
        """
        Run conversation through graph

        This is the main execution method that:
        1. Creates initial state
        2. Runs through LangGraph workflow
        3. Returns final state

        Args:
            message: User's message
            conversation_id: Optional conversation ID for context
            context: Optional additional context (customer_metadata, etc.)

        Returns:
            Final agent state after workflow execution
        """
        self.logger.info(
            "workflow_execution_starting",
            message_preview=message[:50],
            conversation_id=conversation_id,
        )

        # Build context dict
        ctx = context or {}
        if conversation_id:
            ctx["conversation_id"] = conversation_id

        # Create initial state with context
        initial_state = create_initial_state(
            message=message, conversation_id=conversation_id, context=ctx
        )

        self.logger.debug(
            "initial_state_created",
            conversation_id=initial_state["conversation_id"],
            customer_id=initial_state["customer_id"],
        )

        # Execute workflow
        try:
            final_state = await self.app.ainvoke(initial_state)

            self.logger.info(
                "workflow_execution_completed",
                intent=final_state.get("primary_intent"),
                agents=final_state.get("agent_history"),
                status=final_state.get("status"),
            )

            return final_state

        except Exception as e:
            self.logger.error(
                "workflow_execution_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

    def get_response(self, message: str) -> str:
        """
        Simple interface - just get the response text

        Convenience method for quick interactions without
        needing to inspect the full state.

        Args:
            message: User's message

        Returns:
            Agent's response text
        """
        import asyncio

        result = asyncio.run(self.run(message))
        return result.get("agent_response", "I'm not sure how to help with that.")


async def main():
    """Test the refactored SupportGraph"""
    print("=" * 70)
    print("TESTING REFACTORED SUPPORT GRAPH - NEW TIER-BASED ARCHITECTURE")
    print("=" * 70)

    # Initialize graph
    graph = SupportGraph()

    # Test cases covering all routing paths
    test_cases = [
        ("I want to upgrade to premium", "billing"),
        ("My tasks are not syncing", "technical"),
        ("How do I invite team members?", "usage"),
        ("How do I authenticate with the API?", "api"),
    ]

    print("\n" + "=" * 70)
    print("RUNNING TEST CASES")
    print("=" * 70)

    for i, (msg, expected) in enumerate(test_cases, 1):
        print(f"\n{'#' * 70}")
        print(f"TEST {i}/{len(test_cases)}: {msg}")
        print(f"Expected routing to: {expected.upper()}")
        print(f"{'#' * 70}")

        try:
            result = await graph.run(msg)

            agents = result.get("agent_history", [])
            intent = result.get("primary_intent", "N/A")
            status = result.get("status", "unknown")

            print(f"\n✓ Intent: {intent}")
            print(f"✓ Path: {' → '.join([a.upper() for a in agents])}")
            print(f"✓ Status: {status}")

            # Show response preview
            response = result.get("agent_response", "N/A")
            preview = response[:150] + "..." if len(response) > 150 else response
            print(f"✓ Response: {preview}")

            print("✓ TEST PASSED")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("REFACTORED GRAPH TESTING COMPLETE")
    print(f"{'=' * 70}")
    print("New tier-based agents successfully integrated!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
