"""
Backend Manager Service

Manages LLM backend selection and switching.

Features:
- Runtime backend switching (Anthropic ↔ vLLM)
- Backend health monitoring
- Automatic failover (future)
- Usage tracking
- vLLM endpoint management
- Multi-provider GPU orchestration (Vast.ai / Modal)

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
Part of: Phase 3 - GPU Orchestration (Vast.ai / Modal)
"""

import os
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import httpx
import structlog

from src.llm.litellm_config import litellm_config, LLMBackend
from src.llm.client import llm_client
from src.vllm.vastai.orchestrator import gpu_orchestrator
from src.vllm import get_modal_orchestrator, init_modal_orchestrator, is_modal_configured
from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


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

        # Detect and initialize GPU provider
        self.gpu_provider = self._detect_gpu_provider()

        logger.info(
            "backend_manager_initialized",
            gpu_provider=self.gpu_provider,
        )

    def _detect_gpu_provider(self) -> Literal["modal", "vastai", "none"]:
        """
        Detect which GPU provider is configured.

        Returns:
            "modal" if Modal is configured
            "vastai" if Vast.ai is configured
            "none" if neither is configured
        """
        # Priority 1: Check if Modal is configured
        if is_modal_configured():
            logger.info("gpu_provider_detected_modal")
            # Initialize Modal orchestrator
            try:
                init_modal_orchestrator(settings.modal.web_url)
                return "modal"
            except Exception as e:
                logger.warning(
                    "modal_orchestrator_init_failed",
                    error=str(e),
                )

        # Priority 2: Check if Vast.ai is configured
        if settings.vastai.api_key:
            logger.info("gpu_provider_detected_vastai")
            return "vastai"

        logger.info("gpu_provider_none_configured")
        return "none"

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

        # Try to ping vLLM models endpoint (OpenAI-compatible)
        # Note: Modal vLLM has /health at root, but /v1/models under the API path
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.vllm_endpoint}/models",
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

    async def launch_vllm_gpu(
        self,
        keep_alive_minutes: int = 45,
        auto_switch: bool = True,
    ) -> Dict[str, Any]:
        """
        Launch vLLM GPU instance via GPU provider (Vast.ai / Modal).

        This is the Phase 3 integration point for GPU orchestration.

        **Behavior depends on GPU provider:**
        - **Modal (serverless):** Configures endpoint instantly, no launch needed
        - **Vast.ai:** Async launch, returns immediately, GPU boots in background (3-5 min)

        Args:
            keep_alive_minutes: Keep-alive time (Vast.ai only, ignored for Modal)
            auto_switch: Automatically switch to vLLM backend after launch

        Returns:
            Dictionary with launch/configuration status

        Examples:
            >>> manager = backend_manager
            >>> result = await manager.launch_vllm_gpu(keep_alive_minutes=45)
            >>> print(result)
            {"success": True, "provider": "modal", "status": "ready"}
        """
        logger.info(
            "vllm_gpu_launch_requested",
            provider=self.gpu_provider,
            keep_alive_minutes=keep_alive_minutes,
            auto_switch=auto_switch,
        )

        try:
            # Route to appropriate provider
            if self.gpu_provider == "modal":
                return await self._launch_modal_vllm(auto_switch)
            elif self.gpu_provider == "vastai":
                return await self._launch_vastai_vllm(keep_alive_minutes, auto_switch)
            else:
                return {
                    "success": False,
                    "error": "No GPU provider configured",
                    "message": (
                        "Neither Modal nor Vast.ai is configured. "
                        "Set MODAL_WEB_URL or VASTAI_API_KEY environment variable."
                    ),
                }

        except Exception as e:
            logger.error(
                "vllm_gpu_launch_failed",
                provider=self.gpu_provider,
                error=str(e),
                exc_info=True,
            )

            self.health_status[LLMBackend.VLLM] = False

            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to launch vLLM GPU via {self.gpu_provider}",
            }

    async def _launch_modal_vllm(self, auto_switch: bool) -> Dict[str, Any]:
        """
        Configure Modal vLLM endpoint (instant, no launch needed).

        Args:
            auto_switch: Automatically switch to vLLM backend

        Returns:
            Configuration status dictionary
        """
        logger.info("modal_vllm_configuration_requested")

        # Get Modal orchestrator (will raise RuntimeError if not initialized)
        orchestrator = get_modal_orchestrator()

        # Get Modal endpoint
        endpoint = orchestrator.get_endpoint()

        # Validate health
        is_healthy = await orchestrator.validate_health()

        if not is_healthy:
            return {
                "success": False,
                "provider": "modal",
                "message": (
                    "Modal endpoint is not healthy. "
                    "Make sure you've deployed: modal deploy src/vllm/modal_vllm.py"
                ),
                "endpoint": endpoint,
            }

        # Configure endpoint
        await self.set_vllm_endpoint(endpoint)

        # Auto-switch if requested
        if auto_switch:
            await self.switch_backend(LLMBackend.VLLM)

        logger.info(
            "modal_vllm_configured",
            endpoint=endpoint,
            auto_switched=auto_switch,
        )

        return {
            "success": True,
            "provider": "modal",
            "status": "ready",
            "endpoint": endpoint,
            "message": "Modal vLLM endpoint configured and ready",
            "auto_switched": auto_switch,
        }

    async def _launch_vastai_vllm(
        self,
        keep_alive_minutes: int,
        auto_switch: bool,
    ) -> Dict[str, Any]:
        """
        Launch Vast.ai GPU instance (async, non-blocking).

        Args:
            keep_alive_minutes: Keep-alive time
            auto_switch: Automatically switch to vLLM backend

        Returns:
            Launch initiation status dictionary
        """
        # Launch GPU instance asynchronously (returns immediately)
        result = gpu_orchestrator.launch_gpu_async(
            keep_alive_minutes=keep_alive_minutes
        )

        logger.info(
            "vastai_vllm_launch_initiated",
            launch_state=result["launch_state"],
        )

        return {
            "success": True,
            "provider": "vastai",
            "launch_state": result["launch_state"],
            "message": result["message"],
            "status_endpoint": "/api/admin/vllm/status",
        }

    async def destroy_vllm_gpu(self) -> Dict[str, Any]:
        """
        Destroy current vLLM GPU instance (Vast.ai only).

        For Modal: This is a no-op since Modal auto-scales down.

        Returns:
            Dictionary with destruction status
        """
        logger.info(
            "vllm_gpu_destroy_requested",
            provider=self.gpu_provider,
        )

        try:
            # Route to appropriate provider
            if self.gpu_provider == "modal":
                logger.info("modal_gpu_destroy_skipped")
                return {
                    "success": True,
                    "provider": "modal",
                    "message": (
                        "Modal auto-scales down automatically. "
                        "No manual destruction needed."
                    ),
                }

            elif self.gpu_provider == "vastai":
                # Destroy Vast.ai instance
                success = await gpu_orchestrator.destroy_instance()

                if success:
                    # Switch back to Anthropic if we were on vLLM
                    if self.config.current_backend == LLMBackend.VLLM:
                        await self.switch_backend(
                            backend=LLMBackend.ANTHROPIC,
                            skip_health_check=False,
                        )

                    logger.info("vastai_gpu_destroy_success")

                    return {
                        "success": True,
                        "provider": "vastai",
                        "message": "Vast.ai GPU instance destroyed",
                    }
                else:
                    return {
                        "success": False,
                        "provider": "vastai",
                        "message": "Failed to destroy Vast.ai GPU instance",
                    }

            else:
                return {
                    "success": False,
                    "error": "No GPU provider configured",
                    "message": "No GPU instance to destroy",
                }

        except Exception as e:
            logger.error(
                "vllm_gpu_destroy_failed",
                provider=self.gpu_provider,
                error=str(e),
                exc_info=True,
            )

            return {
                "success": False,
                "error": str(e),
                "message": f"Error destroying {self.gpu_provider} GPU instance",
            }

    async def get_vllm_status(self) -> Dict[str, Any]:
        """
        Get vLLM GPU orchestrator status.

        Returns different information depending on provider:
        - Modal: Health status, endpoint, uptime
        - Vast.ai: Instance status, launch state, cost tracking

        Returns:
            Status dictionary with provider-specific details
        """
        try:
            if self.gpu_provider == "modal":
                # Get Modal orchestrator (will raise RuntimeError if not initialized)
                orchestrator = get_modal_orchestrator()

                # Get Modal status
                status = await orchestrator.get_status()
                return {
                    "provider": "modal",
                    **status,
                }

            elif self.gpu_provider == "vastai":
                # Get Vast.ai status
                status = gpu_orchestrator.get_status()
                return {
                    "provider": "vastai",
                    **status,
                }

            else:
                return {
                    "provider": "none",
                    "status": "unconfigured",
                    "message": (
                        "No GPU provider configured. "
                        "Set MODAL_WEB_URL or VASTAI_API_KEY."
                    ),
                }

        except Exception as e:
            logger.error(
                "vllm_status_failed",
                provider=self.gpu_provider,
                error=str(e),
                exc_info=True,
            )

            return {
                "provider": self.gpu_provider,
                "status": "error",
                "error": str(e),
            }


# Global backend manager instance
backend_manager = BackendManager()
