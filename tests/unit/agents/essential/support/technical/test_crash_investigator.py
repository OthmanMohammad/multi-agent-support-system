"""
Unit tests for Crash Investigator agent.
"""

import pytest
from src.agents.essential.support.technical.crash_investigator import CrashInvestigator
from src.workflow.state import create_initial_state


class TestCrashInvestigator:
    """Test suite for Crash Investigator agent"""

    @pytest.fixture
    def crash_investigator(self):
        """Crash Investigator instance"""
        return CrashInvestigator()

    def test_initialization(self, crash_investigator):
        """Test Crash Investigator initializes correctly"""
        assert crash_investigator.config.name == "crash_investigator"
        assert crash_investigator.config.type.value == "specialist"
        assert crash_investigator.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_request_crash_info_when_no_logs(self, crash_investigator):
        """Test that agent requests crash info when no logs provided"""
        state = create_initial_state("My app keeps crashing")
        state["primary_intent"] = "technical_crash"

        result = await crash_investigator.process(state)

        assert "agent_response" in result
        assert result["crash_logs_collected"] is False
        assert result["awaiting_logs"] is True
        assert "browser" in result["agent_response"].lower()
        assert "error message" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_analyze_known_crash(self, crash_investigator, sample_crash_data):
        """Test analysis of known crash pattern"""
        state = create_initial_state("TypeError crash")
        state["crash_logs_collected"] = True
        state["crash_data"] = sample_crash_data

        result = await crash_investigator.process(state)

        assert result["crash_logs_collected"] is True
        assert "crash_analysis" in result
        assert result["crash_analysis"]["type"] == "known_issue"
        assert "solution" in result["crash_analysis"]

    @pytest.mark.asyncio
    async def test_analyze_memory_crash(self, crash_investigator):
        """Test analysis of memory-related crash"""
        crash_data = {
            "error_message": "Memory exceeded - heap out of memory",
            "browser": "Chrome",
            "browser_version": "120"
        }

        state = create_initial_state("App crashes with memory error")
        state["crash_logs_collected"] = True
        state["crash_data"] = crash_data

        result = await crash_investigator.process(state)

        assert result["crash_analysis"]["type"] == "memory_leak"
        assert result["crash_analysis"]["severity"] == "high"
        assert "cache" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_create_bug_ticket(self, crash_investigator):
        """Test bug ticket creation for unknown crashes"""
        crash_data = {
            "error_message": "UnknownError: Something went wrong",
            "browser": "Firefox",
            "browser_version": "115"
        }

        state = create_initial_state("Unknown crash")
        state["crash_logs_collected"] = True
        state["crash_data"] = crash_data
        state["customer_metadata"] = {"customer_id": "cust_123"}

        result = await crash_investigator.process(state)

        assert "bug_ticket_created" in result
        assert result["bug_ticket_created"].startswith("BUG-")
        assert "ticket" in result["agent_response"].lower()

    def test_check_known_issues(self, crash_investigator):
        """Test known issue detection"""
        # Test known issue
        known = crash_investigator._check_known_issues(
            "TypeError: Cannot read property",
            "Chrome"
        )
        assert known is not None
        assert "solution" in known

        # Test unknown issue
        unknown = crash_investigator._check_known_issues(
            "RandomError: Something weird",
            "Chrome"
        )
        assert unknown is None

    def test_analyze_crash_data(self, crash_investigator, sample_crash_data):
        """Test crash data analysis"""
        analysis = crash_investigator._analyze_crash(sample_crash_data)

        assert "type" in analysis
        assert "severity" in analysis
        assert "solution" in analysis
        assert "browser" in analysis
        assert analysis["browser"] == "Chrome"
