"""
Unit tests for OAuth Specialist agent.

Tests OAuth topic detection, error handling, and guidance for
OAuth 2.0 flows, token management, and authentication issues.

Part of: STORY-006 Integration Specialists Sub-Swarm (TASK-602)
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.integration.oauth_specialist import OAuthSpecialist
from src.workflow.state import create_initial_state


@pytest.fixture
def oauth_specialist():
    """Create OAuthSpecialist instance for testing."""
    return OAuthSpecialist()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        context={"customer_metadata": {"plan": "premium"}}
    )


class TestOAuthSpecialistInitialization:
    """Test OAuth Specialist initialization and configuration."""

    def test_initialization(self, oauth_specialist):
        """Test that agent initializes with correct configuration."""
        assert oauth_specialist.config.name == "oauth_specialist"
        assert oauth_specialist.config.type.value == "specialist"
        assert oauth_specialist.config.model == "claude-3-haiku-20240307"
        assert oauth_specialist.config.temperature == 0.3
        assert oauth_specialist.config.tier == "essential"

    def test_has_required_capabilities(self, oauth_specialist):
        """Test that agent has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = oauth_specialist.config.capabilities
        assert AgentCapability.KB_SEARCH in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities


class TestTopicDetection:
    """Test OAuth topic detection."""

    def test_detect_setup_topic(self, oauth_specialist):
        """Test detecting OAuth setup requests."""
        topic = oauth_specialist._detect_oauth_topic("How do I setup OAuth?")
        assert topic == "setup"

    def test_detect_callback_error_topic(self, oauth_specialist):
        """Test detecting callback error requests."""
        topic = oauth_specialist._detect_oauth_topic("Getting redirect_uri error in callback")
        assert topic == "callback_error"

    def test_detect_token_refresh_topic(self, oauth_specialist):
        """Test detecting token refresh requests."""
        topic = oauth_specialist._detect_oauth_topic("How to refresh expired tokens?")
        assert topic == "token_refresh"

    def test_detect_scope_error_topic(self, oauth_specialist):
        """Test detecting scope-related requests."""
        topic = oauth_specialist._detect_oauth_topic("What scopes are available?")
        assert topic == "scope_error"

    def test_detect_pkce_topic(self, oauth_specialist):
        """Test detecting PKCE requests."""
        topic = oauth_specialist._detect_oauth_topic("How do I implement PKCE?")
        assert topic == "pkce"


class TestErrorCodeExtraction:
    """Test OAuth error code extraction."""

    def test_extract_redirect_uri_mismatch(self, oauth_specialist):
        """Test extracting redirect_uri_mismatch error."""
        error = oauth_specialist._extract_error_code("I'm getting redirect_uri_mismatch error")
        assert error == "redirect_uri_mismatch"

    def test_extract_invalid_scope(self, oauth_specialist):
        """Test extracting invalid_scope error."""
        error = oauth_specialist._extract_error_code("Error: invalid scope")
        assert error == "invalid_scope"

    def test_extract_access_denied(self, oauth_specialist):
        """Test extracting access_denied error."""
        error = oauth_specialist._extract_error_code("User access denied")
        assert error == "access_denied"

    def test_extract_invalid_grant(self, oauth_specialist):
        """Test extracting invalid_grant error."""
        error = oauth_specialist._extract_error_code("Getting invalid_grant error")
        assert error == "invalid_grant"

    def test_no_error_code(self, oauth_specialist):
        """Test when no error code present."""
        error = oauth_specialist._extract_error_code("General OAuth question")
        assert error is None


