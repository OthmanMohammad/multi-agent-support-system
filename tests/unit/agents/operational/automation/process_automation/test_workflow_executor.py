"""
Unit tests for Workflow Executor Agent.

Tests workflow execution, orchestration, and monitoring.
Part of: TASK-2211 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.workflow_executor import WorkflowExecutorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create WorkflowExecutorAgent instance."""
    return WorkflowExecutorAgent()


class TestWorkflowExecutorInitialization:
    """Test Workflow Executor initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "workflow_executor"
        assert agent.config.tier == "operational"


class TestWorkflowExecution:
    """Test workflow execution logic."""

    @pytest.mark.asyncio
    async def test_successful_workflow_execution(self, agent):
        """Test successful workflow execution."""
        state = create_initial_state(
            message="Execute onboarding workflow",
            context={}
        )
        state["entities"] = {
            "workflow_id": "WF-001",
            "workflow_type": "onboarding"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_multi_step_workflow(self, agent):
        """Test multi-step workflow execution."""
        state = create_initial_state(message="Execute multi-step workflow", context={})
        state["entities"] = {
            "workflow_steps": ["validate", "process", "notify"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_workflow_failure(self, agent):
        """Test handling of workflow execution failure."""
        state = create_initial_state(message="Execute workflow", context={})
        state["entities"] = {"workflow_id": "INVALID"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
