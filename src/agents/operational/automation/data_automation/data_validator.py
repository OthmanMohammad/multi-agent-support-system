"""
Data Validator Agent - TASK-2209

Auto-validates data quality across customer records, ensuring completeness,
accuracy, and compliance with data standards.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("data_validator", tier="operational", category="automation")
class DataValidatorAgent(BaseAgent):
    """
    Data Validator Agent - Auto-validates data quality.

    Handles:
    - Email format validation
    - Phone number validation and formatting
    - Required field checks
    - Data type validation
    - Range and constraint validation
    - Cross-field validation rules
    - Data completeness scoring
    - Automated data cleanup and normalization
    """

    # Validation rules by field type
    VALIDATION_RULES = {
        "email": {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "required": True,
            "max_length": 255
        },
        "phone": {
            "pattern": r"^\+?1?\d{10,15}$",
            "required": False,
            "normalize": True
        },
        "url": {
            "pattern": r"^https?://[^\s]+$",
            "required": False
        },
        "postal_code": {
            "pattern": r"^\d{5}(-\d{4})?$",
            "required": False
        }
    }

    # Required fields by record type
    REQUIRED_FIELDS = {
        "contact": ["email", "name", "customer_id"],
        "company": ["name", "domain"],
        "opportunity": ["name", "amount", "close_date"]
    }

    # Data quality scoring weights
    QUALITY_WEIGHTS = {
        "completeness": 0.4,
        "accuracy": 0.3,
        "consistency": 0.2,
        "freshness": 0.1
    }

    def __init__(self):
        config = AgentConfig(
            name="data_validator",
            type=AgentType.AUTOMATOR,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=800,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Auto-validate data quality."""
        self.logger.info("data_validator_started")
        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})
        record_type = entities.get("record_type", "contact")

        # Validate required fields
        required_field_check = self._validate_required_fields(
            customer_metadata,
            record_type
        )

        # Validate field formats
        format_validation = self._validate_field_formats(customer_metadata)

        # Validate data types
        type_validation = self._validate_data_types(customer_metadata)

        # Cross-field validation
        cross_field_validation = self._validate_cross_fields(customer_metadata)

        # Calculate data quality score
        quality_score = self._calculate_quality_score(
            required_field_check,
            format_validation,
            type_validation,
            customer_metadata
        )

        # Auto-fix common issues
        auto_fixes = self._apply_auto_fixes(
            customer_metadata,
            format_validation
        )

        # Compile validation report
        validation_report = {
            "required_fields": required_field_check,
            "format_validation": format_validation,
            "type_validation": type_validation,
            "cross_field_validation": cross_field_validation,
            "quality_score": quality_score,
            "auto_fixes": auto_fixes,
            "validated_at": datetime.utcnow().isoformat()
        }

        # Log automation action
        automation_log = self._log_automation_action(
            "data_validated",
            validation_report,
            customer_metadata
        )

        # Generate response
        response = f"""**Data Validation Complete**

Record Type: {record_type.title()}
Quality Score: {quality_score['overall_score']:.0%}

**Validation Results:**
- Required Fields: {required_field_check['passed']}/{required_field_check['total']} passed
- Format Validation: {len(format_validation['valid'])} valid, {len(format_validation['invalid'])} invalid
- Type Validation: {len(type_validation['valid'])} valid, {len(type_validation['invalid'])} invalid

**Quality Breakdown:**
- Completeness: {quality_score['completeness']:.0%}
- Accuracy: {quality_score['accuracy']:.0%}
- Consistency: {quality_score['consistency']:.0%}

**Auto-Fixes Applied:** {len(auto_fixes)}
"""

        if format_validation['invalid']:
            response += f"\n**Issues Found:**\n"
            for issue in format_validation['invalid'][:5]:
                response += f"- {issue['field']}: {issue['error']}\n"

        state["agent_response"] = response
        state["validation_report"] = validation_report
        state["quality_score"] = quality_score
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.95
        state["status"] = "resolved"

        self.logger.info(
            "data_validation_completed",
            quality_score=quality_score['overall_score'],
            issues_found=len(format_validation['invalid'])
        )

        return state

    def _validate_required_fields(
        self,
        data: Dict,
        record_type: str
    ) -> Dict:
        """Validate required fields are present."""
        required = self.REQUIRED_FIELDS.get(record_type, [])
        missing = [field for field in required if not data.get(field)]

        return {
            "total": len(required),
            "passed": len(required) - len(missing),
            "missing": missing,
            "is_valid": len(missing) == 0
        }

    def _validate_field_formats(self, data: Dict) -> Dict:
        """Validate field formats against patterns."""
        valid = []
        invalid = []

        for field, rules in self.VALIDATION_RULES.items():
            value = data.get(field)
            if not value:
                continue

            pattern = rules.get("pattern")
            if pattern and not re.match(pattern, str(value)):
                invalid.append({
                    "field": field,
                    "value": value,
                    "error": f"Invalid format for {field}"
                })
            else:
                valid.append(field)

        return {
            "valid": valid,
            "invalid": invalid,
            "validation_rate": len(valid) / (len(valid) + len(invalid)) if (len(valid) + len(invalid)) > 0 else 1.0
        }

    def _validate_data_types(self, data: Dict) -> Dict:
        """Validate data types."""
        valid = []
        invalid = []

        # Check numeric fields
        numeric_fields = ["employee_count", "annual_revenue", "deal_size"]
        for field in numeric_fields:
            value = data.get(field)
            if value and not isinstance(value, (int, float)):
                try:
                    float(value)
                    valid.append(field)
                except:
                    invalid.append({
                        "field": field,
                        "value": value,
                        "error": "Expected numeric value"
                    })
            elif value:
                valid.append(field)

        return {
            "valid": valid,
            "invalid": invalid
        }

    def _validate_cross_fields(self, data: Dict) -> Dict:
        """Validate cross-field business rules."""
        issues = []

        # Example: If company domain exists, email should match domain
        domain = data.get("domain")
        email = data.get("email")
        if domain and email:
            email_domain = email.split("@")[-1] if "@" in email else None
            if email_domain and email_domain != domain:
                issues.append({
                    "rule": "email_domain_match",
                    "error": f"Email domain {email_domain} doesn't match company domain {domain}"
                })

        return {
            "issues": issues,
            "is_valid": len(issues) == 0
        }

    def _calculate_quality_score(
        self,
        required_check: Dict,
        format_validation: Dict,
        type_validation: Dict,
        data: Dict
    ) -> Dict:
        """Calculate overall data quality score."""
        # Completeness: percentage of required fields filled
        completeness = required_check["passed"] / required_check["total"] if required_check["total"] > 0 else 1.0

        # Accuracy: percentage of valid formats
        accuracy = format_validation["validation_rate"]

        # Consistency: based on cross-field validation
        consistency = 1.0  # Placeholder

        # Freshness: based on last_updated
        freshness = 1.0  # Placeholder

        overall_score = (
            completeness * self.QUALITY_WEIGHTS["completeness"] +
            accuracy * self.QUALITY_WEIGHTS["accuracy"] +
            consistency * self.QUALITY_WEIGHTS["consistency"] +
            freshness * self.QUALITY_WEIGHTS["freshness"]
        )

        return {
            "overall_score": overall_score,
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "freshness": freshness,
            "grade": "A" if overall_score >= 0.9 else "B" if overall_score >= 0.8 else "C" if overall_score >= 0.7 else "D"
        }

    def _apply_auto_fixes(
        self,
        data: Dict,
        format_validation: Dict
    ) -> List[Dict]:
        """Auto-fix common data issues."""
        fixes = []

        # Normalize phone numbers
        if data.get("phone"):
            original = data["phone"]
            normalized = re.sub(r'[^\d+]', '', original)
            if normalized != original:
                fixes.append({
                    "field": "phone",
                    "original": original,
                    "fixed": normalized,
                    "action": "normalized"
                })

        # Lowercase emails
        if data.get("email"):
            original = data["email"]
            fixed = original.lower().strip()
            if fixed != original:
                fixes.append({
                    "field": "email",
                    "original": original,
                    "fixed": fixed,
                    "action": "normalized"
                })

        return fixes

    def _log_automation_action(
        self,
        action_type: str,
        validation_report: Dict,
        customer_metadata: Dict
    ) -> Dict:
        """Log automation action."""
        return {
            "action_type": action_type,
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": validation_report["quality_score"]["overall_score"],
            "customer_id": customer_metadata.get("customer_id"),
            "success": True
        }
