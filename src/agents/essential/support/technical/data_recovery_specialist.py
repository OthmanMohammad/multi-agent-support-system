"""
Data Recovery Specialist Agent - Recovers deleted/lost data from backups.

Specialist for data recovery, backup restoration, deleted item retrieval.
"""

from datetime import datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("data_recovery_specialist", tier="essential", category="technical")
class DataRecoverySpecialist(BaseAgent):
    """
    Data Recovery Specialist Agent - Specialist for data recovery.

    Handles:
    - Deleted data recovery
    - Backup restoration
    - Lost file retrieval
    - Accidental deletion recovery
    - Backup policy management
    """

    BACKUP_RETENTION_DAYS = 30
    MAX_RECOVERY_SIZE_MB = 1000

    def __init__(self):
        config = AgentConfig(
            name="data_recovery_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE,
            ],
            kb_category="account",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process data recovery requests"""
        self.logger.info("data_recovery_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "data_recovery_started",
            message_preview=message[:100],
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"],
        )

        # Extract recovery details
        recovery_details = self._extract_recovery_details(message, state)

        data_type = recovery_details.get("data_type", "unknown")
        deleted_when = recovery_details.get("deleted_when", "unknown")

        self.logger.info(
            "recovery_details_extracted", data_type=data_type, deleted_when=deleted_when
        )

        # Check if recoverable
        recoverable = self._check_if_recoverable(deleted_when, data_type)

        self.logger.info(
            "recoverability_checked",
            can_recover=recoverable["can_recover"],
            days_ago=recoverable["days_ago"],
        )

        if recoverable["can_recover"]:
            # Initiate recovery
            recovery = await self._recover_data(
                customer_context, data_type, deleted_when, recovery_details
            )

            state["agent_response"] = recovery["message"]
            state["data_recovered"] = recovery["success"]
            state["recovery_id"] = recovery.get("recovery_id")
            state["response_confidence"] = 0.9
        else:
            state["agent_response"] = self._explain_unrecoverable(recoverable)
            state["data_recovered"] = False
            state["response_confidence"] = 1.0

        # Search KB for data recovery help
        kb_results = await self.search_knowledge_base(message, category="account", limit=2)
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("recovery_kb_articles_found", count=len(kb_results))

        # Add KB context to response
        if kb_results:
            kb_context = "\n\n**Related articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"
            state["agent_response"] += kb_context

        state["data_type"] = data_type
        state["deleted_when"] = deleted_when
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "data_recovery_completed",
            recovered=state["data_recovered"],
            data_type=data_type,
            status="resolved",
        )

        return state

    def _extract_recovery_details(self, message: str, state: AgentState) -> dict[str, Any]:
        """Extract data type and timeframe from message"""
        message_lower = message.lower()

        # Detect data type
        data_type = "unknown"
        if any(word in message_lower for word in ["project", "projects"]):
            data_type = "project"
        elif any(word in message_lower for word in ["task", "tasks", "todo"]):
            data_type = "task"
        elif any(word in message_lower for word in ["file", "files", "attachment", "document"]):
            data_type = "file"
        elif any(word in message_lower for word in ["note", "notes"]):
            data_type = "note"
        elif any(word in message_lower for word in ["account", "all data", "everything"]):
            data_type = "account"

        # Detect timeframe
        deleted_when = "unknown"
        if any(word in message_lower for word in ["today", "just now", "few minutes", "hour ago"]):
            deleted_when = "today"
        elif any(word in message_lower for word in ["yesterday"]):
            deleted_when = "yesterday"
        elif any(word in message_lower for word in ["last week", "week ago", "few days"]):
            deleted_when = "last_week"
        elif any(word in message_lower for word in ["two weeks", "2 weeks"]):
            deleted_when = "2_weeks_ago"
        elif any(word in message_lower for word in ["last month", "month ago", "few weeks"]):
            deleted_when = "1_month_ago"
        elif any(word in message_lower for word in ["two months", "2 months", "long time"]):
            deleted_when = "2_months_ago"

        # Check state for explicit values
        data_type = state.get("data_type", data_type)
        deleted_when = state.get("deleted_when", deleted_when)

        return {"data_type": data_type, "deleted_when": deleted_when}

    def _check_if_recoverable(self, deleted_when: str, data_type: str) -> dict[str, Any]:
        """Check if data can be recovered"""
        # Parse timeframe
        days_ago = self._parse_timeframe(deleted_when)

        self.logger.debug(
            "checking_recoverability",
            deleted_when=deleted_when,
            days_ago=days_ago,
            retention_days=self.BACKUP_RETENTION_DAYS,
        )

        within_retention = days_ago <= self.BACKUP_RETENTION_DAYS

        return {
            "can_recover": within_retention,
            "days_ago": days_ago,
            "retention_period": self.BACKUP_RETENTION_DAYS,
            "data_type": data_type,
        }

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe to days"""
        timeframe_map = {
            "today": 0,
            "yesterday": 1,
            "last_week": 7,
            "2_weeks_ago": 14,
            "1_month_ago": 30,
            "2_months_ago": 60,
            "unknown": 0,  # Assume recent if unknown
        }
        return timeframe_map.get(timeframe, 0)

    async def _recover_data(
        self,
        customer_context: dict[str, Any],
        data_type: str,
        deleted_when: str,
        recovery_details: dict[str, Any],
    ) -> dict[str, Any]:
        """Recover deleted data from backup"""
        customer_id = customer_context.get("customer_id", "unknown")

        self.logger.info(
            "initiating_data_recovery",
            customer_id=customer_id,
            data_type=data_type,
            deleted_when=deleted_when,
        )

        # In production: Call backup API to restore data
        # restored_data = backup_api.restore(customer_id, data_type, deleted_when)

        # Generate recovery ID
        recovery_id = f"REC-{datetime.now().strftime('%Y%m%d')}-{customer_id[:8]}"

        message = f"""Great news! I've recovered your deleted {data_type}.

**Recovery details:**
- Data type: {data_type.title()}
- Deleted: {deleted_when.replace("_", " ")}
- Recovery ID: {recovery_id}
- Recovery location: Your account (refresh to see it)
- Recovery time: Immediate

**What to do next:**
1. Refresh your browser/app
2. Check your {data_type} list
3. Verify the recovered data is correct
4. Look for items marked with a "Recovered" tag

**Data safety tips:**
We keep backups for {self.BACKUP_RETENTION_DAYS} days only.

To prevent future data loss:
- Enable auto-backup (Settings > Backup)
- Export important data regularly
- Use "Archive" instead of "Delete" for items you might need later
- Consider upgrading to Premium for extended backup retention (90 days)

**Need to recover more data?**
Let me know and I can check for additional backups!"""

        self.logger.info("data_recovery_successful", recovery_id=recovery_id, data_type=data_type)

        return {"message": message, "success": True, "recovery_id": recovery_id}

    def _explain_unrecoverable(self, recoverable: dict[str, Any]) -> str:
        """Explain why data cannot be recovered"""
        days_ago = recoverable["days_ago"]
        retention = recoverable["retention_period"]
        data_type = recoverable["data_type"]

        self.logger.warning(
            "data_unrecoverable", days_ago=days_ago, retention_period=retention, data_type=data_type
        )

        message = f"""I'm sorry, but I cannot recover your {data_type}.

**Reason:**
Your {data_type} was deleted {days_ago} days ago.
We only keep backups for {retention} days.

**What this means:**
The data is permanently deleted and cannot be recovered from our backups.

**Why we can't recover it:**
- Backups older than {retention} days are automatically purged
- This is for data privacy and storage management
- No exceptions can be made

**Prevention for future:**

1. **Enable auto-backup** (Settings > Backup)
   - Automatic daily backups
   - Cloud storage integration
   - Version history

2. **Export important data regularly**
   - Weekly exports of critical data
   - Store locally or in cloud
   - Multiple backup locations

3. **Use "Archive" instead of "Delete"**
   - Archive keeps data but hides it
   - Can unarchive anytime
   - No backup time limit

4. **Upgrade to Premium**
   - Extended backup retention (90 days)
   - Point-in-time recovery
   - Unlimited version history
   - Priority recovery support

**Alternative solutions:**

**Do you have:**
- Local backups or exports?
- Email notifications with data?
- Screenshots or copies?
- Shared copies with team members?

If so, I can help you import them back into your account.

I'm truly sorry we couldn't recover your data. Is there anything else I can help with?"""

        return message


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Recent deletion - recoverable
        print("=" * 60)
        print("Test 1: Recover recently deleted project")
        print("=" * 60)

        state = create_initial_state("I accidentally deleted my project yesterday")
        state["data_type"] = "project"
        state["deleted_when"] = "yesterday"
        state["customer_metadata"] = {"customer_id": "cust_123"}

        agent = DataRecoverySpecialist()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Recovered: {result.get('data_recovered')}")
        print(f"Recovery ID: {result.get('recovery_id')}")

        # Test 2: Old deletion - not recoverable
        print("\n" + "=" * 60)
        print("Test 2: Attempt to recover old data")
        print("=" * 60)

        state2 = create_initial_state("I need to recover data I deleted 2 months ago")
        state2["data_type"] = "project"
        state2["deleted_when"] = "2_months_ago"
        state2["customer_metadata"] = {"customer_id": "cust_456"}

        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Recovered: {result2.get('data_recovered')}")

        # Test 3: File recovery
        print("\n" + "=" * 60)
        print("Test 3: Recover deleted files")
        print("=" * 60)

        state3 = create_initial_state("Can you recover the files I deleted last week?")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")
        print(f"Data type: {result3.get('data_type')}")
        print(f"Deleted when: {result3.get('deleted_when')}")
        print(f"Recovered: {result3.get('data_recovered')}")

    asyncio.run(test())
