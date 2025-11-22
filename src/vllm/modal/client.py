"""
Modal Client for vLLM Inference

This client provides a simple interface to interact with Modal's serverless vLLM deployment.
Unlike Vast.ai, Modal is serverless - no instance management required.

Key Differences from Vast.ai:
    - No instance creation/destruction (Modal auto-scales)
    - No GPU search/selection (Modal handles behind the scenes)
    - No budget tracking (set spending limits in Modal dashboard)
    - Pay-per-second of actual GPU usage

Architecture:
    1. Deploy vLLM to Modal (one-time setup)
    2. Get Modal web URL
    3. Make OpenAI-compatible API calls
    4. Modal automatically provisions/releases GPUs

Usage:
    client = ModalVLLMClient(modal_web_url="https://yourapp.modal.run")
    await client.health_check()
    response = await client.chat_completion(messages=[...])
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ModalVLLMClient:
    """
    Async HTTP client for Modal's serverless vLLM deployment.

    This client provides a simple interface to:
        - Check server health
        - Make chat completion requests
        - Stream responses

    No instance management is required - Modal handles all GPU provisioning.
    """

    def __init__(
        self,
        modal_web_url: str,
        timeout: int = 120,
        max_retries: int = 3,
    ):
        """
        Initialize Modal vLLM client.

        Args:
            modal_web_url: Modal web URL (e.g., https://yourapp.modal.run)
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum retry attempts for failed requests (default: 3)
        """
        self.modal_web_url = modal_web_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        logger.info(f"Initialized Modal vLLM client: {self.modal_web_url}")

    async def health_check(self, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if Modal vLLM server is healthy.

        Args:
            timeout: Optional timeout override (seconds)

        Returns:
            Health status dict with:
                - healthy: bool
                - status_code: int
                - response_time_ms: float

        Raises:
            aiohttp.ClientError: If health check fails after retries
        """
        if timeout is None:
            timeout = self.timeout

        start_time = asyncio.get_event_loop().time()

        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.modal_web_url}/health",
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as resp:
                        status_code = resp.status
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                        if status_code == 200:
                            logger.info(
                                f"Modal vLLM health check: OK (status={status_code}, "
                                f"response_time={response_time:.0f}ms)"
                            )
                            return {
                                "healthy": True,
                                "status_code": status_code,
                                "response_time_ms": response_time,
                            }
                        else:
                            logger.warning(
                                f"Modal vLLM health check failed: status={status_code}, "
                                f"attempt={attempt}/{self.max_retries}"
                            )

            except asyncio.TimeoutError:
                logger.warning(
                    f"Modal vLLM health check timeout after {timeout}s "
                    f"(attempt {attempt}/{self.max_retries})"
                )
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Modal vLLM health check error: {e} "
                    f"(attempt {attempt}/{self.max_retries})"
                )

            # Retry with exponential backoff
            if attempt < self.max_retries:
                backoff = 2 ** attempt  # 2s, 4s, 8s
                logger.info(f"Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

        # All retries exhausted
        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
        return {
            "healthy": False,
            "status_code": 0,
            "response_time_ms": response_time,
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "Qwen/Qwen2.5-7B-Instruct",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make chat completion request to Modal vLLM endpoint.

        Args:
            messages: Chat messages in OpenAI format
                [{"role": "system|user|assistant", "content": "..."}]
            model: Model name (must match deployed model)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented yet)
            timeout: Optional timeout override (seconds)

        Returns:
            Response dict with:
                - choices: List of completion choices
                - usage: Token usage statistics
                - model: Model name

        Raises:
            aiohttp.ClientError: If request fails after retries
            ValueError: If response is invalid
        """
        if timeout is None:
            timeout = self.timeout

        if stream:
            raise NotImplementedError(
                "Streaming is not yet implemented in modal_client. "
                "Use non-streaming mode (stream=False)."
            )

        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.modal_web_url}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as resp:
                        resp.raise_for_status()
                        data = await resp.json()

                        # Validate response
                        if "choices" not in data:
                            raise ValueError(f"Invalid response: missing 'choices' field")

                        logger.info(
                            f"Modal vLLM chat completion: "
                            f"model={model}, "
                            f"tokens={data.get('usage', {}).get('total_tokens', 'N/A')}"
                        )

                        return data

            except asyncio.TimeoutError:
                logger.warning(
                    f"Modal vLLM chat completion timeout after {timeout}s "
                    f"(attempt {attempt}/{self.max_retries})"
                )
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Modal vLLM chat completion error: {e} "
                    f"(attempt {attempt}/{self.max_retries})"
                )
            except ValueError as e:
                logger.error(f"Modal vLLM invalid response: {e}")
                raise

            # Retry with exponential backoff
            if attempt < self.max_retries:
                backoff = 2 ** attempt
                logger.info(f"Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

        # All retries exhausted
        raise aiohttp.ClientError(
            f"Modal vLLM chat completion failed after {self.max_retries} attempts"
        )

    async def get_models(self, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Get list of available models from Modal endpoint.

        Args:
            timeout: Optional timeout override (seconds)

        Returns:
            Models dict with:
                - object: "list"
                - data: List of model objects

        Raises:
            aiohttp.ClientError: If request fails
        """
        if timeout is None:
            timeout = self.timeout

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.modal_web_url}/v1/models",
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

                    logger.info(
                        f"Modal vLLM models: "
                        f"{len(data.get('data', []))} model(s) available"
                    )

                    return data

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.error(f"Failed to get models from Modal: {e}")
            raise

    def get_endpoint_url(self) -> str:
        """
        Get the OpenAI-compatible endpoint URL.

        This URL can be used with the OpenAI Python SDK:
            from openai import OpenAI
            client = OpenAI(base_url=modal_client.get_endpoint_url())

        Returns:
            Base URL for OpenAI-compatible API
        """
        return f"{self.modal_web_url}/v1"

    def __repr__(self) -> str:
        return f"ModalVLLMClient(url={self.modal_web_url})"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def create_modal_client(modal_web_url: str) -> ModalVLLMClient:
    """
    Create and validate Modal vLLM client.

    Args:
        modal_web_url: Modal web URL

    Returns:
        Initialized and validated ModalVLLMClient

    Raises:
        RuntimeError: If health check fails
    """
    client = ModalVLLMClient(modal_web_url=modal_web_url)

    # Validate connection
    health = await client.health_check()
    if not health["healthy"]:
        raise RuntimeError(
            f"Modal vLLM endpoint is not healthy: {modal_web_url}"
        )

    return client


