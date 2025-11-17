#!/usr/bin/env python3
"""
Verification script to check AgentRegistry status.

Checks:
1. How many agents are registered
2. Breakdown by tier
3. Breakdown by category
4. Lists all registered agents
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("AGENT REGISTRY VERIFICATION")
print("=" * 70)
print()

print("Loading agents...")
try:
    # Import agents package (triggers auto-load)
    import src.agents

    from src.services.infrastructure.agent_registry import AgentRegistry

    print("✅ Agents loaded successfully")
    print()

    # Get all agents
    all_agents = AgentRegistry.list_agents()
    total = len(all_agents)

    print(f"📊 TOTAL REGISTERED AGENTS: {total}")
    print()

    # By tier
    print("📋 AGENTS BY TIER:")
    by_tier = AgentRegistry.get_tier_summary()
    for tier, count in sorted(by_tier.items()):
        print(f"  - {tier:15s}: {count:3d} agents")
    print()

    # By category
    print("📋 AGENTS BY CATEGORY:")
    by_category = AgentRegistry.get_category_summary()
    for category, count in sorted(by_category.items()):
        if category:  # Skip None/unknown
            print(f"  - {category:20s}: {count:3d} agents")
    print()

    # List all agents
    print("📝 ALL REGISTERED AGENTS:")
    print("-" * 70)

    # Group by tier
    for tier in ["essential", "revenue", "operational", "advanced", "unknown"]:
        tier_agents = [a for a in all_agents if a.get("tier") == tier]
        if tier_agents:
            print(f"\n{tier.upper()} ({len(tier_agents)} agents):")
            for agent in sorted(tier_agents, key=lambda x: x.get("name", "")):
                name = agent.get("name", "unknown")
                category = agent.get("category", "N/A")
                print(f"  ✓ {name:40s} [{category}]")

    print()
    print("=" * 70)

    # Check if we have expected number
    EXPECTED_MIN = 50  # We should have at least 50 agents
    if total >= EXPECTED_MIN:
        print(f"✅ SUCCESS: {total} agents registered (>= {EXPECTED_MIN} expected)")
    else:
        print(f"⚠️  WARNING: Only {total} agents registered (expected >= {EXPECTED_MIN})")
        print(f"   Some agents may not be imported in loader.py")

    print("=" * 70)

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)