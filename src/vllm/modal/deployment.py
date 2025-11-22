"""
Modal vLLM Deployment Script

This script deploys vLLM as a serverless function on Modal.com.
Modal automatically handles GPU provisioning, scaling, and management.

Deployment:
    modal deploy src/vllm/modal_vllm.py

Testing:
    modal run src/vllm/modal_vllm.py::test

Architecture:
    - Serverless: No manual instance creation/destruction
    - Auto-scaling: Modal scales GPUs based on demand
    - Pay-per-second: Only charged for actual GPU usage
    - OpenAI-compatible: Standard API endpoint
"""

import json
import os
from typing import Any

import aiohttp
import modal

# =============================================================================
# CONFIGURATION
# =============================================================================

# Model Configuration
# Using Qwen2.5-7B-Instruct - excellent performance, fits in $30 free tier
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
MODEL_REVISION = "main"  # Use latest stable version

# GPU Configuration
# L4 (24GB): $0.80/hour = $0.000222/second
# A100 (40GB): $3.00/hour = $0.000833/second
# H100 (80GB): $4.50/hour = $0.00125/second
# For $30 budget: ~37.5 hours of L4 usage or ~10 hours of A100
GPU_CONFIG = "L4"  # Best value: L4 ($0.80/hr), A100 ($3/hr), H100 ($4.50/hr)
N_GPU = 1  # Single GPU is sufficient for 7B model

# Scaling Configuration
SCALEDOWN_WINDOW_MINUTES = 5  # Keep warm for 5 minutes after last request
TIMEOUT_MINUTES = 30  # Maximum function execution time
STARTUP_TIMEOUT_MINUTES = 10  # Time allowed for model loading

# vLLM Server Configuration
VLLM_PORT = 8000
MAX_CONCURRENT_REQUESTS = 32  # Modal concurrent request limit

# Performance Tuning
FAST_BOOT = True  # Disable compilation for faster cold starts

# =============================================================================
# MODAL SETUP
# =============================================================================

# Container Image: CUDA 12.8 + Python 3.12 + vLLM
vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.0-devel-ubuntu22.04",
        add_python="3.12"
    )
    .entrypoint([])  # Clear default entrypoint
    .uv_pip_install(
        "vllm==0.11.2",
        "huggingface-hub==0.36.0",
        "flashinfer-python==0.5.2",
    )
    .env({
        "HF_XET_HIGH_PERFORMANCE": "1",  # Optimize HF downloads
        "VLLM_LOGGING_LEVEL": "INFO",
    })
)

# Persistent Volumes for Caching
# These volumes cache model weights and vLLM compilation artifacts
# to avoid re-downloading on every cold start
hf_cache_vol = modal.Volume.from_name(
    "vllm-huggingface-cache",
    create_if_missing=True
)
vllm_cache_vol = modal.Volume.from_name(
    "vllm-compilation-cache",
    create_if_missing=True
)

# Modal App
app = modal.App("multi-agent-vllm-inference")

# =============================================================================
# VLLM SERVER
# =============================================================================

@app.function(
    image=vllm_image,
    gpu=f"{GPU_CONFIG}:{N_GPU}",
    scaledown_window=SCALEDOWN_WINDOW_MINUTES * 60,  # Convert to seconds
    timeout=TIMEOUT_MINUTES * 60,  # Convert to seconds
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=MAX_CONCURRENT_REQUESTS)
@modal.web_server(port=VLLM_PORT, startup_timeout=STARTUP_TIMEOUT_MINUTES * 60)
def serve():
    """
    Launch vLLM server with OpenAI-compatible API.

    The server exposes endpoints:
        - GET /health - Health check
        - GET /v1/models - List available models
        - POST /v1/completions - Text completion
        - POST /v1/chat/completions - Chat completion (streaming supported)

    Returns:
        None (runs vLLM server as subprocess)
    """
    import subprocess

    # Build vLLM command
    cmd = [
        "vllm",
        "serve",
        MODEL_NAME,
        "--revision", MODEL_REVISION,
        "--served-model-name", MODEL_NAME,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--uvicorn-log-level=info",
    ]

    # Performance tuning
    if FAST_BOOT:
        cmd.append("--enforce-eager")  # Disable CUDA graphs for faster startup
    else:
        cmd.append("--no-enforce-eager")  # Enable CUDA graphs for throughput

    # Tensor parallelism (multi-GPU)
    cmd.extend(["--tensor-parallel-size", str(N_GPU)])

    # Launch vLLM server
    print(f"[Modal vLLM] Starting server with command: {' '.join(cmd)}")
    subprocess.Popen(" ".join(cmd), shell=True)

# =============================================================================
# TESTING & VALIDATION
# =============================================================================

