"""
PII Filtering - Mask sensitive data in logs

This module provides automatic PII masking to ensure GDPR/CCPA compliance.
Sensitive fields are detected and masked before logging.

Masked Data:
- Passwords, tokens, API keys, secrets
- Email addresses (partial masking)
- Credit card numbers
- SSN and other identifiers
- Authorization headers
"""

import re
from typing import Any, Dict


# Sensitive field patterns
SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "credit_card",
    "ssn",
    "social_security",
    "authorization",
    "auth",
    "cookie",
    "session",
}


def mask_email(email: str) -> str:
    """
    Partially mask email address
    
    Masks middle portion of email while keeping first/last chars
    and domain visible for debugging.
    
    Args:
        email: Email address
    
    Returns:
        Masked email (e.g., us***@example.com)
    
    Example:
        >>> mask_email("user@example.com")
        "us***@example.com"
    """
    if "@" not in email:
        return "***"
    
    local, domain = email.split("@", 1)
    
    if len(local) <= 2:
        return f"***@{domain}"
    
    return f"{local[0]}{local[1]}***@{domain}"


def mask_credit_card(card: str) -> str:
    """
    Mask credit card number
    
    Shows only last 4 digits.
    
    Args:
        card: Credit card number
    
    Returns:
        Masked card (e.g., ****1234)
    """
    digits_only = re.sub(r"\D", "", card)
    
    if len(digits_only) < 4:
        return "****"
    
    return f"****{digits_only[-4:]}"


def should_mask_key(key: str) -> bool:
    """
    Check if key contains sensitive data
    
    Args:
        key: Dictionary key name
    
    Returns:
        True if key should be masked
    """
    key_lower = key.lower()
    
    # Check for exact matches
    if key_lower in SENSITIVE_KEYS:
        return True
    
    # Check for partial matches
    for sensitive in SENSITIVE_KEYS:
        if sensitive in key_lower:
            return True
    
    return False


def mask_value(value: Any) -> str:
    """
    Mask sensitive value
    
    Applies appropriate masking based on value type/format.
    
    Args:
        value: Value to mask
    
    Returns:
        Masked value
    """
    if not isinstance(value, str):
        return "***"
    
    # Email pattern
    if "@" in value and "." in value:
        return mask_email(value)
    
    # Credit card pattern (16 digits)
    if re.match(r"^\d{13,19}$", value.replace(" ", "").replace("-", "")):
        return mask_credit_card(value)
    
    # SSN pattern (xxx-xx-xxxx)
    if re.match(r"^\d{3}-\d{2}-\d{4}$", value):
        return "***-**-" + value[-4:]
    
    # Generic masking
    if len(value) <= 3:
        return "***"
    
    return f"{value[0]}***{value[-1]}"


def mask_sensitive_data(
    logger: Any,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Structlog processor to mask sensitive data
    
    Recursively walks through event dict and masks sensitive fields.
    
    Args:
        logger: Logger instance (unused)
        method_name: Method name (unused)
        event_dict: Log event dictionary
    
    Returns:
        Event dict with sensitive data masked
    """
    return _mask_dict(event_dict)


def _mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively mask sensitive data in dict
    
    Args:
        data: Dictionary to process
    
    Returns:
        Dictionary with sensitive data masked
    """
    masked = {}
    
    for key, value in data.items():
        if should_mask_key(key):
            # Mask sensitive field
            masked[key] = mask_value(value)
        elif isinstance(value, dict):
            # Recursively mask nested dicts
            masked[key] = _mask_dict(value)
        elif isinstance(value, list):
            # Process lists
            masked[key] = [
                _mask_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Keep as-is
            masked[key] = value
    
    return masked