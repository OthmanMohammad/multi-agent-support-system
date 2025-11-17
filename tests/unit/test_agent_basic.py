"""Test basic agent execution"""
import asyncio
from src.agents.essential.routing.meta_router import MetaRouter
from src.workflow.state import create_initial_state

async def test_meta_router():
    print("=" * 60)
    print("TESTING META ROUTER AGENT")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        ("I want to upgrade my plan", "SALES"),
        ("My app keeps crashing", "SUPPORT"),
        ("How do I use this feature?", "SUPPORT"),
        ("I'm thinking about canceling", "CUSTOMER_SUCCESS"),
    ]
    
    router = MetaRouter()
    
    for query, expected_domain in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print(f"   Expected: {expected_domain}")
        
        state = create_initial_state(
            message=query,
            conversation_id=f"test-{hash(query)}"
        )
        
        try:
            result = await router.process(state)

            # MetaRouter stores domain in 'domain' field and next agent in 'next_agent'
            domain = result.get('domain', 'N/A')
            next_agent = result.get('next_agent', 'N/A')
            confidence = result.get('confidence', 0)

            match = "✓" if expected_domain.lower() in str(domain).lower() else "✗"
            print(f"   {match} Domain: {domain} → {next_agent} (confidence: {confidence:.2f})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Meta Router Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_meta_router())