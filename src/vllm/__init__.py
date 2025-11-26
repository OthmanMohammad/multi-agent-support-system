"""
vLLM Multi-Provider Integration

Supports multiple GPU providers for vLLM deployment:
- Modal.com (ACTIVE): Serverless L4 GPU, auto-scaling, $0.80/hr
- Vast.ai (LEGACY): Deprecated due to infrastructure issues

Recommended: Use Modal.com for production deployments.
"""

from src.vllm.modal import (
    ModalOrchestrator,
    ModalVLLMClient,
    get_modal_orchestrator,
    init_modal_orchestrator,
    is_modal_configured,
    modal_orchestrator,
)

__all__ = [
    "ModalOrchestrator",
    # Modal.com (ACTIVE - RECOMMENDED)
    "ModalVLLMClient",
    "get_modal_orchestrator",
    "init_modal_orchestrator",
    "is_modal_configured",
    "modal_orchestrator",
]
