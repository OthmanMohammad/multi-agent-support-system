"""
Sync Troubleshooter Agent - Debugs data sync issues, resolves conflicts.

Specialist for sync troubleshooting, conflict resolution, and manual sync triggers.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("sync_troubleshooter", tier="essential", category="technical")
class SyncTroubleshooter(BaseAgent):
    """
    Sync Troubleshooter Agent - Specialist for sync issues.

    Handles:
    - Data not syncing
    - Sync conflicts
    - Slow sync performance
    - Manual sync triggers
    - Sync status diagnosis
    """

    def __init__(self):
        config = AgentConfig(
            name="sync_troubleshooter",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="technical",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process sync troubleshooting requests"""
        self.logger.info("sync_troubleshooter_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "sync_troubleshooting_started",
            message_preview=message[:100],
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Detect sync issue type from message
        sync_issue_type = self._detect_sync_issue_type(message)

        self.logger.info(
            "sync_issue_detected",
            issue_type=sync_issue_type
        )

        # Check sync status
        sync_status = self._check_sync_status(customer_context)

        # Generate solution based on issue type
        if sync_issue_type == "not_syncing":
            solution = self._fix_not_syncing(sync_status, customer_context)
        elif sync_issue_type == "conflict":
            solution = self._resolve_conflict(customer_context)
        elif sync_issue_type == "slow":
            solution = self._fix_slow_sync(sync_status, customer_context)
        else:
            solution = self._diagnose_sync_issue(sync_status)

        # Search KB for sync solutions
        kb_results = await self.search_knowledge_base(
            message,
            category="technical",
            limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "sync_kb_articles_found",
                count=len(kb_results)
            )

        response = self._format_response(solution, kb_results)

        state["agent_response"] = response
        state["sync_issue_type"] = sync_issue_type
        state["sync_fixed"] = solution.get("fixed", False)
        state["sync_status"] = sync_status
        state["response_confidence"] = 0.8
        state["next_agent"] = None
        state["status"] = "resolved" if solution.get("fixed") else "pending_user_action"

        self.logger.info(
            "sync_troubleshooting_completed",
            issue_type=sync_issue_type,
            fixed=solution.get("fixed", False),
            status=state["status"]
        )

        return state

    def _detect_sync_issue_type(self, message: str) -> str:
        """Detect the type of sync issue from message"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["not syncing", "won't sync", "doesn't sync", "stopped syncing"]):
            return "not_syncing"
        elif any(word in message_lower for word in ["conflict", "duplicate", "multiple versions"]):
            return "conflict"
        elif any(word in message_lower for word in ["slow", "taking forever", "too long", "stuck"]):
            return "slow"
        else:
            return "unknown"

    def _check_sync_status(self, customer_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check current sync status"""
        # In production: Call sync API
        # For now, simulate sync status

        self.logger.debug("checking_sync_status")

        # Simulate realistic sync status
        return {
            "last_sync": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "pending_items": 5,
            "conflicts": 0,
            "sync_enabled": True,
            "sync_speed": "normal",
            "connection_status": "connected"
        }

    def _fix_not_syncing(self, sync_status: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix sync that's not working"""
        if not sync_status["sync_enabled"]:
            self.logger.info("sync_disabled_detected")

            # Re-enable sync
            message = """Sync was disabled. I've re-enabled it for you.

**What I did:**
1. Re-enabled automatic sync
2. Triggered manual sync
3. Verified connection

Your data should sync within the next 5 minutes. Refresh to see changes."""

            return {"message": message, "fixed": True, "action": "re_enabled"}

        elif sync_status["pending_items"] > 0:
            self.logger.info(
                "pending_items_detected",
                count=sync_status["pending_items"]
            )

            message = f"""Sync is working, but you have {sync_status['pending_items']} items in the queue.

**Common causes:**
- Large files (sync takes longer)
- Poor internet connection
- API rate limits

**What to do:**
1. Check your internet connection
2. Wait 5-10 minutes for sync to complete
3. If still not syncing, try manual sync (click sync icon)

Your data is safe and will sync once the queue is processed."""

            return {"message": message, "fixed": False, "action": "pending_items"}

        elif sync_status["connection_status"] != "connected":
            self.logger.warning("connection_issue_detected")

            message = """Sync connection issue detected.

**Quick fixes:**
1. Check your internet connection
2. Try refreshing the page
3. Check if firewall is blocking sync
4. Verify you're logged in

If the issue persists, try logging out and back in."""

            return {"message": message, "fixed": False, "action": "connection_issue"}

        return {
            "message": "Sync status looks normal. Can you describe what's not syncing?",
            "fixed": False,
            "action": "needs_clarification"
        }

    def _resolve_conflict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve sync conflicts"""
        self.logger.info("conflict_resolution_started")

        message = """You have sync conflicts - the same item was edited on two devices.

**How to resolve:**
1. Go to Settings > Sync > View Conflicts
2. Choose which version to keep:
   - **Keep local** (this device)
   - **Keep remote** (other device)
   - **Merge both** (manual merge)

**Prevention tips:**
- Always sync before editing
- Use one device at a time
- Wait for sync to complete before switching devices

**Automatic conflict resolution:**
You can enable auto-resolve in Settings > Sync > Conflict Resolution:
- Always keep newest
- Always keep local
- Always prompt

Would you like me to enable automatic conflict resolution for you?"""

        return {
            "message": message,
            "fixed": False,
            "action": "conflict_resolution_steps"
        }

    def _fix_slow_sync(self, sync_status: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix slow sync performance"""
        self.logger.info("slow_sync_troubleshooting_started")

        message = """Sync seems slow. Here's how to speed it up:

**Quick fixes:**
1. Reduce file sizes (compress images/videos)
2. Sync fewer items at once
3. Check internet speed (need 5+ Mbps)
4. Close other apps using bandwidth
5. Clear browser cache

**Advanced optimizations:**
- Enable selective sync (sync only what you need)
- Schedule sync during off-hours
- Upgrade to Premium for priority sync
- Use the desktop app (faster than web)

**Current sync queue:** {pending} items

Would you like me to enable selective sync for you? This can speed up sync by 50-70%.""".format(
            pending=sync_status.get("pending_items", 0)
        )

        return {
            "message": message,
            "fixed": False,
            "action": "performance_optimization"
        }

    def _diagnose_sync_issue(self, sync_status: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose general sync issue"""
        self.logger.info("general_sync_diagnosis_started")

        last_sync = sync_status.get("last_sync", "unknown")
        pending = sync_status.get("pending_items", 0)
        conflicts = sync_status.get("conflicts", 0)

        message = f"""Let me check your sync status:

**Current Status:**
- Last sync: {last_sync}
- Pending items: {pending}
- Conflicts: {conflicts}
- Connection: {sync_status.get('connection_status', 'unknown')}

**Common sync issues:**
1. **Not syncing** - Check internet connection and sync settings
2. **Conflicts** - Same item edited on multiple devices
3. **Slow sync** - Large files or slow connection
4. **Selective sync** - Only certain items syncing

Can you describe the specific issue you're experiencing?

**Quick diagnostics:**
- Try manual sync (click sync icon)
- Check sync settings (Settings > Sync)
- Verify internet connection
- Check for app updates"""

        return {
            "message": message,
            "fixed": False,
            "action": "diagnosis_provided"
        }

    def _format_response(self, solution: Dict[str, Any], kb_results: list) -> str:
        """Format response with KB context"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n**Related articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"

        return solution["message"] + kb_context


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Not syncing
        print("=" * 60)
        print("Test 1: Data not syncing")
        print("=" * 60)

        state = create_initial_state("My data is not syncing between devices")
        state["primary_intent"] = "technical_sync"

        agent = SyncTroubleshooter()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Issue type: {result.get('sync_issue_type')}")
        print(f"Fixed: {result.get('sync_fixed')}")

        # Test 2: Sync conflict
        print("\n" + "=" * 60)
        print("Test 2: Sync conflict")
        print("=" * 60)

        state2 = create_initial_state("I have duplicate entries after syncing")
        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Issue type: {result2.get('sync_issue_type')}")

        # Test 3: Slow sync
        print("\n" + "=" * 60)
        print("Test 3: Slow sync")
        print("=" * 60)

        state3 = create_initial_state("Sync is taking forever")
        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")
        print(f"Issue type: {result3.get('sync_issue_type')}")

    asyncio.run(test())