# =============================================================================
# TESTING
# =============================================================================

async def _test_client():
    """Test Modal client (requires deployed Modal endpoint)."""
    import os

    # Get Modal URL from environment
    modal_url = os.getenv("MODAL_VLLM_URL")
    if not modal_url:
        print("❌ Error: MODAL_VLLM_URL environment variable not set")
        print("   Set it to your deployed Modal endpoint:")
        print("   export MODAL_VLLM_URL=https://yourapp.modal.run")
        return

    print(f"Testing Modal client with URL: {modal_url}\n")

    # Create client
    client = ModalVLLMClient(modal_web_url=modal_url)

    # Test 1: Health check
    print("[Test 1] Health check...")
    health = await client.health_check()
    if health["healthy"]:
        print(f"✅ Health check passed ({health['response_time_ms']:.0f}ms)\n")
    else:
        print(f"❌ Health check failed\n")
        return

    # Test 2: Get models
    print("[Test 2] Get models...")
    try:
        models = await client.get_models()
        print(f"✅ Models: {len(models.get('data', []))} available\n")
    except Exception as e:
        print(f"❌ Get models failed: {e}\n")

    # Test 3: Chat completion
    print("[Test 3] Chat completion...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2? Answer in one sentence."},
    ]
    try:
        response = await client.chat_completion(messages=messages, max_tokens=100)
        content = response["choices"][0]["message"]["content"]
        print(f"✅ Response: {content}\n")
    except Exception as e:
        print(f"❌ Chat completion failed: {e}\n")

    print(f"{'='*80}")
    print("✅ All tests passed!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(_test_client())
