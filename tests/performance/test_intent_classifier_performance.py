"""
Performance tests for Intent Classifier.

Tests latency, throughput, and resource usage for hierarchical classification.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-102)
"""

import pytest
import time
import asyncio
import os
from unittest.mock import AsyncMock
import json
from statistics import mean, median

from src.agents.essential.routing.intent_classifier import IntentClassifier
from src.workflow.state import create_initial_state


@pytest.mark.performance
class TestIntentClassifierPerformance:
    """Performance benchmarks for Intent Classifier."""

    @pytest.fixture
    def classifier(self):
        """Create IntentClassifier for performance testing."""
        return IntentClassifier()

    @pytest.fixture
    def mock_fast_llm(self):
        """Mock LLM with realistic latency (~60ms for more complex task)."""
        async def mock_llm(*args, **kwargs):
            await asyncio.sleep(0.06)  # Simulate 60ms LLM call
            return json.dumps({
                "domain": "support",
                "category": "billing",
                "subcategory": "subscription",
                "action": "upgrade",
                "confidence_scores": {
                    "domain": 0.98,
                    "category": 0.95,
                    "subcategory": 0.92,
                    "action": 0.90
                },
                "entities": {"plan_name": "premium"},
                "reasoning": "Test classification"
            })
        return mock_llm

    @pytest.mark.asyncio
    async def test_single_classification_latency(self, classifier, mock_fast_llm):
        """Test latency for single classification."""
        classifier.call_llm = mock_fast_llm

        state = create_initial_state(
            message="I want to upgrade to Premium",
            context={"customer_metadata": {"plan": "basic"}}
        )

        start = time.time()
        result = await classifier.process(state)
        latency_ms = (time.time() - start) * 1000

        print(f"\n✓ Single Classification Latency: {latency_ms:.1f}ms")
        print(f"  Reported latency: {result['intent_metadata']['latency_ms']}ms")

        # With mocked LLM (~60ms), total should be <150ms
        assert latency_ms < 150, f"Single classification too slow: {latency_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_average_latency_over_multiple_calls(self, classifier, mock_fast_llm):
        """Test average latency over 20 calls."""
        classifier.call_llm = mock_fast_llm

        latencies = []
        num_calls = 20

        for i in range(num_calls):
            state = create_initial_state(
                message=f"Test message {i}",
                context={"customer_metadata": {"plan": "basic"}}
            )

            start = time.time()
            await classifier.process(state)
            latency_ms = (time.time() - start) * 1000

            latencies.append(latency_ms)

        avg_latency = mean(latencies)
        median_latency = median(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"\n✓ Latency Statistics (n={num_calls}):")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  Median:  {median_latency:.1f}ms")
        print(f"  Min:     {min_latency:.1f}ms")
        print(f"  Max:     {max_latency:.1f}ms")

        # Average should be <150ms with mocked LLM
        assert avg_latency < 150, f"Average latency too high: {avg_latency:.1f}ms"

    @pytest.mark.asyncio
    async def test_p95_latency(self, classifier, mock_fast_llm):
        """Test p95 latency (95th percentile)."""
        classifier.call_llm = mock_fast_llm

        latencies = []
        num_calls = 20

        for i in range(num_calls):
            state = create_initial_state(
                message=f"Test message {i}",
                context={}
            )

            start = time.time()
            await classifier.process(state)
            latency_ms = (time.time() - start) * 1000

            latencies.append(latency_ms)

        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        print(f"\n✓ P95 Latency: {p95_latency:.1f}ms")

        # P95 should be <200ms
        assert p95_latency < 200, f"P95 latency too high: {p95_latency:.1f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_classifications(self, classifier, mock_fast_llm):
        """Test handling multiple concurrent classifications."""
        classifier.call_llm = mock_fast_llm

        num_concurrent = 5

        async def classify():
            state = create_initial_state(
                message="Concurrent test message",
                context={}
            )
            return await classifier.process(state)

        start = time.time()
        results = await asyncio.gather(*[classify() for _ in range(num_concurrent)])
        total_time_ms = (time.time() - start) * 1000

        print(f"\n✓ Concurrent Classifications:")
        print(f"  Count: {num_concurrent}")
        print(f"  Total time: {total_time_ms:.1f}ms")
        print(f"  Per classification: {total_time_ms/num_concurrent:.1f}ms")

        # All should succeed
        assert len(results) == num_concurrent
        for result in results:
            assert "intent_domain" in result
            assert "intent_category" in result

    @pytest.mark.asyncio
    async def test_context_formatting_overhead(self, classifier):
        """Test overhead of context formatting."""
        # Minimal context
        minimal_context = {"plan": "free"}

        # Rich context
        rich_context = {
            "plan": "enterprise",
            "health_score": 75,
            "team_size": 100,
            "mrr": 5000,
            "churn_risk": 0.3,
            "account_age_days": 365
        }

        # Test formatting times
        start = time.time()
        for _ in range(1000):
            classifier._format_customer_context(minimal_context)
        minimal_time = (time.time() - start) * 1000

        start = time.time()
        for _ in range(1000):
            classifier._format_customer_context(rich_context)
        rich_time = (time.time() - start) * 1000

        print(f"\n✓ Context Formatting (1000 iterations):")
        print(f"  Minimal context: {minimal_time:.1f}ms ({minimal_time/1000:.3f}ms each)")
        print(f"  Rich context:    {rich_time:.1f}ms ({rich_time/1000:.3f}ms each)")

        # Should be negligible (<10ms per 1000 iterations)
        assert minimal_time < 10
        assert rich_time < 10

    @pytest.mark.asyncio
    async def test_json_parsing_overhead(self, classifier):
        """Test overhead of JSON response parsing."""
        valid_json = json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "subscription",
            "action": "upgrade",
            "confidence_scores": {
                "domain": 0.98,
                "category": 0.95,
                "subcategory": 0.92,
                "action": 0.90
            },
            "entities": {"plan_name": "premium"},
            "alternative_intents": [],
            "reasoning": "Test"
        })

        # Test parsing times
        start = time.time()
        for _ in range(1000):
            classifier._parse_response(valid_json)
        parsing_time = (time.time() - start) * 1000

        print(f"\n✓ JSON Parsing (1000 iterations): {parsing_time:.1f}ms")
        print(f"  Per parse: {parsing_time/1000:.3f}ms")

        # Should be very fast (<30ms per 1000 iterations)
        assert parsing_time < 30

    @pytest.mark.asyncio
    async def test_error_handling_overhead(self, classifier):
        """Test overhead of error handling."""
        state = create_initial_state(
            message="Test message",
            context={}
        )

        # Mock LLM to always fail
        classifier.call_llm = AsyncMock(side_effect=Exception("API Error"))

        start = time.time()
        result = await classifier.process(state)
        error_handling_time = (time.time() - start) * 1000

        print(f"\n✓ Error Handling Time: {error_handling_time:.1f}ms")

        # Error handling should be fast (<50ms)
        assert error_handling_time < 50

        # Should still return valid result
        assert result["intent_domain"] == "support"

    @pytest.mark.asyncio
    async def test_throughput(self, classifier, mock_fast_llm):
        """Test throughput (classifications per second)."""
        classifier.call_llm = mock_fast_llm

        num_classifications = 30
        states = [
            create_initial_state(
                message=f"Test message {i}",
                context={}
            )
            for i in range(num_classifications)
        ]

        start = time.time()
        for state in states:
            await classifier.process(state)
        elapsed = time.time() - start

        throughput = num_classifications / elapsed

        print(f"\n✓ Throughput Test:")
        print(f"  Classifications: {num_classifications}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} classifications/sec")

        # Should achieve >8 classifications/sec with mocked LLM
        assert throughput > 8

    @pytest.mark.asyncio
    async def test_memory_efficient_state_updates(self, classifier, mock_fast_llm):
        """Test that state updates don't cause memory bloat."""
        classifier.call_llm = mock_fast_llm

        state = create_initial_state(
            message="Test message",
            context={}
        )

        # Process multiple times
        for i in range(50):
            state = await classifier.process(state)

        # Agent history shouldn't have duplicates
        assert state["agent_history"].count("intent_classifier") == 1

        # Turn count should be reasonable
        assert state["turn_count"] == 50

        print(f"\n✓ State Management:")
        print(f"  Turn count: {state['turn_count']}")
        print(f"  Agent history length: {len(state['agent_history'])}")

    @pytest.mark.asyncio
    async def test_hierarchical_depth_overhead(self, classifier, mock_fast_llm):
        """Test overhead of 4-level vs 2-level classification."""
        # 2-level classification
        mock_2_level = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {"domain": 0.98, "category": 0.95}
        }))

        # 4-level classification
        mock_4_level = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "subscription",
            "action": "upgrade",
            "confidence_scores": {
                "domain": 0.98,
                "category": 0.95,
                "subcategory": 0.92,
                "action": 0.90
            }
        }))

        state = create_initial_state(message="Test", context={})

        # Test 2-level
        classifier.call_llm = mock_2_level
        start = time.time()
        for _ in range(10):
            await classifier.process(state)
        time_2_level = (time.time() - start) * 1000

        # Test 4-level
        classifier.call_llm = mock_4_level
        start = time.time()
        for _ in range(10):
            await classifier.process(state)
        time_4_level = (time.time() - start) * 1000

        print(f"\n✓ Hierarchical Depth Overhead (10 iterations):")
        print(f"  2-level: {time_2_level:.1f}ms")
        print(f"  4-level: {time_4_level:.1f}ms")
        print(f"  Overhead: {time_4_level - time_2_level:.1f}ms")

        # Overhead should be minimal (<100ms for 10 iterations)
        overhead = time_4_level - time_2_level
        assert overhead < 100


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestIntentClassifierRealPerformance:
    """Performance tests with real LLM calls (requires API key)."""

    @pytest.fixture
    def classifier(self):
        """Create IntentClassifier with real Anthropic client."""
        return IntentClassifier()

    @pytest.mark.asyncio
    async def test_real_llm_latency(self, classifier):
        """Test real LLM latency (should be under 3s)."""
        state = create_initial_state(
            message="I want to upgrade to Premium for 50 users",
            context={"customer_metadata": {"plan": "basic", "team_size": 20}}
        )

        start = time.time()
        result = await classifier.process(state)
        latency_ms = (time.time() - start) * 1000

        print(f"\n✓ Real LLM Latency: {latency_ms:.1f}ms")
        print(f"  Model: {classifier.config.model}")
        print(f"  Domain: {result['intent_domain']}")
        print(f"  Category: {result['intent_category']}")
        print(f"  Confidence: {result['intent_confidence_scores']['overall']:.2%}")

        # Real LLM should be fast with Haiku (<3s)
        assert latency_ms < 3000, f"Real LLM too slow: {latency_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_real_llm_batch_performance(self, classifier):
        """Test performance on a batch of real classifications."""
        messages = [
            "Cancel my subscription",
            "The app is crashing",
            "What's the pricing?",
            "We need help with onboarding",
            "How do I export data?"
        ]

        latencies = []

        for msg in messages:
            state = create_initial_state(message=msg, context={})

            start = time.time()
            result = await classifier.process(state)
            latency_ms = (time.time() - start) * 1000

            latencies.append(latency_ms)

            print(f"✓ '{msg[:30]}...' → {result['intent_domain']}/{result['intent_category']} ({latency_ms:.0f}ms)")

        avg_latency = mean(latencies)
        print(f"\n✓ Average Latency: {avg_latency:.1f}ms")

        # Average should be reasonable (<3s)
        assert avg_latency < 3000
