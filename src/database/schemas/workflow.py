"""
Workflow automation Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Workflow Schemas
# ============================================================================


class WorkflowBase(BaseModel):
    """Base schema for workflows"""

    name: str = Field(..., max_length=255)
    trigger_type: str = Field(..., pattern="^(time_based|event_based|condition_based|manual)$")
    trigger_config: dict = Field(default_factory=dict)
    actions: list = Field(default_factory=list)
    is_active: bool = True
    extra_metadata: dict = Field(default_factory=dict)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow"""

    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow"""

    name: str | None = Field(None, max_length=255)
    trigger_type: str | None = Field(
        None, pattern="^(time_based|event_based|condition_based|manual)$"
    )
    trigger_config: dict | None = None
    actions: list | None = None
    is_active: bool | None = None
    extra_metadata: dict | None = None


class WorkflowInDB(WorkflowBase):
    """Schema for workflow as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowResponse(WorkflowInDB):
    """Schema for workflow API response"""

    action_count: int


# ============================================================================
# WorkflowExecution Schemas
# ============================================================================


class WorkflowExecutionBase(BaseModel):
    """Base schema for workflow executions"""

    workflow_id: UUID
    status: str = Field("running", pattern="^(running|completed|failed|canceled)$")
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    execution_log: list = Field(default_factory=list)
    extra_metadata: dict = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Schema for creating a workflow execution"""

    pass


class WorkflowExecutionUpdate(BaseModel):
    """Schema for updating a workflow execution"""

    status: str | None = Field(None, pattern="^(running|completed|failed|canceled)$")
    completed_at: datetime | None = None
    error_message: str | None = None
    execution_log: list | None = None
    extra_metadata: dict | None = None


class WorkflowExecutionInDB(WorkflowExecutionBase):
    """Schema for workflow execution as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionResponse(WorkflowExecutionInDB):
    """Schema for workflow execution API response"""

    is_running: bool
    is_successful: bool
    duration_seconds: float


# ============================================================================
# ScheduledTask Schemas
# ============================================================================


class ScheduledTaskBase(BaseModel):
    """Base schema for scheduled tasks"""

    task_name: str = Field(..., max_length=100)
    task_type: str = Field(..., max_length=50)
    schedule: str = Field(..., max_length=100)
    parameters: dict = Field(default_factory=dict)
    is_active: bool = True
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    extra_metadata: dict = Field(default_factory=dict)


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating a scheduled task"""

    pass


class ScheduledTaskUpdate(BaseModel):
    """Schema for updating a scheduled task"""

    task_name: str | None = Field(None, max_length=100)
    task_type: str | None = Field(None, max_length=50)
    schedule: str | None = Field(None, max_length=100)
    parameters: dict | None = None
    is_active: bool | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    extra_metadata: dict | None = None


class ScheduledTaskInDB(ScheduledTaskBase):
    """Schema for scheduled task as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskResponse(ScheduledTaskInDB):
    """Schema for scheduled task API response"""

    is_overdue: bool
