"""
Access Controller Agent - TASK-2302

Enforces role-based access control (RBAC) for all system operations.
Implements least privilege principle and validates all access requests.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("access_controller", tier="operational", category="security")
class AccessControllerAgent(BaseAgent):
    """
    Access Controller Agent.

    Enforces role-based access control (RBAC):
    - User role validation
    - Permission checking for resources
    - Least privilege enforcement
    - Dynamic access rule evaluation
    - Session validation and timeout
    - Multi-factor authentication (MFA) requirements
    - Access request logging and audit

    Security Principles:
    - Zero trust: Validate every access attempt
    - Least privilege: Minimum permissions required
    - Defense in depth: Multiple validation layers
    """

    # Default roles and permissions
    ROLE_PERMISSIONS = {
        "admin": {
            "read", "write", "delete", "admin", "security",
            "user_management", "system_config", "audit_log"
        },
        "manager": {
            "read", "write", "delete", "team_management",
            "report_access", "user_view"
        },
        "agent": {
            "read", "write", "ticket_management", "customer_interaction"
        },
        "user": {
            "read", "self_service", "ticket_create"
        },
        "readonly": {
            "read"
        },
        "guest": set()
    }

    # Resource protection levels
    RESOURCE_PROTECTION_LEVELS = {
        "public": 0,
        "internal": 1,
        "confidential": 2,
        "secret": 3,
        "top_secret": 4
    }

    # MFA requirements
    MFA_REQUIRED_OPERATIONS = {
        "delete", "admin", "security", "user_management",
        "system_config", "data_export"
    }

    def __init__(self):
        config = AgentConfig(
            name="access_controller",
            type=AgentType.SECURITY,
            model="claude-sonnet-4-5-20250929",
            temperature=0.1,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Validate access control for requested operation.

        Args:
            state: Current agent state with access request details

        Returns:
            Updated state with access control decision
        """
        self.logger.info("access_control_check_started")

        state = self.update_state(state)

        # Extract parameters
        user_id = state.get("entities", {}).get("user_id", "unknown")
        user_role = state.get("entities", {}).get("user_role", "guest")
        requested_operation = state.get("entities", {}).get("operation", "read")
        resource_id = state.get("entities", {}).get("resource_id", "unknown")
        resource_type = state.get("entities", {}).get("resource_type", "unknown")
        protection_level = state.get("entities", {}).get("protection_level", "internal")
        session_valid = state.get("entities", {}).get("session_valid", False)
        mfa_verified = state.get("entities", {}).get("mfa_verified", False)
        ip_address = state.get("entities", {}).get("ip_address", "unknown")

        self.logger.debug(
            "access_control_details",
            user_id=user_id,
            user_role=user_role,
            operation=requested_operation,
            resource_type=resource_type,
            protection_level=protection_level
        )

        # Validate session
        session_check = self._validate_session(session_valid, user_id)

        # Check user permissions
        permission_check = self._check_permissions(user_role, requested_operation)

        # Validate resource access
        resource_check = self._validate_resource_access(
            user_role,
            resource_type,
            protection_level
        )

        # Check MFA requirement
        mfa_check = self._check_mfa_requirement(
            requested_operation,
            mfa_verified,
            protection_level
        )

        # Evaluate access rules
        access_granted, denial_reason = self._evaluate_access(
            session_check,
            permission_check,
            resource_check,
            mfa_check
        )

        # Log access attempt
        access_log = self._log_access_attempt(
            user_id,
            user_role,
            requested_operation,
            resource_id,
            resource_type,
            access_granted,
            denial_reason,
            ip_address
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            access_granted,
            denial_reason,
            user_role,
            requested_operation
        )

        # Check for security violations
        violations = self._check_security_violations(
            access_granted,
            user_id,
            requested_operation,
            denial_reason
        )

        # Format response
        response = self._format_access_report(
            user_id,
            user_role,
            requested_operation,
            resource_id,
            access_granted,
            denial_reason,
            recommendations,
            violations
        )

        state["agent_response"] = response
        state["access_granted"] = access_granted
        state["denial_reason"] = denial_reason
        state["access_log"] = access_log
        state["security_violations"] = violations
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.98
        state["status"] = "resolved"
        state["next_agent"] = None

        # Alert on security violations
        if violations:
            state["alert_pagerduty"] = True
            state["alert_severity"] = "high"
            state["alert_message"] = f"Security violation detected: {violations[0]['type']}"

        self.logger.info(
            "access_control_completed",
            user_id=user_id,
            access_granted=access_granted,
            violations=len(violations)
        )

        return state

    def _validate_session(self, session_valid: bool, user_id: str) -> Dict[str, Any]:
        """
        Validate user session.

        Args:
            session_valid: Session validity status
            user_id: User ID

        Returns:
            Session validation result
        """
        return {
            "passed": session_valid,
            "reason": "Valid session" if session_valid else "Invalid or expired session",
            "user_id": user_id,
            "checked_at": datetime.utcnow().isoformat()
        }

    def _check_permissions(self, user_role: str, operation: str) -> Dict[str, Any]:
        """
        Check if role has permission for operation.

        Args:
            user_role: User's role
            operation: Requested operation

        Returns:
            Permission check result
        """
        role_perms = self.ROLE_PERMISSIONS.get(user_role.lower(), set())
        has_permission = operation in role_perms

        return {
            "passed": has_permission,
            "user_role": user_role,
            "operation": operation,
            "role_permissions": list(role_perms),
            "reason": f"Role '{user_role}' has permission for '{operation}'" if has_permission
                     else f"Role '{user_role}' lacks permission for '{operation}'"
        }

    def _validate_resource_access(
        self,
        user_role: str,
        resource_type: str,
        protection_level: str
    ) -> Dict[str, Any]:
        """
        Validate access to resource based on protection level.

        Args:
            user_role: User's role
            resource_type: Type of resource
            protection_level: Protection level of resource

        Returns:
            Resource access validation result
        """
        # Get role clearance level
        role_clearance = {
            "admin": 4,
            "manager": 3,
            "agent": 2,
            "user": 1,
            "readonly": 1,
            "guest": 0
        }

        user_clearance = role_clearance.get(user_role.lower(), 0)
        required_clearance = self.RESOURCE_PROTECTION_LEVELS.get(protection_level, 1)

        has_access = user_clearance >= required_clearance

        return {
            "passed": has_access,
            "user_clearance": user_clearance,
            "required_clearance": required_clearance,
            "protection_level": protection_level,
            "resource_type": resource_type,
            "reason": f"User clearance level {user_clearance} sufficient for {protection_level}" if has_access
                     else f"User clearance level {user_clearance} insufficient for {protection_level}"
        }

    def _check_mfa_requirement(
        self,
        operation: str,
        mfa_verified: bool,
        protection_level: str
    ) -> Dict[str, Any]:
        """
        Check if MFA is required and verified.

        Args:
            operation: Requested operation
            mfa_verified: MFA verification status
            protection_level: Resource protection level

        Returns:
            MFA check result
        """
        mfa_required = (
            operation in self.MFA_REQUIRED_OPERATIONS or
            protection_level in ["secret", "top_secret"]
        )

        passed = not mfa_required or (mfa_required and mfa_verified)

        return {
            "passed": passed,
            "mfa_required": mfa_required,
            "mfa_verified": mfa_verified,
            "reason": "MFA verified" if passed else "MFA required but not verified"
        }

    def _evaluate_access(
        self,
        session_check: Dict[str, Any],
        permission_check: Dict[str, Any],
        resource_check: Dict[str, Any],
        mfa_check: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluate all checks and determine access decision.

        Args:
            session_check: Session validation result
            permission_check: Permission check result
            resource_check: Resource access check result
            mfa_check: MFA check result

        Returns:
            Tuple of (access_granted, denial_reason)
        """
        checks = [session_check, permission_check, resource_check, mfa_check]

        # All checks must pass
        for check in checks:
            if not check["passed"]:
                return False, check["reason"]

        return True, None

    def _log_access_attempt(
        self,
        user_id: str,
        user_role: str,
        operation: str,
        resource_id: str,
        resource_type: str,
        access_granted: bool,
        denial_reason: Optional[str],
        ip_address: str
    ) -> Dict[str, Any]:
        """
        Log access attempt for audit trail.

        Args:
            user_id: User ID
            user_role: User role
            operation: Requested operation
            resource_id: Resource ID
            resource_type: Resource type
            access_granted: Access decision
            denial_reason: Reason for denial (if denied)
            ip_address: IP address of request

        Returns:
            Audit log entry
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_role": user_role,
            "operation": operation,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "access_granted": access_granted,
            "denial_reason": denial_reason,
            "ip_address": ip_address,
            "log_id": f"ACCESS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "compliance_flags": ["SOC2", "ISO27001"]
        }

    def _generate_recommendations(
        self,
        access_granted: bool,
        denial_reason: Optional[str],
        user_role: str,
        operation: str
    ) -> List[str]:
        """
        Generate security recommendations.

        Args:
            access_granted: Access decision
            denial_reason: Denial reason
            user_role: User role
            operation: Requested operation

        Returns:
            List of recommendations
        """
        recommendations = []

        if not access_granted:
            if "session" in (denial_reason or "").lower():
                recommendations.append("User needs to re-authenticate with valid credentials")
            elif "permission" in (denial_reason or "").lower():
                recommendations.append(
                    f"User role '{user_role}' requires elevation for operation '{operation}'"
                )
                recommendations.append("Contact administrator for role adjustment if access needed")
            elif "clearance" in (denial_reason or "").lower():
                recommendations.append("Resource requires higher security clearance")
            elif "mfa" in (denial_reason or "").lower():
                recommendations.append("Multi-factor authentication required for this operation")

        if access_granted and operation in self.MFA_REQUIRED_OPERATIONS:
            recommendations.append("Sensitive operation performed - logged for audit trail")

        return recommendations

    def _check_security_violations(
        self,
        access_granted: bool,
        user_id: str,
        operation: str,
        denial_reason: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Check for security violations.

        Args:
            access_granted: Access decision
            user_id: User ID
            operation: Requested operation
            denial_reason: Denial reason

        Returns:
            List of security violations
        """
        violations = []

        # Track repeated access denials (potential brute force)
        if not access_granted:
            violations.append({
                "type": "access_denied",
                "severity": "medium",
                "user_id": user_id,
                "operation": operation,
                "reason": denial_reason,
                "message": "Access denied - potential unauthorized access attempt",
                "detected_at": datetime.utcnow().isoformat()
            })

        # High-risk operations on sensitive resources
        if access_granted and operation in ["delete", "admin"]:
            violations.append({
                "type": "high_risk_operation",
                "severity": "low",
                "user_id": user_id,
                "operation": operation,
                "message": "High-risk operation performed - requires monitoring",
                "detected_at": datetime.utcnow().isoformat()
            })

        return violations

    def _format_access_report(
        self,
        user_id: str,
        user_role: str,
        operation: str,
        resource_id: str,
        access_granted: bool,
        denial_reason: Optional[str],
        recommendations: List[str],
        violations: List[Dict[str, Any]]
    ) -> str:
        """Format access control report."""
        status_icon = "✅" if access_granted else "❌"

        report = f"""**Access Control Report**

**Decision:** {status_icon} {"ACCESS GRANTED" if access_granted else "ACCESS DENIED"}
**User ID:** {user_id}
**Role:** {user_role}
**Operation:** {operation}
**Resource ID:** {resource_id}

"""

        if not access_granted:
            report += f"**Denial Reason:** {denial_reason}\n\n"

        # Security violations
        if violations:
            report += f"**Security Events:**\n"
            for violation in violations:
                severity_icon = "🔴" if violation["severity"] == "high" else "⚠️" if violation["severity"] == "medium" else "ℹ️"
                report += f"{severity_icon} [{violation['severity'].upper()}] {violation['message']}\n"
            report += "\n"

        # Recommendations
        if recommendations:
            report += f"**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Access control evaluated at {datetime.utcnow().isoformat()}*"
        report += f"\n*Compliance: SOC 2, ISO 27001*"

        return report
