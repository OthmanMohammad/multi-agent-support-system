"""
Vast.ai API Client

Async HTTP client for Vast.ai REST API with retry logic and error handling.

API Documentation: https://vast.ai/docs/api

Vast.ai GPU Orchestration
"""

import asyncio
import json
from typing import Any

import httpx
import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class VastAIError(Exception):
    """Base exception for Vast.ai API errors"""

    pass


class VastAIAuthError(VastAIError):
    """Authentication error"""

    pass


class VastAINotFoundError(VastAIError):
    """Resource not found"""

    pass


class VastAIRateLimitError(VastAIError):
    """Rate limit exceeded"""

    pass


class VastAIClient:
    """
    Async Vast.ai API client.

    Features:
    - Exponential backoff retry logic
    - Automatic error handling
    - Request/response logging
    - Timeout management
    - Rate limit handling

    Usage:
        >>> client = VastAIClient()
        >>>
        >>> # Search for GPU offers
        >>> offers = await client.search_offers(
        ...     gpu_name="RTX 3090",
        ...     min_vram_gb=24,
        ...     max_price=0.15
        ... )
        >>>
        >>> # Launch instance
        >>> instance = await client.create_instance(
        ...     offer_id=12345,
        ...     image="vllm/vllm-openai:latest",
        ...     onstart_script="#!/bin/bash\necho 'Starting...'"
        ... )
        >>>
        >>> # Destroy instance
        >>> await client.destroy_instance(instance_id=67890)
        >>>
        >>> # Cleanup
        >>> await client.close()
    """

    BASE_URL = "https://console.vast.ai/api/v0"

    def __init__(self, api_key: str | None = None):
        """
        Initialize Vast.ai client.

        Args:
            api_key: Vast.ai API key (defaults to settings.vastai.api_key)

        Raises:
            ValueError: If API key is not provided and not in settings
        """
        self.api_key = api_key or settings.vastai.api_key

        if not self.api_key:
            raise ValueError(
                "Vast.ai API key required. "
                "Set VASTAI_API_KEY environment variable or pass api_key parameter."
            )

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(
                timeout=settings.vastai.search_timeout_seconds,
                connect=10.0,
            ),
            follow_redirects=True,  # Follow 301/302 redirects from Vast.ai API
        )

        self.max_retries = settings.vastai.max_search_retries
        self.base_delay = 2.0  # seconds

        logger.info("vastai_client_initialized", base_url=self.BASE_URL)

    async def _request_with_retry(
        self, method: str, endpoint: str, max_retries: int | None = None, **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with exponential backoff retry.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            max_retries: Maximum retry attempts (defaults to self.max_retries)
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            VastAIError: On API errors
            VastAIAuthError: On authentication failures
            VastAINotFoundError: On 404 errors
            VastAIRateLimitError: On rate limit errors
        """
        max_retries = max_retries or self.max_retries
        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.debug(
                    "vastai_api_request",
                    method=method,
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                )

                response = await self.client.request(method, endpoint, **kwargs)

                # Handle specific status codes
                if response.status_code == 401:
                    raise VastAIAuthError("Invalid API key")

                elif response.status_code == 404:
                    raise VastAINotFoundError(f"Resource not found: {endpoint}")

                elif response.status_code == 429:
                    raise VastAIRateLimitError("Rate limit exceeded")

                elif response.status_code >= 500:
                    # Server error - retry
                    logger.warning(
                        "vastai_api_server_error",
                        status_code=response.status_code,
                        endpoint=endpoint,
                        attempt=attempt + 1,
                    )
                    last_exception = VastAIError(f"Server error: {response.status_code}")
                    continue

                elif response.status_code >= 400:
                    # Client error - don't retry
                    error_text = response.text
                    raise VastAIError(f"API error {response.status_code}: {error_text}")

                # Success
                response.raise_for_status()

                logger.debug(
                    "vastai_api_success",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                )

                return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(
                    "vastai_api_network_error",
                    error=str(e),
                    attempt=attempt + 1,
                    endpoint=endpoint,
                )
                last_exception = VastAIError(f"Network error: {e!s}")

            except (VastAIAuthError, VastAINotFoundError):
                # Don't retry auth or not-found errors
                raise

            except VastAIRateLimitError:
                # Longer delay for rate limiting
                delay = self.base_delay * (2**attempt) * 2
                logger.warning(
                    "vastai_api_rate_limited",
                    delay_seconds=delay,
                    attempt=attempt + 1,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

            # Exponential backoff before retry
            if attempt < max_retries - 1:
                delay = self.base_delay * (2**attempt)  # 2s, 4s, 8s
                logger.info(
                    "vastai_api_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=delay,
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise last_exception or VastAIError("All retry attempts failed")

    async def search_offers(
        self,
        gpu_name: str,
        min_vram_gb: int,
        max_price: float,
        verified_only: bool = True,
        available_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search for available GPU offers.

        Args:
            gpu_name: GPU model name (e.g., "RTX 3090")
            min_vram_gb: Minimum VRAM in GB
            max_price: Maximum price per hour in USD
            verified_only: Only include verified hosts
            available_only: Only include available instances

        Returns:
            List of offer dictionaries, sorted by price (cheapest first)

        Examples:
            >>> client = VastAIClient()
            >>> offers = await client.search_offers(
            ...     gpu_name="RTX 3090",
            ...     min_vram_gb=24,
            ...     max_price=0.15
            ... )
            >>> print(f"Found {len(offers)} offers")
        """
        try:
            # Build query filter
            query_filter = {
                "gpu_name": {"eq": gpu_name},
            }

            if verified_only:
                query_filter["verified"] = {"eq": True}

            if available_only:
                query_filter["rentable"] = {"eq": True}

            # Make request
            params = {
                "q": json.dumps(query_filter),  # Proper JSON serialization
                "order": '[["dph_total", "asc"]]',  # Sort by price
            }

            response = await self._request_with_retry(
                "GET",
                "/bundles",
                params=params,
            )

            data = response.json()
            offers = data.get("offers", [])

            # Filter by VRAM and price
            filtered_offers = [
                offer
                for offer in offers
                if (
                    offer.get("gpu_ram", 0) >= min_vram_gb * 1024  # MB to GB
                    and offer.get("dph_total", 999) <= max_price
                    and (not available_only or offer.get("rentable", False))
                )
            ]

            logger.info(
                "vastai_search_complete",
                gpu_name=gpu_name,
                min_vram_gb=min_vram_gb,
                max_price=max_price,
                total_offers=len(offers),
                filtered_offers=len(filtered_offers),
                cheapest_price=filtered_offers[0].get("dph_total") if filtered_offers else None,
            )

            return filtered_offers

        except Exception as e:
            logger.error(
                "vastai_search_failed",
                gpu_name=gpu_name,
                error=str(e),
                exc_info=True,
            )
            raise

    async def create_instance(
        self,
        offer_id: int,
        image: str,
        disk_gb: int = 50,
        label: str | None = None,
        docker_args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
        runtype: str = "args",
        onstart: str | None = None,
    ) -> dict[str, Any]:
        """
        Launch GPU instance from offer.

        Args:
            offer_id: Vast.ai offer ID
            image: Docker image to run
            disk_gb: Disk space in GB
            label: Optional instance label
            docker_args: Docker CMD arguments (for runtype='args')
            env_vars: Environment variables as dict (optional)
            runtype: Launch mode - 'args', 'ssh', 'ssh_direct', 'ssh_proxy'
            onstart: Onstart script to run after instance boots (for SSH mode)

        Returns:
            Instance information dictionary

        Raises:
            VastAIError: On launch failure

        Notes:
            - Use runtype='args' with docker_args for direct Docker container launch
            - Use runtype='ssh_direct' with onstart for SSH mode with port forwarding
            - Ports in SSH mode are exposed via the instance's 'ports' field

        Examples:
            >>> # Docker args mode
            >>> instance = await client.create_instance(
            ...     offer_id=12345,
            ...     image="vllm/vllm-openai:latest",
            ...     docker_args=["--model", "meta-llama/Llama-2-7b-hf"],
            ...     runtype="args"
            ... )
            >>> # SSH mode with onstart script
            >>> instance = await client.create_instance(
            ...     offer_id=12345,
            ...     image="nvidia/cuda:12.1.0-base-ubuntu22.04",
            ...     onstart="docker run -d -p 8000:8000 vllm/vllm-openai:latest ...",
            ...     runtype="ssh_direct"
            ... )
        """
        try:
            payload = {
                "client_id": "me",  # Use current account
                "image": image,
                "disk": disk_gb,
                "runtype": runtype,  # 'args' for Docker mode
            }

            if label:
                payload["label"] = label

            if docker_args:
                payload["args"] = docker_args

            # Add environment variables as dict (REST API format)
            if env_vars:
                payload["env"] = env_vars

            # Add onstart script for SSH mode
            # Note: Vast.ai API expects "onstart_cmd" not "onstart"
            if onstart:
                payload["onstart_cmd"] = onstart

            response = await self._request_with_retry(
                "PUT",
                f"/asks/{offer_id}/",
                json=payload,
            )

            instance_data = response.json()

            logger.info(
                "vastai_instance_created",
                offer_id=offer_id,
                instance_id=instance_data.get("new_contract"),
                image=image,
            )

            return instance_data

        except Exception as e:
            logger.error(
                "vastai_instance_creation_failed",
                offer_id=offer_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def get_instance(self, instance_id: int) -> dict[str, Any]:
        """
        Get instance details by querying all instances and filtering by ID.

        Args:
            instance_id: Instance ID

        Returns:
            Instance details dictionary

        Raises:
            VastAINotFoundError: If instance not found
        """
        try:
            # Query all instances (Vast.ai doesn't support direct instance query by ID)
            response = await self._request_with_retry(
                "GET",
                "/instances/",
            )

            data = response.json()
            instances = data.get("instances", [])

            # Filter by instance ID
            matching_instances = [inst for inst in instances if inst.get("id") == instance_id]

            if not matching_instances:
                logger.warning(
                    "vastai_instance_not_found_yet",
                    instance_id=instance_id,
                    total_instances=len(instances),
                )
                raise VastAINotFoundError(
                    f"Instance {instance_id} not found in instances list (may still be starting up)"
                )

            instance = matching_instances[0]
            logger.debug(
                "vastai_instance_found",
                instance_id=instance_id,
                status=instance.get("actual_status"),
                public_ip=instance.get("public_ipaddr"),
            )

            return instance

        except VastAINotFoundError:
            # Re-raise not found errors
            raise
        except Exception as e:
            logger.error(
                "vastai_get_instance_failed",
                instance_id=instance_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def list_instances(self) -> list[dict[str, Any]]:
        """
        List all running instances.

        Returns:
            List of instance dictionaries
        """
        try:
            response = await self._request_with_retry(
                "GET",
                "/instances/",
            )

            data = response.json()
            instances = data.get("instances", [])

            logger.info(
                "vastai_instances_listed",
                count=len(instances),
            )

            return instances

        except Exception as e:
            logger.error("vastai_list_instances_failed", error=str(e))
            raise

    async def destroy_instance(self, instance_id: int) -> bool:
        """
        Destroy (terminate) GPU instance.

        Args:
            instance_id: Instance ID to destroy

        Returns:
            True if successful, False otherwise
        """
        try:
            await self._request_with_retry(
                "DELETE",
                f"/instances/{instance_id}/",
            )

            logger.info(
                "vastai_instance_destroyed",
                instance_id=instance_id,
            )

            return True

        except VastAINotFoundError:
            logger.warning(
                "vastai_instance_not_found_on_destroy",
                instance_id=instance_id,
            )
            return True  # Already gone

        except Exception as e:
            logger.error(
                "vastai_instance_destroy_failed",
                instance_id=instance_id,
                error=str(e),
                exc_info=True,
            )
            return False

    async def get_instance_status(self, instance_id: int) -> str:
        """
        Get instance status.

        Args:
            instance_id: Instance ID

        Returns:
            Status string (e.g., "running", "loading", "stopped")
        """
        try:
            instance = await self.get_instance(instance_id)
            status = instance.get("actual_status", "unknown")

            logger.debug(
                "vastai_instance_status",
                instance_id=instance_id,
                status=status,
            )

            return status

        except Exception as e:
            logger.error(
                "vastai_get_status_failed",
                instance_id=instance_id,
                error=str(e),
            )
            return "error"

    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self.client.aclose()
        logger.info("vastai_client_closed")
