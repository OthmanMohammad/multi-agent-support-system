"""
Unit tests for Coordinator.

Tests all 5 collaboration patterns: sequential, parallel, debate,
verification, and expert_panel.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-111)
"""

import pytest
from unittest.mock import AsyncMock
from typing import Any

from src.agents.essential.routing.coordinator import Coordinator
from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType
from src.workflow.state import create_initial_state, AgentState


# ==================== Mock Agent for Testing ====================

class MockAgent(BaseAgent):
    """Mock agent for testing coordination patterns."""

    def __init__(self, name: str, decision: Any = None, should_fail: bool = False):
        config = AgentConfig(
            name=name,
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307"
        )
        super().__init__(config=config)
        self.decision = decision
        self.should_fail = should_fail
        self.process_count = 0

    async def process(self, state: AgentState) -> AgentState:
        """Mock process method."""
        self.process_count += 1

        if self.should_fail:
            raise Exception(f"Mock error from {self.config.name}")

        state = state.copy()
        state[f"{self.config.name}_processed"] = True
        state[f"{self.config.name}_count"] = self.process_count

        if self.decision is not None:
            state["decision"] = self.decision

        return state


# ==================== Coordinator Tests ====================

class TestCoordinator:
    """Test suite for Coordinator."""

    @pytest.fixture
    def coordinator(self):
        """Create Coordinator instance for testing."""
        return Coordinator()

    def test_initialization(self, coordinator):
        """Test Coordinator initializes correctly."""
        assert coordinator.config.name == "coordinator"
        assert coordinator.config.type == AgentType.ORCHESTRATOR
        assert coordinator.config.temperature == 0.1

    @pytest.mark.asyncio
    async def test_process_sets_ready_flag(self, coordinator):
        """Test process method sets coordinator_ready flag."""
        state = create_initial_state(message="Test", context={})

        result = await coordinator.process(state)

        assert result["coordinator_ready"] is True
        assert "coordinator" in result["agent_history"]

    # ==================== Sequential Pattern Tests ====================

    @pytest.mark.asyncio
    async def test_sequential_execution_three_agents(self, coordinator):
        """Test sequential execution with three agents."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_sequential(
            [agent1, agent2, agent3],
            state
        )

        # All agents should have processed
        assert result["agent1_processed"] is True
        assert result["agent2_processed"] is True
        assert result["agent3_processed"] is True

        # Check metadata
        assert result["coordination_pattern"] == "sequential"
        assert result["coordination_metadata"]["num_agents"] == 3
        assert result["coordination_metadata"]["successful_agents"] == 3
        assert result["coordination_metadata"]["failed_agents"] == 0

    @pytest.mark.asyncio
    async def test_sequential_execution_preserves_order(self, coordinator):
        """Test sequential execution preserves agent order."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_sequential(
            [agent1, agent2, agent3],
            state
        )

        # Each agent should have seen previous agents' work
        assert result["agent1_count"] == 1
        assert result["agent2_count"] == 1
        assert result["agent3_count"] == 1

    @pytest.mark.asyncio
    async def test_sequential_execution_with_error_continue(self, coordinator):
        """Test sequential execution continues on error."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2", should_fail=True)
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_sequential(
            [agent1, agent2, agent3],
            state,
            stop_on_error=False
        )

        # Agent 1 and 3 should succeed, agent 2 should fail
        assert result["agent1_processed"] is True
        assert "agent2_processed" not in result  # Failed
        assert result["agent3_processed"] is True

        assert result["coordination_metadata"]["successful_agents"] == 2
        assert result["coordination_metadata"]["failed_agents"] == 1

    @pytest.mark.asyncio
    async def test_sequential_execution_stop_on_error(self, coordinator):
        """Test sequential execution stops on error."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2", should_fail=True)
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_sequential(
            [agent1, agent2, agent3],
            state,
            stop_on_error=True
        )

        # Agent 1 succeeds, agent 2 fails, agent 3 doesn't run
        assert result["agent1_processed"] is True
        assert "agent2_processed" not in result
        assert "agent3_processed" not in result

        # Only 2 agents attempted
        assert len(result["coordination_results"]) == 2

    # ==================== Parallel Pattern Tests ====================

    @pytest.mark.asyncio
    async def test_parallel_execution_three_agents(self, coordinator):
        """Test parallel execution with three agents."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_parallel(
            [agent1, agent2, agent3],
            state
        )

        # All agents should have processed
        assert result["agent1_processed"] is True
        assert result["agent2_processed"] is True
        assert result["agent3_processed"] is True

        # Check metadata
        assert result["coordination_pattern"] == "parallel"
        assert result["coordination_metadata"]["num_agents"] == 3
        assert result["coordination_metadata"]["successful_agents"] == 3
        assert result["coordination_metadata"]["failed_agents"] == 0

    @pytest.mark.asyncio
    async def test_parallel_execution_merge_all_strategy(self, coordinator):
        """Test parallel execution with merge_all strategy."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_parallel(
            [agent1, agent2],
            state,
            merge_strategy="merge_all"
        )

        # Both agents' outputs should be merged
        assert result["agent1_processed"] is True
        assert result["agent2_processed"] is True
        assert result["coordination_metadata"]["merge_strategy"] == "merge_all"

    @pytest.mark.asyncio
    async def test_parallel_execution_with_failures(self, coordinator):
        """Test parallel execution handles failures gracefully."""
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2", should_fail=True)
        agent3 = MockAgent("agent3")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_parallel(
            [agent1, agent2, agent3],
            state
        )

        # Successful agents should complete
        assert result["agent1_processed"] is True
        assert result["agent3_processed"] is True

        # Failed agent should be logged
        assert result["coordination_metadata"]["successful_agents"] == 2
        assert result["coordination_metadata"]["failed_agents"] == 1

    @pytest.mark.asyncio
    async def test_parallel_execution_all_fail(self, coordinator):
        """Test parallel execution when all agents fail."""
        agent1 = MockAgent("agent1", should_fail=True)
        agent2 = MockAgent("agent2", should_fail=True)

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_parallel(
            [agent1, agent2],
            state
        )

        # Should return original state
        assert result["current_message"] == "Test"

    # ==================== Debate Pattern Tests ====================

    @pytest.mark.asyncio
    async def test_debate_execution_majority_wins(self, coordinator):
        """Test debate execution where majority vote wins."""
        agent1 = MockAgent("agent1", decision="approve")
        agent2 = MockAgent("agent2", decision="approve")
        agent3 = MockAgent("agent3", decision="reject")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_debate(
            [agent1, agent2, agent3],
            state
        )

        # Majority should win (2 approve vs 1 reject)
        assert result["decision"] == "approve"
        assert result["debate_winner"] == "approve"
        assert result["debate_vote_count"] == 2
        assert result["debate_total_votes"] == 3
        assert result["debate_consensus"] is False  # Not unanimous

    @pytest.mark.asyncio
    async def test_debate_execution_unanimous(self, coordinator):
        """Test debate execution with unanimous vote."""
        agent1 = MockAgent("agent1", decision="approve")
        agent2 = MockAgent("agent2", decision="approve")
        agent3 = MockAgent("agent3", decision="approve")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_debate(
            [agent1, agent2, agent3],
            state
        )

        assert result["decision"] == "approve"
        assert result["debate_consensus"] is True  # Unanimous
        assert result["debate_vote_count"] == 3
        assert result["debate_total_votes"] == 3

    @pytest.mark.asyncio
    async def test_debate_execution_custom_decision_field(self, coordinator):
        """Test debate with custom decision field."""
        agent1 = MockAgent("agent1", decision="escalate")
        agent2 = MockAgent("agent2", decision="escalate")
        agent3 = MockAgent("agent3", decision="continue")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_debate(
            [agent1, agent2, agent3],
            state,
            decision_field="action"
        )

        # Decision should be in custom field
        assert result["action"] == "escalate"

    @pytest.mark.asyncio
    async def test_debate_insufficient_agents(self, coordinator):
        """Test debate with too few agents."""
        agent1 = MockAgent("agent1", decision="approve")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_debate(
            [agent1],
            state,
            min_agents=3
        )

        # Should return original state (insufficient agents)
        assert result["current_message"] == "Test"

    @pytest.mark.asyncio
    async def test_debate_with_agent_failures(self, coordinator):
        """Test debate handles agent failures."""
        agent1 = MockAgent("agent1", decision="approve")
        agent2 = MockAgent("agent2", should_fail=True)
        agent3 = MockAgent("agent3", decision="approve")

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_debate(
            [agent1, agent2, agent3],
            state
        )

        # Should count only successful votes
        assert result["debate_total_votes"] == 2  # Agent 2 failed
        assert result["decision"] == "approve"

    # ==================== Verification Pattern Tests ====================

    @pytest.mark.asyncio
    async def test_verification_passes_first_time(self, coordinator):
        """Test verification pattern passes on first attempt."""
        proposer = MockAgent("proposer")
        verifier = MockAgent("verifier")

        # Verifier will set verification_passed = True
        async def mock_verify(state):
            result = await verifier.process(state)
            result["verification_passed"] = True
            return result

        verifier.process = mock_verify

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_verification(
            proposer,
            verifier,
            state
        )

        # Verification should pass
        assert result["verification_passed"] is True
        assert len(result["verification_iterations"]) == 1
        assert result["verification_iterations"][0]["verified"] is True

    @pytest.mark.asyncio
    async def test_verification_fails_then_passes(self, coordinator):
        """Test verification pattern with refinement cycle."""
        proposer = MockAgent("proposer")
        verifier = MockAgent("verifier")

        # Track iteration count
        verification_count = 0

        async def mock_verify(state):
            nonlocal verification_count
            verification_count += 1

            result = await verifier.process(state)

            # Fail first time, pass second time
            if verification_count == 1:
                result["verification_passed"] = False
                result["verification_issues"] = ["Issue needs refinement"]
            else:
                result["verification_passed"] = True
                result["verification_issues"] = []

            return result

        verifier.process = mock_verify

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_verification(
            proposer,
            verifier,
            state,
            max_iterations=2
        )

        # Should have 2 iterations
        assert len(result["verification_iterations"]) == 2
        assert result["verification_iterations"][0]["verified"] is False
        assert result["verification_iterations"][1]["verified"] is True
        assert result["verification_passed"] is True

    @pytest.mark.asyncio
    async def test_verification_max_iterations(self, coordinator):
        """Test verification stops at max iterations."""
        proposer = MockAgent("proposer")
        verifier = MockAgent("verifier")

        # Always fail verification
        async def mock_verify(state):
            result = await verifier.process(state)
            result["verification_passed"] = False
            result["verification_issues"] = ["Always fails"]
            return result

        verifier.process = mock_verify

        state = create_initial_state(message="Test", context={})

        result = await coordinator.execute_verification(
            proposer,
            verifier,
            state,
            max_iterations=2
        )

        # Should have exactly 2 iterations
        assert len(result["verification_iterations"]) == 2
        assert result["verification_passed"] is False

    # ==================== Expert Panel Pattern Tests ====================

    @pytest.mark.asyncio
    async def test_expert_panel_parallel_strategy(self, coordinator):
        """Test expert panel with parallel execution."""
        billing = MockAgent("billing_expert")
        technical = MockAgent("technical_expert")
        cs = MockAgent("cs_expert")

        state = create_initial_state(message="Complex issue", context={})

        result = await coordinator.execute_expert_panel(
            [billing, technical, cs],
            state,
            panel_strategy="parallel"
        )

        # All experts should have contributed
        assert result["billing_expert_processed"] is True
        assert result["technical_expert_processed"] is True
        assert result["cs_expert_processed"] is True

        assert result["coordination_pattern"] == "expert_panel"
        assert result["coordination_metadata"]["num_experts"] == 3
        assert result["coordination_metadata"]["strategy"] == "parallel"

    @pytest.mark.asyncio
    async def test_expert_panel_sequential_strategy(self, coordinator):
        """Test expert panel with sequential execution."""
        billing = MockAgent("billing_expert")
        technical = MockAgent("technical_expert")

        state = create_initial_state(message="Complex issue", context={})

        result = await coordinator.execute_expert_panel(
            [billing, technical],
            state,
            panel_strategy="sequential"
        )

        # Experts should have processed sequentially
        assert result["billing_expert_processed"] is True
        assert result["technical_expert_processed"] is True

        assert result["coordination_metadata"]["strategy"] == "sequential"

    # ==================== Helper Method Tests ====================

    def test_merge_states_first_wins(self, coordinator):
        """Test state merging with first_wins strategy."""
        state1 = {"a": 1, "b": 2}
        state2 = {"a": 10, "c": 3}

        merged = coordinator._merge_states([state1, state2], "first_wins")

        assert merged == state1

    def test_merge_states_last_wins(self, coordinator):
        """Test state merging with last_wins strategy."""
        state1 = {"a": 1, "b": 2}
        state2 = {"a": 10, "c": 3}

        merged = coordinator._merge_states([state1, state2], "last_wins")

        assert merged == state2

    def test_merge_states_merge_all(self, coordinator):
        """Test state merging with merge_all strategy."""
        state1 = {"a": 1, "b": 2}
        state2 = {"a": 10, "c": 3}

        merged = coordinator._merge_states([state1, state2], "merge_all")

        # Later values should overwrite earlier ones
        assert merged["a"] == 10  # From state2
        assert merged["b"] == 2   # From state1
        assert merged["c"] == 3   # From state2

    def test_merge_states_concatenates_lists(self, coordinator):
        """Test state merging concatenates list values."""
        state1 = {"items": [1, 2]}
        state2 = {"items": [3, 4]}

        merged = coordinator._merge_states([state1, state2], "merge_all")

        assert merged["items"] == [1, 2, 3, 4]

    def test_merge_states_empty_list(self, coordinator):
        """Test state merging with empty list."""
        merged = coordinator._merge_states([], "merge_all")

        assert merged == {}


