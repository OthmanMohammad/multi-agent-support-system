"""
Admin API Routes

Administrative endpoints for LLM backend management, cost tracking, and metrics.

Endpoints:
- Backend switching (Anthropic ↔ vLLM)
- Cost tracking and budgets
- Metrics and usage statistics
- Backend health monitoring

Part of: Phase 2 - LiteLLM Multi-Backend Abstraction Layer
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import structlog

from src.llm.litellm_config import LLMBackend
from src.services.infrastructure.backend_manager import backend_manager
from src.utils.cost_tracking import cost_tracker
from src.utils.monitoring.metrics import llm_metrics
from src.llm.client import llm_client
from src.api.dependencies.auth_dependencies import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Request Models
class BackendSwitchRequest(BaseModel):
    """Request to switch LLM backend"""
    backend: LLMBackend
    skip_health_check: bool = False


class VLLMEndpointRequest(BaseModel):
    """Request to configure vLLM endpoint"""
    endpoint: str


class BudgetUpdateRequest(BaseModel):
    """Request to update budget limit"""
    budget_limit: float


# Admin authentication dependency (simplified for now)
async def require_admin(current_user = Depends(get_current_user)):
    """
    Require admin privileges.

    For now, all authenticated users can access admin endpoints.
    TODO: Implement proper role-based access control.
    """
    # In production, check if user has admin role
    # if not current_user.get("is_admin"):
    #     raise HTTPException(status_code=403, detail="Admin access required")

    return current_user


# ============================================================================
# Backend Management Endpoints
# ============================================================================

@router.post("/backend/switch")
async def switch_backend(
    request: BackendSwitchRequest,
    _user = Depends(require_admin),
):
    """
    Switch LLM backend.

    Switches between Anthropic Claude API and vLLM (self-hosted).

    **Permissions:** Admin only

    **Example:**
    ```bash
    curl -X POST https://your-domain.com/api/admin/backend/switch \\
      -H "Authorization: Bearer <TOKEN>" \\
      -H "Content-Type: application/json" \\
      -d '{"backend": "anthropic"}'
    ```
    """
    try:
        result = await backend_manager.switch_backend(
            backend=request.backend,
            skip_health_check=request.skip_health_check
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

        logger.info(
            "admin_backend_switch",
            backend=request.backend.value,
            success=True,
        )

        return result

    except ValueError as e:
        logger.error("admin_backend_switch_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("admin_backend_switch_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Backend switch failed")


@router.get("/backend/current")
async def get_current_backend(_user = Depends(require_admin)):
    """
    Get current LLM backend and status.

    Returns detailed information about the currently active backend.

    **Permissions:** Admin only
    """
    info = backend_manager.get_backend_info()
    return info


@router.get("/backend/health")
async def check_backend_health(_user = Depends(require_admin)):
    """
    Check health of all LLM backends.

    Tests connectivity to Anthropic API and vLLM endpoints.

    **Permissions:** Admin only
    """
    health = await backend_manager.check_all_backends()
    return health


@router.post("/vllm/endpoint")
async def set_vllm_endpoint(
    request: VLLMEndpointRequest,
    _user = Depends(require_admin),
):
    """
    Configure vLLM endpoint.

    Sets the URL for the vLLM server and checks its health.

    **Permissions:** Admin only

    **Example:**
    ```bash
    curl -X POST https://your-domain.com/api/admin/vllm/endpoint \\
      -H "Authorization: Bearer <TOKEN>" \\
      -H "Content-Type: application/json" \\
      -d '{"endpoint": "http://165.22.45.67:8000"}'
    ```
    """
    try:
        result = await backend_manager.set_vllm_endpoint(request.endpoint)

        logger.info(
            "admin_vllm_endpoint_set",
            endpoint=request.endpoint,
            healthy=result["healthy"],
        )

        return result

    except Exception as e:
        logger.error("admin_vllm_endpoint_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to configure vLLM endpoint")


# ============================================================================
# vLLM GPU Orchestration Endpoints (Phase 3)
# ============================================================================

class VLLMLaunchRequest(BaseModel):
    """Request to launch vLLM GPU instance"""
    keep_alive_minutes: int = 45
    auto_switch: bool = True


class VLLMExtendRequest(BaseModel):
    """Request to extend keep-alive time"""
    additional_minutes: int = 15


@router.post("/vllm/launch")
async def launch_vllm_gpu(
    request: VLLMLaunchRequest,
    _user = Depends(require_admin),
):
    """
    Launch vLLM GPU instance on Vast.ai.

    **Phase 3 Feature:** On-demand GPU rental with automatic orchestration.

    This endpoint:
    1. Searches for available GPU across 10 fallback configurations
    2. Launches the cheapest compatible instance
    3. Waits for vLLM to be ready
    4. Optionally switches backend to vLLM

    **Permissions:** Admin only

    **Example:**
    ```bash
    curl -X POST https://your-domain.com/api/admin/vllm/launch \\
      -H "Authorization: Bearer <TOKEN>" \\
      -H "Content-Type: application/json" \\
      -d '{"keep_alive_minutes": 45, "auto_switch": true}'
    ```

    **Response:**
    ```json
    {
      "success": true,
      "endpoint": "http://165.22.45.67:8000",
      "instance": {
        "id": 12345,
        "gpu_name": "RTX 3090",
        "price_per_hour": 0.14
      },
      "keep_alive_until": "2024-11-22T12:00:00",
      "estimated_cost": 0.105,
      "backend_switched": true
    }
    ```
    """
    try:
        result = await backend_manager.launch_vllm_gpu(
            keep_alive_minutes=request.keep_alive_minutes,
            auto_switch=request.auto_switch,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to launch vLLM GPU")
            )

        logger.info(
            "admin_vllm_gpu_launched",
            endpoint=result.get("endpoint"),
            instance_id=result.get("instance", {}).get("id"),
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("admin_vllm_launch_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch vLLM GPU: {str(e)}"
        )


@router.post("/vllm/destroy")
async def destroy_vllm_gpu(_user = Depends(require_admin)):
    """
    Destroy vLLM GPU instance.

    Terminates the current GPU instance and stops billing.

    **Permissions:** Admin only

    **Example:**
    ```bash
    curl -X POST https://your-domain.com/api/admin/vllm/destroy \\
      -H "Authorization: Bearer <TOKEN>"
    ```
    """
    try:
        result = await backend_manager.destroy_vllm_gpu()

        if not result["success"]:
            logger.warning("admin_vllm_destroy_failed", message=result.get("message"))

        logger.info("admin_vllm_gpu_destroyed", success=result["success"])

        return result

    except Exception as e:
        logger.error("admin_vllm_destroy_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to destroy vLLM GPU: {str(e)}")


@router.get("/vllm/status")
async def get_vllm_status(_user = Depends(require_admin)):
    """
    Get vLLM GPU instance status.

    Returns current instance details, runtime, and costs.

    **Permissions:** Admin only

    **Response:**
    ```json
    {
      "status": "running",
      "instance": {
        "id": 12345,
        "gpu_name": "RTX 3090",
        "endpoint": "http://165.22.45.67:8000",
        "price_per_hour": 0.14
      },
      "runtime_minutes": 22.5,
      "keep_alive_until": "2024-11-22T12:00:00",
      "estimated_cost": 0.0525,
      "health_failures": 0
    }
    ```
    """
    try:
        status = await backend_manager.get_vllm_status()

        logger.debug("admin_vllm_status_checked", status=status.get("status"))

        return status

    except Exception as e:
        logger.error("admin_vllm_status_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get vLLM status: {str(e)}")


@router.post("/vllm/extend")
async def extend_vllm_keep_alive(
    request: VLLMExtendRequest,
    _user = Depends(require_admin),
):
    """
    Extend vLLM GPU keep-alive time.

    Adds additional minutes to prevent automatic shutdown.

    **Permissions:** Admin only

    **Example:**
    ```bash
    curl -X POST https://your-domain.com/api/admin/vllm/extend \\
      -H "Authorization: Bearer <TOKEN>" \\
      -H "Content-Type: application/json" \\
      -d '{"additional_minutes": 15}'
    ```
    """
    try:
        from src.vllm.orchestrator import gpu_orchestrator

        # Check if instance running
        status = gpu_orchestrator.get_status()
        if status["status"] != "running":
            raise HTTPException(
                status_code=400,
                detail="No vLLM GPU instance running"
            )

        # Extend keep-alive
        await gpu_orchestrator.extend_keep_alive(request.additional_minutes)

        # Get updated status
        updated_status = gpu_orchestrator.get_status()

        logger.info(
            "admin_vllm_keep_alive_extended",
            additional_minutes=request.additional_minutes,
            new_keep_alive=updated_status.get("keep_alive_until"),
        )

        return {
            "success": True,
            "additional_minutes": request.additional_minutes,
            "keep_alive_until": updated_status.get("keep_alive_until"),
            "message": f"Keep-alive extended by {request.additional_minutes} minutes",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("admin_vllm_extend_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extend keep-alive: {str(e)}")


# ============================================================================
# Cost Tracking Endpoints
# ============================================================================

@router.get("/costs")
async def get_costs(_user = Depends(require_admin)):
    """
    Get cost breakdown by backend.

    Returns cumulative costs for Anthropic and vLLM backends.

    **Permissions:** Admin only

    **Example Response:**
    ```json
    {
      "anthropic": 2.45,
      "vllm": 0.80,
      "total": 3.25,
      "budget_limit": 15.0,
      "remaining": 11.75,
      "budget_used_percent": 21.67
    }
    ```
    """
    breakdown = cost_tracker.get_breakdown()
    return breakdown


@router.get("/costs/budget")
async def get_budget_status(_user = Depends(require_admin)):
    """
    Get budget status with alerts.

    Returns detailed budget information including alert level.

    **Permissions:** Admin only
    """
    status = cost_tracker.get_budget_status()
    return status


@router.post("/costs/budget")
async def update_budget(
    request: BudgetUpdateRequest,
    _user = Depends(require_admin),
):
    """
    Update budget limit.

    Sets a new budget limit for LLM usage.

    **Permissions:** Admin only
    """
    try:
        cost_tracker.set_budget_limit(request.budget_limit)

        logger.info(
            "admin_budget_updated",
            new_limit=request.budget_limit,
        )

        return {
            "success": True,
            "budget_limit": request.budget_limit,
            "message": f"Budget limit updated to ${request.budget_limit:.2f}",
        }

    except Exception as e:
        logger.error("admin_budget_update_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update budget")


@router.get("/costs/recent")
async def get_recent_costs(
    limit: int = 10,
    _user = Depends(require_admin),
):
    """
    Get recent cost entries.

    Returns the most recent cost-incurring operations.

    **Permissions:** Admin only

    **Query Parameters:**
    - limit: Number of entries to return (default: 10)
    """
    recent = cost_tracker.get_recent_costs(limit=limit)
    return {"recent_costs": recent}


@router.post("/costs/reset")
async def reset_costs(_user = Depends(require_admin)):
    """
    Reset all cost tracking.

    **WARNING:** This clears all cost history. Use for testing or new billing period.

    **Permissions:** Admin only
    """
    old_total = cost_tracker.get_total_cost()
    cost_tracker.reset()

    logger.warning(
        "admin_costs_reset",
        previous_total=old_total,
    )

    return {
        "success": True,
        "message": "All costs reset",
        "previous_total": old_total,
    }


# ============================================================================
# Metrics Endpoints
# ============================================================================

@router.get("/metrics")
async def get_metrics(_user = Depends(require_admin)):
    """
    Get LLM usage metrics.

    Returns comprehensive metrics including token usage, latency, and error rates.

    **Permissions:** Admin only
    """
    stats = llm_metrics.get_all_stats()
    return stats


@router.get("/metrics/backend/{backend}")
async def get_backend_metrics(
    backend: str,
    _user = Depends(require_admin),
):
    """
    Get metrics for a specific backend.

    **Permissions:** Admin only

    **Path Parameters:**
    - backend: Backend name (anthropic or vllm)
    """
    stats = llm_metrics.get_backend_stats(backend)
    return {"backend": backend, "metrics": stats}


@router.get("/metrics/model/{model}")
async def get_model_metrics(
    model: str,
    _user = Depends(require_admin),
):
    """
    Get metrics for a specific model.

    **Permissions:** Admin only

    **Path Parameters:**
    - model: Model name (e.g., claude-3-haiku-20240307)
    """
    stats = llm_metrics.get_model_stats(model)
    return {"model": model, "metrics": stats}


@router.get("/metrics/recent")
async def get_recent_metrics(
    limit: int = 10,
    _user = Depends(require_admin),
):
    """
    Get recent LLM calls.

    Returns the most recent LLM API calls with details.

    **Permissions:** Admin only

    **Query Parameters:**
    - limit: Number of calls to return (default: 10)
    """
    recent = llm_metrics.get_recent_calls(limit=limit)
    return {"recent_calls": recent}


@router.post("/metrics/reset")
async def reset_metrics(_user = Depends(require_admin)):
    """
    Reset all metrics.

    **WARNING:** This clears all metrics history. Use for testing only.

    **Permissions:** Admin only
    """
    llm_metrics.reset_metrics()

    logger.warning("admin_metrics_reset")

    return {
        "success": True,
        "message": "All metrics reset",
    }


# ============================================================================
# System Status Endpoint
# ============================================================================

@router.get("/status")
async def get_system_status(_user = Depends(require_admin)):
    """
    Get comprehensive system status.

    Returns unified view of backend status, costs, and metrics.

    **Permissions:** Admin only
    """
    backend_info = backend_manager.get_backend_info()
    costs = cost_tracker.get_breakdown()
    budget_status = cost_tracker.get_budget_status()
    metrics_overview = llm_metrics.get_all_stats()["overview"]

    return {
        "backend": backend_info,
        "costs": costs,
        "budget": budget_status,
        "metrics": metrics_overview,
    }
