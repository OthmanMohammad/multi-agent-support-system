"""
vLLM Docker Configuration

Defines Docker container setup for vLLM on Vast.ai GPU instances.
Includes startup scripts, health checks, and configuration management.

Vast.ai GPU Orchestration
"""

import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class VLLMDockerConfig:
    """
    vLLM Docker container configuration.

    Provides:
    - Docker image specification
    - Container startup commands
    - Environment variable management
    - Health check configuration
    - Onstart script generation
    """

    # Official vLLM image (OpenAI-compatible API)
    IMAGE = "vllm/vllm-openai:latest"

    # Alternative images for testing
    IMAGE_ALTERNATIVES = {
        "latest": "vllm/vllm-openai:latest",
        "v0.6.0": "vllm/vllm-openai:v0.6.0",
        "v0.5.5": "vllm/vllm-openai:v0.5.5",
    }

    @staticmethod
    def get_vllm_args(
        model: str | None = None,
        gpu_memory_utilization: float | None = None,
        max_model_len: int | None = None,
        tensor_parallel_size: int = 1,
        port: int = 8000,
    ) -> list[str]:
        """
        Generate vLLM server arguments.

        Args:
            model: Model to load (defaults to settings.vastai.vllm_model)
            gpu_memory_utilization: GPU memory usage (defaults to settings)
            max_model_len: Max context length (defaults to settings)
            tensor_parallel_size: Number of GPUs for tensor parallelism
            port: Server port

        Returns:
            List of command-line arguments for vLLM
        """
        # Use settings as defaults
        model = model or settings.vastai.vllm_model
        gpu_mem = gpu_memory_utilization or settings.vastai.vllm_gpu_memory_utilization
        max_len = max_model_len or settings.vastai.vllm_max_model_len

        args = [
            "--model",
            model,
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--tensor-parallel-size",
            str(tensor_parallel_size),
            "--gpu-memory-utilization",
            str(gpu_mem),
            "--max-model-len",
            str(max_len),
            "--dtype",
            "auto",  # Automatic dtype selection
            "--disable-log-requests",  # Reduce log noise
            "--trust-remote-code",  # Required for some models
        ]

        logger.info(
            "vllm_args_generated",
            model=model,
            gpu_memory_utilization=gpu_mem,
            max_model_len=max_len,
            tensor_parallel_size=tensor_parallel_size,
        )

        return args

    @staticmethod
    def get_docker_run_command(
        image: str | None = None,
        model: str | None = None,
        port: int = 8000,
        container_name: str = "vllm-server",
        shm_size: str = "8g",
    ) -> str:
        """
        Generate Docker run command for vLLM.

        Args:
            image: Docker image (defaults to IMAGE)
            model: Model to load
            port: Server port
            container_name: Container name
            shm_size: Shared memory size

        Returns:
            Complete Docker run command as string
        """
        image = image or VLLMDockerConfig.IMAGE
        vllm_args = VLLMDockerConfig.get_vllm_args(model=model, port=port)

        # Build command
        cmd_parts = [
            "docker run -d",
            f"--name {container_name}",
            "--gpus all",
            f"--shm-size {shm_size}",
            f"-p {port}:{port}",
            "--restart unless-stopped",  # Auto-restart on failure
            image,
        ] + vllm_args

        return " \\\n  ".join(cmd_parts)

    @staticmethod
    def get_onstart_script(
        model: str | None = None,
        port: int = 8000,
        container_name: str = "vllm-server",
    ) -> str:
        """
        Generate onstart script for Vast.ai instance.

        This script runs when the instance boots up and:
        1. Pulls the vLLM Docker image
        2. Starts the vLLM container
        3. Waits for the server to be ready
        4. Reports readiness

        Args:
            model: Model to load
            port: Server port
            container_name: Container name

        Returns:
            Bash script as string
        """
        vllm_args = VLLMDockerConfig.get_vllm_args(model=model, port=port)
        vllm_args_str = " \\\n      ".join(vllm_args)

        script = f"""#!/bin/bash
set -e  # Exit on any error

echo "======================================"
echo "vLLM Server Startup Script"
echo "Model: {model or settings.vastai.vllm_model}"
echo "Port: {port}"
echo "======================================"

# Update package lists
echo "[1/5] Updating package lists..."
apt-get update -qq

# Install required tools
echo "[2/5] Installing dependencies..."
apt-get install -y -qq curl docker.io

# Start Docker daemon if not running
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker daemon..."
    systemctl start docker
fi

# Pull vLLM image
echo "[3/5] Pulling vLLM Docker image..."
docker pull {VLLMDockerConfig.IMAGE}

# Remove old container if exists
if docker ps -a --format '{{{{.Names}}}}' | grep -q "^{container_name}$"; then
    echo "Removing old container..."
    docker rm -f {container_name}
fi

# Start vLLM container
echo "[4/5] Starting vLLM container..."
docker run -d \\
  --name {container_name} \\
  --gpus all \\
  --shm-size 8g \\
  -p {port}:{port} \\
  --restart unless-stopped \\
  {VLLMDockerConfig.IMAGE} \\
      {vllm_args_str}

# Wait for vLLM to be ready
echo "[5/5] Waiting for vLLM server to be ready..."
MAX_WAIT=600  # 10 minutes
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -f http://localhost:{port}/health 2>/dev/null; then
        echo ""
        echo "======================================"
        echo "✅ vLLM server is ready!"
        echo "Endpoint: http://$(curl -s ifconfig.me):{port}"
        echo "Health: http://$(curl -s ifconfig.me):{port}/health"
        echo "======================================"
        exit 0
    fi

    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "======================================"
echo "❌ vLLM server failed to start within $MAX_WAIT seconds"
echo "======================================"

# Show container logs for debugging
echo "Container logs:"
docker logs {container_name} --tail 50

exit 1
"""

        return script

    @staticmethod
    def get_environment_variables(
        hf_token: str | None = None,
    ) -> dict[str, str]:
        """
        Get environment variables for vLLM container.

        Args:
            hf_token: HuggingFace API token (for gated models)

        Returns:
            Dictionary of environment variables
        """
        env_vars = {
            "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
            "CUDA_VISIBLE_DEVICES": "0",  # Use first GPU
        }

        if hf_token:
            env_vars["HF_TOKEN"] = hf_token

        return env_vars

    @staticmethod
    def get_health_check_config() -> dict[str, any]:
        """
        Get health check configuration for vLLM.

        Returns:
            Health check configuration dictionary
        """
        return {
            "endpoint": "/health",
            "method": "GET",
            "expected_status": 200,
            "timeout_seconds": settings.vastai.health_check_timeout_seconds,
            "interval_seconds": settings.vastai.health_check_interval_seconds,
            "max_failures": 3,
        }

    @staticmethod
    def get_model_cache_config() -> dict[str, str]:
        """
        Get model cache configuration.

        Returns:
            Model cache paths and settings
        """
        return {
            "cache_dir": "/root/.cache/huggingface",
            "model_dir": "/root/.cache/huggingface/hub",
            "cache_size_gb": 50,
        }

    @staticmethod
    def validate_configuration():
        """
        Validate vLLM Docker configuration.

        Checks:
        - Model name is valid
        - GPU memory utilization is reasonable
        - Max model length is supported

        Raises:
            ValueError: If configuration is invalid
        """
        model = settings.vastai.vllm_model
        gpu_mem = settings.vastai.vllm_gpu_memory_utilization
        max_len = settings.vastai.vllm_max_model_len

        # Validate model name format
        if "/" not in model:
            raise ValueError(
                f"Invalid model name '{model}'. Expected format: 'organization/model-name'"
            )

        # Validate GPU memory utilization
        if not 0.1 <= gpu_mem <= 1.0:
            raise ValueError(
                f"Invalid GPU memory utilization: {gpu_mem}. Must be between 0.1 and 1.0"
            )

        # Validate max model length
        if max_len < 512 or max_len > 32768:
            raise ValueError(f"Invalid max model length: {max_len}. Must be between 512 and 32768")

        logger.info(
            "vllm_docker_config_validated",
            model=model,
            gpu_memory_utilization=gpu_mem,
            max_model_len=max_len,
        )

    @staticmethod
    def get_stop_script(container_name: str = "vllm-server") -> str:
        """
        Generate script to stop vLLM container.

        Args:
            container_name: Container name

        Returns:
            Bash script to stop and remove container
        """
        script = f"""#!/bin/bash
echo "Stopping vLLM container..."

if docker ps --format '{{{{.Names}}}}' | grep -q "^{container_name}$"; then
    docker stop {container_name}
    docker rm {container_name}
    echo "✅ vLLM container stopped and removed"
else
    echo "⚠️  Container '{container_name}' not running"
fi
"""
        return script


# Validate configuration on module import
try:
    VLLMDockerConfig.validate_configuration()
except Exception as e:
    logger.warning(
        "vllm_docker_config_validation_failed",
        error=str(e),
        message="Configuration will use defaults",
    )
