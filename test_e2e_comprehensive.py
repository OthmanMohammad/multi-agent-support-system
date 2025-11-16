"""Comprehensive end-to-end integration test suite"""
import asyncio
from src.agents.essential.routing.meta_router import MetaRouter
from src.agents.essential.routing.support_domain_router import SupportDomainRouter
from src.agents.essential.routing.intent_classifier import IntentClassifier
from src.agents.essential.routing.entity_extractor import EntityExtractor
from src.agents.essential.routing.sentiment_analyzer import SentimentAnalyzer
from src.workflow.state import create_initial_state
from src.workflow.patterns.sequential import SequentialWorkflow, SequentialStep
from src.workflow.patterns.parallel import ParallelWorkflow, ParallelAgent

async def agent_executor(agent_name: str, state):
    """Execute agent based on name"""
    agents = {
        "meta_router": MetaRouter(),
        "support_domain_router": SupportDomainRouter(),
        "intent_classifier": IntentClassifier(),
        "entity_extractor": EntityExtractor(),
        "sentiment_analyzer": SentimentAnalyzer(),
    }

    agent = agents.get(agent_name)
    if agent:
        return await agent.process(state)
    return state

async def test_1_basic_routing():
    """Test 1: Basic MetaRouter routing"""
    print("\n" + "=" * 70)
    print("TEST 1: Basic MetaRouter Routing")
    print("=" * 70)

    test_cases = [
        ("I want to upgrade to premium", "sales"),
        ("My app crashes on startup", "support"),
        ("How do I invite teammates?", "support"),
        ("I'm considering canceling", "customer_success"),
    ]

    router = MetaRouter()
    passed = 0

    for msg, expected_domain in test_cases:
        state = create_initial_state(message=msg)
        result = await router.process(state)
        domain = result.get("domain", "").lower()

        if expected_domain in domain:
            print(f"✓ PASS: '{msg}' → {domain}")
            passed += 1
        else:
            print(f"✗ FAIL: '{msg}' → {domain} (expected {expected_domain})")

    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

async def test_2_sequential_workflow():
    """Test 2: Sequential workflow with multiple agents"""
    print("\n" + "=" * 70)
    print("TEST 2: Sequential Workflow (MetaRouter → SupportDomainRouter)")
    print("=" * 70)

    workflow = SequentialWorkflow(
        name="support_routing",
        steps=[
            SequentialStep("meta_router", required=True),
            SequentialStep("support_domain_router", required=True),
        ]
    )

    state = create_initial_state(
        message="I need help with billing for my subscription",
        conversation_id="test-seq-001"
    )

    result = await workflow.execute(state, agent_executor)

    print(f"Success: {result.success}")
    print(f"Steps executed: {' → '.join(result.steps_executed)}")
    print(f"Final domain: {result.final_state.get('domain')}")
    print(f"Final category: {result.final_state.get('support_category')}")

    return result.success and len(result.steps_executed) == 2

async def test_3_parallel_analysis():
    """Test 3: Parallel workflow with multiple analyzers"""
    print("\n" + "=" * 70)
    print("TEST 3: Parallel Analysis (Intent + Entity + Sentiment)")
    print("=" * 70)

    workflow = ParallelWorkflow(
        name="parallel_analysis",
        agents=[
            ParallelAgent("intent_classifier", weight=1.0),
            ParallelAgent("entity_extractor", weight=1.0),
            ParallelAgent("sentiment_analyzer", weight=1.0),
        ]
    )

    state = create_initial_state(
        message="URGENT: My payment failed and I can't access my account!",
        conversation_id="test-par-001"
    )

    result = await workflow.execute(state, agent_executor)

    print(f"Success: {result.success}")
    print(f"Agents completed: {', '.join(result.agents_completed)}")
    print(f"Intent: {result.aggregated_state.get('intent_category')}")
    print(f"Emotion: {result.aggregated_state.get('emotion')}")
    print(f"Entities: {result.aggregated_state.get('extracted_entities')}")

    return result.success and len(result.agents_completed) == 3

async def test_4_full_pipeline():
    """Test 4: Full pipeline with all routing stages"""
    print("\n" + "=" * 70)
    print("TEST 4: Full Routing Pipeline")
    print("=" * 70)

    # Stage 1: Parallel analysis
    analysis_workflow = ParallelWorkflow(
        name="analysis",
        agents=[
            ParallelAgent("intent_classifier", weight=1.0),
            ParallelAgent("entity_extractor", weight=1.0),
            ParallelAgent("sentiment_analyzer", weight=1.0),
        ]
    )

    state = create_initial_state(
        message="I've been trying to sync my data for hours and it keeps failing!",
        conversation_id="test-full-001"
    )

    # Run analysis
    analysis_result = await analysis_workflow.execute(state, agent_executor)

    if not analysis_result.success:
        print("✗ Analysis stage failed")
        return False

    # Stage 2: Sequential routing
    routing_workflow = SequentialWorkflow(
        name="routing",
        steps=[
            SequentialStep("meta_router", required=True),
            SequentialStep("support_domain_router", required=True),
        ]
    )

    routing_result = await routing_workflow.execute(
        analysis_result.aggregated_state,
        agent_executor
    )

    print(f"\nPipeline Results:")
    print(f"  Analysis: {len(analysis_result.agents_completed)} agents")
    print(f"  Routing: {' → '.join(routing_result.steps_executed)}")
    print(f"  Final domain: {routing_result.final_state.get('domain')}")
    print(f"  Final category: {routing_result.final_state.get('support_category')}")
    print(f"  Detected intent: {routing_result.final_state.get('intent_category')}")
    print(f"  Detected emotion: {routing_result.final_state.get('emotion')}")

    return routing_result.success

async def test_5_error_handling():
    """Test 5: Error handling and fallbacks"""
    print("\n" + "=" * 70)
    print("TEST 5: Error Handling & Fallbacks")
    print("=" * 70)

    workflow = SequentialWorkflow(
        name="error_test",
        steps=[
            SequentialStep("meta_router", required=True),
            SequentialStep("nonexistent_agent", required=False),  # Should skip
        ]
    )

    state = create_initial_state(message="Test message")

    result = await workflow.execute(state, agent_executor)

    print(f"Success: {result.success}")
    print(f"Steps executed: {result.steps_executed}")
    print(f"Note: Non-existent optional step should be skipped gracefully")

    return result.success and len(result.steps_executed) >= 1

async def run_all_tests():
    """Run all end-to-end tests"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 70)

    tests = [
        ("Basic Routing", test_1_basic_routing),
        ("Sequential Workflow", test_2_sequential_workflow),
        ("Parallel Analysis", test_3_parallel_analysis),
        ("Full Pipeline", test_4_full_pipeline),
        ("Error Handling", test_5_error_handling),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_count - passed_count} tests failed")

    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_all_tests())