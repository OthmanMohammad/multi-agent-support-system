"""
PII filtering and masking for context data.

Detects and masks personally identifiable information (PII) to ensure
privacy and compliance with data protection regulations.
"""

from typing import Dict, Any, Optional, Pattern
import re
import structlog

from src.services.infrastructure.context_enrichment.types import PIIFilterLevel

logger = structlog.get_logger(__name__)


class PIIFilter:
    """
    Filter and mask PII in context data.

    Detects and masks:
    - Email addresses
    - Phone numbers
    - Social Security Numbers (SSN)
    - Credit card numbers
    - Custom patterns

    Example:
        >>> filter = PIIFilter()
        >>> filtered = filter.filter(
        ...     {"email": "john@example.com"},
        ...     PIIFilterLevel.PARTIAL
        ... )
        >>> print(filtered["email"])  # "j***@example.com"
    """

    # Regex patterns for PII detection
    PATTERNS = {
        "email": re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        "phone": re.compile(
            r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
        ),
        "ssn": re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        ),
        "credit_card": re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        ),
        "ip_address": re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ),
    }

    # Fields that commonly contain PII
    PII_FIELDS = {
        "email",
        "phone",
        "phone_number",
        "mobile",
        "ssn",
        "social_security_number",
        "credit_card",
        "card_number",
        "ip_address",
        "address",
        "street",
        "postal_code",
        "zip_code",
    }

    def __init__(self):
        """Initialize PII filter"""
        self.logger = logger.bind(component="pii_filter")

    def filter(
        self,
        data: Dict[str, Any],
        level: PIIFilterLevel = PIIFilterLevel.PARTIAL
    ) -> Dict[str, Any]:
        """
        Filter PII from data.

        Args:
            data: Data dictionary to filter
            level: Filtering level (none, partial, full)

        Returns:
            Filtered data dictionary

        Example:
            >>> filter = PIIFilter()
            >>> filtered = filter.filter(
            ...     {"email": "test@example.com", "plan": "enterprise"},
            ...     PIIFilterLevel.PARTIAL
            ... )
        """
        if level == PIIFilterLevel.NONE:
            return data

        filtered = {}
        pii_found = []

        for key, value in data.items():
            # Handle nested dictionaries
            if isinstance(value, dict):
                filtered[key] = self.filter(value, level)

            # Handle lists
            elif isinstance(value, list):
                filtered[key] = [
                    self.filter(item, level) if isinstance(item, dict) else item
                    for item in value
                ]

            # Handle strings
            elif isinstance(value, str):
                # Check if this is a known PII field
                if key.lower() in self.PII_FIELDS:
                    filtered[key] = self._mask_by_field(key, value, level)
                    pii_found.append(key)
                else:
                    # Scan for PII patterns
                    filtered[key] = self._mask_patterns(value, level)

            # Pass through other types
            else:
                filtered[key] = value

        if pii_found:
            self.logger.debug(
                "pii_filtered",
                fields=pii_found,
                level=level.value
            )

        return filtered

    def _mask_by_field(
        self,
        field_name: str,
        value: str,
        level: PIIFilterLevel
    ) -> str:
        """
        Mask value based on field name.

        Args:
            field_name: Field name
            value: Value to mask
            level: Filtering level

        Returns:
            Masked value
        """
        field_lower = field_name.lower()

        if "email" in field_lower:
            return self.mask_email(value, level)
        elif "phone" in field_lower or "mobile" in field_lower:
            return self.mask_phone(value, level)
        elif "ssn" in field_lower or "social_security" in field_lower:
            return self.mask_ssn(value, level)
        elif "credit_card" in field_lower or "card_number" in field_lower:
            return self.mask_credit_card(value, level)
        else:
            # Full redaction for unknown PII fields
            return self._redact(value, level)

    def _mask_patterns(
        self,
        text: str,
        level: PIIFilterLevel
    ) -> str:
        """
        Scan text for PII patterns and mask them.

        Args:
            text: Text to scan
            level: Filtering level

        Returns:
            Text with PII masked
        """
        result = text

        # Apply each pattern
        for pii_type, pattern in self.PATTERNS.items():
            if pattern.search(result):
                if pii_type == "email":
                    result = pattern.sub(
                        lambda m: self.mask_email(m.group(0), level),
                        result
                    )
                elif pii_type == "phone":
                    result = pattern.sub(
                        lambda m: self.mask_phone(m.group(0), level),
                        result
                    )
                elif pii_type == "ssn":
                    result = pattern.sub(
                        lambda m: self.mask_ssn(m.group(0), level),
                        result
                    )
                elif pii_type == "credit_card":
                    result = pattern.sub(
                        lambda m: self.mask_credit_card(m.group(0), level),
                        result
                    )
                elif pii_type == "ip_address":
                    result = pattern.sub("[IP_REDACTED]", result)

        return result

    def _redact(self, value: str, level: PIIFilterLevel) -> str:
        """Fully redact a value"""
        if level == PIIFilterLevel.FULL:
            return "[REDACTED]"
        elif level == PIIFilterLevel.PARTIAL:
            if len(value) <= 2:
                return "*" * len(value)
            return value[0] + "*" * (len(value) - 2) + value[-1]
        return value

    def mask_value(
        self,
        value: str,
        value_type: str,
        level: PIIFilterLevel = PIIFilterLevel.PARTIAL
    ) -> str:
        """
        Mask individual PII value.

        Args:
            value: Value to mask
            value_type: Type of PII (email, phone, ssn, credit_card)
            level: Filtering level

        Returns:
            Masked value

        Example:
            >>> filter = PIIFilter()
            >>> masked = filter.mask_value(
            ...     "john@example.com",
            ...     "email",
            ...     PIIFilterLevel.PARTIAL
            ... )
        """
        if level == PIIFilterLevel.NONE:
            return value

        if value_type == "email":
            return self.mask_email(value, level)
        elif value_type == "phone":
            return self.mask_phone(value, level)
        elif value_type == "ssn":
            return self.mask_ssn(value, level)
        elif value_type == "credit_card":
            return self.mask_credit_card(value, level)
        else:
            return self._redact(value, level)

    @staticmethod
    def mask_email(email: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
        """
        Mask email address.

        Args:
            email: Email to mask
            level: Filtering level

        Returns:
            Masked email

        Example:
            >>> mask_email("john.doe@example.com", PIIFilterLevel.PARTIAL)
            'j***@example.com'
        """
        if level == PIIFilterLevel.NONE:
            return email

        if level == PIIFilterLevel.FULL:
            return "[EMAIL_REDACTED]"

        # Partial masking
        if "@" not in email:
            return email

        local, domain = email.split("@", 1)

        if len(local) <= 1:
            masked_local = "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 1)

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
        """
        Mask phone number.

        Args:
            phone: Phone number to mask
            level: Filtering level

        Returns:
            Masked phone number

        Example:
            >>> mask_phone("123-456-7890", PIIFilterLevel.PARTIAL)
            '***-***-7890'
        """
        if level == PIIFilterLevel.NONE:
            return phone

        if level == PIIFilterLevel.FULL:
            return "[PHONE_REDACTED]"

        # Extract digits
        digits = re.sub(r'\D', '', phone)

        if len(digits) < 4:
            return "*" * len(digits)

        # Show last 4 digits
        masked = "*" * (len(digits) - 4) + digits[-4:]

        # Try to preserve formatting
        if "-" in phone:
            # Format: ***-***-7890
            if len(digits) == 10:
                return f"{masked[0:3]}-{masked[3:6]}-{masked[6:10]}"
        elif "(" in phone:
            # Format: (***) ***-7890
            if len(digits) == 10:
                return f"({masked[0:3]}) {masked[3:6]}-{masked[6:10]}"

        return masked

    @staticmethod
    def mask_ssn(ssn: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
        """
        Mask Social Security Number.

        Args:
            ssn: SSN to mask
            level: Filtering level

        Returns:
            Masked SSN

        Example:
            >>> mask_ssn("123-45-6789", PIIFilterLevel.PARTIAL)
            '***-**-6789'
        """
        if level == PIIFilterLevel.NONE:
            return ssn

        if level == PIIFilterLevel.FULL:
            return "[SSN_REDACTED]"

        # Show last 4 digits
        digits = re.sub(r'\D', '', ssn)

        if len(digits) == 9:
            return f"***-**-{digits[-4:]}"

        return "*" * len(ssn)

    @staticmethod
    def mask_credit_card(
        card: str,
        level: PIIFilterLevel = PIIFilterLevel.PARTIAL
    ) -> str:
        """
        Mask credit card number.

        Args:
            card: Credit card number to mask
            level: Filtering level

        Returns:
            Masked credit card number

        Example:
            >>> mask_credit_card("4532-1234-5678-9010", PIIFilterLevel.PARTIAL)
            '****-****-****-9010'
        """
        if level == PIIFilterLevel.NONE:
            return card

        if level == PIIFilterLevel.FULL:
            return "[CARD_REDACTED]"

        # Extract digits
        digits = re.sub(r'\D', '', card)

        if len(digits) < 4:
            return "*" * len(digits)

        # Show last 4 digits
        masked_digits = "*" * (len(digits) - 4) + digits[-4:]

        # Preserve formatting
        if "-" in card or " " in card:
            separator = "-" if "-" in card else " "
            # Format: ****-****-****-9010
            parts = [masked_digits[i:i+4] for i in range(0, len(masked_digits), 4)]
            return separator.join(parts)

        return masked_digits


# Convenience functions
_filter_instance: Optional[PIIFilter] = None


def _get_filter() -> PIIFilter:
    """Get or create filter instance"""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = PIIFilter()
    return _filter_instance


def filter_pii(
    data: Dict[str, Any],
    level: PIIFilterLevel = PIIFilterLevel.PARTIAL
) -> Dict[str, Any]:
    """
    Convenience function to filter PII.

    Args:
        data: Data to filter
        level: Filtering level

    Returns:
        Filtered data

    Example:
        >>> filtered = filter_pii({"email": "test@example.com"})
    """
    return _get_filter().filter(data, level)


def mask_email(email: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
    """Convenience function to mask email"""
    return PIIFilter.mask_email(email, level)


def mask_phone(phone: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
    """Convenience function to mask phone"""
    return PIIFilter.mask_phone(phone, level)


def mask_ssn(ssn: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
    """Convenience function to mask SSN"""
    return PIIFilter.mask_ssn(ssn, level)


def mask_credit_card(card: str, level: PIIFilterLevel = PIIFilterLevel.PARTIAL) -> str:
    """Convenience function to mask credit card"""
    return PIIFilter.mask_credit_card(card, level)
