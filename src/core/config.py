"""
Centralized configuration management using Pydantic Settings.

All configuration loaded from environment variables with validation.
Supports staging and production environments only.
Integrates with Doppler for secrets management.
"""

from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration"""

    url: PostgresDsn = Field(
        ...,
        description="PostgreSQL database URL",
        examples=["postgresql+asyncpg://user:pass@host:5432/db"],
    )
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=60)
    echo: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class APIConfig(BaseSettings):
    """API server configuration"""

    title: str = Field(default="Multi-Agent Support System")
    version: str = Field(default="1.4.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)

    # CORS configuration
    cors_origins: list[str] = Field(..., description="Allowed CORS origins (no wildcards allowed)")
    cors_credentials: bool = Field(default=True)
    cors_methods: list[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
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
                "Wildcard CORS origin '*' is not allowed. Specify explicit origins for security."
            )
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"Invalid CORS origin '{origin}'. Must start with http:// or https://"
                )
        return v

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AnthropicConfig(BaseSettings):
    """Anthropic Claude API configuration"""

    api_key: str = Field(..., min_length=10)
    model: str = Field(
        default="claude-3-haiku-20240307",
        description="Claude model to use (set via ANTHROPIC_MODEL env var)",
    )
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

    model_config = SettingsConfigDict(
        env_prefix="ANTHROPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class QdrantConfig(BaseSettings):
    """Qdrant vector database configuration"""

    url: str = Field(..., description="Qdrant server URL")
    api_key: str | None = Field(default=None)
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

    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class LoggingConfig(BaseSettings):
    """Logging configuration"""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    format: Literal["json", "pretty"] = Field(
        default="json", description="json for production, pretty for development"
    )
    correlation_id: bool = Field(default=True)
    mask_pii: bool = Field(default=True)
    include_timestamp: bool = Field(default=True)
    include_caller: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class SentryConfig(BaseSettings):
    """Sentry error tracking configuration"""

    dsn: str | None = Field(default=None)
    environment: str = Field(...)
    traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    profiles_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    send_default_pii: bool = Field(default=False)
    attach_stacktrace: bool = Field(default=True)
    max_breadcrumbs: int = Field(default=100, ge=0, le=1000)

    @field_validator("dsn")
    @classmethod
    def validate_dsn(cls, v: str | None) -> str | None:
        """Validate Sentry DSN format"""
        if v and not v.startswith("https://"):
            raise ValueError("Sentry DSN must start with https://")
        return v

    model_config = SettingsConfigDict(
        env_prefix="SENTRY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class NotificationConfig(BaseSettings):
    """Notification services configuration"""

    enabled: bool = Field(default=False)
    email_enabled: bool = Field(default=False)
    slack_enabled: bool = Field(default=False)
    slack_webhook_url: str | None = Field(default=None)
    email_from: str = Field(default="noreply@example.com")

    model_config = SettingsConfigDict(
        env_prefix="NOTIFICATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class CacheConfig(BaseSettings):
    """Cache configuration"""

    enabled: bool = Field(default=False)
    redis_url: str | None = Field(default=None)
    ttl: int = Field(default=3600, ge=1)
    max_connections: int = Field(default=10, ge=1, le=100)

    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class JWTConfig(BaseSettings):
    """JWT authentication configuration"""

    secret_key: str = Field(
        ..., min_length=32, description="Secret key for JWT encoding (min 32 characters)"
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=90)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough"""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class RedisConfig(BaseSettings):
    """Redis configuration for caching and rate limiting"""

    enabled: bool = Field(
        default=True, description="Enable Redis (set to False for development without Redis)"
    )
    url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    password: str | None = Field(default=None)
    max_connections: int = Field(default=50, ge=1, le=500)
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)
    decode_responses: bool = Field(default=True)

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)

    # Token blacklist
    token_blacklist_enabled: bool = Field(default=True)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Redis URL format"""
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class ContextEnrichmentConfig(BaseSettings):
    """Context enrichment system configuration"""

    # Enable/disable features
    enabled: bool = Field(default=True)
    enable_l1_cache: bool = Field(default=True, description="In-memory L1 cache")
    enable_l2_cache: bool = Field(default=True, description="Redis L2 cache")
    enable_external_apis: bool = Field(default=False, description="External data providers")

    # Cache settings
    l1_cache_ttl: int = Field(default=30, ge=1, le=300, description="L1 cache TTL in seconds")
    l2_cache_ttl: int = Field(default=300, ge=1, le=3600, description="L2 cache TTL in seconds")
    l1_max_size: int = Field(default=1000, ge=100, le=10000, description="L1 cache max entries")

    # Timeout settings
    provider_timeout_ms: int = Field(
        default=500, ge=100, le=5000, description="Individual provider timeout (ms)"
    )
    orchestrator_timeout_ms: int = Field(
        default=200, ge=50, le=2000, description="Total enrichment timeout (ms)"
    )

    # Parallel execution
    parallel_execution: bool = Field(default=True, description="Execute providers in parallel")
    max_concurrent_providers: int = Field(
        default=10, ge=1, le=50, description="Max concurrent provider calls"
    )

    # PII filtering
    enable_pii_filtering: bool = Field(default=True, description="Enable PII masking")
    pii_filter_level: Literal["none", "partial", "full"] = Field(default="partial")

    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable OpenTelemetry tracing")

    # Provider-specific settings
    customer_intelligence_enabled: bool = Field(default=True)
    subscription_details_enabled: bool = Field(default=True)
    support_history_enabled: bool = Field(default=True)
    engagement_metrics_enabled: bool = Field(default=True)
    account_health_enabled: bool = Field(default=True)
    sales_pipeline_enabled: bool = Field(default=True)
    feature_usage_enabled: bool = Field(default=True)
    security_context_enabled: bool = Field(
        default=False, description="Security context provider (opt-in)"
    )

    model_config = SettingsConfigDict(
        env_prefix="CONTEXT_ENRICHMENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class VastAIConfig(BaseSettings):
    """
    Vast.ai GPU orchestration configuration.

    Part of Phase 3: On-demand GPU rental for vLLM backend.
    """

    # Vast.ai API configuration
    api_key: str | None = Field(
        default=None, description="Vast.ai API key (optional - vLLM backend requires this)"
    )

    # Budget and cost management
    budget_limit: float = Field(
        default=15.0, ge=0.0, description="Maximum budget in USD for GPU rental"
    )
    session_budget_limit: float = Field(
        default=2.0, ge=0.0, description="Maximum budget per GPU session in USD"
    )

    # GPU instance settings
    default_keep_alive_minutes: int = Field(
        default=45, ge=5, le=180, description="Default keep-alive time for GPU instances (minutes)"
    )
    max_startup_time_minutes: int = Field(
        default=10, ge=1, le=30, description="Maximum time to wait for vLLM to start (minutes)"
    )

    # Health check settings
    health_check_interval_seconds: int = Field(
        default=60, ge=10, le=300, description="Interval for GPU instance health checks (seconds)"
    )
    health_check_timeout_seconds: int = Field(
        default=5, ge=1, le=30, description="Timeout for individual health check requests (seconds)"
    )

    # Search and retry settings
    max_search_retries: int = Field(
        default=3, ge=1, le=10, description="Maximum retries for GPU search/launch"
    )
    search_timeout_seconds: int = Field(
        default=30, ge=10, le=120, description="Timeout for Vast.ai API search requests (seconds)"
    )

    # vLLM configuration
    vllm_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="Model to load in vLLM")
    vllm_gpu_memory_utilization: float = Field(
        default=0.95, ge=0.1, le=1.0, description="GPU memory utilization for vLLM (0-1)"
    )
    vllm_max_model_len: int = Field(
        default=4096, ge=512, le=32768, description="Maximum context length for vLLM model"
    )

    # Safety settings
    auto_destroy_on_error: bool = Field(
        default=True, description="Automatically destroy GPU instance on errors"
    )
    auto_destroy_on_shutdown: bool = Field(
        default=True, description="Automatically destroy GPU instance on application shutdown"
    )
    orphan_cleanup_enabled: bool = Field(
        default=True, description="Enable automatic cleanup of orphaned instances"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Validate Vast.ai API key format if provided"""
        if v and not v.startswith(("sk_", "vastai_")):
            # Note: Vast.ai API keys may have different formats
            # This is a lenient check
            pass
        return v

    model_config = SettingsConfigDict(
        env_prefix="VASTAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class ModalConfig(BaseSettings):
    """
    Modal.com serverless GPU configuration.

    Part of Phase 3: Serverless vLLM deployment (alternative to Vast.ai).

    Key Differences from Vast.ai:
        - No instance management (Modal auto-scales)
        - No budget tracking (set limits in Modal dashboard)
        - Pay-per-second of GPU usage
        - Simpler configuration (just web URL + token)
    """

    # Modal API configuration
    token_id: str | None = Field(
        default=None, description="Modal API token ID (optional - only needed for deployment)"
    )
    token_secret: str | None = Field(
        default=None, description="Modal API token secret (optional - only needed for deployment)"
    )

    # Modal deployment
    web_url: str | None = Field(
        default=None, description="Modal web URL (e.g., https://yourapp--modal-run.modal.run)"
    )
    app_name: str = Field(default="multi-agent-vllm-inference", description="Modal app name")

    # vLLM model configuration
    model: str = Field(default="Qwen/Qwen2.5-7B-Instruct", description="Model to deploy on Modal")
    gpu_type: Literal["L4", "A100", "H100", "A10G"] = Field(
        default="L4",
        description="GPU type (L4: $0.80/hr, A100: $3/hr, H100: $4.50/hr, A10G: $1/hr)",
    )
    scaledown_window_minutes: int = Field(
        default=5, ge=1, le=60, description="Keep GPU warm for N minutes after last request"
    )

    # Health and timeout settings
    health_check_timeout_seconds: int = Field(
        default=30, ge=5, le=120, description="Timeout for health check requests (seconds)"
    )
    startup_timeout_minutes: int = Field(
        default=10, ge=1, le=30, description="Maximum time to wait for Modal to start (minutes)"
    )

    # Request settings
    max_retries: int = Field(
        default=3, ge=1, le=10, description="Maximum retry attempts for failed requests"
    )
    request_timeout_seconds: int = Field(
        default=120, ge=30, le=600, description="Timeout for chat completion requests (seconds)"
    )

    @field_validator("web_url")
    @classmethod
    def validate_web_url(cls, v: str | None) -> str | None:
        """Validate Modal web URL format if provided"""
        if v:
            if not v.startswith("https://"):
                raise ValueError("Modal web URL must start with https://")
            if not (".modal.run" in v or "modal.com" in v):
                raise ValueError("Modal web URL must contain .modal.run or modal.com")
        return v

    @field_validator("token_id")
    @classmethod
    def validate_token_id(cls, v: str | None) -> str | None:
        """Validate Modal token ID format if provided"""
        if v and not v.startswith("ak-"):
            raise ValueError("Modal token ID must start with 'ak-'")
        return v

    model_config = SettingsConfigDict(
        env_prefix="MODAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """
    Main application settings.

    All configuration loaded from environment variables.
    Only staging and production environments supported.
    Integrates with Doppler for secrets management.
    """

    # Application environment
    environment: Literal["staging", "production"] = Field(
        default="staging", description="Application environment (staging or production only)"
    )

    # Application info
    app_name: str = Field(default="multi-agent-support-system")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    context_enrichment: ContextEnrichmentConfig = Field(default_factory=ContextEnrichmentConfig)
    vastai: VastAIConfig = Field(default_factory=VastAIConfig)
    modal: ModalConfig = Field(default_factory=ModalConfig)

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Debug mode not allowed in production"""
        environment = info.data.get("environment")
        if v and environment == "production":
            raise ValueError("Debug mode cannot be enabled in production")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
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
_settings: Settings | None = None


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