# ==================== Integration Tests ====================

class TestCoordinatorIntegration:
    """Integration tests for realistic coordination scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_sequential_routing_pipeline(self):
        """Test realistic sequential routing pipeline."""
        coordinator = Coordinator()

        # Mock routing pipeline: intent → sentiment → complexity
        intent_agent = MockAgent("intent_classifier")
        sentiment_agent = MockAgent("sentiment_analyzer")
        complexity_agent = MockAgent("complexity_assessor")

        state = create_initial_state(
            message="This is broken and I need help ASAP!",
            context={}
        )

        result = await coordinator.execute_sequential(
            [intent_agent, sentiment_agent, complexity_agent],
            state
        )

        # All agents should have processed in order
        assert result["intent_classifier_processed"] is True
        assert result["sentiment_analyzer_processed"] is True
        assert result["complexity_assessor_processed"] is True

        # Metadata should reflect successful pipeline
        assert result["coordination_metadata"]["successful_agents"] == 3
        assert result["coordination_metadata"]["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_realistic_parallel_analysis(self):
        """Test realistic parallel analysis scenario."""
        coordinator = Coordinator()

        # Analyze message from multiple angles simultaneously
        sentiment = MockAgent("sentiment_analyzer")
        entities = MockAgent("entity_extractor")
        complexity = MockAgent("complexity_assessor")

        state = create_initial_state(
            message="I want to upgrade to Premium and need API integration help",
            context={}
        )

        result = await coordinator.execute_parallel(
            [sentiment, entities, complexity],
            state
        )

        # All analyses should complete
        assert result["sentiment_analyzer_processed"] is True
        assert result["entity_extractor_processed"] is True
        assert result["complexity_assessor_processed"] is True

    @pytest.mark.asyncio
    async def test_realistic_escalation_debate(self):
        """Test realistic escalation debate scenario."""
        coordinator = Coordinator()

        # 3 specialists vote on whether to escalate
        specialist1 = MockAgent("specialist1", decision=True)
        specialist2 = MockAgent("specialist2", decision=True)
        specialist3 = MockAgent("specialist3", decision=False)

        state = create_initial_state(
            message="Critical production issue",
            context={}
        )

        result = await coordinator.execute_debate(
            [specialist1, specialist2, specialist3],
            state,
            decision_field="should_escalate"
        )

        # Majority should win (2-1 for escalation)
        assert result["should_escalate"] is True
        assert result["debate_vote_count"] >= 2
