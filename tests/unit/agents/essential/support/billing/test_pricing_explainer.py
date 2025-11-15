"""
Unit tests for Pricing Explainer Agent.
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.billing.pricing_explainer import PricingExplainer
from src.workflow.state import create_initial_state


class TestPricingExplainer:
    """Test suite for Pricing Explainer."""

    @pytest.fixture
    def explainer(self):
        """Create explainer instance for testing."""
        return PricingExplainer()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state(
            "How much does it cost?",
            context={
                "customer_metadata": {
                    "plan": "free",
                    "mrr": 0
                }
            }
        )

    # Initialization Tests
    def test_initialization(self, explainer):
        """Test agent initializes correctly."""
        assert explainer.config.name == "pricing_explainer"
        assert explainer.config.type.value == "specialist"
        assert len(explainer.PLANS) == 4
        assert explainer.ANNUAL_DISCOUNT == 20

    def test_plans_structure(self, explainer):
        """Test all plans have required structure."""
        for plan_name, plan in explainer.PLANS.items():
            assert "price" in plan
            assert "seats" in plan
            assert "features" in plan
            assert isinstance(plan["features"], list)

    # Query Type Detection Tests
    def test_determine_query_type_compare(self, explainer, base_state):
        """Test detecting comparison query."""
        query_type = explainer._determine_query_type(
            "What's the difference between Basic and Premium?",
            base_state
        )
        assert query_type == "compare"

    def test_determine_query_type_calculate(self, explainer, base_state):
        """Test detecting cost calculation query."""
        query_type = explainer._determine_query_type(
            "How much would it cost for 10 users?",
            base_state
        )
        assert query_type == "calculate"

    def test_determine_query_type_volume_discount(self, explainer, base_state):
        """Test detecting volume discount query."""
        query_type = explainer._determine_query_type(
            "Do you offer volume discounts?",
            base_state
        )
        assert query_type == "volume_discount"

    def test_determine_query_type_annual(self, explainer, base_state):
        """Test detecting annual vs monthly query."""
        query_type = explainer._determine_query_type(
            "Should I pay monthly or annually?",
            base_state
        )
        assert query_type == "annual_vs_monthly"

    def test_determine_query_type_features(self, explainer, base_state):
        """Test detecting features query."""
        query_type = explainer._determine_query_type(
            "What features are included in Premium?",
            base_state
        )
        assert query_type == "features"

    # Plan Comparison Tests
    def test_compare_plans_basic_premium(self, explainer):
        """Test comparing Basic and Premium plans."""
        result = explainer._compare_plans(["basic", "premium"])

        assert "basic" in result.lower()
        assert "premium" in result.lower()
        assert "$10" in result or "10" in result
        assert "$25" in result or "25" in result

    def test_compare_plans_free_basic(self, explainer):
        """Test comparing Free and Basic plans."""
        result = explainer._compare_plans(["free", "basic"])

        assert "free" in result.lower()
        assert "basic" in result.lower()
        assert "$0" in result or "free" in result.lower()

    def test_compare_plans_invalid_plan(self, explainer):
        """Test comparing with invalid plan name."""
        # Should skip invalid plans without error
        result = explainer._compare_plans(["basic", "invalid_plan"])

        assert "basic" in result.lower()
        # Should still return valid result

    # Plan Extraction Tests
    def test_extract_plans_to_compare_from_entities(self, explainer, base_state):
        """Test extracting plans from entities."""
        base_state["entities"] = {"plans_to_compare": ["basic", "premium"]}

        plans = explainer._extract_plans_to_compare(base_state)

        assert plans == ["basic", "premium"]

    def test_extract_plans_to_compare_default_free(self, explainer, base_state):
        """Test default comparison for free plan users."""
        base_state["customer_metadata"]["plan"] = "free"

        plans = explainer._extract_plans_to_compare(base_state)

        assert "free" in plans
        assert "basic" in plans

    def test_extract_plans_to_compare_default_basic(self, explainer, base_state):
        """Test default comparison for basic plan users."""
        base_state["customer_metadata"]["plan"] = "basic"

        plans = explainer._extract_plans_to_compare(base_state)

        assert "basic" in plans
        assert "premium" in plans

    # Cost Calculation Tests
    def test_calculate_cost_monthly_basic(self, explainer, base_state):
        """Test calculating monthly cost for Basic plan."""
        base_state["entities"] = {
            "desired_plan": "basic",
            "team_size": 5,
            "billing_cycle": "monthly"
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        assert "$50" in result  # 5 users * $10
        assert "monthly" in result.lower()

    def test_calculate_cost_annual_with_discount(self, explainer, base_state):
        """Test calculating annual cost with discount."""
        base_state["entities"] = {
            "desired_plan": "basic",
            "team_size": 5,
            "billing_cycle": "annual"
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        assert "annual" in result.lower()
        assert "20%" in result or "save" in result.lower()
        assert "$480" in result  # 5 * 10 * 12 * 0.8

    def test_calculate_cost_with_volume_discount(self, explainer, base_state):
        """Test calculating cost with volume discount."""
        base_state["entities"] = {
            "desired_plan": "premium",
            "team_size": 15,  # Should get 10% discount
            "billing_cycle": "monthly"
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        # Should mention volume discount
        assert "discount" in result.lower()

    def test_calculate_cost_enterprise_plan(self, explainer, base_state):
        """Test calculating cost for Enterprise plan."""
        base_state["entities"] = {
            "desired_plan": "enterprise",
            "team_size": 50
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        assert "custom" in result.lower()
        assert "sales" in result.lower()

    # Volume Discount Tests
    def test_get_volume_discount_no_discount(self, explainer):
        """Test no volume discount for small teams."""
        discount = explainer._get_volume_discount(5)
        assert discount == 0

    def test_get_volume_discount_10_users(self, explainer):
        """Test 10% discount for 10+ users."""
        discount = explainer._get_volume_discount(15)
        assert discount == 10

    def test_get_volume_discount_50_users(self, explainer):
        """Test 15% discount for 50+ users."""
        discount = explainer._get_volume_discount(60)
        assert discount == 15

    def test_get_volume_discount_100_users(self, explainer):
        """Test 20% discount for 100+ users."""
        discount = explainer._get_volume_discount(150)
        assert discount == 20

    # Annual vs Monthly Tests
    def test_explain_annual_vs_monthly(self, explainer, base_state):
        """Test explaining annual vs monthly billing."""
        base_state["customer_metadata"]["mrr"] = 100

        result = explainer._explain_annual_vs_monthly(
            base_state,
            base_state["customer_metadata"]
        )

        assert "annual" in result.lower()
        assert "monthly" in result.lower()
        assert "20%" in result
        assert "$1200" in result  # Annual total without discount
        assert "$960" in result  # Annual with 20% discount

    # Feature Explanation Tests
    def test_explain_plan_features_basic(self, explainer, base_state):
        """Test explaining Basic plan features."""
        base_state["entities"] = {"plan": "basic"}

        result = explainer._explain_plan_features(base_state)

        assert "basic" in result.lower()
        assert "$10" in result
        assert "features" in result.lower()

    def test_explain_plan_features_premium(self, explainer, base_state):
        """Test explaining Premium plan features."""
        base_state["entities"] = {"plan": "premium"}

        result = explainer._explain_plan_features(base_state)

        assert "premium" in result.lower()
        assert "$25" in result
        assert "best for" in result.lower()

    def test_explain_plan_features_invalid_defaults(self, explainer, base_state):
        """Test explaining features with invalid plan defaults to basic."""
        base_state["entities"] = {"plan": "invalid"}

        result = explainer._explain_plan_features(base_state)

        assert "basic" in result.lower()

    # Volume Discount Explanation Tests
    def test_explain_volume_discount(self, explainer, base_state):
        """Test explaining volume discount structure."""
        result = explainer._explain_volume_discount(base_state)

        assert "10-49 users" in result or "10%" in result
        assert "50-99 users" in result or "15%" in result
        assert "100+" in result or "20%" in result

    # General Overview Tests
    def test_general_pricing_overview(self, explainer):
        """Test general pricing overview."""
        result = explainer._general_pricing_overview()

        assert "free" in result.lower()
        assert "basic" in result.lower()
        assert "premium" in result.lower()
        assert "enterprise" in result.lower()
        assert "$0" in result
        assert "$10" in result
        assert "$25" in result

    # Main Processing Tests
    @pytest.mark.asyncio
    async def test_process_compare_query(self, explainer, base_state):
        """Test processing plan comparison query."""
        base_state["entities"] = {"plans_to_compare": ["basic", "premium"]}

        result = await explainer.process(base_state)

        assert result["pricing_query_type"] == "compare"
        assert result["status"] == "resolved"
        assert "basic" in result["agent_response"].lower()
        assert "premium" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_process_calculate_query(self, explainer, base_state):
        """Test processing cost calculation query."""
        base_state["current_message"] = "How much for 10 users on Premium?"
        base_state["entities"] = {
            "desired_plan": "premium",
            "team_size": 10,
            "billing_cycle": "monthly"
        }

        result = await explainer.process(base_state)

        assert result["pricing_query_type"] == "calculate"
        assert "$250" in result["agent_response"]  # 10 * 25

    @pytest.mark.asyncio
    async def test_process_volume_discount_query(self, explainer, base_state):
        """Test processing volume discount query."""
        base_state["current_message"] = "Do you offer volume discounts?"

        result = await explainer.process(base_state)

        assert result["pricing_query_type"] == "volume_discount"
        assert "discount" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_process_annual_query(self, explainer):
        """Test processing annual vs monthly query."""
        state = create_initial_state(
            "Should I pay annually or monthly?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250
                }
            }
        )

        result = await explainer.process(state)

        assert result["pricing_query_type"] == "annual_vs_monthly"
        assert "annual" in result["agent_response"].lower()
        assert "20%" in result["agent_response"]

    @pytest.mark.asyncio
    async def test_process_general_overview(self, explainer, base_state):
        """Test processing general pricing query."""
        result = await explainer.process(base_state)

        # Should default to overview
        assert result["status"] == "resolved"
        assert len(result["agent_response"]) > 0

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_team_size_defaults(self, explainer, base_state):
        """Test calculation with missing team size uses default."""
        base_state["entities"] = {
            "desired_plan": "basic",
            "billing_cycle": "monthly"
            # No team_size provided
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        # Should use default of 5
        assert "$50" in result

    @pytest.mark.asyncio
    async def test_large_team_volume_discount(self, explainer, base_state):
        """Test calculation with large team gets max discount."""
        base_state["entities"] = {
            "desired_plan": "premium",
            "team_size": 200,
            "billing_cycle": "monthly"
        }

        result = explainer._calculate_cost(base_state, base_state["customer_metadata"])

        # Should have 20% volume discount
        assert "20%" in result or "discount" in result.lower()

    # Integration Tests
    @pytest.mark.asyncio
    async def test_full_pricing_flow(self, explainer):
        """Test complete pricing inquiry flow."""
        state = create_initial_state(
            "How much for 15 users on Premium, paid annually?",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "mrr": 100
                }
            }
        )
        state["entities"] = {
            "desired_plan": "premium",
            "team_size": 15,
            "billing_cycle": "annual"
        }

        result = await explainer.process(state)

        assert result["pricing_query_type"] == "calculate"
        assert result["response_confidence"] == 0.95
        assert "annual" in result["agent_response"].lower()
        assert "discount" in result["agent_response"].lower()
