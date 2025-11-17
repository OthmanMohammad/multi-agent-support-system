"""
Performance Optimizer Agent - Fixes slow performance issues.

Specialist for performance optimization, cache clearing, query optimization.
"""

from typing import Dict, Any, List

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("performance_optimizer", tier="essential", category="technical")
class PerformanceOptimizer(BaseAgent):
    """
    Performance Optimizer Agent - Specialist for performance issues.

    Handles:
    - Slow load times
    - Lag and freezing
    - Timeout issues
    - Cache optimization
    - Browser performance tuning
    """

    def __init__(self):
        config = AgentConfig(
            name="performance_optimizer",
            type=AgentType.SPECIALIST,
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
        """Process performance optimization requests"""
        self.logger.info("performance_optimizer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "performance_optimization_started",
            message_preview=message[:100],
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Detect performance issue type
        performance_issue = self._detect_performance_issue(message)

        self.logger.info(
            "performance_issue_detected",
            issue_type=performance_issue
        )

        # Diagnose performance bottleneck
        diagnosis = self._diagnose_performance(performance_issue, customer_context)

        self.logger.info(
            "performance_diagnosis_completed",
            primary_bottleneck=diagnosis["primary_bottleneck"],
            severity=diagnosis["severity"],
            bottleneck_count=len(diagnosis["all_bottlenecks"])
        )

        # Get optimization steps
        optimization = self._get_optimization_steps(diagnosis)

        # Search KB for performance tips
        kb_results = await self.search_knowledge_base(
            message,
            category="technical",
            limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "performance_kb_articles_found",
                count=len(kb_results)
            )

        response = self._format_response(optimization, kb_results)

        state["agent_response"] = response
        state["performance_issue"] = performance_issue
        state["performance_diagnosis"] = diagnosis
        state["performance_tips_provided"] = True
        state["response_confidence"] = 0.8
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "performance_optimization_completed",
            response_length=len(response),
            status="resolved"
        )

        return state

    def _detect_performance_issue(self, message: str) -> str:
        """Detect the type of performance issue"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["slow", "loading", "takes forever", "long time"]):
            return "slow_load"
        elif any(word in message_lower for word in ["lag", "laggy", "freeze", "freezing", "stuck"]):
            return "lag"
        elif any(word in message_lower for word in ["timeout", "timed out", "not responding"]):
            return "timeout"
        else:
            return "general_slowness"

    def _diagnose_performance(self, issue_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnose performance bottleneck"""
        browser = context.get("browser", "unknown")
        data_size_mb = context.get("data_size_mb", 0)
        active_projects = context.get("active_projects", 1)
        account_age_days = context.get("account_age_days", 0)
        plan = context.get("plan", "free")

        self.logger.debug(
            "diagnosing_performance",
            browser=browser,
            data_size=data_size_mb,
            projects=active_projects
        )

        bottlenecks = []

        # Check for data size issues
        if data_size_mb > 100:
            bottlenecks.append("large_data")
            self.logger.info("large_data_bottleneck_detected", size_mb=data_size_mb)

        # Check for too many projects
        if active_projects > 10:
            bottlenecks.append("too_many_projects")
            self.logger.info("too_many_projects_detected", count=active_projects)

        # Check for unsupported browser
        if browser.lower() in ["ie", "internet explorer"]:
            bottlenecks.append("unsupported_browser")
            self.logger.warning("unsupported_browser_detected", browser=browser)

        # Check for old account with accumulated data
        if account_age_days > 365 and data_size_mb > 50:
            bottlenecks.append("accumulated_data")

        # Check for free plan limitations
        if plan == "free" and data_size_mb > 50:
            bottlenecks.append("plan_limitations")

        # Determine severity
        severity = "high" if len(bottlenecks) >= 2 else "medium" if bottlenecks else "low"

        return {
            "primary_bottleneck": bottlenecks[0] if bottlenecks else "unknown",
            "all_bottlenecks": bottlenecks,
            "severity": severity,
            "browser": browser,
            "data_size_mb": data_size_mb,
            "active_projects": active_projects
        }

    def _get_optimization_steps(self, diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization recommendations"""
        bottleneck = diagnosis["primary_bottleneck"]

        if bottleneck == "large_data":
            message = f"""Your account has a lot of data ({diagnosis['data_size_mb']}+ MB), which can slow things down.

**Speed it up:**
1. **Archive old projects** (Settings > Projects > Archive)
2. **Delete unused attachments** (Settings > Storage > Clean Up)
3. **Enable lazy loading** (Settings > Performance > Lazy Load)
4. **Clear browser cache** (Ctrl+Shift+Delete)

**Expected improvement:** 50-70% faster load times

**Advanced optimizations:**
- Use search instead of browsing all data
- Filter by date to view recent items only
- Export and archive completed work

Try archiving old projects first - this usually makes the biggest difference!"""

            return {
                "message": message,
                "expected_improvement": "50-70%",
                "primary_action": "archive_old_projects"
            }

        elif bottleneck == "too_many_projects":
            message = f"""You have {diagnosis['active_projects']}+ active projects, which impacts performance.

**Optimization tips:**
1. **Close inactive projects** (Right-click > Close)
2. **Archive completed projects** (Settings > Projects > Archive)
3. **Use project folders** to organize (creates hierarchy)
4. **Enable "load on demand"** (Settings > Performance)

**Expected improvement:** 40-60% faster

**Pro tip:** Keep only 3-5 active projects open at a time for best performance.

Would you like me to show you how to archive projects?"""

            return {
                "message": message,
                "expected_improvement": "40-60%",
                "primary_action": "reduce_active_projects"
            }

        elif bottleneck == "unsupported_browser":
            message = f"""Internet Explorer is no longer supported and causes severe performance issues.

**Switch to a modern browser:**
- **Chrome** (recommended) - https://www.google.com/chrome/
- **Firefox** - https://www.mozilla.org/firefox/
- **Edge** - https://www.microsoft.com/edge/
- **Safari** (Mac only)

**Performance will improve 10x with a modern browser!**

Modern browsers have:
- Much faster JavaScript execution
- Better memory management
- Hardware acceleration
- Security updates

After switching, you'll notice:
- Pages load 5-10x faster
- No freezing or lag
- Smooth animations
- All features work properly"""

            return {
                "message": message,
                "expected_improvement": "90%+",
                "primary_action": "upgrade_browser"
            }

        elif bottleneck == "accumulated_data":
            message = """Your account has accumulated a lot of data over time.

**Spring cleaning for performance:**
1. **Archive old projects** (older than 6 months)
2. **Delete old attachments** (Settings > Storage)
3. **Clear completed tasks** (bulk select & archive)
4. **Export historical data** (for records)

**Expected improvement:** 60-80% faster

**Maintenance schedule:**
- Weekly: Clear completed tasks
- Monthly: Archive old projects
- Quarterly: Clean up attachments

This keeps your account fast and organized!"""

            return {
                "message": message,
                "expected_improvement": "60-80%",
                "primary_action": "spring_cleaning"
            }

        elif bottleneck == "plan_limitations":
            message = """Your account is on the free plan with significant data, which may cause slowness.

**Options to improve performance:**

1. **Free optimizations:**
   - Archive old data
   - Delete unused files
   - Use selective loading

2. **Upgrade to Premium:**
   - Priority performance
   - Unlimited data
   - Advanced caching
   - 2x faster sync
   - Dedicated resources

**Expected improvement:**
- Free optimizations: 30-40% faster
- Premium upgrade: 70-90% faster

Would you like to see Premium pricing?"""

            return {
                "message": message,
                "expected_improvement": "30-90%",
                "primary_action": "optimize_or_upgrade"
            }

        else:
            # General performance tips
            message = """Let's optimize your performance:

**Quick wins:**
1. **Clear browser cache** (Ctrl+Shift+Del)
2. **Disable unused browser extensions**
3. **Close unnecessary tabs**
4. **Check internet speed** (need 5+ Mbps)
5. **Restart browser**

**Advanced optimizations:**
- Use desktop app (faster than web)
- Enable hardware acceleration (browser settings)
- Reduce animations (Settings > Preferences > Reduce Motion)
- Use "compact view" for lists

**Browser-specific:**
- Chrome: Check Task Manager (Shift+Esc) for memory hogs
- Firefox: Try "Refresh Firefox"
- Safari: Empty caches more frequently

Try the quick wins first and let me know if it helps!"""

            return {
                "message": message,
                "expected_improvement": "20-40%",
                "primary_action": "general_optimization"
            }

    def _format_response(self, optimization: Dict[str, Any], kb_results: list) -> str:
        """Format response with KB context"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n**Related articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"

        return optimization["message"] + kb_context


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Slow loading
        print("=" * 60)
        print("Test 1: Slow loading with large data")
        print("=" * 60)

        state = create_initial_state("The app is really slow to load")
        state["customer_metadata"] = {
            "browser": "Chrome",
            "data_size_mb": 150,
            "active_projects": 5,
            "plan": "premium"
        }

        agent = PerformanceOptimizer()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Issue: {result.get('performance_issue')}")
        print(f"Diagnosis: {result.get('performance_diagnosis')}")

        # Test 2: Too many projects
        print("\n" + "=" * 60)
        print("Test 2: Too many active projects")
        print("=" * 60)

        state2 = create_initial_state("Everything is lagging")
        state2["customer_metadata"] = {
            "browser": "Firefox",
            "data_size_mb": 50,
            "active_projects": 15,
            "plan": "free"
        }

        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Diagnosis: {result2.get('performance_diagnosis')}")

        # Test 3: Unsupported browser
        print("\n" + "=" * 60)
        print("Test 3: Unsupported browser")
        print("=" * 60)

        state3 = create_initial_state("App keeps freezing")
        state3["customer_metadata"] = {
            "browser": "IE",
            "data_size_mb": 20,
            "active_projects": 2,
            "plan": "free"
        }

        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")

    asyncio.run(test())
