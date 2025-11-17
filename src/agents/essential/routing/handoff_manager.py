"""
Handoff Manager - Manage agent-to-agent handoffs and state transfers.

Tracks handoff history, transfers state cleanly, logs reasons,
and stores handoffs in database for audit trail.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-108)
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from dataclasses import dataclass, asdict
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@dataclass
class HandoffRecord:
    """Record of an agent handoff."""
    conversation_id: str
    from_agent: str
    to_agent: str
    reason: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    handoff_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


@AgentRegistry.register("handoff_manager", tier="essential", category="routing")
class HandoffManager(BaseAgent):
    """
    Handoff Manager - Manage agent-to-agent handoffs.

    Responsibilities:
    - Track handoff history
    - Transfer state cleanly between agents
    - Log handoff reasons and metadata
    - Store handoffs in database
    - Prevent information loss during transfers
    - Provide handoff audit trail

    Use Cases:
    - Specialist escalation (Tier 1 → Tier 2)
    - Domain transfer (Support → Sales)
    - Complexity escalation (Simple → Expert)
    - Human escalation (AI → Human agent)
    """

    # Common handoff reasons
    HANDOFF_REASONS = [
        "complexity_escalation",      # Query too complex
        "specialist_needed",           # Needs specific expertise
        "domain_transfer",             # Moving to different domain
        "human_escalation",            # Escalating to human
        "verification_needed",         # Needs verification
        "insufficient_confidence",     # Low confidence response
        "customer_request",            # Customer asked for transfer
        "policy_required",             # Requires policy decision
        "authorization_needed",        # Needs higher authority
        "multi_domain",                # Crosses multiple domains
    ]

    def __init__(self, **kwargs):
        """Initialize Handoff Manager."""
        config = AgentConfig(
            name="handoff_manager",
            type=AgentType.ORCHESTRATOR,
            temperature=0.1,
            max_tokens=300,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template="",  # Handoff manager doesn't need LLM
            tier="essential",
            role="handoff_manager"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="handoff_manager", agent_type="orchestrator")
        self.handoff_history: List[HandoffRecord] = []

    async def process(self, state: AgentState) -> AgentState:
        """
        Process handoff request from state.

        Looks for handoff instructions in state and executes them.

        Args:
            state: Current agent state

        Returns:
            Updated state after handoff
        """
        state = self.update_state(state)

        # Check if handoff is requested
        if state.get("handoff_requested"):
            from_agent = state.get("current_agent", "unknown")
            to_agent = state.get("handoff_to_agent", "unknown")
            reason = state.get("handoff_reason", "unspecified")

            state = await self.handoff(from_agent, to_agent, reason, state)

        return state

    async def handoff(
        self,
        from_agent: str,
        to_agent: str,
        reason: str,
        state: AgentState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Execute agent-to-agent handoff.

        Args:
            from_agent: Agent transferring control
            to_agent: Agent receiving control
            reason: Reason for handoff
            state: Current state to transfer
            metadata: Additional handoff metadata

        Returns:
            Updated state with handoff recorded

        Example:
            state = await handoff_manager.handoff(
                from_agent="billing_tier1",
                to_agent="billing_tier2",
                reason="complexity_escalation",
                state=state
            )
        """
        try:
            start_time = datetime.now()
            conversation_id = state.get("conversation_id", "unknown")

            self.logger.info(
                "handoff_initiated",
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                conversation_id=conversation_id
            )

            # Create state snapshot for transfer
            state_snapshot = self._create_state_snapshot(state)

            # Create handoff record
            handoff_record = HandoffRecord(
                conversation_id=conversation_id,
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                timestamp=datetime.now(),
                state_snapshot=state_snapshot,
                success=True,
                error=None
            )

            # Store handoff in database (async)
            await self._store_handoff(handoff_record)

            # Update state with handoff information
            state = self._update_state_after_handoff(state, handoff_record, metadata)

            # Add to in-memory history
            self.handoff_history.append(handoff_record)

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.info(
                "handoff_completed",
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                latency_ms=latency_ms,
                conversation_id=conversation_id
            )

            return state

        except Exception as e:
            self.logger.error(
                "handoff_failed",
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                error=str(e)
            )

            # Create failed handoff record
            handoff_record = HandoffRecord(
                conversation_id=state.get("conversation_id", "unknown"),
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                timestamp=datetime.now(),
                state_snapshot={},
                success=False,
                error=str(e)
            )

            # Still try to store failed handoff
            try:
                await self._store_handoff(handoff_record)
            except:
                pass  # Silent fail for storage

            # Return original state (handoff failed)
            return state

    def _create_state_snapshot(self, state: AgentState) -> Dict[str, Any]:
        """
        Create a clean snapshot of state for transfer.

        Includes essential fields for handoff while excluding
        temporary or internal fields.

        Args:
            state: Current state

        Returns:
            Clean state snapshot
        """
        # Essential fields to preserve in handoff
        essential_fields = [
            "conversation_id",
            "customer_id",
            "current_message",
            "message_history",
            "customer_metadata",
            "domain",
            "intent_domain",
            "intent_category",
            "extracted_entities",
            "sentiment_score",
            "emotion",
            "urgency",
            "satisfaction",
            "complexity_score",
            "multi_agent_needed",
            "support_category",
            "sales_category",
            "cs_category",
            "agent_history",
            "response",
            "confidence"
        ]

        snapshot = {}
        for field in essential_fields:
            if field in state:
                snapshot[field] = state[field]

        return snapshot

    def _update_state_after_handoff(
        self,
        state: AgentState,
        handoff_record: HandoffRecord,
        metadata: Optional[Dict[str, Any]]
    ) -> AgentState:
        """
        Update state after handoff execution.

        Args:
            state: Current state
            handoff_record: Handoff record
            metadata: Additional metadata

        Returns:
            Updated state
        """
        # Update current agent
        state["current_agent"] = handoff_record.to_agent

        # Add to agent history
        if "agent_history" not in state:
            state["agent_history"] = []
        state["agent_history"].append(handoff_record.to_agent)

        # Store handoff information
        state["last_handoff"] = {
            "from_agent": handoff_record.from_agent,
            "to_agent": handoff_record.to_agent,
            "reason": handoff_record.reason,
            "timestamp": handoff_record.timestamp.isoformat()
        }

        state["handoff_reason"] = handoff_record.reason

        # Add handoff chain tracking
        if "handoff_chain" not in state:
            state["handoff_chain"] = []

        state["handoff_chain"].append({
            "from": handoff_record.from_agent,
            "to": handoff_record.to_agent,
            "reason": handoff_record.reason,
            "timestamp": handoff_record.timestamp.isoformat()
        })

        # Add handoff metadata
        state["handoff_metadata"] = {
            "total_handoffs": len(state["handoff_chain"]),
            "last_handoff_timestamp": handoff_record.timestamp.isoformat(),
            "current_agent": handoff_record.to_agent,
            "additional_metadata": metadata or {}
        }

        # Clear handoff request flags
        state["handoff_requested"] = False

        return state

    async def _store_handoff(self, handoff_record: HandoffRecord) -> None:
        """
        Store handoff record in database.

        Args:
            handoff_record: Handoff record to store
        """
        try:
            # In a real implementation, this would write to database
            # For now, we'll log it as a structured event
            self.logger.info(
                "handoff_stored",
                conversation_id=handoff_record.conversation_id,
                from_agent=handoff_record.from_agent,
                to_agent=handoff_record.to_agent,
                reason=handoff_record.reason,
                timestamp=handoff_record.timestamp.isoformat(),
                success=handoff_record.success,
                error=handoff_record.error,
                state_fields=list(handoff_record.state_snapshot.keys())
            )

            # TODO: Implement actual database storage
            # Example:
            # async with self.db.session() as session:
            #     session.add(AgentHandoff(
            #         conversation_id=handoff_record.conversation_id,
            #         from_agent=handoff_record.from_agent,
            #         to_agent=handoff_record.to_agent,
            #         reason=handoff_record.reason,
            #         timestamp=handoff_record.timestamp,
            #         state_snapshot=json.dumps(handoff_record.state_snapshot),
            #         success=handoff_record.success,
            #         error=handoff_record.error
            #     ))
            #     await session.commit()

        except Exception as e:
            self.logger.error(
                "handoff_storage_failed",
                error=str(e),
                conversation_id=handoff_record.conversation_id
            )
            # Don't raise - storage failure shouldn't break handoff

    def get_handoff_history(
        self,
        conversation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[HandoffRecord]:
        """
        Get handoff history.

        Args:
            conversation_id: Filter by conversation (optional)
            limit: Maximum records to return

        Returns:
            List of handoff records
        """
        if conversation_id:
            filtered = [
                h for h in self.handoff_history
                if h.conversation_id == conversation_id
            ]
            return filtered[-limit:]
        else:
            return self.handoff_history[-limit:]

    def get_handoff_chain(self, state: AgentState) -> List[Dict[str, Any]]:
        """
        Get the complete handoff chain from state.

        Args:
            state: Current state

        Returns:
            List of handoff events in order
        """
        return state.get("handoff_chain", [])

    def should_prevent_loop(
        self,
        from_agent: str,
        to_agent: str,
        state: AgentState,
        max_returns: int = 2
    ) -> bool:
        """
        Check if handoff would create a loop.

        Prevents infinite handoff loops (A → B → A → B...).

        Args:
            from_agent: Source agent
            to_agent: Destination agent
            state: Current state
            max_returns: Maximum times same handoff allowed

        Returns:
            True if handoff should be prevented
        """
        handoff_chain = state.get("handoff_chain", [])

        # Count how many times this exact handoff has happened
        same_handoffs = sum(
            1 for h in handoff_chain
            if h["from"] == from_agent and h["to"] == to_agent
        )

        if same_handoffs >= max_returns:
            self.logger.warning(
                "handoff_loop_detected",
                from_agent=from_agent,
                to_agent=to_agent,
                occurrences=same_handoffs
            )
            return True

        return False

    def get_handoff_stats(self, state: AgentState) -> Dict[str, Any]:
        """
        Get handoff statistics for current conversation.

        Args:
            state: Current state

        Returns:
            Handoff statistics
        """
        handoff_chain = state.get("handoff_chain", [])

        if not handoff_chain:
            return {
                "total_handoffs": 0,
                "unique_agents": 0,
                "avg_time_between_handoffs": 0,
                "reasons": {}
            }

        # Count reasons
        reasons = {}
        for h in handoff_chain:
            reason = h.get("reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        # Unique agents
        all_agents = set()
        for h in handoff_chain:
            all_agents.add(h["from"])
            all_agents.add(h["to"])

        return {
            "total_handoffs": len(handoff_chain),
            "unique_agents": len(all_agents),
            "most_common_reason": max(reasons.items(), key=lambda x: x[1])[0] if reasons else None,
            "reasons": reasons,
            "current_agent": state.get("current_agent", "unknown"),
            "first_agent": handoff_chain[0]["from"] if handoff_chain else None,
            "last_handoff_timestamp": handoff_chain[-1]["timestamp"] if handoff_chain else None
        }


# Helper function to create instance
def create_handoff_manager(**kwargs) -> HandoffManager:
    """
    Create HandoffManager instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured HandoffManager instance
    """
    return HandoffManager(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_handoff_manager():
        """Test Handoff Manager with sample handoffs."""
        print("=" * 60)
        print("TESTING HANDOFF MANAGER")
        print("=" * 60)

        manager = HandoffManager()

        # Test 1: Simple handoff
        print("\n" + "="*60)
        print("TEST 1: Simple Handoff")
        print("="*60)

        state = create_initial_state(
            message="Complex billing issue",
            context={"conversation_id": "conv_123"}
        )
        state["current_agent"] = "billing_tier1"

        state = await manager.handoff(
            from_agent="billing_tier1",
            to_agent="billing_tier2",
            reason="complexity_escalation",
            state=state
        )

        print(f"✓ Handoff executed: billing_tier1 → billing_tier2")
        print(f"  Current agent: {state['current_agent']}")
        print(f"  Reason: {state['handoff_reason']}")
        print(f"  Total handoffs: {state['handoff_metadata']['total_handoffs']}")

        # Test 2: Multiple handoffs
        print("\n" + "="*60)
        print("TEST 2: Multiple Handoffs (Chain)")
        print("="*60)

        state = await manager.handoff(
            from_agent="billing_tier2",
            to_agent="billing_specialist",
            reason="specialist_needed",
            state=state
        )

        stats = manager.get_handoff_stats(state)
        print(f"✓ Handoff chain: {stats['total_handoffs']} handoffs")
        print(f"  Unique agents: {stats['unique_agents']}")
        print(f"  Current agent: {stats['current_agent']}")

        # Test 3: Loop detection
        print("\n" + "="*60)
        print("TEST 3: Loop Detection")
        print("="*60)

        # Try to create a loop
        is_loop = manager.should_prevent_loop(
            from_agent="billing_specialist",
            to_agent="billing_tier1",
            state=state
        )

        print(f"✓ Loop detected: {is_loop}")

        # Display handoff chain
        print("\n" + "="*60)
        print("HANDOFF CHAIN")
        print("="*60)

        chain = manager.get_handoff_chain(state)
        for i, handoff in enumerate(chain, 1):
            print(f"{i}. {handoff['from']} → {handoff['to']} ({handoff['reason']})")

    # Run tests
    asyncio.run(test_handoff_manager())
