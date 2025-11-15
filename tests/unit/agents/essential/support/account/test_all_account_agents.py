"""
Comprehensive tests for all 10 Account Specialists agents.
"""

import pytest
from src.workflow.state import create_initial_state
from src.agents.essential.support.account.profile_manager import ProfileManager
from src.agents.essential.support.account.team_manager import TeamManager
from src.agents.essential.support.account.notification_configurator import NotificationConfigurator
from src.agents.essential.support.account.security_advisor import SecurityAdvisor
from src.agents.essential.support.account.sso_specialist import SSOSpecialist
from src.agents.essential.support.account.permission_manager import PermissionManager
from src.agents.essential.support.account.data_export_specialist import DataExportSpecialist
from src.agents.essential.support.account.account_deletion_specialist import AccountDeletionSpecialist
from src.agents.essential.support.account.compliance_specialist import ComplianceSpecialist
from src.agents.essential.support.account.audit_log_specialist import AuditLogSpecialist


class TestProfileManager:
    """Tests for Profile Manager Agent."""

    @pytest.fixture
    def agent(self):
        return ProfileManager()

    def test_initialization(self, agent):
        assert agent.config.name == "profile_manager"
        assert agent.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_user_profile_update(self, agent):
        state = create_initial_state(
            "Update my email",
            context={"customer_metadata": {"plan": "premium", "role": "member"}}
        )
        result = await agent.process(state)
        assert result.get("profile_update_type") == "user"
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_timezone_update(self, agent):
        state = create_initial_state("Change my timezone")
        result = await agent.process(state)
        assert result.get("profile_update_type") == "timezone"


class TestTeamManager:
    """Tests for Team Manager Agent."""

    @pytest.fixture
    def agent(self):
        return TeamManager()

    def test_initialization(self, agent):
        assert agent.config.name == "team_manager"
        assert "owner" in agent.ROLES

    @pytest.mark.asyncio
    async def test_invite_member(self, agent):
        state = create_initial_state(
            "How to invite someone?",
            context={"customer_metadata": {"plan": "premium", "role": "admin", "team_size": 5}}
        )
        result = await agent.process(state)
        assert result.get("team_action") == "invite"
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_permission_denied(self, agent):
        state = create_initial_state(
            "Remove member",
            context={"customer_metadata": {"role": "member"}}
        )
        result = await agent.process(state)
        assert result["status"] == "resolved"


class TestNotificationConfigurator:
    """Tests for Notification Configurator Agent."""

    @pytest.fixture
    def agent(self):
        return NotificationConfigurator()

    def test_initialization(self, agent):
        assert agent.config.name == "notification_configurator"
        assert "email" in agent.NOTIFICATION_CHANNELS

    @pytest.mark.asyncio
    async def test_slack_setup(self, agent):
        state = create_initial_state("Setup Slack notifications")
        result = await agent.process(state)
        assert result.get("notification_action") == "setup_slack"

    @pytest.mark.asyncio
    async def test_mute_notifications(self, agent):
        state = create_initial_state("Mute all notifications")
        result = await agent.process(state)
        assert result.get("notification_action") == "mute"


class TestSecurityAdvisor:
    """Tests for Security Advisor Agent."""

    @pytest.fixture
    def agent(self):
        return SecurityAdvisor()

    def test_initialization(self, agent):
        assert agent.config.name == "security_advisor"
        assert "2fa" in agent.SECURITY_FEATURES

    @pytest.mark.asyncio
    async def test_setup_2fa(self, agent):
        state = create_initial_state("Enable 2FA")
        result = await agent.process(state)
        assert result.get("security_action") == "setup_2fa"

    @pytest.mark.asyncio
    async def test_audit_review(self, agent):
        state = create_initial_state("Review audit logs")
        result = await agent.process(state)
        assert result.get("security_action") == "audit_review"


