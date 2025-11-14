"""
Unit tests for Meta Router Agent.

Tests domain classification, routing logic, error handling,
and edge cases for the Meta Router.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-101)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from src.agents.essential.routing.meta_router import MetaRouter, create_meta_router
from src.workflow.state import AgentState, create_initial_state


@pytest.fixture
def meta_router():
    """Create MetaRouter instance for testing."""
    return MetaRouter()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        customer_id="test_customer_123"
    )


class TestMetaRouterInitialization:
    """Test Meta Router initialization and configuration."""

    def test_meta_router_initialization(self, meta_router):
        """Test that Meta Router initializes with correct configuration."""
        assert meta_router.config.name == "meta_router"
        assert meta_router.config.type.value == "router"
        assert meta_router.config.model == "claude-3-haiku-20240307"
        assert meta_router.config.temperature == 0.1
        assert meta_router.config.max_tokens == 200
        assert meta_router.config.tier == "essential"

    def test_meta_router_has_required_capabilities(self, meta_router):
        """Test that Meta Router has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = meta_router.config.capabilities
        assert AgentCapability.ROUTING in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities

    def test_create_meta_router_helper(self):
        """Test helper function creates valid instance."""
        router = create_meta_router()
        assert isinstance(router, MetaRouter)
        assert router.config.name == "meta_router"


