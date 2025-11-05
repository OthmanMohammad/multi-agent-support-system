"""
Tests for Customer Domain Validators

These tests verify pure validation functions with no side effects.
"""
import pytest
from services.domain.customer.validators import CustomerValidators


class TestValidateEmail:
    """Tests for email validation"""
    
    @pytest.mark.parametrize("email", [
        "user@example.com",
        "test.user@example.com",
        "user+tag@example.co.uk",
        "firstname.lastname@company.org",
        "user123@test-domain.com",
        "a@b.co",
    ])
    def test_valid_email_formats(self, email):
        """Valid email formats pass validation"""
        result = CustomerValidators.validate_email(email)
        
        assert result.is_success
    
    @pytest.mark.parametrize("email", [
        "",              # Empty
        "   ",           # Whitespace
        "invalid",       # No @
        "@example.com",  # Missing local part
        "user@",         # Missing domain
        "user @example.com",  # Space in local
        "user@domain",   # Missing TLD
        "user@@example.com",  # Double @
        "user@domain..com",   # Double dot
        ".user@example.com",  # Starts with dot
        "user.@example.com",  # Ends with dot
    ])
    def test_invalid_email_formats(self, email):
        """Invalid email formats fail validation"""
        result = CustomerValidators.validate_email(email)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert result.error.details["field"] == "email"
    
    def test_empty_email_fails(self):
        """Empty email fails with required error"""
        result = CustomerValidators.validate_email("")
        
        assert result.is_failure
        assert "required" in result.error.message.lower()
        assert result.error.details["constraint"] == "required"
    
    def test_email_too_long_fails(self):
        """Email exceeding 255 characters fails"""
        long_email = "a" * 250 + "@example.com"  # Over 255 chars
        result = CustomerValidators.validate_email(long_email)
        
        assert result.is_failure
        assert "too long" in result.error.message.lower()
        assert result.error.details["constraint"] == "max_length"
    
    def test_email_at_max_length_passes(self):
        """Email at exactly 255 characters passes"""
        # Create email with exactly 255 chars
        local_part = "a" * 242  # 242 + @ + example.com (12) = 255
        email = f"{local_part}@example.com"
        
        result = CustomerValidators.validate_email(email)
        
        assert result.is_success
    
    def test_email_with_special_characters(self):
        """Email with allowed special characters passes"""
        result = CustomerValidators.validate_email("user+tag.name@example-domain.co.uk")
        
        assert result.is_success


class TestValidatePlan:
    """Tests for plan validation"""
    
    @pytest.mark.parametrize("plan", [
        "free",
        "basic",
        "premium",
        "enterprise",
    ])
    def test_valid_plan_values(self, plan):
        """Valid plan values pass validation"""
        result = CustomerValidators.validate_plan(plan)
        
        assert result.is_success
    
    @pytest.mark.parametrize("plan", [
        "pro",           # Not in list
        "starter",       # Not in list
        "FREE",          # Wrong case
        "Premium",       # Wrong case
        "",              # Empty
        "trial",         # Not in list
        "unlimited",     # Not in list
    ])
    def test_invalid_plan_values(self, plan):
        """Invalid plan values fail validation"""
        result = CustomerValidators.validate_plan(plan)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "must be one of" in result.error.message.lower()
        assert result.error.details["field"] == "plan"
        assert result.error.details["constraint"] == "valid_enum"
    
    def test_plan_validation_error_includes_valid_values(self):
        """Error message includes list of valid values"""
        result = CustomerValidators.validate_plan("invalid")
        
        assert result.is_failure
        for plan in ["free", "basic", "premium", "enterprise"]:
            assert plan in result.error.message