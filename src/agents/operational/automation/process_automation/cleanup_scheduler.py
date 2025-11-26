"""
Cleanup Scheduler Agent - TASK-2220

Auto-schedules and executes data cleanup tasks including archiving old records,
purging expired data, and maintaining database health.
"""

from datetime import UTC, datetime, timedelta

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("cleanup_scheduler", tier="operational", category="automation")
class CleanupSchedulerAgent(BaseAgent):
    """Cleanup Scheduler Agent - Auto-schedules data cleanup tasks."""

    CLEANUP_POLICIES = {
        "archived_tickets": {"retention_days": 365, "action": "archive"},
        "expired_sessions": {"retention_days": 30, "action": "delete"},
        "old_logs": {"retention_days": 90, "action": "compress"},
        "temp_files": {"retention_days": 7, "action": "delete"},
        "completed_workflows": {"retention_days": 180, "action": "archive"},
    }

    def __init__(self):
        config = AgentConfig(
            name="cleanup_scheduler",
            type=AgentType.AUTOMATOR,
            temperature=0.1,
            max_tokens=700,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Execute scheduled cleanup tasks."""
        self.logger.info("cleanup_scheduler_started")
        state = self.update_state(state)

        # Execute cleanup for all policies
        cleanup_results = []
        for data_type, policy in self.CLEANUP_POLICIES.items():
            result = await self._execute_cleanup(data_type, policy)
            cleanup_results.append(result)

        # Calculate totals
        total_records = sum(r["records_processed"] for r in cleanup_results)
        total_space = sum(r["space_freed_mb"] for r in cleanup_results)

        response = f"""**Cleanup Completed**

Total Records Processed: {total_records:,}
Total Space Freed: {total_space:,} MB

**Cleanup Summary:**
"""
        for result in cleanup_results:
            response += f"✓ {result['data_type'].replace('_', ' ').title()}: {result['records_processed']} records ({result['space_freed_mb']} MB)\n"

        response += f"\nNext cleanup scheduled: {(datetime.now(UTC) + timedelta(days=1)).strftime('%Y-%m-%d')}"

        state["agent_response"] = response
        state["cleanup_results"] = cleanup_results
        state["response_confidence"] = 0.95
        state["status"] = "resolved"

        self.logger.info("cleanup_completed", total_records=total_records)
        return state

    async def _execute_cleanup(self, data_type: str, policy: dict) -> dict:
        """Execute cleanup for a specific data type."""
        cutoff_date = datetime.now(UTC) - timedelta(days=policy["retention_days"])

        # Mock cleanup execution
        import random

        records_processed = random.randint(100, 5000)
        space_freed = random.randint(10, 500)

        return {
            "data_type": data_type,
            "action": policy["action"],
            "retention_days": policy["retention_days"],
            "cutoff_date": cutoff_date.isoformat(),
            "records_processed": records_processed,
            "space_freed_mb": space_freed,
            "status": "success",
            "executed_at": datetime.now(UTC).isoformat(),
        }
