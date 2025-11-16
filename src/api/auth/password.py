"""
Password hashing and verification using bcrypt

This module provides secure password hashing and verification utilities.
"""

from passlib.context import CryptContext

from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


# Password hashing context
# Uses bcrypt algorithm with automatic salt generation
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor (higher = more secure but slower)
)


class PasswordManager:
    """
    Password hashing and verification manager.

    Uses bcrypt algorithm with automatic salt generation and
    cost factor of 12 (industry standard for security/performance balance).

    Features:
    - Secure password hashing with automatic salt
    - Constant-time password verification (prevents timing attacks)
    - Automatic password hash upgrading
    - Password strength validation
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Bcrypt password hash

        Example:
            >>> hash = PasswordManager.hash_password("my_secure_password123")
            >>> print(hash)
            $2b$12$...  (60 character hash)
        """
        logger.debug("password_hashing_started")

        hashed = pwd_context.hash(password)

        logger.debug("password_hashed_successfully")

        return hashed

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hashed password

        Returns:
            True if password matches, False otherwise

        Example:
            >>> hash = PasswordManager.hash_password("password123")
            >>> PasswordManager.verify_password("password123", hash)
            True
            >>> PasswordManager.verify_password("wrong_password", hash)
            False
        """
        logger.debug("password_verification_started")

        # Constant-time verification
        is_valid = pwd_context.verify(plain_password, hashed_password)

        if is_valid:
            logger.debug("password_verification_successful")
        else:
            logger.debug("password_verification_failed")

        return is_valid

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password hash needs to be updated.

        This can happen if:
        - Cost factor was increased
        - Algorithm was changed
        - Hash is using deprecated scheme

        Args:
            hashed_password: Bcrypt hashed password

        Returns:
            True if hash should be regenerated, False otherwise

        Example:
            >>> if PasswordManager.needs_rehash(user.password_hash):
            ...     user.password_hash = PasswordManager.hash_password(plain_password)
        """
        return pwd_context.needs_update(hashed_password)

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password meets minimum security requirements.

        Requirements:
        - Minimum 8 characters
        - Maximum 128 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Plain text password to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> is_valid, error = PasswordManager.validate_password_strength("Pass123!")
            >>> if not is_valid:
            ...     print(error)
        """
        # Check length
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if len(password) > 128:
            return False, "Password must be at most 128 characters long"

        # Check for lowercase
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        # Check for uppercase
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        # Check for digit
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        # Check for special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return (
                False,
                f"Password must contain at least one special character ({special_chars})"
            )

        return True, ""

    @staticmethod
    def generate_password_reset_token() -> str:
        """
        Generate a secure random token for password reset.

        Returns:
            32-character URL-safe token

        Example:
            >>> token = PasswordManager.generate_password_reset_token()
            >>> print(len(token))
            32
        """
        import secrets

        # Generate 32-byte (256-bit) token
        token = secrets.token_urlsafe(32)

        logger.debug("password_reset_token_generated")

        return token

    @staticmethod
    def generate_email_verification_token() -> str:
        """
        Generate a secure random token for email verification.

        Returns:
            32-character URL-safe token

        Example:
            >>> token = PasswordManager.generate_email_verification_token()
            >>> print(len(token))
            32
        """
        import secrets

        # Generate 32-byte (256-bit) token
        token = secrets.token_urlsafe(32)

        logger.debug("email_verification_token_generated")

        return token