class TestDomainClassification:
    """Test domain classification logic."""

    @pytest.mark.asyncio
    async def test_classifies_support_technical_issue(self, meta_router):
        """Test: Technical issue → support domain"""
        state = create_initial_state(
            message="My app is crashing when I try to export data",
            context={"customer_metadata": {"plan": "premium"}}
        )

        # Mock LLM response
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.95,
            "reasoning": "Customer reporting technical crash issue",
            "next_agent": "support_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "support"
        assert result["domain_confidence"] > 0.9
        assert result["next_agent"] == "support_domain_router"
        assert "meta_router" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_classifies_support_billing_issue(self, meta_router):
        """Test: Billing issue → support domain"""
        state = create_initial_state(
            message="I was charged twice this month",
            context={"customer_metadata": {"plan": "basic", "mrr": 10}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.92,
            "reasoning": "Customer has billing issue with duplicate charges",
            "next_agent": "support_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "support"
        assert result["domain_confidence"] > 0.85
        assert result["next_agent"] == "support_domain_router"

    @pytest.mark.asyncio
    async def test_classifies_sales_pricing_inquiry(self, meta_router):
        """Test: Pricing inquiry → sales domain"""
        state = create_initial_state(
            message="How much does Premium cost for 50 users?",
            context={"customer_metadata": {"plan": "free"}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "confidence": 0.90,
            "reasoning": "Free user asking about premium pricing",
            "next_agent": "sales_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "sales"
        assert result["domain_confidence"] > 0.85
        assert result["next_agent"] == "sales_domain_router"

    @pytest.mark.asyncio
    async def test_classifies_sales_demo_request(self, meta_router):
        """Test: Demo request → sales domain"""
        state = create_initial_state(
            message="I'd like to schedule a demo of your product",
            context={"customer_metadata": {"plan": "free"}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "confidence": 0.93,
            "reasoning": "Prospect requesting product demo",
            "next_agent": "sales_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "sales"
        assert result["domain_confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_classifies_customer_success_value_concern(self, meta_router):
        """Test: Value concern → customer_success domain"""
        state = create_initial_state(
            message="We're not getting the value we expected from the product",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "health_score": 35,
                    "churn_risk": 0.8
                }
            }
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "confidence": 0.88,
            "reasoning": "Paying customer expressing value concerns, high churn risk",
            "next_agent": "cs_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "customer_success"
        assert result["domain_confidence"] > 0.8
        assert result["next_agent"] == "cs_domain_router"

    @pytest.mark.asyncio
    async def test_classifies_customer_success_low_engagement(self, meta_router):
        """Test: Low engagement → customer_success domain"""
        state = create_initial_state(
            message="Our team isn't really using the product",
            context={"customer_metadata": {"plan": "basic", "health_score": 40}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "confidence": 0.85,
            "reasoning": "Low engagement from paying customer",
            "next_agent": "cs_domain_router"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "customer_success"
        assert result["domain_confidence"] > 0.8


class TestContextHandling:
    """Test customer context handling and formatting."""

    def test_format_customer_context_with_all_fields(self, meta_router):
        """Test formatting context with all fields present."""
        context = {
            "plan": "premium",
            "health_score": 75,
            "mrr": 500,
            "churn_risk": 0.3,
            "account_age_days": 365,
            "last_login": "2025-01-14"
        }

        formatted = meta_router._format_customer_context(context)

        assert "Plan: premium" in formatted
        assert "Health Score: 75/100" in formatted
        assert "MRR: $500" in formatted
        assert "Churn Risk: low (0.30)" in formatted
        assert "Account Age: 365 days" in formatted
        assert "Last Login: 2025-01-14" in formatted

    def test_format_customer_context_with_partial_fields(self, meta_router):
        """Test formatting context with only some fields."""
        context = {
            "plan": "basic",
            "health_score": 50
        }

        formatted = meta_router._format_customer_context(context)

        assert "Plan: basic" in formatted
        assert "Health Score: 50/100" in formatted
        assert "MRR" not in formatted

    def test_format_customer_context_empty(self, meta_router):
        """Test formatting empty context."""
        formatted = meta_router._format_customer_context({})
        assert formatted == "No customer context available"

    def test_format_customer_context_churn_risk_labels(self, meta_router):
        """Test churn risk label formatting."""
        # High risk
        context_high = {"churn_risk": 0.8}
        formatted_high = meta_router._format_customer_context(context_high)
        assert "high" in formatted_high.lower()

        # Medium risk
        context_medium = {"churn_risk": 0.5}
        formatted_medium = meta_router._format_customer_context(context_medium)
        assert "medium" in formatted_medium.lower()

        # Low risk
        context_low = {"churn_risk": 0.2}
        formatted_low = meta_router._format_customer_context(context_low)
        assert "low" in formatted_low.lower()

    @pytest.mark.asyncio
    async def test_uses_customer_context_in_classification(self, meta_router):
        """Test that customer context influences routing."""
        # High churn risk customer asking about features
        state = create_initial_state(
            message="What features do you have?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "churn_risk": 0.8,
                    "health_score": 35
                }
            }
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "confidence": 0.85,
            "reasoning": "High churn risk customer needs CS attention"
        }))

        result = await meta_router.process(state)

        # Verify call_llm was called with context
        call_args = meta_router.call_llm.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Churn Risk: high" in system_prompt or "0.80" in system_prompt


class TestResponseParsing:
    """Test LLM response parsing and validation."""

    def test_parse_valid_json_response(self, meta_router):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "domain": "support",
            "confidence": 0.92,
            "reasoning": "Customer has technical issue",
            "next_agent": "support_domain_router"
        })

        parsed = meta_router._parse_response(response)

        assert parsed["domain"] == "support"
        assert parsed["confidence"] == 0.92
        assert parsed["reasoning"] == "Customer has technical issue"
        assert parsed["next_agent"] == "support_domain_router"

    def test_parse_json_without_next_agent(self, meta_router):
        """Test parsing JSON without next_agent field (auto-generated)."""
        response = json.dumps({
            "domain": "sales",
            "confidence": 0.88,
            "reasoning": "Pricing inquiry"
        })

        parsed = meta_router._parse_response(response)

        assert parsed["domain"] == "sales"
        assert parsed["next_agent"] == "sales_domain_router"

    def test_parse_json_with_markdown_code_blocks(self, meta_router):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = """```json
{
    "domain": "customer_success",
    "confidence": 0.85,
    "reasoning": "Value concern"
}
```"""

        parsed = meta_router._parse_response(response)

        assert parsed["domain"] == "customer_success"
        assert parsed["confidence"] == 0.85

    def test_parse_invalid_domain_defaults_to_support(self, meta_router):
        """Test that invalid domain defaults to support."""
        response = json.dumps({
            "domain": "invalid_domain",
            "confidence": 0.9,
            "reasoning": "Test"
        })

        parsed = meta_router._parse_response(response)

        assert parsed["domain"] == "support"  # Defaulted

    def test_parse_confidence_out_of_range_clamped(self, meta_router):
        """Test that confidence is clamped to 0-1 range."""
        # Test > 1
        response_high = json.dumps({
            "domain": "support",
            "confidence": 1.5,
            "reasoning": "Test"
        })
        parsed_high = meta_router._parse_response(response_high)
        assert parsed_high["confidence"] == 1.0

        # Test < 0
        response_low = json.dumps({
            "domain": "support",
            "confidence": -0.5,
            "reasoning": "Test"
        })
        parsed_low = meta_router._parse_response(response_low)
        assert parsed_low["confidence"] == 0.0

    def test_parse_invalid_json_falls_back_to_text_extraction(self, meta_router):
        """Test fallback to text extraction when JSON is invalid."""
        response = "This is not valid JSON but mentions support domain"

        parsed = meta_router._parse_response(response)

        # Should extract "support" from text
        assert parsed["domain"] == "support"
        assert parsed["confidence"] < 0.7  # Lower confidence for fallback

    def test_extract_domain_from_text_support(self, meta_router):
        """Test extracting support domain from text."""
        response = "The customer needs support for their technical issue"
        extracted = meta_router._extract_domain_from_text(response)

        assert extracted["domain"] == "support"
        assert extracted["confidence"] == 0.6
        assert "fallback" in extracted["reasoning"].lower()

    def test_extract_domain_from_text_sales(self, meta_router):
        """Test extracting sales domain from text."""
        response = "This is clearly a sales inquiry"
        extracted = meta_router._extract_domain_from_text(response)

        assert extracted["domain"] == "sales"

    def test_extract_domain_from_text_customer_success(self, meta_router):
        """Test extracting customer_success domain from text."""
        response = "Route to customer_success team"
        extracted = meta_router._extract_domain_from_text(response)

        assert extracted["domain"] == "customer_success"

    def test_extract_domain_from_text_defaults_to_support(self, meta_router):
        """Test that text extraction defaults to support if no domain found."""
        response = "Random text with no domain keywords"
        extracted = meta_router._extract_domain_from_text(response)

        assert extracted["domain"] == "support"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_message(self, meta_router):
        """Test handling of empty message."""
        state = create_initial_state(
            message="",
            customer_id="test_customer"
        )

        result = await meta_router.process(state)

        # Should default to support
        assert result["domain"] == "support"
        assert result["domain_confidence"] == 0.5
        assert "empty" in result["domain_reasoning"].lower()
        assert result["routing_metadata"]["error"] == "empty_message"

    @pytest.mark.asyncio
    async def test_handles_llm_error(self, meta_router):
        """Test handling of LLM errors."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock LLM to raise exception
        meta_router.call_llm = AsyncMock(side_effect=Exception("API Error"))

        result = await meta_router.process(state)

        # Should fallback to support
        assert result["domain"] == "support"
        assert result["domain_confidence"] == 0.5
        assert "error" in result["domain_reasoning"].lower()
        assert "error" in result["routing_metadata"]

    @pytest.mark.asyncio
    async def test_handles_missing_required_fields_in_response(self, meta_router):
        """Test handling of response missing required fields."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock response missing required fields
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support"
            # Missing confidence and reasoning
        }))

        result = await meta_router.process(state)

        # Should use fallback extraction
        assert result["domain"] == "support"
        assert "domain_confidence" in result


