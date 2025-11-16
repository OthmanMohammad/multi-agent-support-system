"""Simple end-to-end test with real conversation"""
import asyncio
from src.agents.essential.routing.meta_router import MetaRouter
from src.workflow.state import create_initial_state
from src.workflow.patterns.sequential import SequentialWorkflow, SequentialStep

async def test_full_conversation():
    print("=" * 60)
    print("END-TO-END TEST: Customer Upgrade Request")
    print("=" * 60)

    # Step 1: Initialize MetaRouter
    router = MetaRouter()

    # Step 2: Create conversation
    user_message = "I want to upgrade to the premium plan"
    state = create_initial_state(
        message=user_message,
        conversation_id="e2e-test-001",
        customer_id="customer-123"
    )

    print(f"\n???? User: {user_message}")

    # Step 3: Route the message
    result = await router.process(state)

    print(f"\n???? MetaRouter Decision:")
    print(f"   Domain: {result.get('domain', 'N/A')}")
    print(f"   Next Agent: {result.get('next_agent', 'N/A')}")
    print(f"   Reasoning: {result.get('reasoning', 'N/A')}")

    # Step 4: Show full state
    print(f"\n???? Conversation State:")
    print(f"   Turn count: {result.get('turn_count', 0)}")
    print(f"   History length: {len(result.get('history', []))}")

    print("\n" + "=" * 60)
    print("??? End-to-End Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_conversation())
