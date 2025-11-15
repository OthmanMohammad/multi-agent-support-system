"""
Unit tests for Browser Compatibility Specialist agent.
"""

import pytest
from src.agents.essential.support.technical.browser_compatibility_specialist import BrowserCompatibilitySpecialist
from src.workflow.state import create_initial_state


class TestBrowserCompatibilitySpecialist:
    """Test suite for Browser Compatibility Specialist agent"""

    @pytest.fixture
    def browser_specialist(self):
        """Browser Compatibility Specialist instance"""
        return BrowserCompatibilitySpecialist()

    def test_initialization(self, browser_specialist):
        """Test Browser Compatibility Specialist initializes correctly"""
        assert browser_specialist.config.name == "browser_compatibility_specialist"
        assert browser_specialist.config.type.value == "specialist"
        assert browser_specialist.config.tier == "essential"

    def test_supported_browsers_defined(self, browser_specialist):
        """Test that supported browsers are properly defined"""
        assert "Chrome" in browser_specialist.SUPPORTED_BROWSERS
        assert "Firefox" in browser_specialist.SUPPORTED_BROWSERS
        assert "Safari" in browser_specialist.SUPPORTED_BROWSERS
        assert "Edge" in browser_specialist.SUPPORTED_BROWSERS
        assert "IE" in browser_specialist.SUPPORTED_BROWSERS

        # Check IE is marked as deprecated
        assert browser_specialist.SUPPORTED_BROWSERS["IE"]["deprecated"] is True

    @pytest.mark.asyncio
    async def test_deprecated_browser_detection(self, browser_specialist):
        """Test detection of deprecated browser (IE)"""
        state = create_initial_state("Features not working")
        state["customer_metadata"] = {
            "browser": "IE",
            "browser_version": 11
        }

        result = await browser_specialist.process(state)

        assert result["browser_supported"] is False
        assert "no longer supported" in result["agent_response"].lower()
        assert "chrome" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_outdated_version_detection(self, browser_specialist):
        """Test detection of outdated browser version"""
        state = create_initial_state("App is slow")
        state["customer_metadata"] = {
            "browser": "Chrome",
            "browser_version": 80  # Below min 90
        }

        result = await browser_specialist.process(state)

        assert result["browser_supported"] is False
        assert "outdated" in result["agent_response"].lower() or "update" in result["agent_response"].lower()
        assert "90" in result["agent_response"]  # Mentions minimum version

    @pytest.mark.asyncio
    async def test_supported_browser_checks_known_issues(self, browser_specialist):
        """Test that supported browser checks for known issues"""
        state = create_initial_state("Cookies not working in Safari")
        state["customer_metadata"] = {
            "browser": "Safari",
            "browser_version": 15
        }

        result = await browser_specialist.process(state)

        assert result["browser_supported"] is True
        # Should check for Safari-specific cookie issues

    def test_check_compatibility(self, browser_specialist):
        """Test browser compatibility checking"""
        # Supported browser
        compat = browser_specialist._check_compatibility("Chrome", 120)
        assert compat["supported"] is True
        assert compat["needs_update"] is False

        # Outdated version
        compat = browser_specialist._check_compatibility("Chrome", 80)
        assert compat["supported"] is False
        assert compat["needs_update"] is True

        # Deprecated browser
        compat = browser_specialist._check_compatibility("IE", 11)
        assert compat["supported"] is False
        assert compat["reason"] == "deprecated"

    def test_detect_browser_from_message(self, browser_specialist):
        """Test browser detection from message"""
        assert browser_specialist._detect_browser("Using Chrome here") == "Chrome"
        assert browser_specialist._detect_browser("Issue in Firefox") == "Firefox"
        assert browser_specialist._detect_browser("Safari cookies problem") == "Safari"
        assert browser_specialist._detect_browser("Edge not working") == "Edge"
        assert browser_specialist._detect_browser("IE compatibility") == "IE"
        assert browser_specialist._detect_browser("Something else") == "unknown"

    def test_recommend_browser_upgrade_for_ie(self, browser_specialist):
        """Test browser upgrade recommendation for IE"""
        compatibility = {
            "reason": "deprecated",
            "browser_info": browser_specialist.SUPPORTED_BROWSERS["IE"]
        }

        result = browser_specialist._recommend_browser_upgrade("IE", 11, compatibility)

        assert "chrome" in result["message"].lower()
        assert "firefox" in result["message"].lower()
        assert "10x" in result["message"].lower()
        assert result["action"] == "recommend_upgrade"

    def test_recommend_version_upgrade(self, browser_specialist):
        """Test version upgrade recommendation"""
        compatibility = {
            "min_version": 90,
            "browser_info": browser_specialist.SUPPORTED_BROWSERS["Chrome"]
        }

        result = browser_specialist._recommend_version_upgrade("Chrome", 80, compatibility)

        assert "90" in result["message"]  # Minimum version
        assert "80" in result["message"]  # Current version
        assert "update" in result["message"].lower()
        assert result["action"] == "recommend_update"

    @pytest.mark.asyncio
    async def test_safari_cookie_issue_detection(self, browser_specialist):
        """Test detection of Safari-specific cookie issue"""
        response = await browser_specialist._check_browser_specific_issues(
            "Safari",
            "Cookies are blocked, can't login"
        )

        assert "cookie" in response["message"].lower()
        assert "safari" in response["message"].lower()
        assert "privacy" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_chrome_extension_issue_detection(self, browser_specialist):
        """Test detection of Chrome extension conflict"""
        response = await browser_specialist._check_browser_specific_issues(
            "Chrome",
            "Features are blocked by extension"
        )

        assert "extension" in response["message"].lower()
        assert "incognito" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_firefox_tracking_protection_issue(self, browser_specialist):
        """Test detection of Firefox tracking protection issue"""
        response = await browser_specialist._check_browser_specific_issues(
            "Firefox",
            "Content is blocked by tracking protection"
        )

        assert "tracking" in response["message"].lower()
        assert "shield" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_chrome_memory_issue_detection(self, browser_specialist):
        """Test detection of Chrome memory issue"""
        response = await browser_specialist._check_browser_specific_issues(
            "Chrome",
            "Chrome is slow and using lots of memory"
        )

        assert "memory" in response["message"].lower()
        assert "task manager" in response["message"].lower()
