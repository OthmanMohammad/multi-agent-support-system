"""
Workflow automation models
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from src.database.models.base import BaseModel


class Workflow(BaseModel):
    """Automated workflow definitions"""

    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    trigger_type = Column(String(50), nullable=False)
    trigger_config = Column(JSONB, default=dict, nullable=False)
    actions = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true", index=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    executions = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('time_based', 'event_based', 'condition_based', 'manual')",
            name="check_workflow_trigger_type"
        ),
    )

    @property
    def action_count(self) -> int:
        """Get number of actions in workflow"""
        return len(self.actions) if self.actions else 0

    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, active={self.is_active})>"


class WorkflowExecution(BaseModel):
    """Workflow execution history and logs"""

    __tablename__ = "workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(String(20), nullable=False, server_default="running", index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSONB, default=list, nullable=False)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'canceled')",
            name="check_workflow_execution_status"
        ),
    )

    @property
    def is_running(self) -> bool:
        """Check if execution is still running"""
        return self.status == "running"

    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully"""
        return self.status == "completed"

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds"""
        if not self.completed_at or not self.started_at:
            return 0.0
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class ScheduledTask(BaseModel):
    """Scheduled automation tasks"""

    __tablename__ = "scheduled_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    schedule = Column(String(100), nullable=False)
    parameters = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true", index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        from datetime import datetime
        if not self.next_run_at or not self.is_active:
            return False
        return datetime.utcnow() > self.next_run_at

    def __repr__(self) -> str:
        return f"<ScheduledTask(id={self.id}, name={self.task_name}, active={self.is_active})>"
