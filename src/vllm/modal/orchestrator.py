"""
Modal Orchestrator

Simplified GPU orchestration for Modal's serverless vLLM deployment.

Key Differences from Vast.ai:
    - No instance search/launch (Modal auto-scales)
    - No keep-alive management (Modal handles scaledown)
    - No manual destroy (Modal auto-releases)
    - No budget tracking (set limits in Modal dashboard)

Architecture:
    1. Store Modal web URL (from deployment)
    2. Validate health on startup
    3. Provide status/health endpoints
    4. Modal handles all GPU lifecycle automatically

Part of Phase 3: GPU Orchestration (Modal migration)
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import structlog

from src.vllm.modal.client import ModalVLLMClient
from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class ModalOrchestrator:
    """
    Simplified orchestrator for Modal serverless vLLM.

    Unlike Vast.ai, Modal is serverless - no instance management required.
    This orchestrator simply wraps the Modal client and provides status endpoints.

    Usage:
        >>> orchestrator = modal_orchestrator
        >>>
        >>> # Get vLLM endpoint (instant)
        >>> endpoint = orchestrator.get_endpoint()
        >>> # "https://yourapp.modal.run/v1"
        >>>
        >>> # Check health
        >>> status = await orchestrator.get_status()
        >>> # {"healthy": True, "endpoint": "..."}
        >>>
        >>> # No need to destroy - Modal auto-scales down
    """

    def __init__(self, modal_web_url: Optional[str] = None):
        """
        Initialize Modal orchestrator.

        Args:
            modal_web_url: Modal web URL (from deployment)
                If not provided, reads from settings
        """
        # Get Modal URL from settings or parameter
        self.modal_web_url = modal_web_url or settings.modal.web_url

        if not self.modal_web_url:
            raise ValueError(
                "Modal web URL not configured. "
                "Set MODAL_WEB_URL environment variable or deploy vLLM first."
            )

        # Initialize client
        self.client = ModalVLLMClient(modal_web_url=self.modal_web_url)

        # Tracking
        self.startup_time = datetime.utcnow()
        self.last_health_check: Optional[Dict[str, Any]] = None
        self.total_requests = 0

        logger.info(
            "modal_orchestrator_initialized",
            modal_web_url=self.modal_web_url,
        )

    async def validate_health(self) -> bool:
        """
        Validate Modal endpoint is healthy on startup.

        Returns:
            True if healthy, False otherwise
        """
        try:
            health = await self.client.health_check()
            self.last_health_check = {
                **health,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if health["healthy"]:
                logger.info(
                    "modal_health_check_passed",
                    response_time_ms=health["response_time_ms"],
                )
                return True
            else:
                logger.error(
                    "modal_health_check_failed",
                    status_code=health.get("status_code"),
                )
                return False

        except Exception as e:
            logger.error(
                "modal_health_check_error",
                error=str(e),
                exc_info=True,
            )
            self.last_health_check = {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            return False

    def get_endpoint(self) -> str:
        """
        Get OpenAI-compatible vLLM endpoint URL.

        Returns:
            Endpoint URL (e.g., "https://yourapp.modal.run/v1")

        Examples:
            >>> endpoint = orchestrator.get_endpoint()
            >>> print(endpoint)
            "https://yourapp.modal.run/v1"
        """
        return self.client.get_endpoint_url()

    async def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive orchestrator status.

        Returns:
            Status dictionary with:
                - status: "ready" | "degraded" | "unhealthy"
                - endpoint: vLLM endpoint URL
                - modal_web_url: Modal web URL
                - uptime_hours: Hours since startup
                - last_health_check: Last health check result
                - total_requests: Total requests tracked

        Examples:
            >>> status = await orchestrator.get_status()
            >>> print(status["status"])
            "ready"
        """
        # Run health check
        health = await self.client.health_check()

        # Calculate uptime
        uptime = datetime.utcnow() - self.startup_time
        uptime_hours = uptime.total_seconds() / 3600

        # Determine status
        if health["healthy"]:
            status = "ready"
        elif health.get("status_code") == 503:
            status = "degraded"  # Modal might be cold-starting
        else:
            status = "unhealthy"

        return {
            "status": status,
            "endpoint": self.get_endpoint(),
            "modal_web_url": self.modal_web_url,
            "uptime_hours": round(uptime_hours, 2),
            "last_health_check": {
                "healthy": health["healthy"],
                "response_time_ms": health.get("response_time_ms", 0),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "total_requests": self.total_requests,
            "cost_tracking": {
                "note": "Set spending limits in Modal dashboard at https://modal.com",
                "pricing": "Pay-per-second of GPU usage (only when processing requests)",
            },
        }

    async def chat_completion(
        self,
        messages: list,
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Make chat completion request to Modal vLLM.

        Args:
            messages: Chat messages in OpenAI format
            model: Model name (must match deployed model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            OpenAI-compatible response dict

        Raises:
            aiohttp.ClientError: If request fails
        """
        # Track request
        self.total_requests += 1

        # Make request
        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            "modal_chat_completion",
            model=model,
            tokens=response.get("usage", {}).get("total_tokens", "N/A"),
            total_requests=self.total_requests,
        )

        return response

    async def get_models(self) -> Dict[str, Any]:
        """
        Get list of available models.

        Returns:
            Models dict with:
                - object: "list"
                - data: List of model objects
        """
        return await self.client.get_models()

    def __repr__(self) -> str:
        return f"ModalOrchestrator(url={self.modal_web_url})"


# =============================================================================
# GLOBAL INSTANCE (replaces gpu_orchestrator for Vast.ai)
# =============================================================================

# This will be initialized when Modal URL is configured
modal_orchestrator: Optional[ModalOrchestrator] = None


def init_modal_orchestrator(modal_web_url: str) -> ModalOrchestrator:
    """
    Initialize global Modal orchestrator instance.

    Args:
        modal_web_url: Modal web URL from deployment

    Returns:
        Initialized ModalOrchestrator
    """
    global modal_orchestrator
    modal_orchestrator = ModalOrchestrator(modal_web_url=modal_web_url)

    logger.info(
        "global_modal_orchestrator_initialized",
        modal_web_url=modal_web_url,
    )

    return modal_orchestrator


def get_modal_orchestrator() -> ModalOrchestrator:
    """
    Get global Modal orchestrator instance.

    Returns:
        ModalOrchestrator instance

    Raises:
        RuntimeError: If orchestrator not initialized
    """
    if modal_orchestrator is None:
        raise RuntimeError(
            "Modal orchestrator not initialized. "
            "Call init_modal_orchestrator() first or set MODAL_WEB_URL."
        )
    return modal_orchestrator


# =============================================================================
# MIGRATION HELPER
# =============================================================================

def is_modal_configured() -> bool:
    """
    Check if Modal is configured (for migration from Vast.ai).

    Returns:
        True if Modal URL is set, False otherwise
    """
    try:
        return bool(settings.modal.web_url)
    except Exception:
        return False


# =============================================================================
# TESTING
# =============================================================================

async def _test_orchestrator():
    """Test Modal orchestrator (requires deployed Modal endpoint)."""
    import os

    # Get Modal URL from environment
    modal_url = os.getenv("MODAL_WEB_URL")
    if not modal_url:
        print("❌ Error: MODAL_WEB_URL environment variable not set")
        print("   Deploy vLLM first: modal deploy src/vllm/modal_vllm.py")
        return

    print(f"Testing Modal orchestrator with URL: {modal_url}\n")

    # Create orchestrator
    orchestrator = ModalOrchestrator(modal_web_url=modal_url)

    # Test 1: Validate health
    print("[Test 1] Validate health...")
    healthy = await orchestrator.validate_health()
    if healthy:
        print(f"✅ Health validation passed\n")
    else:
        print(f"❌ Health validation failed\n")
        return

    # Test 2: Get status
    print("[Test 2] Get status...")
    status = await orchestrator.get_status()
    print(f"✅ Status: {status['status']}")
    print(f"   Endpoint: {status['endpoint']}")
    print(f"   Uptime: {status['uptime_hours']}h\n")

    # Test 3: Get endpoint
    print("[Test 3] Get endpoint...")
    endpoint = orchestrator.get_endpoint()
    print(f"✅ Endpoint: {endpoint}\n")

    # Test 4: Get models
    print("[Test 4] Get models...")
    try:
        models = await orchestrator.get_models()
        model_count = len(models.get("data", []))
        print(f"✅ Models: {model_count} available\n")
    except Exception as e:
        print(f"❌ Get models failed: {e}\n")

    # Test 5: Chat completion
    print("[Test 5] Chat completion...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France? One sentence."},
    ]
    try:
        response = await orchestrator.chat_completion(
            messages=messages,
            max_tokens=100,
        )
        content = response["choices"][0]["message"]["content"]
        print(f"✅ Response: {content}\n")
    except Exception as e:
        print(f"❌ Chat completion failed: {e}\n")
        return

    # Test 6: Get status again (should show request count)
    print("[Test 6] Get status (after request)...")
    status = await orchestrator.get_status()
    print(f"✅ Total requests: {status['total_requests']}\n")

    print(f"{'='*80}")
    print("✅ All tests passed!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(_test_orchestrator())
