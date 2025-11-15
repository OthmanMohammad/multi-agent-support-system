"""
Unit tests for Login Specialist agent.
"""

import pytest
from src.agents.essential.support.technical.login_specialist import LoginSpecialist
from src.workflow.state import create_initial_state


class TestLoginSpecialist:
    """Test suite for Login Specialist agent"""

    @pytest.fixture
    def login_specialist(self):
        """Login Specialist instance"""
        return LoginSpecialist()

    def test_initialization(self, login_specialist):
        """Test Login Specialist initializes correctly"""
        assert login_specialist.config.name == "login_specialist"
        assert login_specialist.config.type.value == "specialist"
        assert login_specialist.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_detect_forgot_password(self, login_specialist):
        """Test detection of forgot password issue"""
        state = create_initial_state("I forgot my password")
        state["customer_metadata"] = {"email": "test@example.com"}

        result = await login_specialist.process(state)

        assert result["login_issue_type"] == "forgot_password"
        assert "password reset link" in result["agent_response"].lower()
        assert result["login_action_taken"] == "password_reset_sent"

    @pytest.mark.asyncio
    async def test_detect_locked_account(self, login_specialist):
        """Test detection of locked account"""
        state = create_initial_state("My account is locked out")
        state["customer_metadata"] = {"email": "user@example.com"}

        result = await login_specialist.process(state)

        assert result["login_issue_type"] == "locked"
        assert "unlocked" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_detect_2fa_issue(self, login_specialist):
        """Test detection of 2FA issue"""
        state = create_initial_state("Lost my authenticator app")

        result = await login_specialist.process(state)

        assert result["login_issue_type"] == "2fa_issue"
        assert "two-factor" in result["agent_response"].lower()
        assert "backup codes" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_detect_sso_issue(self, login_specialist):
        """Test detection of SSO issue"""
        state = create_initial_state("SSO login not working, SAML error")

        result = await login_specialist.process(state)

        assert result["login_issue_type"] == "sso_issue"
        assert "sso" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_detect_session_issue(self, login_specialist):
        """Test detection of session expiration"""
        state = create_initial_state("Keep getting logged out, session expired")

        result = await login_specialist.process(state)

        assert result["login_issue_type"] == "session_expired"
        assert "session" in result["agent_response"].lower()

    def test_detect_login_issue_type(self, login_specialist):
        """Test login issue type detection"""
        # Forgot password
        issue = login_specialist._detect_login_issue("I can't remember my password")
        assert issue == "forgot_password"

        # Locked
        issue = login_specialist._detect_login_issue("account locked after too many attempts")
        assert issue == "locked"

        # 2FA
        issue = login_specialist._detect_login_issue("two factor authentication not working")
        assert issue == "2fa_issue"

        # SSO
        issue = login_specialist._detect_login_issue("SSO SAML not working")
        assert issue == "sso_issue"

        # Session
        issue = login_specialist._detect_login_issue("keep getting logged out session")
        assert issue == "session_expired"

        # Unknown
        issue = login_specialist._detect_login_issue("can't login")
        assert issue == "unknown"

    @pytest.mark.asyncio
    async def test_password_reset_includes_requirements(self, login_specialist):
        """Test password reset response includes requirements"""
        response = await login_specialist._handle_password_reset("test@example.com")

        assert "8 characters" in response["message"]
        assert "uppercase" in response["message"].lower()
        assert "special character" in response["message"].lower()

    def test_2fa_troubleshooting_covers_common_issues(self, login_specialist):
        """Test 2FA troubleshooting covers common scenarios"""
        response = login_specialist._handle_2fa_issue("test@example.com")

        assert "lost your phone" in response["message"].lower()
        assert "backup codes" in response["message"].lower()
        assert "time sync" in response["message"].lower()
        assert "wrong codes" in response["message"].lower()
