"""
Backend Manager Service

Manages LLM backend selection and switching.

Features:
- Runtime backend switching (Anthropic ↔ vLLM)
- Backend health monitoring
- Automatic failover (future)
- Usage tracking
- vLLM endpoint management

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
import structlog

from src.llm.litellm_config import litellm_config, LLMBackend
from src.llm.client import llm_client

logger = structlog.get_logger(__name__)


class BackendManager:
    """
    Manages LLM backend selection and switching.

    Provides:
    - Backend switching with validation
    - Health checks for each backend
    - Backend status monitoring
    - vLLM endpoint configuration

    Usage:
        >>> manager = backend_manager
        >>> # Switch to vLLM
        >>> await manager.switch_backend(LLMBackend.VLLM)
        >>>
        >>> # Check health
        >>> health = await manager.check_all_backends()
        >>> print(health)
        {"anthropic": True, "vllm": False}
    """

    def __init__(self):
        self.config = litellm_config
        self.llm_client = llm_client

        # Track backend health status
        self.health_status: Dict[LLMBackend, bool] = {
            LLMBackend.ANTHROPIC: True,  # Assume healthy initially
            LLMBackend.VLLM: False,      # Initially unavailable
        }

        # Track last health check times
        self.last_health_check: Dict[LLMBackend, Optional[datetime]] = {
            LLMBackend.ANTHROPIC: None,
            LLMBackend.VLLM: None,
        }

        logger.info("backend_manager_initialized")

    async def switch_backend(
        self,
        backend: LLMBackend,
        skip_health_check: bool = False
    ) -> Dict[str, Any]:
        """
        Switch to specified backend.

        Args:
            backend: Target backend (ANTHROPIC or VLLM)
            skip_health_check: Skip health check before switching (default: False)

        Returns:
            Dictionary with switch status and details

        Raises:
            ValueError: If backend is invalid or unhealthy

        Examples:
            >>> manager = backend_manager
            >>> result = await manager.switch_backend(LLMBackend.ANTHROPIC)
            >>> print(result["success"])
            True
        """
        logger.info(
            "backend_switch_requested",
            target_backend=backend.value,
            current_backend=self.config.current_backend.value,
        )

        # Check if already on this backend
        if self.config.current_backend == backend:
            logger.info(
                "backend_switch_unnecessary",
                backend=backend.value,
                message="Already on target backend",
            )
            return {
                "success": True,
                "backend": backend.value,
                "message": "Already on target backend",
                "switched": False,
            }

        # Check health unless skipped
        if not skip_health_check:
            is_healthy = await self.check_health(backend)

            if not is_healthy:
                logger.error(
                    "backend_switch_failed_unhealthy",
                    backend=backend.value,
                )
                return {
                    "success": False,
                    "backend": backend.value,
                    "message": f"Backend {backend.value} is unhealthy",
                    "switched": False,
                }

        # Perform switch
        old_backend = self.config.current_backend
        self.llm_client.switch_backend(backend)

        logger.info(
            "backend_switched",
            from_backend=old_backend.value,
            to_backend=backend.value,
        )

        return {
            "success": True,
            "backend": backend.value,
            "previous_backend": old_backend.value,
            "message": f"Switched from {old_backend.value} to {backend.value}",
            "switched": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def check_health(self, backend: LLMBackend) -> bool:
        """
        Check if backend is healthy and available.

        Args:
            backend: Backend to check

        Returns:
            True if healthy, False otherwise
        """
        try:
            if backend == LLMBackend.ANTHROPIC:
                is_healthy = await self._check_anthropic_health()
            elif backend == LLMBackend.VLLM:
                is_healthy = await self._check_vllm_health()
            else:
                logger.error("unknown_backend", backend=backend)
                is_healthy = False

            # Update status
            self.health_status[backend] = is_healthy
            self.last_health_check[backend] = datetime.utcnow()

            logger.info(
                "backend_health_checked",
                backend=backend.value,
                healthy=is_healthy,
            )

            return is_healthy

        except Exception as e:
            logger.error(
                "backend_health_check_failed",
                backend=backend.value,
                error=str(e),
                exc_info=True,
            )

            self.health_status[backend] = False
            self.last_health_check[backend] = datetime.utcnow()

            return False

    async def _check_anthropic_health(self) -> bool:
        """
        Check Anthropic backend health.

        Returns:
            True if API key is configured
        """
        # Simple check: verify API key exists
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            logger.warning("anthropic_health_check_no_api_key")
            return False

        # Could make a minimal API call here for more thorough check
        # For now, just verify key exists

        return True

    async def _check_vllm_health(self) -> bool:
        """
        Check vLLM backend health.

        Returns:
            True if endpoint is configured and responding
        """
        # Check if endpoint is configured
        if not self.config.vllm_endpoint:
            logger.debug("vllm_health_check_no_endpoint")
            return False

        # Try to ping vLLM health endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.vllm_endpoint}/health",
                    timeout=5.0,
                )

                if response.status_code == 200:
                    logger.debug("vllm_health_check_success")
                    return True
                else:
                    logger.warning(
                        "vllm_health_check_bad_status",
                        status_code=response.status_code,
                    )
                    return False

        except httpx.RequestError as e:
            logger.debug(
                "vllm_health_check_request_failed",
                error=str(e),
            )
            return False

    async def check_all_backends(self) -> Dict[str, Any]:
        """
        Check health of all backends.

        Returns:
            Dictionary with health status for each backend
        """
        health = {}

        for backend in LLMBackend:
            health[backend.value] = await self.check_health(backend)

        return {
            "backends": health,
            "current_backend": self.config.current_backend.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_current_backend(self) -> LLMBackend:
        """Get currently active backend"""
        return self.config.get_current_backend()

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get comprehensive backend information.

        Returns:
            Dictionary with backend status and configuration
        """
        current_backend = self.config.current_backend

        info = {
            "current_backend": current_backend.value,
            "vllm_endpoint": self.config.vllm_endpoint,
            "vllm_configured": self.config.is_vllm_configured(),
            "health_status": {
                backend.value: self.health_status[backend]
                for backend in LLMBackend
            },
            "last_health_check": {
                backend.value: (
                    self.last_health_check[backend].isoformat()
                    if self.last_health_check[backend]
                    else None
                )
                for backend in LLMBackend
            },
        }

        # Add available models for current backend
        if current_backend == LLMBackend.ANTHROPIC:
            info["available_models"] = ["haiku", "sonnet", "opus"]
        else:
            info["available_models"] = ["qwen"]

        return info

    async def set_vllm_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """
        Set vLLM endpoint and check health.

        Args:
            endpoint: vLLM server URL (e.g., "http://165.22.45.67:8000")

        Returns:
            Dictionary with configuration status
        """
        logger.info(
            "vllm_endpoint_configuration_requested",
            endpoint=endpoint,
        )

        # Set endpoint
        self.llm_client.set_vllm_endpoint(endpoint)

        # Check health
        is_healthy = await self.check_health(LLMBackend.VLLM)

        return {
            "success": True,
            "endpoint": endpoint,
            "healthy": is_healthy,
            "message": (
                "vLLM endpoint configured and healthy"
                if is_healthy
                else "vLLM endpoint configured but not responding"
            ),
        }


# Global backend manager instance
backend_manager = BackendManager()