class TestOAuthProcessing:
    """Test OAuth request processing."""

    @pytest.mark.asyncio
    async def test_process_setup_request(self, oauth_specialist):
        """Test processing OAuth setup request."""
        state = create_initial_state("How do I set up OAuth for my app?")

        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert result["oauth_topic"] == "setup"
        assert "agent_response" in result
        assert "client_id" in result["agent_response"].lower() or "oauth" in result["agent_response"].lower()
        assert result["status"] == "resolved"
        assert result["next_agent"] is None

    @pytest.mark.asyncio
    async def test_process_token_refresh_request(self, oauth_specialist):
        """Test processing token refresh request."""
        state = create_initial_state("My access token expired, how do I refresh it?")

        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert result["oauth_topic"] == "token_refresh"
        assert "refresh" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_callback_error(self, oauth_specialist):
        """Test processing callback error."""
        state = create_initial_state("I'm getting redirect_uri_mismatch error")

        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert result["error_code"] == "redirect_uri_mismatch"
        assert "redirect" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_includes_kb_results(self, oauth_specialist):
        """Test that KB results are included in response."""
        state = create_initial_state("OAuth help")

        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[
            {"title": "OAuth 2.0 Guide", "doc_id": "kb_123"},
            {"title": "Token Management", "doc_id": "kb_456"}
        ])

        result = await oauth_specialist.process(state)

        assert len(result["kb_results"]) == 2
        assert "Related documentation" in result["agent_response"] or "documentation" in result["agent_response"].lower()


class TestGuidanceContent:
    """Test OAuth guidance content."""

    def test_setup_guide_contains_flow_steps(self, oauth_specialist):
        """Test that setup guide contains OAuth flow steps."""
        guide = oauth_specialist._guide_oauth_setup()

        assert "client_id" in guide.lower()
        assert "client_secret" in guide.lower()
        assert "authorize" in guide.lower()
        assert "token" in guide.lower()

    def test_callback_guide_contains_error_solutions(self, oauth_specialist):
        """Test that callback guide contains error solutions."""
        guide = oauth_specialist._guide_callback_errors()

        assert "redirect_uri" in guide.lower()
        assert "state" in guide.lower()

    def test_token_refresh_guide_contains_implementation(self, oauth_specialist):
        """Test that token refresh guide contains implementation."""
        guide = oauth_specialist._guide_token_refresh()

        assert "refresh_token" in guide.lower()
        assert "access_token" in guide.lower()

    def test_scope_guide_contains_permissions(self, oauth_specialist):
        """Test that scope guide contains permission info."""
        guide = oauth_specialist._guide_scope_management()

        assert "scope" in guide.lower()

    def test_pkce_guide_contains_code_challenge(self, oauth_specialist):
        """Test that PKCE guide contains code challenge info."""
        guide = oauth_specialist._guide_pkce()

        assert "code_verifier" in guide.lower()
        assert "code_challenge" in guide.lower()
        assert "pkce" in guide.lower()


class TestErrorFixes:
    """Test specific error fixes."""

    def test_redirect_uri_mismatch_fix(self, oauth_specialist):
        """Test redirect_uri_mismatch fix."""
        fix = oauth_specialist._guide_error_fix("redirect_uri_mismatch")

        assert "redirect" in fix.lower()
        assert "match" in fix.lower()

    def test_invalid_scope_fix(self, oauth_specialist):
        """Test invalid_scope fix."""
        fix = oauth_specialist._guide_error_fix("invalid_scope")

        assert "scope" in fix.lower()

    def test_access_denied_fix(self, oauth_specialist):
        """Test access_denied fix."""
        fix = oauth_specialist._guide_error_fix("access_denied")

        assert "denied" in fix.lower() or "deny" in fix.lower()


class TestStateUpdates:
    """Test state updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, oauth_specialist):
        """Test that agent is added to history."""
        state = create_initial_state("OAuth setup")
        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert "oauth_specialist" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_sets_high_confidence(self, oauth_specialist):
        """Test that response confidence is high for OAuth guidance."""
        state = create_initial_state("OAuth setup")
        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert result["response_confidence"] >= 0.85

    @pytest.mark.asyncio
    async def test_marks_as_resolved(self, oauth_specialist):
        """Test that status is marked as resolved."""
        state = create_initial_state("OAuth help")
        oauth_specialist.search_knowledge_base = AsyncMock(return_value=[])

        result = await oauth_specialist.process(state)

        assert result["status"] == "resolved"
        assert result["next_agent"] is None
