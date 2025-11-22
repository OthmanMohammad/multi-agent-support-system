"""
Vast.ai GPU Integration (LEGACY - NOT RECOMMENDED)

Historical implementation using Vast.ai for GPU rental.
Migrated to Modal.com due to infrastructure reliability issues.

This code is kept for reference but should not be used in production.
"""

from src.vllm.vastai.client import VastAIClient
from src.vllm.vastai.orchestrator import GPUOrchestrator, gpu_orchestrator

__all__ = [
    "VastAIClient",
    "GPUOrchestrator",
    "gpu_orchestrator",
]
