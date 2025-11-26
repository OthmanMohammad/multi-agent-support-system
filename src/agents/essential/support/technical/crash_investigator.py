"""
Crash Investigator Agent - Investigates app crashes, collects logs, browser info.

Specialist for crash investigation, log analysis, and bug ticket creation.
"""

import random
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("crash_investigator", tier="essential", category="technical")
class CrashInvestigator(BaseAgent):
    """
    Crash Investigator Agent - Specialist for crash investigation.

    Handles:
    - App crash investigation
    - Log collection and analysis
    - Browser compatibility issues
    - Bug ticket creation
    - Known issue detection
    """

    def __init__(self):
        config = AgentConfig(
            name="crash_investigator",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="technical",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process crash investigation requests"""
        self.logger.info("crash_investigator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        crash_data = state.get("crash_data", {})

        self.logger.debug(
            "crash_investigation_started",
            message_preview=message[:100],
            has_crash_data=bool(crash_data),
            turn_count=state["turn_count"],
        )

        # Check if we have crash logs collected
        if not state.get("crash_logs_collected"):
            response = self._request_crash_info()
            state["agent_response"] = response
            state["crash_logs_collected"] = False
            state["awaiting_logs"] = True
            state["response_confidence"] = 0.5
            state["next_agent"] = None
            state["status"] = "pending_info"

            self.logger.info("crash_info_requested", status="awaiting_logs")
        else:
            # Analyze crash
            analysis = self._analyze_crash(crash_data)

            self.logger.info(
                "crash_analysis_completed",
                crash_type=analysis["type"],
                severity=analysis["severity"],
            )

            # Create bug ticket if needed
            ticket = None
            if analysis["type"] != "known_issue":
                ticket = self._create_bug_ticket(analysis, state.get("customer_metadata", {}))

                self.logger.info(
                    "bug_ticket_created", ticket_id=ticket["id"], severity=ticket["severity"]
                )

            # Search KB for crash solutions
            kb_results = await self.search_knowledge_base(message, category="technical", limit=2)
            state["kb_results"] = kb_results

            if kb_results:
                self.logger.info("crash_kb_articles_found", count=len(kb_results))

            response = self._format_response(analysis, ticket, kb_results)

            state["agent_response"] = response
            state["crash_logs_collected"] = True
            state["crash_analysis"] = analysis
            if ticket:
                state["bug_ticket_created"] = ticket["id"]
            state["response_confidence"] = 0.85
            state["next_agent"] = None
            state["status"] = "resolved"

            self.logger.info(
                "crash_investigation_completed", response_length=len(response), status="resolved"
            )

        return state

    def _request_crash_info(self) -> str:
        """Request crash information from customer"""
        return """I'm sorry you're experiencing crashes. To investigate, I need some information:

**Please provide:**
1. What were you doing when it crashed?
2. Does it crash every time, or randomly?
3. Error message (if any)
4. Your browser: Chrome/Firefox/Safari/Edge
5. Browser version: (Help > About)

**Optional but helpful:**
- Screenshot of error
- Browser console logs (F12 > Console tab)

Once I have this info, I can investigate and likely fix the issue quickly."""

    def _analyze_crash(self, crash_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze crash data"""
        error_msg = crash_data.get("error_message", "")
        browser = crash_data.get("browser", "unknown")
        browser_version = crash_data.get("browser_version", "unknown")
        crash_data.get("reproduction_steps", "")

        self.logger.debug(
            "analyzing_crash_data",
            browser=browser,
            browser_version=browser_version,
            has_error=bool(error_msg),
        )

        # Check for known issues
        known_issue = self._check_known_issues(error_msg, browser)

        if known_issue:
            self.logger.info("known_issue_detected", solution=known_issue["solution"])
            return {
                "type": "known_issue",
                "severity": "medium",
                "solution": known_issue["solution"],
                "workaround": known_issue["workaround"],
                "browser": browser,
            }

        # Check for browser-specific issues
        if "memory" in error_msg.lower() or "heap" in error_msg.lower():
            return {
                "type": "memory_leak",
                "severity": "high",
                "solution": "Memory issue detected - clear browser cache and cookies",
                "workaround": "Use incognito mode temporarily",
                "browser": browser,
            }

        if "script" in error_msg.lower() and "timeout" in error_msg.lower():
            return {
                "type": "script_timeout",
                "severity": "medium",
                "solution": "Script execution timeout - likely due to slow connection or large data",
                "workaround": "Refresh the page and try again",
                "browser": browser,
            }

        # Unknown crash - needs engineering
        return {
            "type": "unknown",
            "severity": "high",
            "solution": "Escalating to engineering team",
            "workaround": None,
            "browser": browser,
        }

    def _check_known_issues(self, error_msg: str, browser: str) -> dict[str, str] | None:
        """Check against known crash patterns"""
        known_issues = {
            "TypeError: Cannot read": {
                "solution": "This is a known issue in v2.5.1, fixed in v2.5.2",
                "workaround": "Refresh the page or clear cache",
            },
            "RangeError: Maximum call": {
                "solution": "Stack overflow - likely infinite loop in custom script",
                "workaround": "Disable custom scripts temporarily",
            },
            "QuotaExceededError": {
                "solution": "Local storage quota exceeded",
                "workaround": "Clear browser data or use incognito mode",
            },
            "NetworkError": {
                "solution": "Network connectivity issue or CORS error",
                "workaround": "Check internet connection and try again",
            },
        }

        for pattern, issue in known_issues.items():
            if pattern in error_msg:
                self.logger.debug("known_issue_pattern_matched", pattern=pattern)
                return issue

        return None

    def _create_bug_ticket(
        self, analysis: dict[str, Any], customer_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Create bug ticket in issue tracker"""
        # In production: Call Jira/Linear/GitHub API
        ticket_id = f"BUG-{random.randint(1000, 9999)}"

        self.logger.info(
            "creating_bug_ticket",
            ticket_id=ticket_id,
            crash_type=analysis["type"],
            severity=analysis["severity"],
        )

        return {
            "id": ticket_id,
            "title": f"Crash: {analysis['type']}",
            "severity": analysis["severity"],
            "customer_id": customer_context.get("customer_id"),
            "browser": analysis.get("browser", "unknown"),
            "url": f"https://issues.example.com/{ticket_id}",
        }

    def _format_response(
        self, analysis: dict[str, Any], ticket: dict[str, Any] | None, kb_results: list
    ) -> str:
        """Format response to customer"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n**Related articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"

        if analysis["type"] == "known_issue":
            return f"""Good news! This is a known issue we've already fixed.

**Solution:** {analysis["solution"]}

**Quick fix:** {analysis["workaround"]}

Try this and let me know if the crash still happens!{kb_context}"""

        elif analysis["type"] == "memory_leak":
            return f"""I've identified the issue - it's a memory problem in {analysis["browser"]}.

**Solution:** {analysis["solution"]}

**Steps to fix:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Clear cookies
3. Restart browser
4. Try again

**Temporary workaround:** {analysis["workaround"]}

This should resolve the crashes. Let me know if you need more help!{kb_context}"""

        elif analysis["type"] == "script_timeout":
            return f"""I've identified the issue - script execution timeout.

**Solution:** {analysis["solution"]}

**Steps to fix:**
1. Check your internet connection
2. Refresh the page
3. If you have large amounts of data, try filtering to smaller datasets

**Temporary workaround:** {analysis["workaround"]}

Let me know if this helps!{kb_context}"""

        else:
            ticket_info = ""
            if ticket:
                ticket_info = f"""
**Ticket:** {ticket["id"]}
**Severity:** {ticket["severity"].title()}

"""

            workaround_info = ""
            if analysis["workaround"]:
                workaround_info = f"\n**Temporary workaround:** {analysis['workaround']}"

            return f"""I've identified the crash issue and created a bug report for our engineering team.

{ticket_info}{workaround_info}

Our engineering team will investigate within 24 hours for high-severity issues.
I'll keep you updated on the progress.{kb_context}"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Request crash info
        print("=" * 60)
        print("Test 1: Requesting crash information")
        print("=" * 60)

        state = create_initial_state("My app keeps crashing")
        state["primary_intent"] = "technical_crash"

        agent = CrashInvestigator()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Awaiting logs: {result.get('awaiting_logs', False)}")

        # Test 2: Analyze known issue
        print("\n" + "=" * 60)
        print("Test 2: Analyzing known crash")
        print("=" * 60)

        state2 = create_initial_state("TypeError: Cannot read property")
        state2["crash_logs_collected"] = True
        state2["crash_data"] = {
            "error_message": "TypeError: Cannot read property 'value' of null",
            "browser": "Chrome",
            "browser_version": "120",
        }

        result2 = await agent.process(state2)
        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Analysis: {result2.get('crash_analysis', {})}")

    asyncio.run(test())
