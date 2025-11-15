"""
Unit tests for Sync Troubleshooter agent.
"""

import pytest
from src.agents.essential.support.technical.sync_troubleshooter import SyncTroubleshooter
from src.workflow.state import create_initial_state


class TestSyncTroubleshooter:
    """Test suite for Sync Troubleshooter agent"""

    @pytest.fixture
    def sync_troubleshooter(self):
        """Sync Troubleshooter instance"""
        return SyncTroubleshooter()

    def test_initialization(self, sync_troubleshooter):
        """Test Sync Troubleshooter initializes correctly"""
        assert sync_troubleshooter.config.name == "sync_troubleshooter"
        assert sync_troubleshooter.config.type.value == "specialist"
        assert sync_troubleshooter.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_detect_not_syncing_issue(self, sync_troubleshooter):
        """Test detection of 'not syncing' issue"""
        state = create_initial_state("My data is not syncing between devices")

        result = await sync_troubleshooter.process(state)

        assert result["sync_issue_type"] == "not_syncing"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_detect_conflict_issue(self, sync_troubleshooter):
        """Test detection of sync conflict"""
        state = create_initial_state("I have duplicate entries, sync conflict")

        result = await sync_troubleshooter.process(state)

        assert result["sync_issue_type"] == "conflict"
        assert "conflict" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_detect_slow_sync_issue(self, sync_troubleshooter):
        """Test detection of slow sync"""
        state = create_initial_state("Sync is taking forever, very slow")

        result = await sync_troubleshooter.process(state)

        assert result["sync_issue_type"] == "slow"
        assert "sync_status" in result

    @pytest.mark.asyncio
    async def test_fix_disabled_sync(self, sync_troubleshooter):
        """Test fixing disabled sync"""
        state = create_initial_state("Sync not working")
        state["customer_metadata"] = {"customer_id": "cust_123"}

        # Mock disabled sync
        sync_status = {
            "sync_enabled": False,
            "pending_items": 0,
            "conflicts": 0
        }

        solution = sync_troubleshooter._fix_not_syncing(sync_status, {})

        assert solution["fixed"] is True
        assert "re-enabled" in solution["message"].lower()

    def test_detect_sync_issue_type(self, sync_troubleshooter):
        """Test sync issue type detection from message"""
        # Not syncing
        issue_type = sync_troubleshooter._detect_sync_issue_type("data not syncing")
        assert issue_type == "not_syncing"

        # Conflict
        issue_type = sync_troubleshooter._detect_sync_issue_type("sync conflict, duplicate")
        assert issue_type == "conflict"

        # Slow
        issue_type = sync_troubleshooter._detect_sync_issue_type("sync is so slow")
        assert issue_type == "slow"

        # Unknown
        issue_type = sync_troubleshooter._detect_sync_issue_type("something weird")
        assert issue_type == "unknown"

    def test_check_sync_status(self, sync_troubleshooter):
        """Test sync status checking"""
        status = sync_troubleshooter._check_sync_status({"customer_id": "test"})

        assert "last_sync" in status
        assert "pending_items" in status
        assert "sync_enabled" in status
        assert "connection_status" in status

    @pytest.mark.asyncio
    async def test_resolve_conflict_provides_steps(self, sync_troubleshooter):
        """Test conflict resolution provides clear steps"""
        solution = sync_troubleshooter._resolve_conflict({})

        assert solution["fixed"] is False
        assert "settings" in solution["message"].lower()
        assert "keep local" in solution["message"].lower()
        assert "keep remote" in solution["message"].lower()
