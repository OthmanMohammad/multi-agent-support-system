"""
vLLM Multi-Provider Integration

Supports multiple GPU providers for vLLM deployment:
- Modal.com (ACTIVE): Serverless L4 GPU, auto-scaling, $0.80/hr
- Vast.ai (LEGACY): Deprecated due to infrastructure issues

Recommended: Use Modal.com for production deployments.
"""

from src.vllm.modal import (
    ModalVLLMClient,
    ModalOrchestrator,
    modal_orchestrator,
    init_modal_orchestrator,
    get_modal_orchestrator,
    is_modal_configured,
)

__all__ = [
    # Modal.com (ACTIVE - RECOMMENDED)
    "ModalVLLMClient",
    "ModalOrchestrator",
    "modal_orchestrator",
    "init_modal_orchestrator",
    "get_modal_orchestrator",
    "is_modal_configured",
]
