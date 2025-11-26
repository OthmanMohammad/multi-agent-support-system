"""
Example usage of the Context Enrichment System.

Run this file to see the context enrichment system in action.
"""

import asyncio

from src.services.infrastructure.context_enrichment import get_context_service


async def example_basic_enrichment():
    """Basic context enrichment example"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Context Enrichment")
    print("=" * 80)

    # Get the context service
    service = get_context_service()

    # Enrich context for a customer
    print("\nEnriching context for customer_test_123...")
    context = await service.enrich_context("customer_test_123")

    # Print summary
    print("\n📊 CONTEXT SUMMARY:")
    summary = context.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Print full context (as it would appear in agent prompt)
    print("\n📝 FULL CONTEXT (for agent prompt):")
    print(context.to_prompt_context())

    print(f"\n⏱️  Enrichment took: {context.enrichment_latency_ms:.2f}ms")
    print(f"💾 Cache hit: {context.cache_hit}")
    print(f"🔧 Providers used: {', '.join(context.providers_used)}")


async def example_cache_performance():
    """Demonstrate caching performance"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Cache Performance")
    print("=" * 80)

    service = get_context_service()
    customer_id = "customer_cache_demo"

    # First call (cache miss)
    print("\n1st call (cache miss):")
    context1 = await service.enrich_context(customer_id)
    print(f"  Latency: {context1.enrichment_latency_ms:.2f}ms")
    print(f"  Cache hit: {context1.cache_hit}")

    # Second call (cache hit)
    print("\n2nd call (cache hit):")
    context2 = await service.enrich_context(customer_id)
    print(f"  Latency: {context2.enrichment_latency_ms:.2f}ms")
    print(f"  Cache hit: {context2.cache_hit}")

    speedup = context1.enrichment_latency_ms / max(context2.enrichment_latency_ms, 0.1)
    print(f"\n🚀 Speedup: {speedup:.1f}x faster with cache!")


async def example_multiple_customers():
    """Enrich context for multiple customers"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Multiple Customers")
    print("=" * 80)

    service = get_context_service()
    customer_ids = ["customer_001", "customer_002", "customer_003"]

    print("\nEnriching context for 3 customers in parallel...")

    # Enrich all in parallel
    tasks = [service.enrich_context(cid) for cid in customer_ids]
    contexts = await asyncio.gather(*tasks)

    # Print comparison
    print("\n📊 CUSTOMER COMPARISON:")
    print(f"{'Customer':<15} {'Plan':<10} {'Health':<8} {'Churn Risk':<12} {'Logins/30d'}")
    print("-" * 65)

    for cid, ctx in zip(customer_ids, contexts, strict=False):
        print(
            f"{cid:<15} "
            f"{ctx.customer_intelligence.plan:<10} "
            f"{ctx.customer_intelligence.health_score:<8} "
            f"{ctx.customer_intelligence.get_churn_risk_level().value:<12} "
            f"{ctx.engagement_metrics.login_count_30d}"
        )


async def example_account_health_flags():
    """Show account health flags"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Account Health Flags")
    print("=" * 80)

    service = get_context_service()

    # Try a few different customers to see different flags
    for i in range(3):
        customer_id = f"customer_health_{i}"
        context = await service.enrich_context(customer_id)

        print(f"\n🏥 {customer_id}:")
        print(f"   Health Score: {context.customer_intelligence.health_score}/100")

        ah = context.account_health

        if ah.red_flags:
            print("   🚨 RED FLAGS:")
            for flag in ah.red_flags:
                print(f"      - {flag}")

        if ah.yellow_flags:
            print("   ⚠️  YELLOW FLAGS:")
            for flag in ah.yellow_flags:
                print(f"      - {flag}")

        if ah.green_flags:
            print("   ✅ GREEN FLAGS (Opportunities):")
            for flag in ah.green_flags:
                print(f"      - {flag}")

        if not (ah.red_flags or ah.yellow_flags or ah.green_flags):
            print("   ℹ️  No flags - account is stable")


async def example_agent_integration():
    """Example of how agents use context"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Agent Integration")
    print("=" * 80)

    from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent

    # Create a simple test agent
    class TestAgent(BaseAgent):
        def __init__(self):
            config = AgentConfig(
                name="test_agent",
                type=AgentType.SPECIALIST,
                capabilities=[AgentCapability.CONTEXT_AWARE],
            )
            super().__init__(config)

        async def process(self, state):
            return state

    agent = TestAgent()
    customer_id = "customer_agent_test"

    print(f"\n🤖 Agent: {agent.config.name}")
    print(f"📋 Capabilities: {[c.value for c in agent.config.capabilities]}")

    # Get enriched context
    print(f"\nGetting enriched context for {customer_id}...")
    context = await agent.get_enriched_context(customer_id)

    if context:
        print("✅ Context retrieved successfully!")
        print("\n📝 Agent would receive this context in prompts:")
        print("-" * 80)
        print(context.to_prompt_context()[:500] + "...")
    else:
        print("❌ Context not available")


async def run_all_examples():
    """Run all examples"""
    await example_basic_enrichment()
    await example_cache_performance()
    await example_multiple_customers()
    await example_account_health_flags()
    await example_agent_integration()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Context Enrichment System - Example Usage            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(run_all_examples())
