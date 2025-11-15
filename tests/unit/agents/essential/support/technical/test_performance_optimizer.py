"""
Unit tests for Performance Optimizer agent.
"""

import pytest
from src.agents.essential.support.technical.performance_optimizer import PerformanceOptimizer
from src.workflow.state import create_initial_state


class TestPerformanceOptimizer:
    """Test suite for Performance Optimizer agent"""

    @pytest.fixture
    def performance_optimizer(self):
        """Performance Optimizer instance"""
        return PerformanceOptimizer()

    def test_initialization(self, performance_optimizer):
        """Test Performance Optimizer initializes correctly"""
        assert performance_optimizer.config.name == "performance_optimizer"
        assert performance_optimizer.config.type.value == "specialist"
        assert performance_optimizer.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_detect_slow_load_issue(self, performance_optimizer):
        """Test detection of slow loading"""
        state = create_initial_state("The app is really slow to load")

        result = await performance_optimizer.process(state)

        assert result["performance_issue"] == "slow_load"
        assert "performance_diagnosis" in result
        assert result["performance_tips_provided"] is True

    @pytest.mark.asyncio
    async def test_detect_lag_issue(self, performance_optimizer):
        """Test detection of lag/freezing"""
        state = create_initial_state("App is laggy and keeps freezing")

        result = await performance_optimizer.process(state)

        assert result["performance_issue"] == "lag"

    @pytest.mark.asyncio
    async def test_diagnose_large_data_bottleneck(self, performance_optimizer):
        """Test diagnosis of large data bottleneck"""
        state = create_initial_state("App is slow")
        state["customer_metadata"] = {
            "browser": "Chrome",
            "data_size_mb": 150,
            "active_projects": 5,
            "plan": "premium"
        }

        result = await performance_optimizer.process(state)

        diagnosis = result["performance_diagnosis"]
        assert "large_data" in diagnosis["all_bottlenecks"]
        assert diagnosis["severity"] in ["medium", "high"]

    @pytest.mark.asyncio
    async def test_diagnose_too_many_projects(self, performance_optimizer):
        """Test diagnosis of too many projects"""
        context = {
            "browser": "Chrome",
            "data_size_mb": 30,
            "active_projects": 15,
            "plan": "free"
        }

        diagnosis = performance_optimizer._diagnose_performance("slow_load", context)

        assert "too_many_projects" in diagnosis["all_bottlenecks"]
        assert diagnosis["active_projects"] == 15

    @pytest.mark.asyncio
    async def test_diagnose_unsupported_browser(self, performance_optimizer):
        """Test diagnosis of unsupported browser"""
        context = {
            "browser": "IE",
            "data_size_mb": 20,
            "active_projects": 2,
            "plan": "free"
        }

        diagnosis = performance_optimizer._diagnose_performance("lag", context)

        assert "unsupported_browser" in diagnosis["all_bottlenecks"]

    def test_optimization_for_large_data(self, performance_optimizer):
        """Test optimization steps for large data"""
        diagnosis = {
            "primary_bottleneck": "large_data",
            "all_bottlenecks": ["large_data"],
            "severity": "high",
            "data_size_mb": 150
        }

        optimization = performance_optimizer._get_optimization_steps(diagnosis)

        assert "archive" in optimization["message"].lower()
        assert "expected_improvement" in optimization
        assert "50-70%" in optimization["expected_improvement"]

    def test_optimization_for_unsupported_browser(self, performance_optimizer):
        """Test optimization for unsupported browser"""
        diagnosis = {
            "primary_bottleneck": "unsupported_browser",
            "all_bottlenecks": ["unsupported_browser"],
            "severity": "high",
            "browser": "IE"
        }

        optimization = performance_optimizer._get_optimization_steps(diagnosis)

        assert "chrome" in optimization["message"].lower()
        assert "firefox" in optimization["message"].lower()
        assert "10x" in optimization["message"].lower()

    def test_detect_performance_issue_type(self, performance_optimizer):
        """Test performance issue type detection"""
        # Slow load
        issue = performance_optimizer._detect_performance_issue("app loads slow")
        assert issue == "slow_load"

        # Lag
        issue = performance_optimizer._detect_performance_issue("freezing and laggy")
        assert issue == "lag"

        # Timeout
        issue = performance_optimizer._detect_performance_issue("request timed out")
        assert issue == "timeout"

        # General
        issue = performance_optimizer._detect_performance_issue("something wrong")
        assert issue == "general_slowness"
