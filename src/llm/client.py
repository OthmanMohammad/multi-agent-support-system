"""
Unified LLM Client Module

Provides unified LLM interface using LiteLLM abstraction.
Supports multiple backends transparently:
- Anthropic Claude API
- vLLM (self-hosted)

Features:
- Automatic prompt format conversion
- Backend switching at runtime
- Error handling & retries
- Cost tracking
- Metrics collection
- Response streaming support

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

import time
from collections.abc import AsyncIterator
from typing import Any

import litellm
import structlog
from litellm import acompletion

from src.llm.litellm_config import LLMBackend, litellm_config
from src.utils.cost_tracking import cost_tracker
from src.utils.monitoring.metrics import llm_metrics

logger = structlog.get_logger(__name__)


class UnifiedLLMClient:
    """
    Unified LLM client using LiteLLM abstraction.

    Automatically handles:
    - Prompt format conversion (Anthropic vs OpenAI)
    - API compatibility layer
    - Error handling & retries
    - Cost tracking per backend
    - Metrics collection
    - Backend health monitoring

    Usage:
        >>> client = llm_client
        >>> response = await client.chat_completion(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     model_tier="haiku"
        ... )
        >>> print(response)
        "Hello! How can I help you today?"

    Backend Switching:
        >>> client.switch_backend(LLMBackend.VLLM)
        >>> # Now all calls use vLLM
    """

    def __init__(self):
        self.config = litellm_config

        # Configure LiteLLM global settings
        litellm.drop_params = True  # Drop unsupported params gracefully
        litellm.telemetry = False  # Disable LiteLLM telemetry
        litellm.set_verbose = False  # Reduce logging noise

        logger.info("unified_llm_client_initialized")

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model_tier: str = "haiku",
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """
        Unified chat completion across backends.

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model_tier: Model tier (haiku/sonnet/opus for Anthropic, ignored for vLLM)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not yet implemented)
            **kwargs: Additional parameters passed to LiteLLM

        Returns:
            Response content as string

        Raises:
            Exception: If LLM call fails after retries

        Examples:
            >>> client = llm_client
            >>> # Simple completion
            >>> response = await client.chat_completion(
            ...     messages=[{"role": "user", "content": "What is 2+2?"}],
            ...     model_tier="haiku"
            ... )
            >>>
            >>> # With custom parameters
            >>> response = await client.chat_completion(
            ...     messages=[{"role": "user", "content": "Write a poem"}],
            ...     model_tier="sonnet",
            ...     temperature=0.9,
            ...     max_tokens=500
            ... )
        """
        start_time = time.time()
        model_config = self.config.get_model_config(model_tier)

        # Build call parameters
        call_params = {
            "model": model_config.model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else model_config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else model_config.max_tokens,
            "timeout": model_config.timeout,
            "num_retries": model_config.max_retries,
        }

        # Add API base for vLLM
        if model_config.api_base:
            call_params["api_base"] = model_config.api_base
            call_params["custom_llm_provider"] = "openai"

        # Add API key if present
        if model_config.api_key:
            call_params["api_key"] = model_config.api_key

        # Merge additional kwargs
        call_params.update(kwargs)

        try:
            logger.info(
                "llm_call_started",
                backend=self.config.current_backend.value,
                model=model_config.model_name,
                messages_count=len(messages),
                temperature=call_params["temperature"],
                max_tokens=call_params["max_tokens"],
            )

            # Make async call via LiteLLM
            response = await acompletion(**call_params)

            # Extract response content
            content = response.choices[0].message.content

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Extract usage information
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens

            # Track metrics
            llm_metrics.track_call(
                backend=self.config.current_backend.value,
                model=model_config.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=True,
            )

            # Track costs
            if self.config.current_backend == LLMBackend.ANTHROPIC:
                cost_tracker.add_anthropic_call(
                    model=model_config.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            logger.info(
                "llm_call_success",
                backend=self.config.current_backend.value,
                model=model_config.model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=round(latency_ms, 2),
            )

            return content

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            # Track failed call
            llm_metrics.track_call(
                backend=self.config.current_backend.value,
                model=model_config.model_name,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

            logger.error(
                "llm_call_failed",
                backend=self.config.current_backend.value,
                model=model_config.model_name,
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=round(latency_ms, 2),
                exc_info=True,
            )

            raise

    async def chat_completion_stream(
        self, messages: list[dict[str, str]], model_tier: str = "haiku", **kwargs
    ) -> AsyncIterator[str]:
        """
        Streaming chat completion (future implementation).

        Args:
            messages: List of message dicts
            model_tier: Model tier
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive

        Note:
            Not yet implemented - placeholder for future streaming support
        """
        raise NotImplementedError(
            "Streaming support not yet implemented. Use chat_completion() for now."
        )

    def switch_backend(self, backend: LLMBackend) -> None:
        """
        Switch to different backend.

        Args:
            backend: Target backend (ANTHROPIC or VLLM)

        Raises:
            ValueError: If backend is invalid or unavailable
        """
        self.config.switch_backend(backend)

        logger.info(
            "client_backend_switched",
            backend=backend.value,
        )

    def set_vllm_endpoint(self, endpoint: str) -> None:
        """
        Set vLLM endpoint URL.

        Args:
            endpoint: vLLM server URL (e.g., "http://165.22.45.67:8000")
        """
        self.config.set_vllm_endpoint(endpoint)

        logger.info(
            "client_vllm_endpoint_set",
            endpoint=endpoint,
        )

    def get_current_backend(self) -> LLMBackend:
        """Get currently active backend"""
        return self.config.get_current_backend()

    def get_backend_info(self) -> dict[str, Any]:
        """
        Get current backend information.

        Returns:
            Dictionary with backend status
        """
        return self.config.get_backend_info()

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        Get LLM usage metrics summary.

        Returns:
            Dictionary with metrics from llm_metrics tracker
        """
        return llm_metrics.get_all_stats()

    def get_cost_summary(self) -> dict[str, Any]:
        """
        Get cost summary.

        Returns:
            Dictionary with cost breakdown from cost_tracker
        """
        return cost_tracker.get_breakdown()

    async def health_check(self) -> dict[str, bool]:
        """
        Check health of available backends.

        Returns:
            Dictionary with backend health status

        Examples:
            >>> client = llm_client
            >>> health = await client.health_check()
            >>> print(health)
            {"anthropic": True, "vllm": False}
        """
        health = {}

        # Check Anthropic (simple check - API key exists)
        try:
            anthropic_config = self.config.models[LLMBackend.ANTHROPIC]["haiku"]
            health["anthropic"] = bool(anthropic_config.api_key)
        except Exception:
            health["anthropic"] = False

        # Check vLLM (endpoint configured)
        health["vllm"] = self.config.is_vllm_configured()

        logger.debug(
            "health_check_completed",
            health=health,
        )

        return health


# Global client instance
llm_client = UnifiedLLMClient()
