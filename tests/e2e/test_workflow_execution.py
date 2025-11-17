"""End-to-end test with complete workflow"""
import asyncio
from src.agents.essential.routing.meta_router import MetaRouter
from src.agents.essential.routing.support_domain_router import SupportDomainRouter
from src.workflow.state import create_initial_state
from src.workflow.patterns.sequential import SequentialWorkflow, SequentialStep

async def agent_executor(agent_name: str, state):
    """Execute agent based on name"""
    if agent_name == "meta_router":
        agent = MetaRouter()
        return await agent.process(state)
    elif agent_name == "support_domain_router":
        agent = SupportDomainRouter()
        return await agent.process(state)
    # Add more agents as needed
    return state

async def test_support_workflow():
    print("=" * 60)
    print("WORKFLOW TEST: Technical Support Issue")
    print("=" * 60)

    # Create workflow
    workflow = SequentialWorkflow(
        name="support_ticket_handling",
        steps=[
            SequentialStep("meta_router", required=True),
            SequentialStep("support_domain_router", required=True),
        ]
    )

    # Initial state
    state = create_initial_state(
        message="My app keeps crashing when I try to sync",
        conversation_id="e2e-workflow-001"
    )

    print(f"\n???? User: {state['current_message']}")

    # Execute workflow
    result = await workflow.execute(state, agent_executor)

    print(f"\n???? Workflow Results:")
    print(f"   Success: {result.success}")
    print(f"   Steps: {' ??? '.join(result.steps_executed)}")
    print(f"   Time: {result.execution_time:.2f}s")
    print(f"   Final domain: {result.final_state.get('domain', 'N/A')}")
    print(f"   Final support category: {result.final_state.get('support_category', 'N/A')}")

    print("\n" + "=" * 60)
    print("??? Workflow Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_support_workflow())
