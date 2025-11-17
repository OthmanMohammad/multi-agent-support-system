"""
API Key Generation and Validation

This module provides utilities for generating and validating API keys
for programmatic authentication.
"""

import secrets
from typing import Tuple
from datetime import datetime, timedelta, UTC
from passlib.context import CryptContext

from src.utils.logging.setup import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


# API key hashing context (same as passwords - bcrypt)
api_key_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class APIKeyManager:
    """
    API key generation and validation manager.

    API Key Format:
        msa_live_RANDOMSTRING  (production)
        msa_test_RANDOMSTRING  (testing)

    Where RANDOMSTRING is a 32-character URL-safe random string.

    Features:
    - Secure random key generation
    - Environment-aware prefixes (live vs test)
    - Bcrypt hashing before storage
    - Prefix extraction for quick database lookup
    - Key validation
    """

    # Key prefixes by environment
    PREFIX_PRODUCTION = "msa_live_"
    PREFIX_TEST = "msa_test_"

    # Key length (excluding prefix)
    KEY_LENGTH = 32  # 256 bits of entropy

    @classmethod
    def generate_api_key(cls, is_test: bool = False) -> Tuple[str, str, str]:
        """
        Generate a new API key.

        Args:
            is_test: Whether this is a test key (default: False for production)

        Returns:
            Tuple of (full_key, key_prefix, key_hash)
            - full_key: The complete API key (show to user once!)
            - key_prefix: First 20 chars for database lookup
            - key_hash: Bcrypt hash for database storage

        Example:
            >>> full_key, prefix, hash = APIKeyManager.generate_api_key()
            >>> print(full_key)
            msa_live_AbCd1234...  (full key)
            >>> print(prefix)
            msa_live_AbCd1234567  (first 20 chars)
            >>> print(hash)
            $2b$12$...  (bcrypt hash)
        """
        # Choose prefix based on environment
        if is_test or settings.environment == "staging":
            prefix_type = cls.PREFIX_TEST
        else:
            prefix_type = cls.PREFIX_PRODUCTION

        # Generate random string
        random_string = secrets.token_urlsafe(cls.KEY_LENGTH)

        # Construct full key
        full_key = f"{prefix_type}{random_string}"

        # Extract prefix (first 20 characters) for quick lookup
        key_prefix = full_key[:20]

        # Hash the full key for storage
        key_hash = api_key_context.hash(full_key)

        logger.info(
            "api_key_generated",
            prefix=key_prefix,
            is_test=is_test,
            environment=settings.environment
        )

        return full_key, key_prefix, key_hash

    @classmethod
    def validate_api_key_format(cls, api_key: str) -> Tuple[bool, str]:
        """
        Validate API key format.

        Checks:
        - Starts with valid prefix (msa_live_ or msa_test_)
        - Has sufficient length
        - Contains only URL-safe characters

        Args:
            api_key: API key to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = APIKeyManager.validate_api_key_format("invalid")
            >>> print(is_valid, error)
            False, "API key must start with msa_live_ or msa_test_"
        """
        # Check prefix
        if not (api_key.startswith(cls.PREFIX_PRODUCTION) or
                api_key.startswith(cls.PREFIX_TEST)):
            return False, "API key must start with msa_live_ or msa_test_"

        # Check minimum length
        min_length = len(cls.PREFIX_PRODUCTION) + 20  # prefix + some random chars
        if len(api_key) < min_length:
            return False, f"API key must be at least {min_length} characters"

        # Check characters (URL-safe base64: A-Za-z0-9_-)
        # Split into prefix and random part
        prefix = (cls.PREFIX_PRODUCTION if api_key.startswith(cls.PREFIX_PRODUCTION)
                  else cls.PREFIX_TEST)
        random_part = api_key[len(prefix):]

        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
        if not all(c in allowed_chars for c in random_part):
            return False, "API key contains invalid characters"

        return True, ""

    @classmethod
    def verify_api_key(cls, plain_key: str, hashed_key: str) -> bool:
        """
        Verify an API key against its hash.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            plain_key: Plain text API key from request
            hashed_key: Bcrypt hashed key from database

        Returns:
            True if key matches, False otherwise

        Example:
            >>> full_key, prefix, hash = APIKeyManager.generate_api_key()
            >>> APIKeyManager.verify_api_key(full_key, hash)
            True
            >>> APIKeyManager.verify_api_key("wrong_key", hash)
            False
        """
        logger.debug("api_key_verification_started")

        # Constant-time verification
        is_valid = api_key_context.verify(plain_key, hashed_key)

        if is_valid:
            logger.debug("api_key_verification_successful")
        else:
            logger.warning("api_key_verification_failed")

        return is_valid

    @classmethod
    def extract_prefix(cls, api_key: str) -> str:
        """
        Extract key prefix for database lookup.

        Args:
            api_key: Full API key

        Returns:
            First 20 characters (prefix for lookup)

        Example:
            >>> prefix = APIKeyManager.extract_prefix("msa_live_AbCd1234567890...")
            >>> print(prefix)
            msa_live_AbCd1234567
        """
        return api_key[:20]

    @classmethod
    def is_test_key(cls, api_key: str) -> bool:
        """
        Check if API key is a test key.

        Args:
            api_key: Full API key

        Returns:
            True if test key, False if production key

        Example:
            >>> APIKeyManager.is_test_key("msa_test_AbCd...")
            True
            >>> APIKeyManager.is_test_key("msa_live_AbCd...")
            False
        """
        return api_key.startswith(cls.PREFIX_TEST)

    @classmethod
    def calculate_expiration(
        cls,
        days: int = 90
    ) -> datetime:
        """
        Calculate API key expiration date.

        Args:
            days: Number of days until expiration (default: 90)

        Returns:
            Expiration datetime

        Example:
            >>> expiration = APIKeyManager.calculate_expiration(days=30)
            >>> print(expiration)
            2025-12-16 12:00:00+00:00
        """
        return datetime.now(UTC) + timedelta(days=days)

    @classmethod
    def is_expired(cls, expires_at: datetime) -> bool:
        """
        Check if API key is expired.

        Args:
            expires_at: Expiration datetime

        Returns:
            True if expired, False otherwise

        Example:
            >>> from datetime import datetime
            >>> past = datetime(2020, 1, 1)
            >>> APIKeyManager.is_expired(past)
            True
        """
        if not expires_at:
            return False
        return datetime.now(UTC) > expires_at
