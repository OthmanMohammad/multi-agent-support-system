"""
Unit tests for Webhook Troubleshooter agent.

Tests webhook issue detection, diagnosis, and troubleshooting guidance
for various webhook delivery problems.

Part of: STORY-006 Integration Specialists Sub-Swarm (TASK-601)
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.integration.webhook_troubleshooter import WebhookTroubleshooter
from src.workflow.state import create_initial_state


@pytest.fixture
def webhook_troubleshooter():
    """Create WebhookTroubleshooter instance for testing."""
    return WebhookTroubleshooter()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        context={"customer_metadata": {"plan": "premium"}}
    )


class TestWebhookTroubleshooterInitialization:
    """Test Webhook Troubleshooter initialization and configuration."""

    def test_initialization(self, webhook_troubleshooter):
        """Test that agent initializes with correct configuration."""
        assert webhook_troubleshooter.config.name == "webhook_troubleshooter"
        assert webhook_troubleshooter.config.type.value == "specialist"
        assert webhook_troubleshooter.config.model == "claude-3-haiku-20240307"
        assert webhook_troubleshooter.config.temperature == 0.3
        assert webhook_troubleshooter.config.tier == "essential"

    def test_has_required_capabilities(self, webhook_troubleshooter):
        """Test that agent has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = webhook_troubleshooter.config.capabilities
        assert AgentCapability.KB_SEARCH in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities


class TestIssueDetection:
    """Test webhook issue type detection."""

    def test_detect_not_receiving_issue(self, webhook_troubleshooter):
        """Test detecting webhooks not being received."""
        issue = webhook_troubleshooter._detect_issue_type("My webhooks are not receiving")
        assert issue == "not_receiving"

    def test_detect_timeout_issue(self, webhook_troubleshooter):
        """Test detecting webhook timeout issues."""
        issue = webhook_troubleshooter._detect_issue_type("Webhook is timing out")
        assert issue == "timeout"

    def test_detect_auth_error(self, webhook_troubleshooter):
        """Test detecting authentication/signature errors."""
        issue = webhook_troubleshooter._detect_issue_type("Signature verification failing")
        assert issue == "auth_error"

    def test_detect_ssl_issue(self, webhook_troubleshooter):
        """Test detecting SSL certificate issues."""
        issue = webhook_troubleshooter._detect_issue_type("SSL certificate error")
        assert issue == "ssl"

    def test_detect_firewall_issue(self, webhook_troubleshooter):
        """Test detecting firewall blocking issues."""
        issue = webhook_troubleshooter._detect_issue_type("Webhooks are being blocked by firewall")
        assert issue == "firewall"

    def test_detect_general_issue(self, webhook_troubleshooter):
        """Test fallback to general help."""
        issue = webhook_troubleshooter._detect_issue_type("I need help with webhooks")
        assert issue == "general"


class TestWebhookTroubleshooting:
    """Test webhook troubleshooting process."""

    @pytest.mark.asyncio
    async def test_troubleshoot_not_receiving(self, webhook_troubleshooter):
        """Test troubleshooting webhooks not being received."""
        state = create_initial_state("My webhook is not receiving events")

        # Mock KB search
        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert result["detected_issue"] == "not_receiving"
        assert "agent_response" in result
        assert "unreachable" in result["agent_response"].lower() or "firewall" in result["agent_response"].lower()
        assert result["status"] == "resolved"
        assert result["next_agent"] is None

    @pytest.mark.asyncio
    async def test_troubleshoot_timeout(self, webhook_troubleshooter):
        """Test troubleshooting webhook timeout issues."""
        state = create_initial_state("Webhook endpoint is timing out")

        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert result["detected_issue"] == "timeout"
        assert "30 seconds" in result["agent_response"] or "timeout" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_troubleshoot_signature_verification(self, webhook_troubleshooter):
        """Test troubleshooting signature verification issues."""
        state = create_initial_state("Webhook signature verification is failing")

        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert result["detected_issue"] == "auth_error"
        assert "signature" in result["agent_response"].lower()
        assert "hmac" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_includes_kb_results(self, webhook_troubleshooter):
        """Test that KB results are included in response."""
        state = create_initial_state("Webhook help needed")

        # Mock KB search with results
        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[
            {"title": "Webhook Setup Guide", "doc_id": "kb_123"},
            {"title": "Debugging Webhooks", "doc_id": "kb_456"}
        ])

        result = await webhook_troubleshooter.process(state)

        assert len(result["kb_results"]) == 2
        assert "Related documentation" in result["agent_response"] or "documentation" in result["agent_response"].lower()


class TestResponseGuidance:
    """Test specific troubleshooting guidance."""

    def test_not_receiving_guide_contains_diagnostics(self, webhook_troubleshooter):
        """Test that not receiving guide contains diagnostic steps."""
        guide = webhook_troubleshooter._guide_not_receiving()

        assert "curl" in guide.lower()
        assert "ip" in guide.lower() or "whitelist" in guide.lower()
        assert "https" in guide.lower()

    def test_timeout_guide_contains_optimization(self, webhook_troubleshooter):
        """Test that timeout guide contains optimization tips."""
        guide = webhook_troubleshooter._guide_timeout()

        assert "30 seconds" in guide or "timeout" in guide.lower()
        assert "queue" in guide.lower() or "background" in guide.lower()

    def test_auth_guide_contains_signature_verification(self, webhook_troubleshooter):
        """Test that auth guide contains signature verification."""
        guide = webhook_troubleshooter._guide_auth_error()

        assert "hmac" in guide.lower()
        assert "signature" in guide.lower()
        assert "sha256" in guide.lower()

    def test_ssl_guide_contains_certificate_info(self, webhook_troubleshooter):
        """Test that SSL guide contains certificate information."""
        guide = webhook_troubleshooter._guide_ssl_issues()

        assert "https" in guide.lower()
        assert "certificate" in guide.lower()
        assert "ssl" in guide.lower()

    def test_firewall_guide_contains_ip_whitelist(self, webhook_troubleshooter):
        """Test that firewall guide contains IP whitelist information."""
        guide = webhook_troubleshooter._guide_firewall_issues()

        assert "ip" in guide.lower()
        assert "firewall" in guide.lower()


class TestStateUpdates:
    """Test state updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, webhook_troubleshooter):
        """Test that agent is added to history."""
        state = create_initial_state("Webhook issue")
        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert "webhook_troubleshooter" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_sets_response_confidence(self, webhook_troubleshooter):
        """Test that response confidence is set."""
        state = create_initial_state("Webhook issue")
        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert "response_confidence" in result
        assert 0 <= result["response_confidence"] <= 1

    @pytest.mark.asyncio
    async def test_marks_as_resolved(self, webhook_troubleshooter):
        """Test that status is marked as resolved."""
        state = create_initial_state("Webhook issue")
        webhook_troubleshooter.search_knowledge_base = AsyncMock(return_value=[])

        result = await webhook_troubleshooter.process(state)

        assert result["status"] == "resolved"
        assert result["next_agent"] is None
