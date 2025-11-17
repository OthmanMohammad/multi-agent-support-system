"""Test debate workflow with multiple agents"""
import asyncio
from src.workflow.patterns.debate import DebateWorkflow, DebateParticipant
from src.workflow.state import create_initial_state

async def mock_agent(agent_name: str, state):
    """Mock agent that provides different perspectives"""
    opinions = {
        "technical_expert": "This is a sync bug in version 2.1.3",
        "support_lead": "Customer needs to clear cache first",
        "product_manager": "Known issue, fix scheduled for next release"
    }

    await asyncio.sleep(0.2)  # Simulate LLM call
    state["agent_response"] = opinions.get(agent_name, "Unknown")
    state["response_confidence"] = 0.85
    return state

async def test_debate():
    print("=" * 60)
    print("DEBATE WORKFLOW: Technical Issue Resolution")
    print("=" * 60)

    workflow = DebateWorkflow(
        name="sync_issue_resolution",
        participants=[
            DebateParticipant("technical_expert"),
            DebateParticipant("support_lead"),
            DebateParticipant("product_manager"),
        ],
        max_rounds=2
    )

    state = create_initial_state(
        message="Sync keeps failing with error code 503",
        conversation_id="debate-001"
    )

    result = await workflow.execute(state, mock_agent)

    print(f"\n📊 Debate Results:")
    print(f"   Success: {result.success}")
    print(f"   Rounds: {len(result.rounds)}")
    print(f"   Participants: {', '.join(result.participants)}")
    if result.final_decision:
        print(f"   Final decision: {result.final_decision[:100]}...")

    print("\n" + "=" * 60)
    print("✓ Debate Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_debate())