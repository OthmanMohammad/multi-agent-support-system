"""
Browser Compatibility Specialist Agent - Fixes browser-specific issues.

Specialist for browser compatibility, version checking, browser recommendations.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("browser_compatibility_specialist", tier="essential", category="technical")
class BrowserCompatibilitySpecialist(BaseAgent):
    """
    Browser Compatibility Specialist Agent - Specialist for browser issues.

    Handles:
    - Browser compatibility checking
    - Version verification
    - Browser-specific bug fixes
    - Browser upgrade recommendations
    - Feature compatibility
    """

    SUPPORTED_BROWSERS = {
        "Chrome": {
            "min_version": 90,
            "recommended": True,
            "download_url": "https://www.google.com/chrome/",
        },
        "Firefox": {
            "min_version": 88,
            "recommended": True,
            "download_url": "https://www.mozilla.org/firefox/",
        },
        "Safari": {
            "min_version": 14,
            "recommended": True,
            "download_url": "https://www.apple.com/safari/",
        },
        "Edge": {
            "min_version": 90,
            "recommended": True,
            "download_url": "https://www.microsoft.com/edge/",
        },
        "IE": {"min_version": 0, "recommended": False, "deprecated": True, "download_url": None},
    }

    def __init__(self):
        config = AgentConfig(
            name="browser_compatibility_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="technical",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process browser compatibility requests"""
        self.logger.info("browser_compatibility_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        # Extract browser info
        browser = customer_context.get("browser", self._detect_browser(message))
        browser_version = customer_context.get("browser_version", 0)

        self.logger.debug(
            "browser_compatibility_check_started",
            message_preview=message[:100],
            browser=browser,
            browser_version=browser_version,
            turn_count=state["turn_count"],
        )

        # Check browser compatibility
        compatibility = self._check_compatibility(browser, browser_version)

        self.logger.info(
            "compatibility_checked",
            browser=browser,
            supported=compatibility["supported"],
            needs_update=compatibility.get("needs_update", False),
        )

        # Generate appropriate response
        if not compatibility["supported"] and compatibility.get("needs_update"):
            # Outdated version of supported browser
            response = self._recommend_version_upgrade(browser, browser_version, compatibility)
        elif not compatibility["supported"]:
            # Unsupported/deprecated browser
            response = self._recommend_browser_upgrade(browser, browser_version, compatibility)
        else:
            # Browser is compatible - check for known issues
            response = await self._check_browser_specific_issues(browser, message)

        # Search KB for browser help
        kb_results = await self.search_knowledge_base(
            f"{browser} {message}", category="technical", limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("browser_kb_articles_found", count=len(kb_results))

        formatted_response = self._format_response(response, kb_results)

        state["agent_response"] = formatted_response
        state["browser"] = browser
        state["browser_version"] = browser_version
        state["browser_supported"] = compatibility["supported"]
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "browser_compatibility_resolved",
            browser=browser,
            supported=compatibility["supported"],
            status="resolved",
        )

        return state

    def _detect_browser(self, message: str) -> str:
        """Detect browser from message"""
        message_lower = message.lower()

        if "chrome" in message_lower:
            return "Chrome"
        elif "firefox" in message_lower:
            return "Firefox"
        elif "safari" in message_lower:
            return "Safari"
        elif "edge" in message_lower:
            return "Edge"
        elif any(word in message_lower for word in ["ie", "internet explorer"]):
            return "IE"

        return "unknown"

    def _check_compatibility(self, browser: str, version: int) -> dict[str, Any]:
        """Check if browser is supported"""
        # Normalize browser name
        browser_key = None
        for key in self.SUPPORTED_BROWSERS:
            if key.lower() == browser.lower() or browser.lower() in key.lower():
                browser_key = key
                break

        if not browser_key:
            browser_key = browser

        browser_info = self.SUPPORTED_BROWSERS.get(browser_key, {})

        self.logger.debug(
            "checking_browser_compatibility",
            browser=browser_key,
            version=version,
            min_version=browser_info.get("min_version", 0),
        )

        if browser_info.get("deprecated"):
            self.logger.warning("deprecated_browser_detected", browser=browser_key)
            return {
                "supported": False,
                "reason": "deprecated",
                "needs_update": False,
                "browser_info": browser_info,
            }

        min_version = browser_info.get("min_version", 0)

        if version and version < min_version:
            self.logger.info(
                "outdated_browser_version_detected",
                browser=browser_key,
                version=version,
                min_version=min_version,
            )
            return {
                "supported": False,
                "reason": "outdated_version",
                "needs_update": True,
                "min_version": min_version,
                "browser_info": browser_info,
            }

        return {"supported": True, "needs_update": False, "browser_info": browser_info}

    def _recommend_browser_upgrade(
        self, browser: str, version: int, compatibility: dict[str, Any]
    ) -> dict[str, str]:
        """Recommend switching browsers"""
        if compatibility["reason"] == "deprecated":
            message = f"""**{browser} is no longer supported.**

Our app requires a modern browser for best performance and security.

**Recommended browsers (free):**

✓ **Chrome** (Recommended)
  - Fast and reliable
  - Best compatibility
  - Download: https://www.google.com/chrome/

✓ **Firefox**
  - Privacy-focused
  - Great performance
  - Download: https://www.mozilla.org/firefox/

✓ **Edge** (Windows)
  - Built into Windows 10/11
  - Chromium-based
  - Download: https://www.microsoft.com/edge/

✓ **Safari** (Mac only)
  - Best for Mac users
  - Built into macOS

**Benefits of upgrading:**
- 10x faster performance
- Better security and privacy
- Access to all features
- Regular updates and bug fixes
- Modern web standards support

**After installing a new browser:**
1. Open the new browser
2. Log in to your account
3. Try again - the issue should be resolved!

**Need help choosing?**
- Most users: Chrome
- Privacy-focused: Firefox
- Windows users: Edge
- Mac users: Safari

The switch takes just 2 minutes and you'll have a much better experience!"""

            return {"message": message, "action": "recommend_upgrade"}

        else:
            message = "Please use a supported browser for the best experience."
            return {"message": message, "action": "recommend_upgrade"}

    def _recommend_version_upgrade(
        self, browser: str, version: int, compatibility: dict[str, Any]
    ) -> dict[str, str]:
        """Recommend updating browser version"""
        min_version = compatibility.get("min_version", 0)

        message = f"""Your {browser} version ({version}) is outdated.

**Minimum required version:** {min_version}
**Your version:** {version}

**How to update {browser}:**

1. Open {browser}
2. Click menu (⋮ or ☰ in top-right)
3. Go to **Help** > **About {browser}**
4. It will check for updates automatically
5. Click **Update** if available
6. Restart {browser} when prompted

**Alternative method:**
Download the latest version from:
{compatibility["browser_info"].get("download_url", "the official website")}

**After updating:**
1. Restart your browser
2. Clear cache (Ctrl+Shift+Delete)
3. Try again - your issue should be resolved!

**Why update?**
- Security fixes
- Performance improvements
- Bug fixes
- New features
- Better compatibility

Updating usually takes 2-5 minutes and fixes most compatibility issues!"""

        return {"message": message, "action": "recommend_update"}

    async def _check_browser_specific_issues(self, browser: str, message: str) -> dict[str, str]:
        """Check for known browser-specific issues"""
        message_lower = message.lower()

        # Browser-specific known issues
        known_issues = {
            "Safari": {
                "cookies": {
                    "keywords": ["cookie", "cookies", "login", "session"],
                    "solution": """**Safari strict cookie policy detected.**

Safari blocks third-party cookies by default, which can cause issues.

**How to fix:**
1. Open Safari > Preferences
2. Go to **Privacy** tab
3. Under "Cookies and website data":
   - Uncheck "Prevent cross-site tracking" (for our site)
   - OR Add our site to exceptions

**Alternative:**
- Use Safari > Develop > Disable Cross-Origin Restrictions
- (For testing only)

This should fix login and session issues!""",
                },
                "cache": {
                    "keywords": ["cache", "old", "refresh", "update"],
                    "solution": """**Safari aggressive caching issue.**

Safari caches pages aggressively, which can show outdated content.

**How to fix:**
1. **Hard refresh:** Cmd+Shift+R
2. **Clear cache:** Safari > Preferences > Privacy > Manage Website Data
3. **Disable cache:** Develop menu > Disable Caches

**Prevent future issues:**
- Enable "Show Develop menu" in Safari > Preferences > Advanced
- Use hard refresh when you see stale content

Try hard refresh first - it usually works!""",
                },
            },
            "Firefox": {
                "tracking": {
                    "keywords": ["blocked", "tracking", "privacy", "shield"],
                    "solution": """**Firefox tracking protection blocking features.**

Firefox's Enhanced Tracking Protection may block some features.

**How to fix:**
1. Click the **shield icon** in address bar
2. Toggle off "Enhanced Tracking Protection"
3. Refresh the page

**Alternative:**
- Add our site to exceptions
- Firefox Options > Privacy > Manage Exceptions

**Note:** This only affects our site, keeping protection on elsewhere.

Try this and let me know if it helps!""",
                },
                "extensions": {
                    "keywords": ["extension", "addon", "blocked"],
                    "solution": """**Firefox extension interference detected.**

Privacy extensions may interfere with features.

**How to diagnose:**
1. Try **Private Window** (Ctrl+Shift+P)
2. Extensions are disabled by default in private windows
3. If it works, an extension is the culprit

**How to fix:**
1. Firefox > Add-ons
2. Disable extensions one by one
3. Common culprits: Privacy Badger, uBlock Origin, NoScript

**Alternative:**
Add our site to extension whitelists

Let me know if private window works!""",
                },
            },
            "Chrome": {
                "memory": {
                    "keywords": ["slow", "freeze", "lag", "memory", "ram"],
                    "solution": """**Chrome high memory usage detected.**

Chrome can use a lot of RAM with many tabs.

**Quick fixes:**
1. Close unused tabs
2. Use Chrome Task Manager (Shift+Esc)
3. Find and close memory-hogging tabs/extensions
4. Restart Chrome

**Long-term solutions:**
- Use "The Great Suspender" extension
- Enable "Memory Saver" (Chrome settings)
- Disable unused extensions
- Use tab groups to organize

**Check memory:**
Chrome Menu > More Tools > Task Manager

Try closing unused tabs first!""",
                },
                "extensions": {
                    "keywords": ["extension", "blocked", "not working"],
                    "solution": """**Chrome extension conflict detected.**

Extensions may interfere with features.

**How to diagnose:**
1. Try **Incognito mode** (Ctrl+Shift+N)
2. Extensions are disabled in incognito
3. If it works, an extension is causing the issue

**How to fix:**
1. Chrome > Extensions
2. Disable extensions one by one
3. Common culprits: Ad blockers, Privacy tools

**Alternative:**
Allow extensions in incognito to test specific ones

Let me know if incognito mode works!""",
                },
            },
            "Edge": {
                "compatibility": {
                    "keywords": ["not working", "broken", "issue"],
                    "solution": """**Edge compatibility mode detected.**

Edge may be running in IE compatibility mode.

**How to fix:**
1. Click **⋯** menu
2. Go to Settings > Default browser
3. Under "Internet Explorer compatibility":
   - Remove our site from the list
4. Refresh the page

**Alternative:**
- Use Edge (Chromium) not IE mode
- Update to latest Edge version

Try this and refresh!""",
                }
            },
        }

        browser_issues = known_issues.get(browser, {})

        # Check for keyword matches
        for issue_type, issue_data in browser_issues.items():
            keywords = issue_data.get("keywords", [])
            if any(keyword in message_lower for keyword in keywords):
                self.logger.info(
                    "browser_specific_issue_detected", browser=browser, issue_type=issue_type
                )
                return {
                    "message": issue_data["solution"],
                    "action": f"browser_specific_fix_{issue_type}",
                }

        # No specific issue found - provide general troubleshooting
        message = f"""Your {browser} browser is up to date. Let me help troubleshoot the specific issue.

**Common {browser} fixes:**

1. **Clear cache and cookies**
   - Settings > Privacy > Clear browsing data
   - Select "Cached images" and "Cookies"
   - Time range: All time

2. **Disable extensions**
   - Try incognito/private mode
   - Extensions often cause conflicts

3. **Update {browser}**
   - Help > About {browser}
   - Install any pending updates

4. **Reset {browser} settings**
   - Settings > Advanced > Reset settings
   - (Only if other fixes don't work)

**Browser-specific tips:**

"""

        # Add browser-specific tips
        if browser == "Chrome":
            message += """- Check Chrome Task Manager (Shift+Esc) for issues
- Try disabling hardware acceleration
- Enable Memory Saver mode"""
        elif browser == "Firefox":
            message += """- Try "Refresh Firefox" (keeps bookmarks/passwords)
- Disable Enhanced Tracking Protection for our site
- Check about:config for custom settings"""
        elif browser == "Safari":
            message += """- Empty caches more frequently
- Check Privacy settings
- Try hard refresh (Cmd+Shift+R)"""
        elif browser == "Edge":
            message += """- Make sure you're not in IE mode
- Clear Edge cached data
- Try disabling tracking prevention"""

        message += "\n\nCan you describe the specific issue you're experiencing in more detail?"

        return {"message": message, "action": "general_browser_troubleshooting"}

    def _format_response(self, response: dict[str, str], kb_results: list) -> str:
        """Format response with KB context"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n**Related help articles:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"

        return response["message"] + kb_context


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Deprecated browser (IE)
        print("=" * 60)
        print("Test 1: Deprecated browser (IE)")
        print("=" * 60)

        state = create_initial_state("Features not working in IE")
        state["customer_metadata"] = {"browser": "IE", "browser_version": 11}

        agent = BrowserCompatibilitySpecialist()
        result = await agent.process(state)

        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Browser supported: {result.get('browser_supported')}")

        # Test 2: Outdated version
        print("\n" + "=" * 60)
        print("Test 2: Outdated Chrome version")
        print("=" * 60)

        state2 = create_initial_state("App is slow in Chrome")
        state2["customer_metadata"] = {
            "browser": "Chrome",
            "browser_version": 80,  # Below min 90
        }

        result2 = await agent.process(state2)

        print(f"\nResponse:\n{result2['agent_response']}")
        print(f"Browser supported: {result2.get('browser_supported')}")

        # Test 3: Safari cookie issue
        print("\n" + "=" * 60)
        print("Test 3: Safari cookie issue")
        print("=" * 60)

        state3 = create_initial_state("Can't stay logged in Safari, cookies not working")
        state3["customer_metadata"] = {"browser": "Safari", "browser_version": 15}

        result3 = await agent.process(state3)

        print(f"\nResponse:\n{result3['agent_response']}")

    asyncio.run(test())
