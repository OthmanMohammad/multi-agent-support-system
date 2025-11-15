"""
Account Support Agents - Specialized agents for account management.

This module contains 10 specialized agents for account-related support:
1. Profile Manager - Profile and settings updates
2. Team Manager - Team member and role management
3. Notification Configurator - Notification settings
4. Security Advisor - Security best practices and 2FA
5. SSO Specialist - SAML/OAuth SSO configuration
6. Permission Manager - Roles and permissions
7. Data Export Specialist - GDPR-compliant data exports
8. Account Deletion Specialist - Account deletion handling
9. Compliance Specialist - GDPR, CCPA compliance
10. Audit Log Specialist - Audit log search and analysis
"""

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


__all__ = [
    "ProfileManager",
    "TeamManager",
    "NotificationConfigurator",
    "SecurityAdvisor",
    "SSOSpecialist",
    "PermissionManager",
    "DataExportSpecialist",
    "AccountDeletionSpecialist",
    "ComplianceSpecialist",
    "AuditLogSpecialist",
]
