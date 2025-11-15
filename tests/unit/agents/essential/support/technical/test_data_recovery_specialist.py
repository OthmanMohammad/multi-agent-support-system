"""
Unit tests for Data Recovery Specialist agent.
"""

import pytest
from src.agents.essential.support.technical.data_recovery_specialist import DataRecoverySpecialist
from src.workflow.state import create_initial_state


class TestDataRecoverySpecialist:
    """Test suite for Data Recovery Specialist agent"""

    @pytest.fixture
    def data_recovery_specialist(self):
        """Data Recovery Specialist instance"""
        return DataRecoverySpecialist()

    def test_initialization(self, data_recovery_specialist):
        """Test Data Recovery Specialist initializes correctly"""
        assert data_recovery_specialist.config.name == "data_recovery_specialist"
        assert data_recovery_specialist.config.type.value == "specialist"
        assert data_recovery_specialist.config.tier == "essential"
        assert data_recovery_specialist.BACKUP_RETENTION_DAYS == 30

    @pytest.mark.asyncio
    async def test_recover_recent_data(self, data_recovery_specialist):
        """Test recovery of recently deleted data"""
        state = create_initial_state("I accidentally deleted my project yesterday")
        state["data_type"] = "project"
        state["deleted_when"] = "yesterday"
        state["customer_metadata"] = {"customer_id": "cust_123"}

        result = await data_recovery_specialist.process(state)

        assert result["data_recovered"] is True
        assert "recovery_id" in result
        assert "recovered" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_cannot_recover_old_data(self, data_recovery_specialist):
        """Test that old data cannot be recovered"""
        state = create_initial_state("Need to recover data from 2 months ago")
        state["data_type"] = "project"
        state["deleted_when"] = "2_months_ago"
        state["customer_metadata"] = {"customer_id": "cust_456"}

        result = await data_recovery_specialist.process(state)

        assert result["data_recovered"] is False
        assert "cannot recover" in result["agent_response"].lower()
        assert "permanently deleted" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_extract_data_type_from_message(self, data_recovery_specialist):
        """Test data type extraction from message"""
        state = create_initial_state("I deleted some files last week")
        result = await data_recovery_specialist.process(state)

        assert result["data_type"] == "file"
        assert result["deleted_when"] == "last_week"

    def test_parse_timeframe(self, data_recovery_specialist):
        """Test timeframe parsing to days"""
        assert data_recovery_specialist._parse_timeframe("today") == 0
        assert data_recovery_specialist._parse_timeframe("yesterday") == 1
        assert data_recovery_specialist._parse_timeframe("last_week") == 7
        assert data_recovery_specialist._parse_timeframe("2_weeks_ago") == 14
        assert data_recovery_specialist._parse_timeframe("1_month_ago") == 30
        assert data_recovery_specialist._parse_timeframe("2_months_ago") == 60

    def test_check_if_recoverable(self, data_recovery_specialist):
        """Test recoverability checking"""
        # Within retention
        result = data_recovery_specialist._check_if_recoverable("yesterday", "project")
        assert result["can_recover"] is True
        assert result["days_ago"] == 1

        # Outside retention
        result = data_recovery_specialist._check_if_recoverable("2_months_ago", "project")
        assert result["can_recover"] is False
        assert result["days_ago"] == 60

    @pytest.mark.asyncio
    async def test_recovery_message_includes_prevention_tips(self, data_recovery_specialist):
        """Test that successful recovery includes prevention tips"""
        result = await data_recovery_specialist._recover_data(
            {"customer_id": "test"},
            "project",
            "yesterday",
            {}
        )

        assert "auto-backup" in result["message"].lower()
        assert "export" in result["message"].lower()
        assert "archive" in result["message"].lower()

    def test_unrecoverable_message_provides_alternatives(self, data_recovery_specialist):
        """Test that unrecoverable message provides alternatives"""
        recoverable = {
            "can_recover": False,
            "days_ago": 60,
            "retention_period": 30,
            "data_type": "project"
        }

        message = data_recovery_specialist._explain_unrecoverable(recoverable)

        assert "local backups" in message.lower()
        assert "premium" in message.lower()
        assert "archive" in message.lower()
        assert "prevention" in message.lower()

    def test_extract_recovery_details(self, data_recovery_specialist):
        """Test extraction of recovery details from message"""
        # Project deletion
        details = data_recovery_specialist._extract_recovery_details(
            "I deleted my project yesterday",
            {}
        )
        assert details["data_type"] == "project"
        assert details["deleted_when"] == "yesterday"

        # File deletion
        details = data_recovery_specialist._extract_recovery_details(
            "Can't find files I deleted last week",
            {}
        )
        assert details["data_type"] == "file"
        assert details["deleted_when"] == "last_week"

        # Task deletion
        details = data_recovery_specialist._extract_recovery_details(
            "My tasks are gone, deleted today",
            {}
        )
        assert details["data_type"] == "task"
        assert details["deleted_when"] == "today"
