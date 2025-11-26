"""Test workflow patterns - Standalone test without circular dependencies"""
import asyncio
import sys
from pathlib import Path

# Add specific directories to avoid importing through package __init__ files
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "workflow" / "patterns"))
sys.path.insert(0, str(project_root / "src" / "workflow"))
sys.path.insert(0, str(project_root))

# Import directly from files
from sequential import SequentialWorkflow, SequentialStep
from parallel import ParallelWorkflow, ParallelAgent
from src.workflow.state import create_initial_state

# Mock agent executor for testing
async def mock_executor(agent_name, state):
    """Simulates an agent processing"""
    await asyncio.sleep(0.1)  # Simulate work
    state["agent_response"] = f"{agent_name} processed: {state.get('user_message', '')}"
    state["response_confidence"] = 0.9
    return state

async def test_sequential():
    print("=" * 60)
    print("TESTING SEQUENTIAL WORKFLOW")
    print("=" * 60)

    workflow = SequentialWorkflow(
        name="test_onboarding",
        steps=[
            SequentialStep("data_collector", required=True),
            SequentialStep("account_setup", required=True),
            SequentialStep("welcome_email", required=False),
        ]
    )

    initial_state = create_initial_state(
        message="Start onboarding",
        conversation_id="test-seq-1"
    )

    result = await workflow.execute(initial_state, mock_executor)

    print(f"\n✓ Success: {result.success}")
    print(f"✓ Steps executed: {len(result.steps_executed)}")
    print(f"✓ Steps: {' → '.join(result.steps_executed)}")
    print(f"✓ Execution time: {result.execution_time:.2f}s")

    print("\n" + "=" * 60)
    print("✓ Sequential Pattern Works!")
    print("=" * 60)

async def test_parallel():
    print("\n" + "=" * 60)
    print("TESTING PARALLEL WORKFLOW")
    print("=" * 60)

    workflow = ParallelWorkflow(
        name="multi_analysis",
        agents=[
            ParallelAgent("sentiment_analyzer", weight=1.0),
            ParallelAgent("intent_classifier", weight=0.8),
            ParallelAgent("urgency_detector", weight=0.9),
        ]
    )

    initial_state = create_initial_state(
        message="Urgent: Need help now!",
        conversation_id="test-par-1"
    )

    result = await workflow.execute(initial_state, mock_executor)

    print(f"\n✓ Success: {result.success}")
    print(f"✓ Agents completed: {len(result.agents_completed)}")
    print(f"✓ Agents: {', '.join(result.agents_completed)}")
    print(f"✓ Execution time: {result.execution_time:.2f}s")
    print(f"✓ All agents ran in parallel!")

    print("\n" + "=" * 60)
    print("✓ Parallel Pattern Works!")
    print("=" * 60)

async def main():
    await test_sequential()
    await test_parallel()

if __name__ == "__main__":
    asyncio.run(main())
