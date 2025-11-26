"""
Workflow package - Agent workflow orchestration and execution

This package contains the Agent Workflow Engine which coordinates
multi-agent AI interactions using LangGraph. It maintains clear
separation of concerns:

- Business Logic     → Domain Services (outside this package)
- AI Coordination    → Workflow Engine (this package)
- Data Persistence   → Infrastructure Services (outside this package)
- Orchestration      → Application Services (outside this package)

The workflow engine is stateless and focuses purely on executing
AI agent workflows and returning structured results.
"""

from src.workflow.engine import AgentWorkflowEngine
from src.workflow.exceptions import (
    AgentExecutionError,
    AgentTimeoutError,
    InvalidStateError,
    RoutingError,
    WorkflowException,
)

__all__ = [
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentWorkflowEngine",
    "InvalidStateError",
    "RoutingError",
    "WorkflowException",
]