class TestSSOSpecialist:
    """Tests for SSO Specialist Agent."""

    @pytest.fixture
    def agent(self):
        return SSOSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "sso_specialist"
        assert "okta" in agent.SUPPORTED_PROVIDERS

    @pytest.mark.asyncio
    async def test_enterprise_required(self, agent):
        state = create_initial_state(
            "Setup SSO",
            context={"customer_metadata": {"plan": "basic"}}
        )
        result = await agent.process(state)
        assert "enterprise" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_okta_setup(self, agent):
        state = create_initial_state(
            "Setup Okta SSO",
            context={"customer_metadata": {"plan": "enterprise"}}
        )
        result = await agent.process(state)
        assert result.get("sso_provider") == "okta"


class TestPermissionManager:
    """Tests for Permission Manager Agent."""

    @pytest.fixture
    def agent(self):
        return PermissionManager()

    def test_initialization(self, agent):
        assert agent.config.name == "permission_manager"
        assert len(agent.ROLES) == 4

    @pytest.mark.asyncio
    async def test_explain_roles(self, agent):
        state = create_initial_state("Explain the roles")
        result = await agent.process(state)
        assert result.get("permission_action") == "explain"

    @pytest.mark.asyncio
    async def test_change_role(self, agent):
        state = create_initial_state("Change someone's role")
        result = await agent.process(state)
        assert result.get("permission_action") == "change"


class TestDataExportSpecialist:
    """Tests for Data Export Specialist Agent."""

    @pytest.fixture
    def agent(self):
        return DataExportSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "data_export_specialist"
        assert "json" in agent.EXPORT_FORMATS

    @pytest.mark.asyncio
    async def test_gdpr_export(self, agent):
        state = create_initial_state("GDPR data export")
        result = await agent.process(state)
        assert result.get("export_action") == "gdpr_export"

    @pytest.mark.asyncio
    async def test_check_status(self, agent):
        state = create_initial_state("Check export status")
        result = await agent.process(state)
        assert result.get("export_action") == "check_status"


class TestAccountDeletionSpecialist:
    """Tests for Account Deletion Specialist Agent."""

    @pytest.fixture
    def agent(self):
        return AccountDeletionSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "account_deletion_specialist"
        assert agent.DELETION_GRACE_PERIOD_DAYS == 30

    @pytest.mark.asyncio
    async def test_deletion_request(self, agent):
        state = create_initial_state(
            "Delete my account",
            context={"customer_metadata": {"plan": "free", "role": "owner", "team_size": 1}}
        )
        result = await agent.process(state)
        assert result.get("deletion_action") == "request_deletion"

    @pytest.mark.asyncio
    async def test_owner_required(self, agent):
        state = create_initial_state(
            "Delete account",
            context={"customer_metadata": {"role": "member", "team_size": 5}}
        )
        result = await agent.process(state)
        assert "owner" in result["agent_response"].lower()


class TestComplianceSpecialist:
    """Tests for Compliance Specialist Agent."""

    @pytest.fixture
    def agent(self):
        return ComplianceSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "compliance_specialist"
        assert "gdpr" in agent.SUPPORTED_REGULATIONS

    @pytest.mark.asyncio
    async def test_gdpr_request(self, agent):
        state = create_initial_state("GDPR rights")
        result = await agent.process(state)
        assert result.get("compliance_action") == "gdpr_request"

    @pytest.mark.asyncio
    async def test_ccpa_request(self, agent):
        state = create_initial_state("CCPA California rights")
        result = await agent.process(state)
        assert result.get("compliance_action") == "ccpa_request"


class TestAuditLogSpecialist:
    """Tests for Audit Log Specialist Agent."""

    @pytest.fixture
    def agent(self):
        return AuditLogSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "audit_log_specialist"
        assert "auth" in agent.EVENT_TYPES

    @pytest.mark.asyncio
    async def test_search_logs(self, agent):
        state = create_initial_state(
            "Search audit logs",
            context={"customer_metadata": {"plan": "premium"}}
        )
        result = await agent.process(state)
        assert result.get("audit_action") == "search"

    @pytest.mark.asyncio
    async def test_export_logs(self, agent):
        state = create_initial_state(
            "Export audit logs",
            context={"customer_metadata": {"plan": "premium"}}
        )
        result = await agent.process(state)
        assert result.get("audit_action") == "export"
