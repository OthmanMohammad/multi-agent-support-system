"""
Sequential Workflow Pattern - Execute agents one after another.

This pattern executes agents in a defined sequence, where each agent's output
becomes the input context for the next agent. Useful for step-by-step workflows
like onboarding, escalation chains, or verification flows.

Example use cases:
- Customer onboarding: Data collection ??? Setup ??? Validation ??? Activation
- Escalation: L1 Support ??? L2 Support ??? Manager ??? Engineering
- Sales qualification: Lead capture ??? BANT qualification ??? Demo scheduling
- Technical troubleshooting: Diagnostics ??? Fix attempt ??? Verification ??? Documentation

Part of: EPIC-006 Advanced Workflow Patterns
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from src.workflow.state import AgentState
from src.workflow.exceptions import (
    WorkflowExecutionError,
    AgentExecutionError,
    WorkflowTimeoutError
)

logger = structlog.get_logger(__name__)


@dataclass
class SequentialStep:
    """
    A single step in a sequential workflow.

    Attributes:
        agent_name: Name of the agent to execute
        required: Whether this step is required (workflow fails if agent fails)
        timeout: Maximum execution time for this step in seconds
        retry_on_failure: Whether to retry this step on failure
        max_retries: Maximum number of retry attempts
        condition: Optional function to determine if step should execute
    """
    agent_name: str
    required: bool = True
    timeout: int = 30
    retry_on_failure: bool = True
    max_retries: int = 2
    condition: Optional[Callable[[AgentState], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SequentialResult:
    """
    Result of sequential workflow execution.

    Attributes:
        success: Whether the workflow completed successfully
        steps_executed: List of agent names that were executed
        steps_skipped: List of agent names that were skipped
        final_state: Final agent state after all steps
        execution_time: Total execution time in seconds
        step_results: Results from each step
        error: Error message if workflow failed
    """
    success: bool
    steps_executed: List[str]
    steps_skipped: List[str]
    final_state: Optional[AgentState]
    execution_time: float
    step_results: Dict[str, Any]
    error: Optional[str] = None


class SequentialWorkflow:
    """
    Sequential workflow pattern for executing agents in order.

    This pattern ensures that agents execute in a specific sequence, with each
    agent building on the work of previous agents. Supports conditional execution,
    retries, and rollback on failure.

    Example:
        workflow = SequentialWorkflow(
            name="customer_onboarding",
            steps=[
                SequentialStep("data_collector", required=True),
                SequentialStep("account_setup", required=True),
                SequentialStep("email_verification", required=False),
                SequentialStep("welcome_tour", required=False)
            ],
            rollback_on_failure=True
        )

        result = await workflow.execute(initial_state)
    """

    def __init__(
        self,
        name: str,
        steps: List[SequentialStep],
        rollback_on_failure: bool = False,
        overall_timeout: Optional[int] = None,
        continue_on_optional_failure: bool = True
    ):
        """
        Initialize sequential workflow.

        Args:
            name: Workflow name for logging and tracking
            steps: List of steps to execute in order
            rollback_on_failure: Whether to rollback on failure
            overall_timeout: Maximum time for entire workflow (seconds)
            continue_on_optional_failure: Continue if optional step fails
        """
        self.name = name
        self.steps = steps
        self.rollback_on_failure = rollback_on_failure
        self.overall_timeout = overall_timeout
        self.continue_on_optional_failure = continue_on_optional_failure
        self.logger = logger.bind(workflow=name, pattern="sequential")

        # Validate workflow
        self._validate_workflow()

    def _validate_workflow(self):
        """Validate workflow configuration."""
        if not self.steps:
            raise ValueError("Sequential workflow must have at least one step")

        if len(self.steps) > 20:
            self.logger.warning(
                "long_workflow",
                step_count=len(self.steps),
                message="Workflow has many steps, consider breaking into smaller workflows"
            )

    async def execute(
        self,
        initial_state: AgentState,
        agent_executor: Callable[[str, AgentState], Any]
    ) -> SequentialResult:
        """
        Execute the sequential workflow.

        Args:
            initial_state: Initial agent state
            agent_executor: Function to execute an agent (agent_name, state) -> result

        Returns:
            SequentialResult with execution details
        """
        start_time = datetime.utcnow()
        executed_steps: List[str] = []
        skipped_steps: List[str] = []
        step_results: Dict[str, Any] = {}
        current_state = initial_state.copy()

        self.logger.info(
            "workflow_started",
            step_count=len(self.steps),
            timeout=self.overall_timeout
        )

        try:
            # Execute each step in sequence
            for idx, step in enumerate(self.steps):
                step_num = idx + 1

                # Check overall timeout
                if self.overall_timeout:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed > self.overall_timeout:
                        raise WorkflowTimeoutError(
                            f"Workflow exceeded timeout of {self.overall_timeout}s"
                        )

                # Check if step should execute
                if step.condition and not step.condition(current_state):
                    self.logger.info(
                        "step_skipped",
                        step=step.agent_name,
                        step_num=step_num,
                        reason="condition_not_met"
                    )
                    skipped_steps.append(step.agent_name)
                    continue

                # Execute step with retries
                step_result = await self._execute_step(
                    step=step,
                    state=current_state,
                    agent_executor=agent_executor,
                    step_num=step_num
                )

                # Handle step result
                if step_result["success"]:
                    executed_steps.append(step.agent_name)
                    step_results[step.agent_name] = step_result
                    current_state = step_result["state"]

                    self.logger.info(
                        "step_completed",
                        step=step.agent_name,
                        step_num=step_num,
                        execution_time=step_result["execution_time"]
                    )
                else:
                    # Step failed
                    if step.required:
                        # Required step failed - workflow fails
                        error_msg = f"Required step '{step.agent_name}' failed: {step_result['error']}"
                        self.logger.error(
                            "workflow_failed",
                            step=step.agent_name,
                            step_num=step_num,
                            error=step_result["error"]
                        )

                        if self.rollback_on_failure:
                            await self._rollback(executed_steps)

                        return SequentialResult(
                            success=False,
                            steps_executed=executed_steps,
                            steps_skipped=skipped_steps,
                            final_state=current_state,
                            execution_time=(datetime.utcnow() - start_time).total_seconds(),
                            step_results=step_results,
                            error=error_msg
                        )
                    else:
                        # Optional step failed
                        if self.continue_on_optional_failure:
                            self.logger.warning(
                                "optional_step_failed",
                                step=step.agent_name,
                                step_num=step_num,
                                error=step_result["error"]
                            )
                            skipped_steps.append(step.agent_name)
                            step_results[step.agent_name] = step_result
                        else:
                            # Don't continue on optional failure
                            return SequentialResult(
                                success=False,
                                steps_executed=executed_steps,
                                steps_skipped=skipped_steps,
                                final_state=current_state,
                                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                                step_results=step_results,
                                error=f"Optional step failed: {step_result['error']}"
                            )

            # All steps completed
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                "workflow_completed",
                steps_executed=len(executed_steps),
                steps_skipped=len(skipped_steps),
                execution_time=execution_time
            )

            return SequentialResult(
                success=True,
                steps_executed=executed_steps,
                steps_skipped=skipped_steps,
                final_state=current_state,
                execution_time=execution_time,
                step_results=step_results
            )

        except WorkflowTimeoutError as e:
            self.logger.error("workflow_timeout", error=str(e))
            return SequentialResult(
                success=False,
                steps_executed=executed_steps,
                steps_skipped=skipped_steps,
                final_state=current_state,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                step_results=step_results,
                error=str(e)
            )
        except Exception as e:
            self.logger.error("workflow_error", error=str(e), exc_info=True)
            return SequentialResult(
                success=False,
                steps_executed=executed_steps,
                steps_skipped=skipped_steps,
                final_state=current_state,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                step_results=step_results,
                error=f"Workflow error: {str(e)}"
            )

    async def _execute_step(
        self,
        step: SequentialStep,
        state: AgentState,
        agent_executor: Callable,
        step_num: int
    ) -> Dict[str, Any]:
        """
        Execute a single step with retries.

        Args:
            step: Step configuration
            state: Current agent state
            agent_executor: Function to execute agent
            step_num: Step number for logging

        Returns:
            Dict with execution result
        """
        attempts = 0
        last_error = None

        while attempts <= step.max_retries if step.retry_on_failure else attempts < 1:
            attempts += 1

            try:
                step_start = datetime.utcnow()

                self.logger.debug(
                    "step_executing",
                    step=step.agent_name,
                    step_num=step_num,
                    attempt=attempts
                )

                # Execute with timeout
                result = await asyncio.wait_for(
                    agent_executor(step.agent_name, state),
                    timeout=step.timeout
                )

                execution_time = (datetime.utcnow() - step_start).total_seconds()

                return {
                    "success": True,
                    "state": result,
                    "execution_time": execution_time,
                    "attempts": attempts
                }

            except asyncio.TimeoutError:
                last_error = f"Step timed out after {step.timeout}s"
                self.logger.warning(
                    "step_timeout",
                    step=step.agent_name,
                    attempt=attempts,
                    timeout=step.timeout
                )
            except Exception as e:
                last_error = str(e)
                self.logger.warning(
                    "step_failed",
                    step=step.agent_name,
                    attempt=attempts,
                    error=str(e)
                )

            # Wait before retry
            if attempts <= step.max_retries and step.retry_on_failure:
                await asyncio.sleep(min(2 ** attempts, 10))  # Exponential backoff

        # All retries exhausted
        return {
            "success": False,
            "error": last_error,
            "attempts": attempts,
            "execution_time": 0
        }

    async def _rollback(self, executed_steps: List[str]):
        """
        Rollback executed steps (if supported by agents).

        Args:
            executed_steps: List of agent names that were executed
        """
        self.logger.info("rollback_started", steps=executed_steps)

        # Reverse order rollback
        for agent_name in reversed(executed_steps):
            try:
                # Call agent's rollback method if it exists
                # This is a placeholder - agents would need to implement rollback
                self.logger.debug("step_rolled_back", step=agent_name)
            except Exception as e:
                self.logger.error(
                    "rollback_failed",
                    step=agent_name,
                    error=str(e)
                )

        self.logger.info("rollback_completed")


# Convenience function for quick sequential execution
async def execute_sequential(
    workflow_name: str,
    agent_names: List[str],
    initial_state: AgentState,
    agent_executor: Callable,
    **kwargs
) -> SequentialResult:
    """
    Quick helper to execute agents sequentially.

    Args:
        workflow_name: Name of the workflow
        agent_names: List of agent names to execute in order
        initial_state: Initial state
        agent_executor: Function to execute agents
        **kwargs: Additional workflow configuration

    Returns:
        SequentialResult

    Example:
        result = await execute_sequential(
            "billing_escalation",
            ["billing_specialist", "billing_manager", "finance_team"],
            initial_state,
            executor
        )
    """
    steps = [SequentialStep(agent_name=name) for name in agent_names]
    workflow = SequentialWorkflow(name=workflow_name, steps=steps, **kwargs)
    return await workflow.execute(initial_state, agent_executor)
