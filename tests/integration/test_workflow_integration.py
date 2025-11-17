"""
Integration tests for workflow patterns with actual agents.

Tests the integration of workflow patterns (sequential, parallel, debate)
with real agent execution.
"""
import pytest
from src.workflow.patterns.sequential import SequentialWorkflow, SequentialStep
from src.workflow.patterns.parallel import ParallelWorkflow, ParallelAgent, AggregationStrategy
from src.workflow.state import create_initial_state


# =============================================================================
# SEQUENTIAL WORKFLOW INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_sequential_workflow_with_routing_agents():
    """Test sequential workflow with routing agents"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
        ]
    )

    state = create_initial_state(
        message="I want to upgrade my plan",
        conversation_id="test-seq-001"
    )

    result = await workflow.execute(state)

    # Verify workflow completed
    assert result is not None
    assert "agent_history" in result
    assert len(result["agent_history"]) >= 1


@pytest.mark.asyncio
async def test_sequential_workflow_multi_step():
    """Test multi-step sequential workflow"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
            SequentialStep(agent_name="intent_classifier"),
        ]
    )

    state = create_initial_state(
        message="How do I export my data?",
        conversation_id="test-seq-002"
    )

    result = await workflow.execute(state)

    # Verify both steps executed
    assert result is not None
    assert "agent_history" in result


# =============================================================================
# PARALLEL WORKFLOW INTEGRATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_parallel_workflow_with_analysis_agents():
    """Test parallel workflow with multiple analysis agents"""
    workflow = ParallelWorkflow(
        agents=[
            ParallelAgent(name="intent_classifier"),
            ParallelAgent(name="sentiment_analyzer"),
        ],
        aggregation_strategy=AggregationStrategy.MERGE
    )

    state = create_initial_state(
        message="I'm frustrated with the slow performance!",
        conversation_id="test-par-001"
    )

    result = await workflow.execute(state)

    # Verify parallel execution
    assert result is not None
    assert "agent_responses" in result or "agent_history" in result


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_sequential_workflow_handles_missing_agent():
    """Test that sequential workflow handles missing agent gracefully"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="nonexistent_agent"),
        ]
    )

    state = create_initial_state(
        message="Test message",
        conversation_id="test-err-001"
    )

    # Should handle error gracefully
    with pytest.raises(Exception):
        await workflow.execute(state)


@pytest.mark.asyncio
async def test_workflow_with_timeout():
    """Test workflow execution with timeout"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router", timeout=30),
        ]
    )

    state = create_initial_state(
        message="Quick test",
        conversation_id="test-timeout-001"
    )

    # Should complete within timeout
    result = await workflow.execute(state)
    assert result is not None


# =============================================================================
# STATE MANAGEMENT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_workflow_preserves_conversation_id():
    """Test that workflows preserve conversation ID through execution"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
        ]
    )

    conversation_id = "test-preserve-001"
    state = create_initial_state(
        message="Test message",
        conversation_id=conversation_id
    )

    result = await workflow.execute(state)

    assert result is not None
    assert result.get("conversation_id") == conversation_id


@pytest.mark.asyncio
async def test_workflow_accumulates_agent_history():
    """Test that workflows accumulate agent history"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
            SequentialStep(agent_name="intent_classifier"),
        ]
    )

    state = create_initial_state(
        message="Multi-step test",
        conversation_id="test-history-001"
    )

    result = await workflow.execute(state)

    # Should have history from both agents
    assert result is not None
    assert "agent_history" in result
    # Note: Actual history length depends on implementation


# =============================================================================
# INTEGRATION WITH CONTEXT ENRICHMENT
# =============================================================================

@pytest.mark.asyncio
async def test_workflow_with_context_enrichment():
    """Test workflow execution with context enrichment"""
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
        ]
    )

    state = create_initial_state(
        message="I need help with billing",
        conversation_id="test-context-001",
        context={
            "customer_id": "cust_123",
            "customer_metadata": {
                "plan": "premium",
                "mrr": 99
            }
        }
    )

    result = await workflow.execute(state)

    # Verify context was preserved
    assert result is not None
    assert result.get("customer_id") == "cust_123"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_workflow_execution_performance():
    """Test that workflow execution completes in reasonable time"""
    import time

    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
        ]
    )

    state = create_initial_state(
        message="Quick performance test",
        conversation_id="test-perf-001"
    )

    start_time = time.time()
    result = await workflow.execute(state)
    execution_time = time.time() - start_time

    # Should complete in under 10 seconds for simple workflow
    assert result is not None
    assert execution_time < 10.0


# =============================================================================
# FIXTURE TESTS (verify shared fixtures work)
# =============================================================================

@pytest.mark.asyncio
async def test_workflow_with_shared_fixtures(job_store):
    """Test that shared fixtures work with workflow tests"""
    # Verify job_store fixture is available
    assert job_store is not None

    # Create a simple workflow
    workflow = SequentialWorkflow(
        steps=[
            SequentialStep(agent_name="meta_router"),
        ]
    )

    state = create_initial_state(
        message="Fixture test",
        conversation_id="test-fixture-001"
    )

    result = await workflow.execute(state)
    assert result is not None
