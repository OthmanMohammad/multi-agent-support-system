"""
Unit tests for Handoff Manager.

Tests handoff execution, state transfer, history tracking,
and loop prevention.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-111)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.essential.routing.handoff_manager import HandoffManager, HandoffRecord
from src.workflow.state import create_initial_state


class TestHandoffManager:
    """Test suite for Handoff Manager."""

    @pytest.fixture
    def manager(self):
        """Create HandoffManager instance for testing."""
        return HandoffManager()

    def test_initialization(self, manager):
        """Test HandoffManager initializes correctly."""
        assert manager.config.name == "handoff_manager"
        assert manager.config.type.value == "orchestrator"
        assert manager.handoff_history == []

    def test_handoff_reasons_defined(self, manager):
        """Test that handoff reasons are defined."""
        assert len(manager.HANDOFF_REASONS) == 10
        assert "complexity_escalation" in manager.HANDOFF_REASONS
        assert "specialist_needed" in manager.HANDOFF_REASONS
        assert "human_escalation" in manager.HANDOFF_REASONS

    # ==================== Handoff Execution Tests ====================

    @pytest.mark.asyncio
    async def test_successful_handoff(self, manager):
        """Test successful handoff execution."""
        state = create_initial_state(
            message="Complex issue",
            context={"conversation_id": "conv_123"}
        )
        state["current_agent"] = "tier1_agent"

        result = await manager.handoff(
            from_agent="tier1_agent",
            to_agent="tier2_agent",
            reason="complexity_escalation",
            state=state
        )

        # Current agent should be updated
        assert result["current_agent"] == "tier2_agent"

        # Handoff reason should be stored
        assert result["handoff_reason"] == "complexity_escalation"

        # Agent history should include new agent
        assert "tier2_agent" in result["agent_history"]

        # Handoff metadata should be present
        assert "handoff_metadata" in result
        assert result["handoff_metadata"]["total_handoffs"] == 1

    @pytest.mark.asyncio
    async def test_handoff_creates_chain(self, manager):
        """Test handoff creates handoff chain."""
        state = create_initial_state(
            message="Test",
            context={"conversation_id": "conv_123"}
        )

        result = await manager.handoff(
            from_agent="agent_a",
            to_agent="agent_b",
            reason="specialist_needed",
            state=state
        )

        # Check handoff chain
        assert "handoff_chain" in result
        assert len(result["handoff_chain"]) == 1
        assert result["handoff_chain"][0]["from"] == "agent_a"
        assert result["handoff_chain"][0]["to"] == "agent_b"
        assert result["handoff_chain"][0]["reason"] == "specialist_needed"

    @pytest.mark.asyncio
    async def test_multiple_handoffs_create_chain(self, manager):
        """Test multiple handoffs create complete chain."""
        state = create_initial_state(
            message="Test",
            context={"conversation_id": "conv_123"}
        )

        # First handoff
        state = await manager.handoff(
            from_agent="agent_a",
            to_agent="agent_b",
            reason="reason1",
            state=state
        )

        # Second handoff
        state = await manager.handoff(
            from_agent="agent_b",
            to_agent="agent_c",
            reason="reason2",
            state=state
        )

        # Third handoff
        state = await manager.handoff(
            from_agent="agent_c",
            to_agent="agent_d",
            reason="reason3",
            state=state
        )

        # Check chain
        assert len(state["handoff_chain"]) == 3
        assert state["current_agent"] == "agent_d"
        assert state["handoff_metadata"]["total_handoffs"] == 3

    @pytest.mark.asyncio
    async def test_handoff_with_metadata(self, manager):
        """Test handoff with additional metadata."""
        state = create_initial_state(message="Test", context={})

        metadata = {
            "escalation_level": 2,
            "ticket_id": "TICK-123"
        }

        result = await manager.handoff(
            from_agent="agent_a",
            to_agent="agent_b",
            reason="specialist_needed",
            state=state,
            metadata=metadata
        )

        # Metadata should be stored
        assert "handoff_metadata" in result
        assert result["handoff_metadata"]["additional_metadata"] == metadata

    # ==================== State Management Tests ====================

    def test_create_state_snapshot(self, manager):
        """Test state snapshot creation."""
        state = create_initial_state(message="Test", context={})
        state["conversation_id"] = "conv_123"
        state["customer_id"] = "cust_456"
        state["sentiment_score"] = 0.5
        state["internal_temp_field"] = "should_not_be_copied"

        snapshot = manager._create_state_snapshot(state)

        # Essential fields should be present
        assert "conversation_id" in snapshot
        assert "customer_id" in snapshot
        assert "sentiment_score" in snapshot

        # Snapshot should be clean (no internal fields added during runtime)
        assert snapshot["conversation_id"] == "conv_123"

    def test_update_state_after_handoff(self, manager):
        """Test state update after handoff."""
        from datetime import datetime

        state = create_initial_state(message="Test", context={})

        handoff_record = HandoffRecord(
            conversation_id="conv_123",
            from_agent="agent_a",
            to_agent="agent_b",
            reason="test_reason",
            timestamp=datetime.now(),
            state_snapshot={}
        )

        result = manager._update_state_after_handoff(state, handoff_record, None)

        # Check updates
        assert result["current_agent"] == "agent_b"
        assert result["handoff_reason"] == "test_reason"
        assert "last_handoff" in result
        assert result["last_handoff"]["from_agent"] == "agent_a"
        assert result["last_handoff"]["to_agent"] == "agent_b"

    # ==================== Loop Prevention Tests ====================

    def test_should_prevent_loop_no_loop(self, manager):
        """Test loop detection when no loop exists."""
        state = create_initial_state(message="Test", context={})
        state["handoff_chain"] = [
            {"from": "agent_a", "to": "agent_b"},
            {"from": "agent_b", "to": "agent_c"}
        ]

        is_loop = manager.should_prevent_loop("agent_c", "agent_d", state)

        assert is_loop is False

    def test_should_prevent_loop_detects_loop(self, manager):
        """Test loop detection detects actual loop."""
        state = create_initial_state(message="Test", context={})
        state["handoff_chain"] = [
            {"from": "agent_a", "to": "agent_b"},
            {"from": "agent_b", "to": "agent_a"},
            {"from": "agent_a", "to": "agent_b"}
        ]

        # Trying to handoff from agent_b to agent_a again (3rd time)
        is_loop = manager.should_prevent_loop("agent_b", "agent_a", state, max_returns=2)

        assert is_loop is True

    def test_should_prevent_loop_allows_within_threshold(self, manager):
        """Test loop prevention allows handoffs within threshold."""
        state = create_initial_state(message="Test", context={})
        state["handoff_chain"] = [
            {"from": "agent_a", "to": "agent_b"}
        ]

        # First time A→B, second attempt should be allowed (max_returns=2)
        is_loop = manager.should_prevent_loop("agent_a", "agent_b", state, max_returns=2)

        assert is_loop is False

    # ==================== History Tests ====================

    @pytest.mark.asyncio
    async def test_get_handoff_history_all(self, manager):
        """Test getting all handoff history."""
        state1 = create_initial_state(message="Test", context={"conversation_id": "conv_1"})
        state2 = create_initial_state(message="Test", context={"conversation_id": "conv_2"})

        await manager.handoff("a", "b", "reason1", state1)
        await manager.handoff("c", "d", "reason2", state2)

        history = manager.get_handoff_history()

        assert len(history) == 2
        assert history[0].from_agent == "a"
        assert history[1].from_agent == "c"

    @pytest.mark.asyncio
    async def test_get_handoff_history_filtered(self, manager):
        """Test getting filtered handoff history."""
        state1 = create_initial_state(message="Test", context={"conversation_id": "conv_1"})
        state2 = create_initial_state(message="Test", context={"conversation_id": "conv_2"})

        await manager.handoff("a", "b", "reason1", state1)
        await manager.handoff("c", "d", "reason2", state2)

        history = manager.get_handoff_history(conversation_id="conv_1")

        assert len(history) == 1
        assert history[0].conversation_id == "conv_1"

    def test_get_handoff_chain(self, manager):
        """Test getting handoff chain from state."""
        state = create_initial_state(message="Test", context={})
        state["handoff_chain"] = [
            {"from": "a", "to": "b"},
            {"from": "b", "to": "c"}
        ]

        chain = manager.get_handoff_chain(state)

        assert len(chain) == 2
        assert chain[0]["from"] == "a"
        assert chain[1]["from"] == "b"

    # ==================== Statistics Tests ====================

    def test_get_handoff_stats_empty(self, manager):
        """Test handoff statistics with no handoffs."""
        state = create_initial_state(message="Test", context={})

        stats = manager.get_handoff_stats(state)

        assert stats["total_handoffs"] == 0
        assert stats["unique_agents"] == 0

    def test_get_handoff_stats_with_handoffs(self, manager):
        """Test handoff statistics with handoffs."""
        state = create_initial_state(message="Test", context={})
        state["handoff_chain"] = [
            {"from": "a", "to": "b", "reason": "reason1", "timestamp": "2024-01-01"},
            {"from": "b", "to": "c", "reason": "reason1", "timestamp": "2024-01-02"},
            {"from": "c", "to": "d", "reason": "reason2", "timestamp": "2024-01-03"}
        ]
        state["current_agent"] = "d"

        stats = manager.get_handoff_stats(state)

        assert stats["total_handoffs"] == 3
        assert stats["unique_agents"] == 4  # a, b, c, d
        assert stats["current_agent"] == "d"
        assert stats["first_agent"] == "a"
        assert stats["most_common_reason"] == "reason1"
        assert stats["reasons"]["reason1"] == 2
        assert stats["reasons"]["reason2"] == 1

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_handoff_handles_storage_error(self, manager):
        """Test handoff handles storage errors gracefully."""
        # Mock _store_handoff to raise exception
        manager._store_handoff = AsyncMock(side_effect=Exception("Storage error"))

        state = create_initial_state(message="Test", context={})

        # Handoff should still succeed despite storage error
        result = await manager.handoff(
            from_agent="agent_a",
            to_agent="agent_b",
            reason="test",
            state=state
        )

        # Handoff should have completed
        assert result["current_agent"] == "agent_b"

    @pytest.mark.asyncio
    async def test_process_without_handoff_request(self, manager):
        """Test process when no handoff requested."""
        state = create_initial_state(message="Test", context={})

        result = await manager.process(state)

        # Should just update agent history
        assert "handoff_manager" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_process_with_handoff_request(self, manager):
        """Test process when handoff requested."""
        state = create_initial_state(message="Test", context={})
        state["handoff_requested"] = True
        state["current_agent"] = "agent_a"
        state["handoff_to_agent"] = "agent_b"
        state["handoff_reason"] = "specialist_needed"

        result = await manager.process(state)

        # Handoff should have been executed
        assert result["current_agent"] == "agent_b"
        assert result["handoff_requested"] is False


# ==================== Integration Tests ====================

class TestHandoffManagerIntegration:
    """Integration tests for realistic handoff scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_tier1_to_tier2_escalation(self):
        """Test realistic Tier 1 to Tier 2 escalation."""
        manager = HandoffManager()

        state = create_initial_state(
            message="Complex billing issue requiring specialist",
            context={"conversation_id": "conv_123", "customer_id": "cust_456"}
        )
        state["current_agent"] = "billing_tier1"
        state["complexity_score"] = 8

        result = await manager.handoff(
            from_agent="billing_tier1",
            to_agent="billing_tier2",
            reason="complexity_escalation",
            state=state,
            metadata={"complexity_score": 8}
        )

        assert result["current_agent"] == "billing_tier2"
        assert result["handoff_reason"] == "complexity_escalation"
        assert len(result["handoff_chain"]) == 1

    @pytest.mark.asyncio
    async def test_realistic_multi_specialist_chain(self):
        """Test realistic multi-specialist handoff chain."""
        manager = HandoffManager()

        state = create_initial_state(
            message="Issue spanning billing and technical domains",
            context={"conversation_id": "conv_123"}
        )

        # Handoff 1: Router → Billing
        state = await manager.handoff("meta_router", "billing_specialist", "domain_transfer", state)

        # Handoff 2: Billing → Technical (cross-domain)
        state = await manager.handoff("billing_specialist", "technical_specialist", "multi_domain", state)

        # Handoff 3: Technical → Senior Technical (complexity)
        state = await manager.handoff("technical_specialist", "senior_technical", "complexity_escalation", state)

        # Check complete chain
        assert len(state["handoff_chain"]) == 3
        assert state["current_agent"] == "senior_technical"

        stats = manager.get_handoff_stats(state)
        assert stats["total_handoffs"] == 3
        assert stats["first_agent"] == "meta_router"

    @pytest.mark.asyncio
    async def test_realistic_human_escalation(self):
        """Test realistic AI to human escalation."""
        manager = HandoffManager()

        state = create_initial_state(
            message="Customer demands human agent",
            context={"conversation_id": "conv_123"}
        )
        state["sentiment_score"] = -0.8
        state["explicit_human_request"] = True

        result = await manager.handoff(
            from_agent="ai_agent",
            to_agent="human_agent",
            reason="customer_request",
            state=state,
            metadata={
                "sentiment_score": -0.8,
                "explicit_request": True
            }
        )

        assert result["current_agent"] == "human_agent"
        assert result["handoff_reason"] == "customer_request"
        assert result["handoff_metadata"]["additional_metadata"]["explicit_request"] is True
