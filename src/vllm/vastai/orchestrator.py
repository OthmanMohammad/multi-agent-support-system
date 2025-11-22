"""
GPU Orchestrator

Enterprise-grade GPU lifecycle management for vLLM on Vast.ai.

Features:
- Intelligent GPU search with 10-config fallback strategy
- Automatic instance launch with health monitoring
- Keep-alive management with auto-destroy
- Budget enforcement at multiple checkpoints
- Error handling with automatic cleanup
- Circuit breaker pattern for reliability
- Prometheus metrics integration

Vast.ai GPU Orchestration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import deque
from enum import Enum
import time
import httpx
import structlog

from src.vllm.vastai.client import VastAIClient, VastAIError, VastAINotFoundError
from src.vllm.vastai.gpu_configs import GPU_FALLBACK_CONFIGS, GPUConfig, filter_compatible_offers
from src.vllm.vastai.docker_config import VLLMDockerConfig
from src.utils.cost_tracking import cost_tracker
from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class LaunchState(str, Enum):
    """GPU instance launch states"""
    IDLE = "idle"
    SEARCHING = "searching"
    LAUNCHING = "launching"
    BOOTING = "booting"
    STARTING_VLLM = "starting_vllm"
    READY = "ready"
    FAILED = "failed"


class GPUOrchestrator:
    """
    Enterprise-grade GPU lifecycle orchestrator.

    Manages the complete lifecycle of GPU instances:
    1. Intelligent search across 10 GPU configurations
    2. Instance launch with automatic retries
    3. vLLM health monitoring
    4. Keep-alive management
    5. Automatic cleanup on errors/timeout/shutdown
    6. Budget enforcement
    7. Cost tracking

    Usage:
        >>> orchestrator = gpu_orchestrator
        >>>
        >>> # Launch GPU instance
        >>> endpoint = await orchestrator.ensure_gpu_ready(keep_alive_minutes=45)
        >>> # "http://165.22.45.67:8000"
        >>>
        >>> # Extend keep-alive
        >>> await orchestrator.extend_keep_alive(15)
        >>>
        >>> # Destroy when done
        >>> await orchestrator.destroy_instance()
    """

    def __init__(self):
        """Initialize GPU orchestrator"""
        self.vast_client: Optional[VastAIClient] = None
        self.current_instance: Optional[Dict[str, Any]] = None
        self.instance_start_time: Optional[datetime] = None
        self.keep_alive_until: Optional[datetime] = None
        self.vllm_endpoint: Optional[str] = None

        # Launch state tracking
        self.launch_state = LaunchState.IDLE
        self.launch_error: Optional[str] = None
        self.launch_task: Optional[asyncio.Task] = None

        # Budget tracking
        self.budget_limit = settings.vastai.budget_limit
        self.session_budget = settings.vastai.session_budget_limit

        # Health monitoring
        self.health_check_failures = 0
        self.max_health_failures = 3

        # Request tracking for intelligent keep-alive
        self.recent_requests = deque(maxlen=100)

        # Background task handles
        self._keep_alive_task: Optional[asyncio.Task] = None
        self._health_monitor_task: Optional[asyncio.Task] = None

        logger.info(
            "gpu_orchestrator_initialized",
            budget_limit=self.budget_limit,
            session_budget=self.session_budget,
        )

    async def _init_client(self):
        """Initialize Vast.ai client lazily"""
        if not self.vast_client:
            self.vast_client = VastAIClient()

    def launch_gpu_async(self, keep_alive_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Launch GPU instance asynchronously (non-blocking).

        Returns immediately with launch status. Use get_status() to check progress.

        Args:
            keep_alive_minutes: Keep-alive time (defaults to settings)

        Returns:
            Dictionary with launch initiation status

        Raises:
            RuntimeError: If launch already in progress

        Examples:
            >>> result = orchestrator.launch_gpu_async(keep_alive_minutes=45)
            >>> print(result["launch_state"])
            "searching"
        """
        if self.launch_state not in [LaunchState.IDLE, LaunchState.READY, LaunchState.FAILED]:
            raise RuntimeError(f"Launch already in progress (state: {self.launch_state})")

        # Reset state
        self.launch_state = LaunchState.SEARCHING
        self.launch_error = None

        # Start background task
        self.launch_task = asyncio.create_task(
            self._launch_gpu_background(keep_alive_minutes)
        )

        logger.info(
            "gpu_async_launch_started",
            keep_alive_minutes=keep_alive_minutes,
        )

        return {
            "success": True,
            "launch_state": self.launch_state.value,
            "message": "GPU launch initiated. Check /api/admin/vllm/status for progress.",
        }

    async def _launch_gpu_background(self, keep_alive_minutes: Optional[int]):
        """
        Background task for launching GPU and waiting for vLLM ready.

        Updates self.launch_state as it progresses.
        """
        try:
            endpoint = await self.ensure_gpu_ready(keep_alive_minutes)
            self.launch_state = LaunchState.READY
            logger.info(
                "gpu_async_launch_complete",
                endpoint=endpoint,
                instance_id=self.current_instance.get("id") if self.current_instance else None,
            )
        except Exception as e:
            self.launch_state = LaunchState.FAILED
            self.launch_error = str(e)
            logger.error(
                "gpu_async_launch_failed",
                error=str(e),
                exc_info=True,
            )

    async def ensure_gpu_ready(
        self,
        keep_alive_minutes: Optional[int] = None,
    ) -> str:
        """
        Ensure GPU instance is running and vLLM is ready.

        This is the main entry point for getting a vLLM endpoint.

        Args:
            keep_alive_minutes: Keep-alive time (defaults to settings)

        Returns:
            vLLM endpoint URL (e.g., "http://165.22.45.67:8000")

        Raises:
            RuntimeError: If no GPU available or budget exceeded
            TimeoutError: If vLLM fails to start

        Examples:
            >>> endpoint = await orchestrator.ensure_gpu_ready(keep_alive_minutes=45)
            >>> print(endpoint)
            "http://165.22.45.67:8000"
        """
        await self._init_client()

        keep_alive_minutes = keep_alive_minutes or settings.vastai.default_keep_alive_minutes

        # Check if instance already running
        if self.current_instance and self._is_instance_alive():
            logger.info(
                "gpu_instance_already_running",
                instance_id=self.current_instance["id"],
                endpoint=self.vllm_endpoint,
            )

            # Extend keep-alive if needed
            await self.extend_keep_alive(keep_alive_minutes)

            return self.vllm_endpoint

        # Need to launch new instance
        logger.info(
            "gpu_instance_launching",
            keep_alive_minutes=keep_alive_minutes,
        )

        # Checkpoint 1: Check budget before search
        self.launch_state = LaunchState.SEARCHING
        self._check_budget()

        # Search and launch
        self.launch_state = LaunchState.LAUNCHING
        instance = await self._search_and_launch()

        # Checkpoint 2: Verify session budget
        self._check_session_budget(keep_alive_minutes)

        # Wait for vLLM ready
        self.launch_state = LaunchState.BOOTING
        endpoint = await self._wait_for_vllm_ready(instance)

        # Set state
        self.current_instance = instance
        self.instance_start_time = datetime.utcnow()
        self.keep_alive_until = datetime.utcnow() + timedelta(minutes=keep_alive_minutes)
        self.vllm_endpoint = endpoint
        self.health_check_failures = 0

        logger.info(
            "gpu_instance_ready",
            instance_id=instance["id"],
            gpu_name=instance.get("gpu_name"),
            endpoint=endpoint,
            keep_alive_until=self.keep_alive_until.isoformat(),
            price_per_hour=instance.get("price_per_hour"),
        )

        # Start background monitoring tasks
        self._start_background_tasks()

        return endpoint

    async def _search_and_launch(self) -> Dict[str, Any]:
        """
        Search for available GPU and launch instance.

        Uses intelligent fallback strategy across 10 GPU configs.

        Returns:
            Instance metadata dictionary

        Raises:
            RuntimeError: If no GPU found across all configs
        """
        for gpu_config in GPU_FALLBACK_CONFIGS:
            logger.info(
                "gpu_search_attempt",
                gpu_name=gpu_config.gpu_name,
                max_price=gpu_config.max_price_per_hour,
                priority=gpu_config.priority,
                min_vram=gpu_config.min_vram,
            )

            try:
                # Search offers
                offers = await self.vast_client.search_offers(
                    gpu_name=gpu_config.gpu_name,
                    min_vram_gb=gpu_config.min_vram,
                    max_price=gpu_config.max_price_per_hour,
                )

                if not offers:
                    logger.warning(
                        "gpu_no_offers_found",
                        gpu_name=gpu_config.gpu_name,
                    )
                    continue

                # Filter and score offers
                scored_offers = filter_compatible_offers(gpu_config, offers)

                if not scored_offers:
                    logger.warning(
                        "gpu_no_compatible_offers",
                        gpu_name=gpu_config.gpu_name,
                    )
                    continue

                # Try to launch best offer
                best_offer = scored_offers[0]

                logger.info(
                    "gpu_attempting_launch",
                    gpu_name=gpu_config.gpu_name,
                    offer_id=best_offer["id"],
                    price_per_hour=best_offer.get("dph_total"),
                    score=best_offer.get("_computed_score"),
                )

                try:
                    # Generate vLLM Docker arguments
                    vllm_args = VLLMDockerConfig.get_vllm_args()

                    # Use Vast.ai direct Docker mode (runtype="args")
                    # Vast.ai will run the vLLM image directly and automatically expose ports
                    # from the image's EXPOSE directive (port 8000)
                    instance_data = await self.vast_client.create_instance(
                        offer_id=best_offer["id"],
                        image=VLLMDockerConfig.IMAGE,  # Use vLLM image directly
                        disk_gb=gpu_config.disk_space_gb,
                        label=f"vllm-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                        docker_args=vllm_args,  # Pass vLLM arguments
                        runtype="args",  # Direct Docker mode
                    )

                    logger.info(
                        "gpu_instance_launched",
                        gpu_name=gpu_config.gpu_name,
                        instance_id=instance_data.get("new_contract"),
                        offer_id=best_offer["id"],
                        price_per_hour=best_offer.get("dph_total"),
                    )

                    return {
                        "id": instance_data.get("new_contract"),
                        "gpu_name": gpu_config.gpu_name,
                        "price_per_hour": best_offer.get("dph_total"),
                        "offer_id": best_offer["id"],
                        "vram_gb": gpu_config.vram_gb,
                    }

                except VastAIError as e:
                    logger.error(
                        "gpu_launch_failed",
                        gpu_name=gpu_config.gpu_name,
                        offer_id=best_offer["id"],
                        error=str(e),
                    )
                    # Try next offer in this config
                    if len(scored_offers) > 1:
                        for fallback_offer in scored_offers[1:3]:  # Try next 2
                            try:
                                vllm_args = VLLMDockerConfig.get_vllm_args()
                                vllm_cmd = " ".join(vllm_args)
                                onstart_script = (
                                    f"docker run -d --gpus all --name vllm "
                                    f"-p 8000:8000 {VLLMDockerConfig.IMAGE} {vllm_cmd}"
                                )
                                instance_data = await self.vast_client.create_instance(
                                    offer_id=fallback_offer["id"],
                                    image="nvidia/cuda:12.1.0-base-ubuntu22.04",
                                    disk_gb=gpu_config.disk_space_gb,
                                    label=f"vllm-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                                    onstart=onstart_script,
                                    runtype="ssh_direct",
                                )
                                return {
                                    "id": instance_data.get("new_contract"),
                                    "gpu_name": gpu_config.gpu_name,
                                    "price_per_hour": fallback_offer.get("dph_total"),
                                    "offer_id": fallback_offer["id"],
                                    "vram_gb": gpu_config.vram_gb,
                                }
                            except VastAIError:
                                continue

                    # All offers in this config failed - try next config
                    continue

            except Exception as e:
                logger.error(
                    "gpu_search_error",
                    gpu_name=gpu_config.gpu_name,
                    error=str(e),
                    exc_info=True,
                )
                continue

        # All 10 configs failed
        logger.error("gpu_all_configs_exhausted")
        raise RuntimeError(
            "No available GPU instances found across all 10 fallback configurations. "
            "All GPUs may be in use or prices exceed maximum thresholds."
        )

    async def _wait_for_vllm_ready(
        self,
        instance: Dict[str, Any],
    ) -> str:
        """
        Wait for vLLM to be ready and responding.

        Polls health endpoint until ready or timeout.

        Args:
            instance: Instance metadata

        Returns:
            vLLM endpoint URL

        Raises:
            TimeoutError: If vLLM doesn't start within timeout
        """
        instance_id = instance["id"]
        start_time = datetime.utcnow()
        timeout = timedelta(minutes=settings.vastai.max_startup_time_minutes)

        logger.info(
            "vllm_startup_waiting",
            instance_id=instance_id,
            timeout_minutes=settings.vastai.max_startup_time_minutes,
        )

        # Metrics tracking
        metrics = {
            "instance_boot_time": None,
            "vllm_ready_time": None,
            "total_startup_time": None,
        }

        instance_running = False
        public_ip = None

        while datetime.utcnow() - start_time < timeout:
            try:
                # Get instance details
                instance_info = await self.vast_client.get_instance(instance_id)

                # Check instance status
                status = instance_info.get("actual_status", "unknown")

                if status == "running":
                    if not instance_running:
                        instance_running = True
                        boot_time = (datetime.utcnow() - start_time).total_seconds()
                        metrics["instance_boot_time"] = boot_time
                        logger.info(
                            "gpu_instance_running",
                            instance_id=instance_id,
                            boot_time_seconds=boot_time,
                        )

                    # Get IP address
                    public_ip = instance_info.get("public_ipaddr")

                    if not public_ip:
                        logger.debug(
                            "gpu_instance_no_ip",
                            instance_id=instance_id,
                        )
                        await asyncio.sleep(10)
                        continue

                    # Get external port mapped to internal port 8000
                    # Vast.ai maps internal ports to random external ports
                    ports = instance_info.get("ports", {})
                    port_mappings = ports.get("8000/tcp", [])

                    if not port_mappings:
                        logger.debug(
                            "gpu_instance_no_port_mapping",
                            instance_id=instance_id,
                            ports=ports,
                        )
                        await asyncio.sleep(10)
                        continue

                    external_port = port_mappings[0].get("HostPort") if port_mappings else None

                    if not external_port:
                        logger.debug(
                            "gpu_instance_no_external_port",
                            instance_id=instance_id,
                        )
                        await asyncio.sleep(10)
                        continue

                    # Build endpoint with actual external port
                    endpoint = f"http://{public_ip}:{external_port}"

                    # Check vLLM health using OpenAI-compatible endpoint
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            # vLLM uses /v1/models endpoint (OpenAI-compatible)
                            response = await client.get(f"{endpoint}/v1/models")

                            if response.status_code == 200:
                                total_time = (datetime.utcnow() - start_time).total_seconds()
                                metrics["vllm_ready_time"] = total_time - (metrics["instance_boot_time"] or 0)
                                metrics["total_startup_time"] = total_time

                                logger.info(
                                    "vllm_server_ready",
                                    instance_id=instance_id,
                                    endpoint=endpoint,
                                    total_startup_seconds=total_time,
                                    boot_time=metrics["instance_boot_time"],
                                    vllm_load_time=metrics["vllm_ready_time"],
                                )

                                return endpoint

                    except httpx.RequestError as e:
                        logger.debug(
                            "vllm_health_check_waiting",
                            instance_id=instance_id,
                            endpoint=endpoint,
                            error=str(e),
                        )

                elif status in ["exited", "stopped"]:
                    logger.error(
                        "vllm_instance_failed",
                        instance_id=instance_id,
                        status=status,
                    )
                    # Destroy failed instance
                    await self.destroy_instance()
                    raise RuntimeError(f"Instance failed with status: {status}")

                else:
                    logger.debug(
                        "vllm_instance_starting",
                        instance_id=instance_id,
                        status=status,
                    )

            except VastAINotFoundError:
                # Instance not found yet - expected during initial startup
                logger.debug(
                    "vllm_instance_not_in_api_yet",
                    instance_id=instance_id,
                    elapsed_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )
            except Exception as e:
                # Unexpected error
                logger.warning(
                    "vllm_wait_error",
                    instance_id=instance_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

            # Wait before next check
            await asyncio.sleep(15)

        # Timeout reached
        logger.error(
            "vllm_ready_timeout",
            instance_id=instance_id,
            timeout_minutes=settings.vastai.max_startup_time_minutes,
        )

        # Destroy failed instance
        if settings.vastai.auto_destroy_on_error:
            await self.destroy_instance()

        raise TimeoutError(
            f"vLLM not ready after {settings.vastai.max_startup_time_minutes} minutes"
        )

    async def extend_keep_alive(self, additional_minutes: int):
        """
        Extend instance keep-alive time.

        Args:
            additional_minutes: Minutes to add to keep-alive
        """
        if not self.current_instance:
            logger.warning("extend_keep_alive_no_instance")
            return

        new_deadline = datetime.utcnow() + timedelta(minutes=additional_minutes)

        if new_deadline > self.keep_alive_until:
            self.keep_alive_until = new_deadline

            logger.info(
                "gpu_keep_alive_extended",
                instance_id=self.current_instance["id"],
                additional_minutes=additional_minutes,
                keep_alive_until=self.keep_alive_until.isoformat(),
            )

    def record_request(self):
        """Record LLM request for intelligent keep-alive"""
        self.recent_requests.append(time.time())

    async def destroy_instance(self) -> bool:
        """
        Destroy current GPU instance and cleanup.

        Returns:
            True if successful, False otherwise
        """
        if not self.current_instance:
            logger.warning("gpu_destroy_no_instance")
            return True

        instance_id = self.current_instance["id"]

        logger.info(
            "gpu_instance_destroying",
            instance_id=instance_id,
        )

        # Stop background tasks
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            self._keep_alive_task = None

        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            self._health_monitor_task = None

        # Calculate runtime cost
        if self.instance_start_time:
            runtime_seconds = (datetime.utcnow() - self.instance_start_time).total_seconds()
            cost = cost_tracker.add_vllm_session(int(runtime_seconds))

            logger.info(
                "gpu_session_cost_tracked",
                instance_id=instance_id,
                runtime_seconds=runtime_seconds,
                runtime_hours=runtime_seconds / 3600,
                cost_usd=cost,
            )

        # Destroy via API
        success = await self.vast_client.destroy_instance(instance_id)

        if success:
            logger.info(
                "gpu_instance_destroyed",
                instance_id=instance_id,
                runtime_minutes=(
                    (datetime.utcnow() - self.instance_start_time).total_seconds() / 60
                    if self.instance_start_time else 0
                ),
            )

            # Clear state
            self.current_instance = None
            self.instance_start_time = None
            self.keep_alive_until = None
            self.vllm_endpoint = None
            self.health_check_failures = 0

        return success

    def _check_budget(self):
        """
        Checkpoint 1: Verify total budget not exceeded.

        Raises:
            RuntimeError: If budget exceeded
        """
        total_spent = cost_tracker.get_total_cost()

        if total_spent >= self.budget_limit:
            logger.error(
                "budget_exceeded",
                total_spent=total_spent,
                budget_limit=self.budget_limit,
            )
            raise RuntimeError(
                f"Budget limit exceeded: ${total_spent:.2f} / ${self.budget_limit:.2f}"
            )

        remaining = self.budget_limit - total_spent

        logger.info(
            "budget_check_passed",
            total_spent=total_spent,
            budget_limit=self.budget_limit,
            remaining=remaining,
        )

    def _check_session_budget(self, keep_alive_minutes: int):
        """
        Checkpoint 2: Verify session won't exceed session budget.

        Args:
            keep_alive_minutes: Planned keep-alive time

        Raises:
            RuntimeError: If session would exceed budget
        """
        if not self.current_instance:
            return

        price_per_hour = self.current_instance.get("price_per_hour", 0.15)
        estimated_cost = (keep_alive_minutes / 60) * price_per_hour

        if estimated_cost > self.session_budget:
            logger.error(
                "session_budget_exceeded",
                estimated_cost=estimated_cost,
                session_budget=self.session_budget,
                keep_alive_minutes=keep_alive_minutes,
                price_per_hour=price_per_hour,
            )
            raise RuntimeError(
                f"Session would exceed budget: ${estimated_cost:.2f} / ${self.session_budget:.2f}"
            )

        logger.info(
            "session_budget_check_passed",
            estimated_cost=estimated_cost,
            session_budget=self.session_budget,
        )

    def _is_instance_alive(self) -> bool:
        """Check if current instance is still alive"""
        return (
            self.current_instance is not None and
            self.keep_alive_until is not None and
            datetime.utcnow() < self.keep_alive_until
        )

    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        if not self._keep_alive_task:
            self._keep_alive_task = asyncio.create_task(self._keep_alive_monitor())

        if not self._health_monitor_task:
            self._health_monitor_task = asyncio.create_task(self._health_monitor())

    async def _keep_alive_monitor(self):
        """Background task to monitor keep-alive and auto-destroy"""
        try:
            while self.current_instance:
                # Check if expired
                if datetime.utcnow() >= self.keep_alive_until:
                    logger.info(
                        "gpu_keep_alive_expired_auto_destroy",
                        instance_id=self.current_instance["id"],
                    )
                    await self.destroy_instance()
                    break

                # Sleep and check again
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.debug("keep_alive_monitor_cancelled")
        except Exception as e:
            logger.error("keep_alive_monitor_error", error=str(e), exc_info=True)

    async def _health_monitor(self):
        """Background task to monitor vLLM health"""
        try:
            interval = settings.vastai.health_check_interval_seconds

            while self.current_instance and self.vllm_endpoint:
                await asyncio.sleep(interval)

                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{self.vllm_endpoint}/health")

                        if response.status_code == 200:
                            self.health_check_failures = 0
                        else:
                            self.health_check_failures += 1
                            logger.warning(
                                "vllm_health_check_failed",
                                instance_id=self.current_instance["id"],
                                status_code=response.status_code,
                                failures=self.health_check_failures,
                            )

                except Exception as e:
                    self.health_check_failures += 1
                    logger.warning(
                        "vllm_health_check_error",
                        instance_id=self.current_instance["id"],
                        error=str(e),
                        failures=self.health_check_failures,
                    )

                # Circuit breaker
                if self.health_check_failures >= self.max_health_failures:
                    logger.error(
                        "vllm_health_circuit_breaker_triggered",
                        instance_id=self.current_instance["id"],
                        consecutive_failures=self.health_check_failures,
                    )
                    if settings.vastai.auto_destroy_on_error:
                        await self.destroy_instance()
                    break

        except asyncio.CancelledError:
            logger.debug("health_monitor_cancelled")
        except Exception as e:
            logger.error("health_monitor_error", error=str(e), exc_info=True)

    async def cleanup_orphaned_instances(self):
        """
        Safety mechanism: Destroy any forgotten/orphaned instances.

        Should be run periodically (e.g., daily cron job).
        """
        await self._init_client()

        logger.info("orphaned_instance_cleanup_starting")

        try:
            instances = await self.vast_client.list_instances()

            for instance in instances:
                instance_id = instance.get("id")

                logger.warning(
                    "orphaned_instance_found",
                    instance_id=instance_id,
                    status=instance.get("actual_status"),
                    label=instance.get("label"),
                )

                await self.vast_client.destroy_instance(instance_id)

            logger.info(
                "orphaned_instance_cleanup_complete",
                instances_cleaned=len(instances),
            )

        except Exception as e:
            logger.error(
                "orphaned_instance_cleanup_failed",
                error=str(e),
                exc_info=True,
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive orchestrator status.

        Returns:
            Status dictionary with instance details, runtime, costs, and launch state
        """
        # Include launch state in all responses
        base_status = {
            "launch_state": self.launch_state.value,
            "launch_error": self.launch_error,
        }

        if not self.current_instance:
            return {
                **base_status,
                "status": "stopped" if self.launch_state == LaunchState.IDLE else "launching",
                "instance": None,
                "runtime_minutes": 0,
                "estimated_cost": 0.0,
            }

        runtime_seconds = (datetime.utcnow() - self.instance_start_time).total_seconds()
        price_per_hour = self.current_instance.get("price_per_hour", 0.15)
        estimated_cost = (runtime_seconds / 3600) * price_per_hour

        return {
            **base_status,
            "status": "running" if self.launch_state == LaunchState.READY else "launching",
            "instance": {
                "id": self.current_instance["id"],
                "gpu_name": self.current_instance.get("gpu_name"),
                "endpoint": self.vllm_endpoint,
                "price_per_hour": price_per_hour,
            },
            "runtime_minutes": round(runtime_seconds / 60, 1),
            "keep_alive_until": self.keep_alive_until.isoformat() if self.keep_alive_until else None,
            "estimated_cost": round(estimated_cost, 6),
            "health_failures": self.health_check_failures,
        }

    async def close(self):
        """Cleanup resources"""
        if settings.vastai.auto_destroy_on_shutdown:
            await self.destroy_instance()

        if self.vast_client:
            await self.vast_client.close()

        logger.info("gpu_orchestrator_closed")


# Global orchestrator instance
gpu_orchestrator = GPUOrchestrator()
