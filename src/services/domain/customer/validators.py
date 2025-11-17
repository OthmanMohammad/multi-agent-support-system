"""
Customer Domain Validators - Pure validation functions
"""

import re
from src.core.result import Result
from src.core.errors import ValidationError


class CustomerValidators:
    """Pure validation functions for customer domain"""
    
    @staticmethod
    def validate_email(email: str) -> Result[None]:
        """
        Validate email format
        
        Args:
            email: Email address
            
        Returns:
            Result with None if valid, error otherwise
        """
        if not email or not email.strip():
            return Result.fail(ValidationError(
                message="Email is required",
                field="email",
                constraint="required"
            ))
        
        # Strict email regex pattern
        # Local part: alphanumeric, dots, underscores, hyphens, plus signs (but not starting/ending with dot)
        # Domain: alphanumeric and hyphens (not starting/ending with hyphen), with dot-separated labels
        # TLD: at least 2 letters
        pattern = r'^[a-zA-Z0-9_%+-]+(?:\.[a-zA-Z0-9_%+-]+)*@[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$'

        # Additional validation: no spaces
        if ' ' in email:
            return Result.fail(ValidationError(
                message="Invalid email format",
                field="email",
                value=email,
                constraint="email_format"
            ))

        # Additional validation: no consecutive dots
        if '..' in email:
            return Result.fail(ValidationError(
                message="Invalid email format",
                field="email",
                value=email,
                constraint="email_format"
            ))

        # Additional validation: no multiple @ signs
        if email.count('@') != 1:
            return Result.fail(ValidationError(
                message="Invalid email format",
                field="email",
                value=email,
                constraint="email_format"
            ))

        if not re.match(pattern, email):
            return Result.fail(ValidationError(
                message="Invalid email format",
                field="email",
                value=email,
                constraint="email_format"
            ))
        
        if len(email) > 255:
            return Result.fail(ValidationError(
                message="Email too long (max 255 characters)",
                field="email",
                value=f"{len(email)} characters",
                constraint="max_length"
            ))
        
        return Result.ok(None)
    
    @staticmethod
    def validate_plan(plan: str) -> Result[None]:
        """
        Validate plan is one of allowed values
        
        Args:
            plan: Plan name
            
        Returns:
            Result with None if valid, error otherwise
        """
        valid_plans = ["free", "basic", "premium", "enterprise"]
        
        if plan not in valid_plans:
            return Result.fail(ValidationError(
                message=f"Plan must be one of {valid_plans}, got '{plan}'",
                field="plan",
                value=plan,
                constraint="valid_enum"
            ))
        
        return Result.ok(None)