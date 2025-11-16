"""
Unit tests for Response Verifier Agent.

Tests quality verification, check orchestration, and verdict determination.
Part of: TASK-2101 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.agents.operational.qa.response_verifier import ResponseVerifierAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ResponseVerifierAgent instance."""
    return ResponseVerifierAgent()


class TestResponseVerifierInitialization:
    """Test Response Verifier initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "response_verifier"
        assert agent.config.tier == "operational"
        assert agent.config.type.value == "analyzer"
        assert agent.config.temperature == 0.1

    def test_check_categories_defined(self, agent):
        """Test check categories are properly defined."""
        assert len(agent.CHECK_CATEGORIES) == 9
        assert "facts" in agent.CHECK_CATEGORIES
        assert "policy" in agent.CHECK_CATEGORIES
        assert "tone" in agent.CHECK_CATEGORIES

    def test_severity_levels_defined(self, agent):
        """Test severity levels are properly defined."""
        assert agent.SEVERITY_LEVELS["critical"] == 1
        assert agent.SEVERITY_LEVELS["high"] == 2
        assert agent.SEVERITY_LEVELS["medium"] == 3
        assert agent.SEVERITY_LEVELS["low"] == 4


class TestQualityVerification:
    """Test quality verification logic."""

    @pytest.mark.asyncio
    async def test_successful_verification_pass(self, agent):
        """Test successful verification with all checks passing."""
        state = create_initial_state(
            message="Verify this response",
            context={}
        )
        state["entities"] = {
            "response_text": "This is a well-written, accurate response that follows all policies.",
            "check_level": "standard"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert result["verification_verdict"]["passed"] is True
        assert result["quality_score"] > 80

    @pytest.mark.asyncio
    async def test_verification_fail_empty_response(self, agent):
        """Test verification fails on empty response."""
        state = create_initial_state(message="Verify response", context={})
        state["entities"] = {
            "response_text": "",
            "check_level": "standard"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert result["verification_verdict"]["passed"] is False

    @pytest.mark.asyncio
    async def test_verification_strict_level(self, agent):
        """Test verification with strict checking level."""
        state = create_initial_state(message="Verify response", context={})
        state["entities"] = {
            "response_text": "Good response with proper content",
            "check_level": "strict"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "verification_verdict" in result

    @pytest.mark.asyncio
    async def test_verification_minimal_level(self, agent):
        """Test verification with minimal checking level."""
        state = create_initial_state(message="Verify response", context={})
        state["entities"] = {
            "response_text": "Basic response",
            "check_level": "minimal"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "verification_verdict" in result


class TestQualityChecks:
    """Test individual quality check methods."""

    def test_check_structure_valid(self, agent):
        """Test structure check with valid response."""
        response_text = "Hello! This is a well-structured response with proper greeting and closing. Thank you!"

        result = agent._check_structure(response_text)

        assert result["passed"] is True
        assert result["confidence"] == 0.99

    def test_check_structure_empty(self, agent):
        """Test structure check with empty response."""
        result = agent._check_structure("")

        assert result["passed"] is False
        assert any(issue["severity"] == "critical" for issue in result["issues"])

    def test_check_structure_too_short(self, agent):
        """Test structure check with too short response."""
        result = agent._check_structure("Hi")

        assert result["passed"] is False

    def test_check_length_valid(self, agent):
        """Test length check with valid response."""
        response_text = " ".join(["word"] * 50)  # 50 words

        result = agent._check_length(response_text)

        assert result["passed"] is True
        assert result["word_count"] == 50

    def test_check_length_too_short(self, agent):
        """Test length check with too short response."""
        result = agent._check_length("Too short")

        assert result["passed"] is False
        assert any(issue["severity"] == "high" for issue in result["issues"])

    def test_check_length_too_long(self, agent):
        """Test length check with too long response."""
        response_text = " ".join(["word"] * 900)  # 900 words

        result = agent._check_length(response_text)

        assert len([i for i in result["issues"] if i["type"] == "excessive_length"]) > 0


class TestResultAggregation:
    """Test result aggregation logic."""

    def test_aggregate_results_all_passed(self, agent):
        """Test aggregation when all checks pass."""
        check_results = {
            "structure": {"passed": True, "issues": [], "confidence": 0.99},
            "length": {"passed": True, "issues": [], "confidence": 0.99},
            "facts": {"passed": True, "issues": [], "confidence": 0.95}
        }

        aggregated = agent._aggregate_results(check_results)

        assert aggregated["total_checks"] == 3
        assert aggregated["passed_checks"] == 3
        assert aggregated["failed_checks"] == 0
        assert aggregated["pass_rate"] == 100.0

    def test_aggregate_results_with_failures(self, agent):
        """Test aggregation with some failures."""
        check_results = {
            "structure": {"passed": False, "issues": [{"severity": "critical", "message": "Test"}], "confidence": 0.9},
            "length": {"passed": True, "issues": [], "confidence": 0.99}
        }

        aggregated = agent._aggregate_results(check_results)

        assert aggregated["passed_checks"] == 1
        assert aggregated["failed_checks"] == 1
        assert len(aggregated["issues"]) == 1

    def test_aggregate_results_issues_by_severity(self, agent):
        """Test issues are grouped by severity."""
        check_results = {
            "check1": {
                "passed": False,
                "issues": [
                    {"severity": "critical", "message": "Critical issue"},
                    {"severity": "high", "message": "High issue"},
                    {"severity": "low", "message": "Low issue"}
                ],
                "confidence": 0.9
            }
        }

        aggregated = agent._aggregate_results(check_results)

        assert len(aggregated["issues_by_severity"]["critical"]) == 1
        assert len(aggregated["issues_by_severity"]["high"]) == 1
        assert len(aggregated["issues_by_severity"]["low"]) == 1


class TestVerdictDetermination:
    """Test verdict determination logic."""

    def test_verdict_standard_level_pass(self, agent):
        """Test verdict determination with standard level - pass."""
        aggregated_results = {
            "issues_by_severity": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            }
        }

        verdict = agent._determine_verdict(aggregated_results, "standard")

        assert verdict["passed"] is True
        assert verdict["status"] == "PASS"
        assert verdict["can_send"] is True

    def test_verdict_standard_level_fail(self, agent):
        """Test verdict determination with standard level - fail."""
        aggregated_results = {
            "issues_by_severity": {
                "critical": [{"message": "Critical issue"}],
                "high": [],
                "medium": [],
                "low": []
            }
        }

        verdict = agent._determine_verdict(aggregated_results, "standard")

        assert verdict["passed"] is False
        assert verdict["status"] == "FAIL"
        assert verdict["can_send"] is False

    def test_verdict_strict_level_blocks_high_issues(self, agent):
        """Test strict level blocks high severity issues."""
        aggregated_results = {
            "issues_by_severity": {
                "critical": [],
                "high": [{"message": "High issue"}],
                "medium": [],
                "low": []
            }
        }

        verdict = agent._determine_verdict(aggregated_results, "strict")

        assert verdict["passed"] is False
        assert verdict["status"] == "FAIL"

    def test_verdict_minimal_level_allows_high_issues(self, agent):
        """Test minimal level allows high severity issues."""
        aggregated_results = {
            "issues_by_severity": {
                "critical": [],
                "high": [{"message": "High issue"}],
                "medium": [],
                "low": []
            }
        }

        verdict = agent._determine_verdict(aggregated_results, "minimal")

        assert verdict["passed"] is True


class TestQualityScore:
    """Test quality score calculation."""

    def test_calculate_quality_score_perfect(self, agent):
        """Test quality score calculation with perfect checks."""
        check_results = {
            "check1": {"passed": True, "issues": [], "confidence": 0.99},
            "check2": {"passed": True, "issues": [], "confidence": 0.99}
        }

        score = agent._calculate_quality_score(check_results)

        assert score == 100.0

    def test_calculate_quality_score_with_critical_issue(self, agent):
        """Test quality score with critical issue."""
        check_results = {
            "check1": {
                "passed": False,
                "issues": [{"severity": "critical", "message": "Critical"}],
                "confidence": 0.9
            }
        }

        score = agent._calculate_quality_score(check_results)

        assert score == 75.0  # 100 - 25 for critical

    def test_calculate_quality_score_with_multiple_issues(self, agent):
        """Test quality score with multiple issues."""
        check_results = {
            "check1": {
                "passed": False,
                "issues": [
                    {"severity": "high", "message": "High"},
                    {"severity": "medium", "message": "Medium"},
                    {"severity": "low", "message": "Low"}
                ],
                "confidence": 0.9
            }
        }

        score = agent._calculate_quality_score(check_results)

        assert score == 84.0  # 100 - 10 - 5 - 1

    def test_calculate_quality_score_floor_at_zero(self, agent):
        """Test quality score floors at 0."""
        check_results = {
            "check1": {
                "passed": False,
                "issues": [{"severity": "critical", "message": "Critical"}] * 10,
                "confidence": 0.9
            }
        }

        score = agent._calculate_quality_score(check_results)

        assert score == 0.0


class TestFeedbackGeneration:
    """Test feedback generation."""

    def test_generate_feedback_pass(self, agent):
        """Test feedback generation for passing verification."""
        check_results = {}
        aggregated_results = {
            "issues_by_severity": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            }
        }
        verdict = {"passed": True, "status": "PASS"}

        feedback = agent._generate_feedback(check_results, aggregated_results, verdict)

        assert any("passed" in item.lower() for item in feedback)

    def test_generate_feedback_fail(self, agent):
        """Test feedback generation for failing verification."""
        check_results = {}
        aggregated_results = {
            "issues_by_severity": {
                "critical": [{"category": "structure", "message": "Empty response"}],
                "high": [],
                "medium": [],
                "low": []
            }
        }
        verdict = {"passed": False, "status": "FAIL"}

        feedback = agent._generate_feedback(check_results, aggregated_results, verdict)

        assert any("failed" in item.lower() for item in feedback)
        assert any("critical" in item.lower() for item in feedback)


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_response_text(self, agent):
        """Test handling of missing response text."""
        state = create_initial_state(message="Verify response", context={})
        state["entities"] = {"check_level": "standard"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_empty_check_level(self, agent):
        """Test handling of missing check level (uses default)."""
        state = create_initial_state(message="Verify response", context={})
        state["entities"] = {"response_text": "Test response"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    def test_empty_check_results(self, agent):
        """Test handling of empty check results."""
        score = agent._calculate_quality_score({})

        assert score == 0.0
