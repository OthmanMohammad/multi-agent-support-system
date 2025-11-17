"""
Coordinator - Orchestrate multi-agent collaboration patterns.

Implements 5 collaboration patterns: sequential, parallel, debate,
verification, and expert_panel for complex multi-agent workflows.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-107)
"""

from typing import Dict, Any, Optional, List, Literal
import asyncio
from datetime import datetime
from collections import Counter
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)

# Type alias for collaboration patterns
CollaborationPattern = Literal["sequential", "parallel", "debate", "verification", "expert_panel"]


@AgentRegistry.register("coordinator", tier="essential", category="routing")
class Coordinator(BaseAgent):
    """
    Coordinator - Orchestrate multi-agent collaboration.

    Implements 5 collaboration patterns:
    1. Sequential: Execute agents one after another (A → B → C)
    2. Parallel: Execute agents concurrently (A + B + C)
    3. Debate: Multiple agents vote on decision (majority wins)
    4. Verification: Agent A proposes, Agent B verifies
    5. Expert Panel: Assemble specialists from multiple domains

    Use Cases:
    - Complex queries requiring multiple specialists
    - High-stakes decisions needing verification
    - Cross-domain issues (billing + technical)
    - Quality assurance (proposal + verification)
    - Consensus building (debate voting)
    """

    def __init__(self, **kwargs):
        """Initialize Coordinator with orchestration capabilities."""
        config = AgentConfig(
            name="coordinator",
            type=AgentType.ORCHESTRATOR,
            temperature=0.1,
            max_tokens=500,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template="",  # Coordinator doesn't need LLM
            tier="essential",
            role="coordinator"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="coordinator", agent_type="orchestrator")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process coordination request.

        This is a pass-through - coordination is done via specific methods.

        Args:
            state: Current agent state

        Returns:
            Updated state with coordination metadata
        """
        state = self.update_state(state)
        state["coordinator_ready"] = True
        return state

    # ==================== Sequential Pattern ====================

    async def execute_sequential(
        self,
        agents: List[BaseAgent],
        state: AgentState,
        stop_on_error: bool = False
    ) -> AgentState:
        """
        Execute agents sequentially (A → B → C).

        Each agent receives output from previous agent. Use for dependent tasks
        where later agents need results from earlier agents.

        Args:
            agents: List of agents to execute in order
            state: Initial state
            stop_on_error: If True, stop on first error; if False, continue

        Returns:
            State after all agents have processed

        Example:
            # Intent → Entity → Sentiment (each uses previous output)
            state = await coordinator.execute_sequential(
                [intent_classifier, entity_extractor, sentiment_analyzer],
                state
            )
        """
        start_time = datetime.now()
        self.logger.info(
            "sequential_execution_started",
            num_agents=len(agents),
            agent_names=[a.config.name for a in agents]
        )

        results = []
        current_state = state.copy()

        for i, agent in enumerate(agents):
            try:
                self.logger.debug(
                    "sequential_agent_executing",
                    agent=agent.config.name,
                    step=i + 1,
                    total=len(agents)
                )

                # Execute agent
                current_state = await agent.process(current_state)
                results.append({
                    "agent": agent.config.name,
                    "success": True,
                    "error": None
                })

            except Exception as e:
                self.logger.error(
                    "sequential_agent_failed",
                    agent=agent.config.name,
                    error=str(e),
                    step=i + 1
                )

                results.append({
                    "agent": agent.config.name,
                    "success": False,
                    "error": str(e)
                })

                if stop_on_error:
                    break

        # Calculate total latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Add coordination metadata
        current_state["coordination_pattern"] = "sequential"
        current_state["coordination_results"] = results
        current_state["coordination_metadata"] = {
            "pattern": "sequential",
            "num_agents": len(agents),
            "successful_agents": sum(1 for r in results if r["success"]),
            "failed_agents": sum(1 for r in results if not r["success"]),
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }

        self.logger.info(
            "sequential_execution_completed",
            num_agents=len(agents),
            successful=sum(1 for r in results if r["success"]),
            failed=sum(1 for r in results if not r["success"]),
            latency_ms=latency_ms
        )

        return current_state

    # ==================== Parallel Pattern ====================

    async def execute_parallel(
        self,
        agents: List[BaseAgent],
        state: AgentState,
        merge_strategy: Literal["last_wins", "merge_all", "first_wins"] = "merge_all"
    ) -> AgentState:
        """
        Execute agents in parallel (A + B + C).

        All agents receive same initial state and execute concurrently.
        Use for independent tasks that don't depend on each other.

        Args:
            agents: List of agents to execute in parallel
            state: Initial state (same for all agents)
            merge_strategy: How to merge results
                - "last_wins": Last agent's state overwrites others
                - "merge_all": Merge all agent outputs (default)
                - "first_wins": First agent's state wins conflicts

        Returns:
            Merged state from all agents

        Example:
            # Sentiment + Complexity + Entities (all analyze same message)
            state = await coordinator.execute_parallel(
                [sentiment_analyzer, complexity_assessor, entity_extractor],
                state
            )
        """
        start_time = datetime.now()
        self.logger.info(
            "parallel_execution_started",
            num_agents=len(agents),
            agent_names=[a.config.name for a in agents],
            merge_strategy=merge_strategy
        )

        # Execute all agents concurrently
        try:
            results = await asyncio.gather(
                *[agent.process(state.copy()) for agent in agents],
                return_exceptions=True
            )
        except Exception as e:
            self.logger.error("parallel_execution_failed", error=str(e))
            return state

        # Separate successful results from errors
        successful_results = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "agent": agents[i].config.name,
                    "error": str(result)
                })
                self.logger.error(
                    "parallel_agent_failed",
                    agent=agents[i].config.name,
                    error=str(result)
                )
            else:
                successful_results.append(result)

        # Merge results based on strategy
        if not successful_results:
            # All agents failed, return original state
            self.logger.warning("parallel_all_agents_failed", num_errors=len(errors))
            return state

        merged_state = self._merge_states(successful_results, merge_strategy)

        # Calculate total latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Add coordination metadata
        merged_state["coordination_pattern"] = "parallel"
        merged_state["coordination_metadata"] = {
            "pattern": "parallel",
            "num_agents": len(agents),
            "successful_agents": len(successful_results),
            "failed_agents": len(errors),
            "merge_strategy": merge_strategy,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
            "errors": errors if errors else []
        }

        self.logger.info(
            "parallel_execution_completed",
            num_agents=len(agents),
            successful=len(successful_results),
            failed=len(errors),
            latency_ms=latency_ms
        )

        return merged_state

    # ==================== Debate Pattern ====================

    async def execute_debate(
        self,
        agents: List[BaseAgent],
        state: AgentState,
        decision_field: str = "decision",
        min_agents: int = 3
    ) -> AgentState:
        """
        Execute debate pattern with voting.

        Multiple agents analyze the same issue and vote on a decision.
        Majority vote wins. Use for high-stakes decisions needing consensus.

        Args:
            agents: List of agents (typically 3-5 for odd voting)
            state: Initial state
            decision_field: Field name where agents store their decision
            min_agents: Minimum agents required (default: 3)

        Returns:
            State with final decision based on majority vote

        Example:
            # 3 specialists vote on escalation decision
            state = await coordinator.execute_debate(
                [specialist1, specialist2, specialist3],
                state,
                decision_field="should_escalate"
            )
        """
        start_time = datetime.now()

        if len(agents) < min_agents:
            self.logger.warning(
                "debate_insufficient_agents",
                required=min_agents,
                provided=len(agents)
            )
            return state

        self.logger.info(
            "debate_execution_started",
            num_agents=len(agents),
            decision_field=decision_field
        )

        # Execute all agents in parallel
        try:
            results = await asyncio.gather(
                *[agent.process(state.copy()) for agent in agents],
                return_exceptions=True
            )
        except Exception as e:
            self.logger.error("debate_execution_failed", error=str(e))
            return state

        # Collect votes
        votes = []
        vote_details = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    "debate_agent_failed",
                    agent=agents[i].config.name,
                    error=str(result)
                )
                continue

            # Get vote from result
            vote = result.get(decision_field)
            if vote is not None:
                votes.append(vote)
                vote_details.append({
                    "agent": agents[i].config.name,
                    "vote": vote,
                    "confidence": result.get("confidence", 0.5)
                })

        # No valid votes
        if not votes:
            self.logger.warning("debate_no_valid_votes")
            return state

        # Count votes and determine winner
        vote_counts = Counter(votes)
        final_decision = vote_counts.most_common(1)[0][0]
        vote_count = vote_counts[final_decision]

        # Calculate latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Update state with decision
        state[decision_field] = final_decision
        state["debate_votes"] = vote_details
        state["debate_winner"] = final_decision
        state["debate_vote_count"] = vote_count
        state["debate_total_votes"] = len(votes)
        state["debate_consensus"] = vote_count == len(votes)  # Unanimous?

        state["coordination_pattern"] = "debate"
        state["coordination_metadata"] = {
            "pattern": "debate",
            "num_agents": len(agents),
            "valid_votes": len(votes),
            "final_decision": final_decision,
            "vote_count": vote_count,
            "total_votes": len(votes),
            "consensus": vote_count == len(votes),
            "vote_distribution": dict(vote_counts),
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }

        self.logger.info(
            "debate_execution_completed",
            final_decision=final_decision,
            vote_count=vote_count,
            total_votes=len(votes),
            consensus=vote_count == len(votes),
            latency_ms=latency_ms
        )

        return state

    # ==================== Verification Pattern ====================

    async def execute_verification(
        self,
        proposer_agent: BaseAgent,
        verifier_agent: BaseAgent,
        state: AgentState,
        max_iterations: int = 2
    ) -> AgentState:
        """
        Execute verification pattern (propose → verify → refine).

        Proposer agent generates initial response, verifier checks it,
        and proposer can refine if verification fails.

        Args:
            proposer_agent: Agent that proposes solution
            verifier_agent: Agent that verifies solution
            state: Initial state
            max_iterations: Maximum propose-verify cycles (default: 2)

        Returns:
            State with verified solution

        Example:
            # Billing specialist proposes, senior specialist verifies
            state = await coordinator.execute_verification(
                billing_specialist,
                senior_billing_specialist,
                state
            )
        """
        start_time = datetime.now()
        self.logger.info(
            "verification_execution_started",
            proposer=proposer_agent.config.name,
            verifier=verifier_agent.config.name,
            max_iterations=max_iterations
        )

        iterations = []
        current_state = state.copy()
        verified = False

        for iteration in range(max_iterations):
            try:
                # Step 1: Proposer generates solution
                self.logger.debug(
                    "verification_proposing",
                    iteration=iteration + 1,
                    agent=proposer_agent.config.name
                )

                proposal_state = await proposer_agent.process(current_state)

                # Step 2: Verifier checks solution
                self.logger.debug(
                    "verification_verifying",
                    iteration=iteration + 1,
                    agent=verifier_agent.config.name
                )

                # Add verification instruction to state
                verification_state = proposal_state.copy()
                verification_state["verification_mode"] = True
                verification_state["proposed_solution"] = proposal_state.get("response", "")

                verified_state = await verifier_agent.process(verification_state)

                # Check if verified
                verified = verified_state.get("verification_passed", True)

                iterations.append({
                    "iteration": iteration + 1,
                    "proposer": proposer_agent.config.name,
                    "verifier": verifier_agent.config.name,
                    "verified": verified,
                    "issues": verified_state.get("verification_issues", [])
                })

                if verified:
                    current_state = verified_state
                    self.logger.info(
                        "verification_passed",
                        iteration=iteration + 1
                    )
                    break
                else:
                    # Verification failed, provide feedback for next iteration
                    current_state = verified_state
                    current_state["verification_feedback"] = verified_state.get("verification_issues", [])
                    self.logger.info(
                        "verification_failed_refining",
                        iteration=iteration + 1,
                        issues=len(current_state["verification_feedback"])
                    )

            except Exception as e:
                self.logger.error(
                    "verification_iteration_failed",
                    iteration=iteration + 1,
                    error=str(e)
                )
                iterations.append({
                    "iteration": iteration + 1,
                    "error": str(e),
                    "verified": False
                })
                break

        # Calculate latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Add coordination metadata
        current_state["coordination_pattern"] = "verification"
        current_state["verification_iterations"] = iterations
        current_state["verification_passed"] = verified
        current_state["coordination_metadata"] = {
            "pattern": "verification",
            "proposer": proposer_agent.config.name,
            "verifier": verifier_agent.config.name,
            "iterations": len(iterations),
            "verified": verified,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }

        self.logger.info(
            "verification_execution_completed",
            iterations=len(iterations),
            verified=verified,
            latency_ms=latency_ms
        )

        return current_state

    # ==================== Expert Panel Pattern ====================

    async def execute_expert_panel(
        self,
        agents: List[BaseAgent],
        state: AgentState,
        panel_strategy: Literal["parallel", "sequential"] = "parallel"
    ) -> AgentState:
        """
        Execute expert panel pattern.

        Assembles specialists from multiple domains to collaboratively
        solve complex cross-domain issues.

        Args:
            agents: List of specialist agents from different domains
            state: Initial state
            panel_strategy: "parallel" for concurrent, "sequential" for ordered

        Returns:
            State with insights from all experts

        Example:
            # Complex issue needs billing + technical + CS experts
            state = await coordinator.execute_expert_panel(
                [billing_expert, technical_expert, cs_expert],
                state
            )
        """
        start_time = datetime.now()
        self.logger.info(
            "expert_panel_started",
            num_experts=len(agents),
            experts=[a.config.name for a in agents],
            strategy=panel_strategy
        )

        # Execute based on strategy
        if panel_strategy == "parallel":
            panel_state = await self.execute_parallel(agents, state, merge_strategy="merge_all")
        else:
            panel_state = await self.execute_sequential(agents, state)

        # Calculate latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Compile expert insights
        expert_insights = []
        for agent in agents:
            agent_name = agent.config.name
            # Look for agent-specific output in state
            insight = {
                "expert": agent_name,
                "domain": agent.config.tier,
                "contribution": panel_state.get(f"{agent_name}_response", "")
            }
            expert_insights.append(insight)

        # Add expert panel metadata
        panel_state["coordination_pattern"] = "expert_panel"
        panel_state["expert_panel_insights"] = expert_insights
        panel_state["coordination_metadata"] = {
            "pattern": "expert_panel",
            "num_experts": len(agents),
            "expert_names": [a.config.name for a in agents],
            "strategy": panel_strategy,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }

        self.logger.info(
            "expert_panel_completed",
            num_experts=len(agents),
            strategy=panel_strategy,
            latency_ms=latency_ms
        )

        return panel_state

    # ==================== Helper Methods ====================

    def _merge_states(
        self,
        states: List[AgentState],
        strategy: Literal["last_wins", "merge_all", "first_wins"]
    ) -> AgentState:
        """
        Merge multiple agent states based on strategy.

        Args:
            states: List of states to merge
            strategy: Merge strategy

        Returns:
            Merged state
        """
        if not states:
            return {}

        if strategy == "first_wins":
            return states[0]

        if strategy == "last_wins":
            return states[-1]

        # merge_all: Merge all states, later values overwrite earlier
        merged = {}
        for state in states:
            for key, value in state.items():
                # Special handling for lists - concatenate
                if isinstance(value, list) and key in merged:
                    if isinstance(merged[key], list):
                        merged[key].extend(value)
                    else:
                        merged[key] = value
                # Special handling for agent_history - concatenate
                elif key == "agent_history" and key in merged:
                    merged[key].extend(value)
                else:
                    merged[key] = value

        return merged


# Helper function to create instance
def create_coordinator(**kwargs) -> Coordinator:
    """
    Create Coordinator instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured Coordinator instance
    """
    return Coordinator(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_coordinator():
        """Test Coordinator with mock agents."""
        print("=" * 60)
        print("TESTING COORDINATOR")
        print("=" * 60)

        coordinator = Coordinator()

        # Create mock agents
        class MockAgent(BaseAgent):
            def __init__(self, name: str, decision: Any = None):
                config = AgentConfig(
                    name=name,
                    type=AgentType.ANALYZER
                )
                super().__init__(config=config)
                self.decision = decision

            async def process(self, state: AgentState) -> AgentState:
                state = state.copy()
                state[f"{self.config.name}_processed"] = True
                if self.decision is not None:
                    state["decision"] = self.decision
                return state

        # Test Sequential
        print("\n" + "="*60)
        print("TEST: Sequential Execution")
        print("="*60)

        state = create_initial_state(message="Test", context={})
        agents = [MockAgent("agent1"), MockAgent("agent2"), MockAgent("agent3")]

        result = await coordinator.execute_sequential(agents, state)
        print(f"✓ Sequential completed: {result['coordination_metadata']['successful_agents']} agents")

        # Test Parallel
        print("\n" + "="*60)
        print("TEST: Parallel Execution")
        print("="*60)

        result = await coordinator.execute_parallel(agents, state)
        print(f"✓ Parallel completed: {result['coordination_metadata']['successful_agents']} agents")

        # Test Debate
        print("\n" + "="*60)
        print("TEST: Debate Execution")
        print("="*60)

        debate_agents = [
            MockAgent("agent1", decision="approve"),
            MockAgent("agent2", decision="approve"),
            MockAgent("agent3", decision="reject")
        ]

        result = await coordinator.execute_debate(debate_agents, state)
        print(f"✓ Debate winner: {result['debate_winner']} ({result['debate_vote_count']}/{result['debate_total_votes']} votes)")

    # Run tests
    asyncio.run(test_coordinator())
