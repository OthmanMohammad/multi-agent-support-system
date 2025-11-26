"""
Modal.com Serverless GPU Integration

Production vLLM deployment using Modal's serverless platform.
- L4 GPU ($0.80/hr)
- Auto-scaling (5-minute scaledown)
- Pay-per-second billing
"""

from src.vllm.modal.client import ModalVLLMClient
from src.vllm.modal.orchestrator import (
    ModalOrchestrator,
    get_modal_orchestrator,
    init_modal_orchestrator,
    is_modal_configured,
    modal_orchestrator,
)

__all__ = [
    "ModalOrchestrator",
    "ModalVLLMClient",
    "get_modal_orchestrator",
    "init_modal_orchestrator",
    "is_modal_configured",
    "modal_orchestrator",
]
