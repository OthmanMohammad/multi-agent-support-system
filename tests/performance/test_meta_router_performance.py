"""
Performance tests for Meta Router Agent.

Tests latency, throughput, and resource usage under various conditions.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-101)
"""

import pytest
import time
import asyncio
from unittest.mock import AsyncMock
import json
from statistics import mean, median

from src.agents.essential.routing.meta_router import MetaRouter
from src.workflow.state import create_initial_state


@pytest.mark.performance
class TestMetaRouterPerformance:
    """Performance benchmarks for Meta Router."""

    @pytest.fixture
    def router(self):
        """Create MetaRouter for performance testing."""
        return MetaRouter()

    @pytest.fixture
    def mock_fast_llm(self):
        """Mock LLM with realistic latency (~50ms)."""
        async def mock_llm(*args, **kwargs):
            await asyncio.sleep(0.05)  # Simulate 50ms LLM call
            return json.dumps({
                "domain": "support",
                "confidence": 0.90,
                "reasoning": "Test classification"
            })
        return mock_llm

    @pytest.mark.asyncio
    async def test_single_classification_latency(self, router, mock_fast_llm):
        """Test latency for single classification."""
        router.call_llm = mock_fast_llm

        state = create_initial_state(
            message="Test message",
            context={"customer_metadata": {"plan": "premium"}}
        )

        start = time.time()
        result = await router.process(state)
        latency_ms = (time.time() - start) * 1000

        print(f"\n✓ Single Classification Latency: {latency_ms:.1f}ms")
        print(f"  Reported latency: {result['routing_metadata']['latency_ms']}ms")

        # With mocked LLM (~50ms), total should be <100ms
        assert latency_ms < 100, f"Single classification too slow: {latency_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_average_latency_over_multiple_calls(self, router, mock_fast_llm):
        """Test average latency over 10 calls."""
        router.call_llm = mock_fast_llm

        latencies = []
        num_calls = 10

        for i in range(num_calls):
            state = create_initial_state(
                message=f"Test message {i}",
                context={"customer_metadata": {"plan": "premium"}}
            )

            start = time.time()
            await router.process(state)
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

        # Average should be <100ms with mocked LLM
        assert avg_latency < 100, f"Average latency too high: {avg_latency:.1f}ms"

    @pytest.mark.asyncio
    async def test_p95_latency(self, router, mock_fast_llm):
        """Test p95 latency (95th percentile)."""
        router.call_llm = mock_fast_llm

        latencies = []
        num_calls = 20

        for i in range(num_calls):
            state = create_initial_state(
                message=f"Test message {i}",
                context={"customer_metadata": {"plan": "premium"}}
            )

            start = time.time()
            await router.process(state)
            latency_ms = (time.time() - start) * 1000

            latencies.append(latency_ms)

        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        print(f"\n✓ P95 Latency: {p95_latency:.1f}ms")

        # P95 should be <150ms
        assert p95_latency < 150, f"P95 latency too high: {p95_latency:.1f}ms"

    @pytest.mark.asyncio
    async def test_concurrent_classifications(self, router, mock_fast_llm):
        """Test handling multiple concurrent classifications."""
        router.call_llm = mock_fast_llm

        num_concurrent = 5

        async def classify():
            state = create_initial_state(
                message="Concurrent test message",
                context={"customer_metadata": {"plan": "premium"}}
            )
            return await router.process(state)

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
            assert "domain" in result
            assert "domain_confidence" in result

    @pytest.mark.asyncio
    async def test_latency_with_different_message_lengths(self, router, mock_fast_llm):
        """Test latency variance with different message lengths."""
        router.call_llm = mock_fast_llm

        test_messages = [
            "Short",
            "This is a medium length message with some detail about the issue",
            "This is a very long message " * 20  # ~600 chars
        ]

        for msg in test_messages:
            state = create_initial_state(
                message=msg,
                context={"customer_metadata": {"plan": "premium"}}
            )

            start = time.time()
            result = await router.process(state)
            latency_ms = (time.time() - start) * 1000

            print(f"\n✓ Message length: {len(msg)} chars, Latency: {latency_ms:.1f}ms")

            # All should be fast regardless of length (with mocked LLM)
            assert latency_ms < 150

    @pytest.mark.asyncio
    async def test_context_formatting_overhead(self, router):
        """Test overhead of context formatting."""
        # Minimal context
        minimal_context = {"plan": "free"}

        # Rich context
        rich_context = {
            "plan": "enterprise",
            "health_score": 75,
            "mrr": 5000,
            "churn_risk": 0.3,
            "account_age_days": 365,
            "last_login": "2025-01-14"
        }

        # Test formatting times
        start = time.time()
        for _ in range(1000):
            router._format_customer_context(minimal_context)
        minimal_time = (time.time() - start) * 1000

        start = time.time()
        for _ in range(1000):
            router._format_customer_context(rich_context)
        rich_time = (time.time() - start) * 1000

        print(f"\n✓ Context Formatting (1000 iterations):")
        print(f"  Minimal context: {minimal_time:.1f}ms ({minimal_time/1000:.3f}ms each)")
        print(f"  Rich context:    {rich_time:.1f}ms ({rich_time/1000:.3f}ms each)")

        # Should be negligible (<10ms per 1000 iterations)
        assert minimal_time < 10
        assert rich_time < 10

    @pytest.mark.asyncio
    async def test_json_parsing_overhead(self, router):
        """Test overhead of JSON response parsing."""
        valid_json = json.dumps({
            "domain": "support",
            "confidence": 0.92,
            "reasoning": "Customer has technical issue"
        })

        # Test parsing times
        start = time.time()
        for _ in range(1000):
            router._parse_response(valid_json)
        parsing_time = (time.time() - start) * 1000

        print(f"\n✓ JSON Parsing (1000 iterations): {parsing_time:.1f}ms")
        print(f"  Per parse: {parsing_time/1000:.3f}ms")

        # Should be very fast (<20ms per 1000 iterations)
        assert parsing_time < 20

    @pytest.mark.asyncio
    async def test_error_handling_overhead(self, router):
        """Test overhead of error handling."""
        state = create_initial_state(
            message="Test message",
            context={"customer_metadata": {"plan": "premium"}}
        )

        # Mock LLM to always fail
        router.call_llm = AsyncMock(side_effect=Exception("API Error"))

        start = time.time()
        result = await router.process(state)
        error_handling_time = (time.time() - start) * 1000

        print(f"\n✓ Error Handling Time: {error_handling_time:.1f}ms")

        # Error handling should be fast (<50ms)
        assert error_handling_time < 50

        # Should still return valid result
        assert result["domain"] == "support"
        assert "error" in result["routing_metadata"]

    @pytest.mark.asyncio
    async def test_throughput(self, router, mock_fast_llm):
        """Test throughput (classifications per second)."""
        router.call_llm = mock_fast_llm

        num_classifications = 50
        states = [
            create_initial_state(
                message=f"Test message {i}",
                context={"customer_metadata": {"plan": "premium"}}
            )
            for i in range(num_classifications)
        ]

        start = time.time()
        for state in states:
            await router.process(state)
        elapsed = time.time() - start

        throughput = num_classifications / elapsed

        print(f"\n✓ Throughput Test:")
        print(f"  Classifications: {num_classifications}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.1f} classifications/sec")

        # Should achieve >10 classifications/sec with mocked LLM
        assert throughput > 10

    @pytest.mark.asyncio
    async def test_memory_efficient_state_updates(self, router, mock_fast_llm):
        """Test that state updates don't cause memory bloat."""
        router.call_llm = mock_fast_llm

        state = create_initial_state(
            message="Test message",
            context={"customer_metadata": {"plan": "premium"}}
        )

        # Process multiple times
        for i in range(100):
            state = await router.process(state)

        # Agent history shouldn't have duplicates
        assert state["agent_history"].count("meta_router") == 1

        # Turn count should be reasonable
        assert state["turn_count"] == 100

        print(f"\n✓ State Management:")
        print(f"  Turn count: {state['turn_count']}")
        print(f"  Agent history length: {len(state['agent_history'])}")
        print(f"  Agent history: {state['agent_history']}")


@pytest.mark.performance
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestMetaRouterRealPerformance:
    """Performance tests with real LLM calls (requires API key)."""

    @pytest.fixture
    def router(self):
        """Create MetaRouter with real Anthropic client."""
        return MetaRouter()

    @pytest.mark.asyncio
    async def test_real_llm_latency(self, router):
        """Test real LLM latency (should be under 3s)."""
        state = create_initial_state(
            message="My application is running very slowly",
            context={"customer_metadata": {"plan": "premium"}}
        )

        start = time.time()
        result = await router.process(state)
        latency_ms = (time.time() - start) * 1000

        print(f"\n✓ Real LLM Latency: {latency_ms:.1f}ms")
        print(f"  Model: {router.config.model}")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")

        # Real LLM should be fast with Haiku (<3s)
        assert latency_ms < 3000, f"Real LLM too slow: {latency_ms:.1f}ms"


# Fix missing import
import os
