"""
Workflow automation repository - Business logic for workflow data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta

from src.database.base import BaseRepository
from src.database.models import Workflow, WorkflowExecution, ScheduledTask


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for workflow operations"""

    def __init__(self, session):
        super().__init__(Workflow, session)

    async def get_active_workflows(
        self,
        limit: int = 100
    ) -> List[Workflow]:
        """Get all active workflows"""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.is_active == True)
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_trigger_type(
        self,
        trigger_type: str,
        limit: int = 100
    ) -> List[Workflow]:
        """Get workflows by trigger type"""
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.trigger_type == trigger_type)
            .order_by(Workflow.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Optional[Workflow]:
        """Get workflow by name"""
        result = await self.session.execute(
            select(Workflow).where(Workflow.name == name)
        )
        return result.scalar_one_or_none()


class WorkflowExecutionRepository(BaseRepository[WorkflowExecution]):
    """Repository for workflow execution operations"""

    def __init__(self, session):
        super().__init__(WorkflowExecution, session)

    async def get_by_workflow(
        self,
        workflow_id: UUID,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """Get all executions for a workflow"""
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_running_executions(
        self,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """Get currently running executions"""
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.status == 'running')
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_failed_executions(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """Get recent failed executions"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(WorkflowExecution)
            .where(and_(
                WorkflowExecution.status == 'failed',
                WorkflowExecution.started_at >= cutoff
            ))
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_success_rate(
        self,
        workflow_id: UUID,
        days: Optional[int] = None
    ) -> float:
        """Get success rate for a workflow"""
        conditions = [WorkflowExecution.workflow_id == workflow_id]

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            conditions.append(WorkflowExecution.started_at >= cutoff)

        total_result = await self.session.execute(
            select(func.count(WorkflowExecution.id))
            .where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        success_result = await self.session.execute(
            select(func.count(WorkflowExecution.id))
            .where(and_(
                WorkflowExecution.status == 'completed',
                *conditions
            ))
        )
        successes = success_result.scalar() or 0

        return (successes / total * 100) if total > 0 else 0.0

    async def get_average_duration(
        self,
        workflow_id: UUID,
        days: Optional[int] = None
    ) -> float:
        """Get average execution duration in seconds"""
        conditions = [
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.completed_at.isnot(None)
        ]

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            conditions.append(WorkflowExecution.started_at >= cutoff)

        result = await self.session.execute(
            select(
                func.avg(
                    func.extract('epoch', WorkflowExecution.completed_at - WorkflowExecution.started_at)
                )
            )
            .where(and_(*conditions))
        )
        return result.scalar() or 0.0


class ScheduledTaskRepository(BaseRepository[ScheduledTask]):
    """Repository for scheduled task operations"""

    def __init__(self, session):
        super().__init__(ScheduledTask, session)

    async def get_active_tasks(
        self,
        limit: int = 100
    ) -> List[ScheduledTask]:
        """Get all active scheduled tasks"""
        result = await self.session.execute(
            select(ScheduledTask)
            .where(ScheduledTask.is_active == True)
            .order_by(ScheduledTask.next_run_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_task_type(
        self,
        task_type: str,
        limit: int = 100
    ) -> List[ScheduledTask]:
        """Get tasks by type"""
        result = await self.session.execute(
            select(ScheduledTask)
            .where(ScheduledTask.task_type == task_type)
            .order_by(ScheduledTask.next_run_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_due_tasks(
        self,
        limit: int = 100
    ) -> List[ScheduledTask]:
        """Get tasks that are due to run"""
        result = await self.session.execute(
            select(ScheduledTask)
            .where(and_(
                ScheduledTask.is_active == True,
                ScheduledTask.next_run_at <= datetime.utcnow()
            ))
            .order_by(ScheduledTask.next_run_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_overdue_tasks(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[ScheduledTask]:
        """Get tasks that are overdue"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(ScheduledTask)
            .where(and_(
                ScheduledTask.is_active == True,
                ScheduledTask.next_run_at < cutoff
            ))
            .order_by(ScheduledTask.next_run_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_run(
        self,
        task_id: UUID,
        next_run_at: datetime
    ) -> Optional[ScheduledTask]:
        """Update task after execution"""
        return await self.update(
            task_id,
            last_run_at=datetime.utcnow(),
            next_run_at=next_run_at
        )
