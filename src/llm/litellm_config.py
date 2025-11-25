"""
LiteLLM Configuration Module

Centralized configuration for LLM backends (Anthropic, vLLM).
Enables runtime backend switching and model configuration management.

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)


class LLMBackend(str, Enum):
    """Supported LLM backends"""
    ANTHROPIC = "anthropic"
    VLLM = "vllm"


class ModelConfig(BaseModel):
    """
    Configuration for a specific model.

    Attributes:
        provider: LiteLLM provider name (anthropic, openai, etc.)
        model_name: Full model name/identifier
        api_base: Optional API base URL (for vLLM)
        api_key: Optional API key override
        max_tokens: Maximum tokens for completion
        temperature: Sampling temperature (0-1)
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts on failure
    """
    provider: str
    model_name: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    max_retries: int = 2

    class Config:
        frozen = False  # Allow modification for dynamic endpoint updates


class LiteLLMConfig:
    """
    Central LiteLLM configuration manager.

    Manages:
    - Backend selection (Anthropic vs vLLM)
    - Model configurations for each backend
    - Runtime backend switching
    - vLLM endpoint management

    Usage:
        >>> config = litellm_config
        >>> config.switch_backend(LLMBackend.VLLM)
        >>> model_config = config.get_model_config("haiku")
    """

    def __init__(self):
        self.current_backend: LLMBackend = LLMBackend.ANTHROPIC
        self.vllm_endpoint: Optional[str] = None

        # Get API key from settings (loads from .env via Pydantic)
        settings = get_settings()
        anthropic_api_key = settings.anthropic.api_key

        # Model configurations for each backend
        self.models: Dict[LLMBackend, Dict[str, ModelConfig]] = {
            LLMBackend.ANTHROPIC: {
                # Fast, cost-effective model for routing and simple tasks
                "haiku": ModelConfig(
                    provider="anthropic",
                    model_name="claude-3-haiku-20240307",
                    api_key=anthropic_api_key,
                    max_tokens=4096,
                    temperature=0.7,
                ),
                # Balanced model for most specialist tasks
                "sonnet": ModelConfig(
                    provider="anthropic",
                    model_name="claude-3-5-sonnet-20241022",
                    api_key=anthropic_api_key,
                    max_tokens=8192,
                    temperature=0.7,
                ),
                # Most capable model for complex reasoning
                "opus": ModelConfig(
                    provider="anthropic",
                    model_name="claude-3-opus-20240229",
                    api_key=anthropic_api_key,
                    max_tokens=4096,
                    temperature=0.7,
                ),
            },
            LLMBackend.VLLM: {
                # Qwen 2.5 7B - open source model for vLLM
                "qwen": ModelConfig(
                    provider="openai",  # vLLM uses OpenAI-compatible API
                    model_name="Qwen/Qwen2.5-7B-Instruct",
                    api_base=None,  # Set dynamically when vLLM endpoint is configured
                    max_tokens=4096,
                    temperature=0.7,
                ),
            },
        }

        logger.info(
            "litellm_config_initialized",
            default_backend=self.current_backend.value,
            anthropic_models=list(self.models[LLMBackend.ANTHROPIC].keys()),
            vllm_models=list(self.models[LLMBackend.VLLM].keys()),
        )

    def get_model_config(
        self,
        model_tier: str = "haiku"
    ) -> ModelConfig:
        """
        Get model configuration for current backend.

        Args:
            model_tier: Model tier for Anthropic (haiku/sonnet/opus)
                       Ignored for vLLM (always uses qwen)

        Returns:
            ModelConfig for the selected model

        Examples:
            >>> config = litellm_config
            >>> # Get Anthropic Haiku config
            >>> haiku_config = config.get_model_config("haiku")
            >>>
            >>> # Switch to vLLM and get config
            >>> config.switch_backend(LLMBackend.VLLM)
            >>> vllm_config = config.get_model_config()  # tier ignored for vLLM
        """
        backend_models = self.models[self.current_backend]

        if self.current_backend == LLMBackend.ANTHROPIC:
            # Use requested tier, fallback to haiku if invalid
            config = backend_models.get(model_tier, backend_models["haiku"])
        else:  # vLLM
            # vLLM always uses qwen model
            config = backend_models["qwen"]

            # Set dynamic endpoint if configured
            if self.vllm_endpoint:
                # Create a copy to avoid modifying the original
                config = config.copy(deep=True)
                config.api_base = f"{self.vllm_endpoint}/v1"

        return config

    def switch_backend(self, backend: LLMBackend) -> None:
        """
        Switch to different LLM backend.

        Args:
            backend: Target backend (ANTHROPIC or VLLM)

        Raises:
            ValueError: If switching to vLLM without endpoint configured

        Examples:
            >>> config = litellm_config
            >>> config.switch_backend(LLMBackend.VLLM)
            >>> config.switch_backend(LLMBackend.ANTHROPIC)
        """
        # Validate vLLM endpoint is set
        if backend == LLMBackend.VLLM and not self.vllm_endpoint:
            logger.warning(
                "vllm_switch_attempted_without_endpoint",
                current_backend=self.current_backend.value,
            )
            raise ValueError(
                "Cannot switch to vLLM backend: endpoint not configured. "
                "Call set_vllm_endpoint() first."
            )

        old_backend = self.current_backend
        self.current_backend = backend

        logger.info(
            "llm_backend_switched",
            from_backend=old_backend.value,
            to_backend=backend.value,
        )

    def set_vllm_endpoint(self, endpoint: str) -> None:
        """
        Set vLLM endpoint URL.

        Args:
            endpoint: vLLM server URL (e.g., "http://165.22.45.67:8000")

        Examples:
            >>> config = litellm_config
            >>> config.set_vllm_endpoint("http://165.22.45.67:8000")
            >>> config.switch_backend(LLMBackend.VLLM)
        """
        # Normalize endpoint (remove trailing slash)
        endpoint = endpoint.rstrip('/')

        self.vllm_endpoint = endpoint

        logger.info(
            "vllm_endpoint_configured",
            endpoint=endpoint,
        )

    def get_current_backend(self) -> LLMBackend:
        """Get currently active backend"""
        return self.current_backend

    def is_vllm_configured(self) -> bool:
        """Check if vLLM endpoint is configured"""
        return self.vllm_endpoint is not None

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get current backend information.

        Returns:
            Dictionary with backend status and configuration
        """
        info = {
            "current_backend": self.current_backend.value,
            "vllm_endpoint": self.vllm_endpoint,
            "vllm_configured": self.is_vllm_configured(),
            "available_backends": [b.value for b in LLMBackend],
        }

        # Add available models for current backend
        if self.current_backend == LLMBackend.ANTHROPIC:
            info["available_models"] = list(self.models[LLMBackend.ANTHROPIC].keys())
        else:
            info["available_models"] = ["qwen"]

        return info


# Global singleton instance
litellm_config = LiteLLMConfig()