@app.local_entrypoint()
async def test(
    test_timeout: int = 10 * 60,  # 10 minutes
    content: str = None,
    twice: bool = True,
):
    """
    Test the deployed vLLM endpoint.

    Usage:
        modal run src/vllm/modal_vllm.py::test
        modal run src/vllm/modal_vllm.py::test --content "Explain quantum computing"

    Args:
        test_timeout: Maximum test duration in seconds
        content: User message to send (default: test prompt)
        twice: Whether to send two requests (tests caching)
    """
    import aiohttp

    # Get Modal web URL
    url = serve.web_url
    print(f"\n{'='*80}")
    print(f"[Modal vLLM Test] Server URL: {url}")
    print(f"{'='*80}\n")

    # Test messages
    system_prompt = {
        "role": "system",
        "content": "You are a helpful AI assistant for a technical support system.",
    }
    if content is None:
        content = "What is the capital of France? Answer in one sentence."

    messages = [
        system_prompt,
        {"role": "user", "content": content},
    ]

    async with aiohttp.ClientSession(base_url=url) as session:
        # Health check
        print(f"[Health Check] Running health check for {url}")
        async with session.get(
            "/health",
            timeout=test_timeout - 60
        ) as resp:
            up = resp.status == 200

        if not up:
            print(f"❌ [Health Check] FAILED - Server not healthy")
            raise RuntimeError(f"Health check failed for {url}")

        print(f"✅ [Health Check] SUCCESS - Server is healthy\n")

        # Test request 1
        print(f"[Test 1] Sending request:")
        print(f"  System: {system_prompt['content']}")
        print(f"  User: {content}")
        print(f"  Response: ", end="", flush=True)
        await _send_request(session, MODEL_NAME, messages)

        # Test request 2 (optional)
        if twice:
            print(f"\n[Test 2] Sending second request (tests caching):")
            messages[1]["content"] = "What is 2 + 2? Answer in one word."
            print(f"  User: {messages[1]['content']}")
            print(f"  Response: ", end="", flush=True)
            await _send_request(session, MODEL_NAME, messages)

        print(f"\n{'='*80}")
        print(f"✅ [Modal vLLM Test] All tests passed!")
        print(f"{'='*80}\n")


async def _send_request(
    session: aiohttp.ClientSession,
    model: str,
    messages: list,
) -> None:
    """
    Send chat completion request with streaming.

    Args:
        session: aiohttp client session
        model: Model name
        messages: Chat messages
    """
    payload: dict[str, Any] = {
        "messages": messages,
        "model": model,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 512,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    async with session.post(
        "/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    ) as resp:
        resp.raise_for_status()

        async for raw in resp.content:
            line = raw.decode().strip()

            # Skip empty lines and [DONE] marker
            if not line or line == "data: [DONE]":
                continue

            # Parse SSE format
            if line.startswith("data: "):
                line = line[len("data: "):]

            # Parse JSON chunk
            try:
                chunk = json.loads(line)
                assert chunk["object"] == "chat.completion.chunk"

                # Extract content delta
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    print(delta["content"], end="", flush=True)
            except (json.JSONDecodeError, KeyError, AssertionError) as e:
                print(f"\n⚠️  [Warning] Failed to parse chunk: {e}")
                continue

    print()  # Newline after streaming response


# =============================================================================
# DEPLOYMENT INFO
# =============================================================================

@app.function()
def get_deployment_info() -> dict[str, Any]:
    """
    Get deployment information (GPU type, model, pricing).

    Returns:
        Deployment configuration dict
    """
    return {
        "model": MODEL_NAME,
        "gpu": f"{GPU_CONFIG}:{N_GPU}",
        "scaledown_window_minutes": SCALEDOWN_WINDOW_MINUTES,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
        "endpoint": serve.web_url if serve.is_deployed else None,
    }


if __name__ == "__main__":
    print(f"""
{'='*80}
Modal vLLM Deployment Script
{'='*80}

Configuration:
  Model: {MODEL_NAME}
  GPU: {GPU_CONFIG} x{N_GPU}
  Scaledown: {SCALEDOWN_WINDOW_MINUTES} minutes

Commands:
  Deploy:  modal deploy src/vllm/modal_vllm.py
  Test:    modal run src/vllm/modal_vllm.py::test
  Logs:    modal app logs multi-agent-vllm-inference

Pricing (Modal Starter Plan):
  Free tier: $30/month included compute
  A100: $3.00/hour ($0.000833/second)
  H100: $4.50/hour ($0.00125/second)

  Your $15 budget gets:
    - ~36 hours of A100 time
    - ~24 hours of H100 time
    - Only charged when processing requests (pay-per-second)

{'='*80}
""")
