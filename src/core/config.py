"""
Centralized configuration management using Pydantic Settings.

All configuration loaded from environment variables with validation.
Supports staging and production environments only.
Integrates with Doppler for secrets management.
"""

from typing import Literal, Optional
from pydantic import Field, field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration"""

    url: PostgresDsn = Field(
        ...,
        description="PostgreSQL database URL",
        examples=["postgresql+asyncpg://user:pass@host:5432/db"]
    )
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=60)
    echo: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class APIConfig(BaseSettings):
    """API server configuration"""

    title: str = Field(default="Multi-Agent Support System")
    version: str = Field(default="1.0.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)

    # CORS configuration
    cors_origins: list[str] = Field(
        ...,
        description="Allowed CORS origins (no wildcards allowed)"
    )
    cors_credentials: bool = Field(default=True)
    cors_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    )
    cors_headers: list[str] = Field(default=["*"])

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Ensure no wildcard origins"""
        if "*" in v:
            raise ValueError(
                "Wildcard CORS origin '*' is not allowed. "
                "Specify explicit origins for security."
            )
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"Invalid CORS origin '{origin}'. "
                    "Must start with http:// or https://"
                )
        return v

    model_config = SettingsConfigDict(env_prefix="API_")


class AnthropicConfig(BaseSettings):
    """Anthropic Claude API configuration"""

    api_key: str = Field(..., min_length=10)
    model: str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    timeout: int = Field(default=60, ge=1)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate Anthropic API key format"""
        if not v.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        return v

    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_")


class QdrantConfig(BaseSettings):
    """Qdrant vector database configuration"""

    url: str = Field(..., description="Qdrant server URL")
    api_key: Optional[str] = Field(default=None)
    collection_name: str = Field(default="support_knowledge_base")
    vector_size: int = Field(default=384, ge=1)
    distance_metric: Literal["cosine", "euclid", "dot"] = Field(default="cosine")
    timeout: int = Field(default=30, ge=1)
    prefer_grpc: bool = Field(default=True)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Qdrant URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Qdrant URL must start with http:// or https://")
        return v

    model_config = SettingsConfigDict(env_prefix="QDRANT_")


class LoggingConfig(BaseSettings):
    """Logging configuration"""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    format: Literal["json", "pretty"] = Field(
        default="json",
        description="json for production, pretty for development"
    )
    correlation_id: bool = Field(default=True)
    mask_pii: bool = Field(default=True)
    include_timestamp: bool = Field(default=True)
    include_caller: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="LOG_")


class SentryConfig(BaseSettings):
    """Sentry error tracking configuration"""

    dsn: Optional[str] = Field(default=None)
    environment: str = Field(...)
    traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    profiles_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    send_default_pii: bool = Field(default=False)
    attach_stacktrace: bool = Field(default=True)
    max_breadcrumbs: int = Field(default=100, ge=0, le=1000)

    @field_validator("dsn")
    @classmethod
    def validate_dsn(cls, v: Optional[str]) -> Optional[str]:
        """Validate Sentry DSN format"""
        if v and not v.startswith("https://"):
            raise ValueError("Sentry DSN must start with https://")
        return v

    model_config = SettingsConfigDict(env_prefix="SENTRY_")


class NotificationConfig(BaseSettings):
    """Notification services configuration"""

    enabled: bool = Field(default=False)
    email_enabled: bool = Field(default=False)
    slack_enabled: bool = Field(default=False)
    slack_webhook_url: Optional[str] = Field(default=None)
    email_from: str = Field(default="noreply@example.com")

    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_")


class CacheConfig(BaseSettings):
    """Cache configuration"""

    enabled: bool = Field(default=False)
    redis_url: Optional[str] = Field(default=None)
    ttl: int = Field(default=3600, ge=1)
    max_connections: int = Field(default=10, ge=1, le=100)

    model_config = SettingsConfigDict(env_prefix="CACHE_")


class Settings(BaseSettings):
    """
    Main application settings.

    All configuration loaded from environment variables.
    Only staging and production environments supported.
    Integrates with Doppler for secrets management.
    """

    # Application environment
    environment: Literal["staging", "production"] = Field(
        ...,
        description="Application environment (staging or production only)"
    )

    # Application info
    app_name: str = Field(default="multi-agent-support-system")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Debug mode not allowed in production"""
        environment = info.data.get("environment")
        if v and environment == "production":
            raise ValueError("Debug mode cannot be enabled in production")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.environment == "staging"

    def __repr__(self) -> str:
        """Safe representation without sensitive data"""
        return (
            f"Settings("
            f"environment={self.environment}, "
            f"app_name={self.app_name}, "
            f"app_version={self.app_version})"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance

    Raises:
        ValidationError: If configuration is invalid
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings (for testing).
    
    Returns:
        New Settings instance
    """
    global _settings
    _settings = None
    return get_settings()