class TestStateManagement:
    """Test state management and updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, meta_router):
        """Test that agent history is updated correctly."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock LLM
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.9,
            "reasoning": "Test"
        }))

        result = await meta_router.process(state)

        assert "meta_router" in result["agent_history"]
        assert result["current_agent"] == "meta_router"

    @pytest.mark.asyncio
    async def test_increments_turn_count(self, meta_router):
        """Test that turn count is incremented."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )
        initial_turn_count = state.get("turn_count", 0)

        # Mock LLM
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.9,
            "reasoning": "Test"
        }))

        result = await meta_router.process(state)

        assert result["turn_count"] == initial_turn_count + 1

    @pytest.mark.asyncio
    async def test_adds_routing_metadata(self, meta_router):
        """Test that routing metadata is added to state."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock LLM
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.9,
            "reasoning": "Test"
        }))

        result = await meta_router.process(state)

        assert "routing_metadata" in result
        assert "latency_ms" in result["routing_metadata"]
        assert "model" in result["routing_metadata"]
        assert result["routing_metadata"]["model"] == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_tracks_latency(self, meta_router):
        """Test that latency is tracked."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock LLM
        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.9,
            "reasoning": "Test"
        }))

        result = await meta_router.process(state)

        assert "routing_metadata" in result
        assert "latency_ms" in result["routing_metadata"]
        assert result["routing_metadata"]["latency_ms"] >= 0


class TestClassifyAndRoute:
    """Test the classify_and_route method."""

    @pytest.mark.asyncio
    async def test_classify_and_route_calls_process(self, meta_router):
        """Test that classify_and_route calls process."""
        state = create_initial_state(
            message="Test message",
            customer_id="test_customer"
        )

        # Mock process method
        meta_router.process = AsyncMock(return_value=state)

        result = await meta_router.classify_and_route(state)

        # Should have called process
        meta_router.process.assert_called_once_with(state)
        assert result == state


class TestSystemPrompt:
    """Test system prompt generation."""

    def test_system_prompt_contains_required_sections(self, meta_router):
        """Test that system prompt contains all required sections."""
        prompt = meta_router._get_system_prompt()

        # Check for domain descriptions
        assert "SUPPORT" in prompt
        assert "SALES" in prompt
        assert "CUSTOMER_SUCCESS" in prompt

        # Check for classification rules
        assert "Classification Rules" in prompt or "Rules" in prompt

        # Check for output format
        assert "domain" in prompt.lower()
        assert "confidence" in prompt.lower()
        assert "reasoning" in prompt.lower()

        # Check for JSON output instruction
        assert "JSON" in prompt

    def test_system_prompt_has_context_placeholder(self, meta_router):
        """Test that system prompt has customer context placeholder."""
        prompt = meta_router._get_system_prompt()
        assert "{customer_context}" in prompt


# Integration-like tests (still mocked but more realistic flows)
class TestRealisticFlows:
    """Test realistic end-to-end flows with mocked LLM."""

    @pytest.mark.asyncio
    async def test_free_user_upgrade_inquiry_routes_to_sales(self, meta_router):
        """Test: Free user asking about upgrade → sales"""
        state = create_initial_state(
            message="I want to upgrade my plan, what are my options?",
            context={"customer_metadata": {"plan": "free", "account_age_days": 7}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "confidence": 0.91,
            "reasoning": "Free user inquiring about plan upgrade - sales opportunity"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "sales"
        assert result["next_agent"] == "sales_domain_router"

    @pytest.mark.asyncio
    async def test_paid_user_upgrade_inquiry_routes_to_support(self, meta_router):
        """Test: Paid user asking about upgrade → support (billing)"""
        state = create_initial_state(
            message="I want to upgrade from Basic to Premium",
            context={"customer_metadata": {"plan": "basic", "mrr": 100}}
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "confidence": 0.89,
            "reasoning": "Existing paying customer - billing/support matter"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "support"
        assert result["next_agent"] == "support_domain_router"

    @pytest.mark.asyncio
    async def test_high_value_customer_with_concern_routes_to_cs(self, meta_router):
        """Test: High-value customer with concern → customer_success"""
        state = create_initial_state(
            message="We're thinking of switching to a competitor",
            context={
                "customer_metadata": {
                    "plan": "enterprise",
                    "mrr": 5000,
                    "health_score": 30,
                    "churn_risk": 0.9
                }
            }
        )

        meta_router.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "confidence": 0.95,
            "reasoning": "High-value customer at risk of churn - CS intervention needed"
        }))

        result = await meta_router.process(state)

        assert result["domain"] == "customer_success"
        assert result["next_agent"] == "cs_domain_router"
        assert result["domain_confidence"] > 0.9
