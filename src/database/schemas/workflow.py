"""
Workflow automation Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


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
    name: Optional[str] = Field(None, max_length=255)
    trigger_type: Optional[str] = Field(None, pattern="^(time_based|event_based|condition_based|manual)$")
    trigger_config: Optional[dict] = None
    actions: Optional[list] = None
    is_active: Optional[bool] = None
    extra_metadata: Optional[dict] = None


class WorkflowInDB(WorkflowBase):
    """Schema for workflow as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: list = Field(default_factory=list)
    extra_metadata: dict = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Schema for creating a workflow execution"""
    pass


class WorkflowExecutionUpdate(BaseModel):
    """Schema for updating a workflow execution"""
    status: Optional[str] = Field(None, pattern="^(running|completed|failed|canceled)$")
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_log: Optional[list] = None
    extra_metadata: Optional[dict] = None


class WorkflowExecutionInDB(WorkflowExecutionBase):
    """Schema for workflow execution as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    extra_metadata: dict = Field(default_factory=dict)


class ScheduledTaskCreate(ScheduledTaskBase):
    """Schema for creating a scheduled task"""
    pass


class ScheduledTaskUpdate(BaseModel):
    """Schema for updating a scheduled task"""
    task_name: Optional[str] = Field(None, max_length=100)
    task_type: Optional[str] = Field(None, max_length=50)
    schedule: Optional[str] = Field(None, max_length=100)
    parameters: Optional[dict] = None
    is_active: Optional[bool] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class ScheduledTaskInDB(ScheduledTaskBase):
    """Schema for scheduled task as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskResponse(ScheduledTaskInDB):
    """Schema for scheduled task API response"""
    is_overdue: bool
