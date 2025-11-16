"""
Automation & Workflow models for Tier 3
Automation Swarm database tables
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from src.database.models.base import BaseModel


class AutomatedTask(BaseModel):
    """
    Automated tasks by TASK-2201 to TASK-2220
    Track all automated task executions
    """

    __tablename__ = "automated_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Task details
    task_type = Column(String(100), nullable=False, index=True)
    task_category = Column(String(100), nullable=True, index=True)
    triggered_by = Column(String(100), nullable=True)
    trigger_context = Column(JSONB, default=dict, nullable=False)

    # Task configuration
    automation_agent = Column(String(100), nullable=True, index=True)
    task_config = Column(JSONB, default=dict, nullable=False)

    # Execution
    status = Column(String(50), default="pending", nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Results
    result = Column(JSONB, default=dict, nullable=False)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # External systems
    external_system = Column(String(100), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)
    external_url = Column(String(500), nullable=True)

    # Impact
    time_saved_seconds = Column(Integer, nullable=True)
    cost_impact = Column(Float, nullable=True)

    # Tracking
    created_by = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<AutomatedTask(type={self.task_type}, status={self.status}, success={self.success})>"


class AutomationWorkflowExecution(BaseModel):
    """
    Workflow executions by TASK-2211
    Track multi-step workflow progress
    """

    __tablename__ = "automation_workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Workflow details
    workflow_name = Column(String(255), nullable=False, index=True)
    workflow_version = Column(String(50), nullable=True)

    # Context
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    triggered_by = Column(String(100), nullable=True)

    # Steps
    total_steps = Column(Integer, nullable=True)
    completed_steps = Column(Integer, nullable=True)
    failed_steps = Column(Integer, nullable=True)
    step_execution_log = Column(JSONB, default=list, nullable=False)

    # Status
    status = Column(String(50), default="pending", nullable=False, index=True)
    current_step = Column(Integer, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Results
    success = Column(Boolean, nullable=True)
    output = Column(JSONB, default=dict, nullable=False)
    error_details = Column(Text, nullable=True)

    # SLA tracking
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    sla_met = Column(Boolean, nullable=True)
    sla_buffer_seconds = Column(Integer, nullable=True)

    __table_args__ = (
        Index('idx_entity', 'entity_type', 'entity_id'),
    )

    def __repr__(self) -> str:
        return f"<AutomationWorkflowExecution(workflow={self.workflow_name}, status={self.status}, steps={self.completed_steps}/{self.total_steps})>"


class SLACompliance(BaseModel):
    """
    SLA compliance tracking by TASK-2213
    Monitor and enforce service level agreements
    """

    __tablename__ = "sla_compliance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # SLA details
    sla_type = Column(String(100), nullable=False, index=True)
    sla_tier = Column(String(50), nullable=True)
    sla_target_minutes = Column(Integer, nullable=True)

    # Entity
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)

    # Compliance
    sla_met = Column(Boolean, nullable=True, index=True)
    sla_buffer_minutes = Column(Integer, nullable=True)
    sla_breach_severity = Column(String(50), nullable=True)

    # Impact
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    customer_plan = Column(String(100), nullable=True)
    escalated = Column(Boolean, default=False, nullable=False)
    compensation_required = Column(Boolean, default=False, nullable=False)
    compensation_amount = Column(Integer, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="sla_compliance")

    __table_args__ = (
        Index('idx_entity_sla', 'entity_type', 'entity_id'),
    )

    def __repr__(self) -> str:
        return f"<SLACompliance(type={self.sla_type}, met={self.sla_met}, buffer={self.sla_buffer_minutes}min)>"