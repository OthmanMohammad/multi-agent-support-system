"""
Parallel Workflow Pattern - Execute multiple agents simultaneously.

This pattern executes multiple agents in parallel, collecting and aggregating
their results. Useful for gathering diverse perspectives, parallel data collection,
or concurrent analysis tasks.

Example use cases:
- Multi-agent research: Multiple specialists research different aspects simultaneously
- Parallel analysis: Sentiment, intent, urgency analysis all at once
- Competitive intelligence: Multiple agents analyze different competitors in parallel
- Content generation: Multiple writers generate different content variations
- Risk assessment: Multiple risk agents evaluate different risk dimensions

Part of: EPIC-006 Advanced Workflow Patterns
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

from src.workflow.exceptions import AgentTimeoutError, WorkflowException
from src.workflow.state import AgentState

# Alias for backward compatibility
WorkflowExecutionError = WorkflowException
WorkflowTimeoutError = AgentTimeoutError

logger = structlog.get_logger(__name__)


class AggregationStrategy(str, Enum):
    """Strategy for aggregating parallel agent results."""

    MERGE = "merge"  # Merge all results into single state
    VOTE = "vote"  # Use majority voting for decisions
    BEST = "best"  # Select best result based on confidence
    CONSENSUS = "consensus"  # Require consensus among agents
    ALL = "all"  # Return all results separately


class CompletionStrategy(str, Enum):
    """Strategy for when to complete parallel execution."""

    ALL = "all"  # Wait for all agents to complete
    ANY = "any"  # Complete when any agent finishes
    MAJORITY = "majority"  # Complete when majority finish
    THRESHOLD = "threshold"  # Complete when threshold met


@dataclass
class ParallelAgent:
    """
    Configuration for an agent in parallel execution.

    Attributes:
        agent_name: Name of the agent to execute
        timeout: Maximum execution time in seconds
        required: Whether this agent must succeed
        weight: Weight for voting/aggregation (0.0-1.0)
        metadata: Additional metadata for this agent
    """

    agent_name: str
    timeout: int = 30
    required: bool = False
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParallelResult:
    """
    Result of parallel workflow execution.

    Attributes:
        success: Whether the workflow completed successfully
        agents_completed: List of agents that completed successfully
        agents_failed: List of agents that failed
        aggregated_state: Aggregated final state
        individual_results: Results from each agent
        execution_time: Total execution time in seconds
        error: Error message if workflow failed
    """

    success: bool
    agents_completed: list[str]
    agents_failed: list[str]
    aggregated_state: AgentState | None
    individual_results: dict[str, Any]
    execution_time: float
    error: str | None = None


class ParallelWorkflow:
    """
    Parallel workflow pattern for executing multiple agents simultaneously.

    This pattern runs agents concurrently to gather diverse insights, perform
    parallel analysis, or collect information from multiple sources at once.
    Results can be aggregated using various strategies.

    Example:
        workflow = ParallelWorkflow(
            name="competitive_analysis",
            agents=[
                ParallelAgent("competitor_tracker", weight=1.0),
                ParallelAgent("pricing_analyzer", weight=0.8),
                ParallelAgent("feature_comparator", weight=0.9),
            ],
            aggregation_strategy=AggregationStrategy.MERGE,
            completion_strategy=CompletionStrategy.ALL
        )

        result = await workflow.execute(initial_state, executor)
    """

    def __init__(
        self,
        name: str,
        agents: list[ParallelAgent],
        aggregation_strategy: AggregationStrategy = AggregationStrategy.MERGE,
        completion_strategy: CompletionStrategy = CompletionStrategy.ALL,
        threshold: float = 0.7,
        overall_timeout: int | None = None,
        fail_fast: bool = False,
    ):
        """
        Initialize parallel workflow.

        Args:
            name: Workflow name for logging and tracking
            agents: List of agents to execute in parallel
            aggregation_strategy: How to combine results
            completion_strategy: When to consider workflow complete
            threshold: Threshold for THRESHOLD completion strategy (0.0-1.0)
            overall_timeout: Maximum time for entire workflow (seconds)
            fail_fast: Stop all agents if any required agent fails
        """
        self.name = name
        self.agents = agents
        self.aggregation_strategy = aggregation_strategy
        self.completion_strategy = completion_strategy
        self.threshold = threshold
        self.overall_timeout = overall_timeout
        self.fail_fast = fail_fast
        self.logger = logger.bind(workflow=name, pattern="parallel")

        # Validate configuration
        self._validate_workflow()

    def _validate_workflow(self):
        """Validate workflow configuration."""
        if not self.agents:
            raise ValueError("Parallel workflow must have at least one agent")

        if len(self.agents) > 50:
            self.logger.warning(
                "many_parallel_agents",
                count=len(self.agents),
                message="Large number of parallel agents may impact performance",
            )

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")

        # Validate weights
        for agent in self.agents:
            if not 0.0 <= agent.weight <= 1.0:
                raise ValueError(f"Agent weight must be between 0.0 and 1.0: {agent.agent_name}")

    async def execute(
        self, initial_state: AgentState, agent_executor: Callable[[str, AgentState], Any]
    ) -> ParallelResult:
        """
        Execute the parallel workflow.

        Args:
            initial_state: Initial agent state
            agent_executor: Function to execute an agent (agent_name, state) -> result

        Returns:
            ParallelResult with execution details
        """
        start_time = datetime.now(UTC)
        individual_results: dict[str, Any] = {}
        completed: list[str] = []
        failed: list[str] = []

        self.logger.info(
            "workflow_started",
            agent_count=len(self.agents),
            strategy=self.aggregation_strategy.value,
            timeout=self.overall_timeout,
        )

        try:
            # Create tasks for all agents
            tasks = {
                agent.agent_name: asyncio.create_task(
                    self._execute_agent(
                        agent=agent, state=initial_state.copy(), agent_executor=agent_executor
                    )
                )
                for agent in self.agents
            }

            # Wait for completion based on strategy
            if self.completion_strategy == CompletionStrategy.ALL:
                # Wait for all agents
                results = await self._wait_for_all(tasks)
            elif self.completion_strategy == CompletionStrategy.ANY:
                # Wait for any agent
                results = await self._wait_for_any(tasks)
            elif self.completion_strategy == CompletionStrategy.MAJORITY:
                # Wait for majority
                results = await self._wait_for_majority(tasks)
            elif self.completion_strategy == CompletionStrategy.THRESHOLD:
                # Wait for threshold
                results = await self._wait_for_threshold(tasks, self.threshold)
            else:
                raise ValueError(f"Unknown completion strategy: {self.completion_strategy}")

            # Process results
            for agent_name, result in results.items():
                if result["success"]:
                    completed.append(agent_name)
                    individual_results[agent_name] = result
                    self.logger.info(
                        "agent_completed", agent=agent_name, execution_time=result["execution_time"]
                    )
                else:
                    failed.append(agent_name)
                    individual_results[agent_name] = result
                    self.logger.warning("agent_failed", agent=agent_name, error=result.get("error"))

                    # Check if this is a required agent
                    agent_config = next(
                        (a for a in self.agents if a.agent_name == agent_name), None
                    )
                    if agent_config and agent_config.required:
                        if self.fail_fast:
                            # Cancel all other tasks
                            for task in tasks.values():
                                if not task.done():
                                    task.cancel()

                            error_msg = (
                                f"Required agent '{agent_name}' failed: {result.get('error')}"
                            )
                            return ParallelResult(
                                success=False,
                                agents_completed=completed,
                                agents_failed=failed,
                                aggregated_state=None,
                                individual_results=individual_results,
                                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                                error=error_msg,
                            )

            # Check if any required agents failed
            required_agents = {a.agent_name for a in self.agents if a.required}
            failed_required = required_agents.intersection(set(failed))

            if failed_required:
                error_msg = f"Required agents failed: {', '.join(failed_required)}"
                return ParallelResult(
                    success=False,
                    agents_completed=completed,
                    agents_failed=failed,
                    aggregated_state=None,
                    individual_results=individual_results,
                    execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                    error=error_msg,
                )

            # Aggregate results
            aggregated_state = self._aggregate_results(individual_results, initial_state)

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            self.logger.info(
                "workflow_completed",
                completed=len(completed),
                failed=len(failed),
                execution_time=execution_time,
            )

            return ParallelResult(
                success=True,
                agents_completed=completed,
                agents_failed=failed,
                aggregated_state=aggregated_state,
                individual_results=individual_results,
                execution_time=execution_time,
            )

        except TimeoutError:
            # Cancel all pending tasks
            for task in tasks.values():
                if not task.done():
                    task.cancel()

            error_msg = f"Workflow exceeded timeout of {self.overall_timeout}s"
            self.logger.error("workflow_timeout", error=error_msg)

            return ParallelResult(
                success=False,
                agents_completed=completed,
                agents_failed=failed,
                aggregated_state=None,
                individual_results=individual_results,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=error_msg,
            )

        except Exception as e:
            self.logger.error("workflow_error", error=str(e), exc_info=True)

            return ParallelResult(
                success=False,
                agents_completed=completed,
                agents_failed=failed,
                aggregated_state=None,
                individual_results=individual_results,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=f"Workflow error: {e!s}",
            )

    async def _execute_agent(
        self, agent: ParallelAgent, state: AgentState, agent_executor: Callable
    ) -> dict[str, Any]:
        """Execute a single agent with timeout."""
        agent_start = datetime.now(UTC)

        try:
            self.logger.debug("agent_executing", agent=agent.agent_name)

            result = await asyncio.wait_for(
                agent_executor(agent.agent_name, state), timeout=agent.timeout
            )

            execution_time = (datetime.now(UTC) - agent_start).total_seconds()

            return {
                "success": True,
                "state": result,
                "execution_time": execution_time,
                "weight": agent.weight,
                "metadata": agent.metadata,
            }

        except TimeoutError:
            error = f"Agent timed out after {agent.timeout}s"
            self.logger.warning("agent_timeout", agent=agent.agent_name, timeout=agent.timeout)
            return {
                "success": False,
                "error": error,
                "execution_time": agent.timeout,
                "weight": agent.weight,
            }

        except Exception as e:
            self.logger.warning("agent_execution_failed", agent=agent.agent_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now(UTC) - agent_start).total_seconds(),
                "weight": agent.weight,
            }

    async def _wait_for_all(self, tasks: dict[str, asyncio.Task]) -> dict[str, Any]:
        """Wait for all agents to complete."""
        timeout_task = None
        if self.overall_timeout:
            timeout_task = asyncio.create_task(asyncio.sleep(self.overall_timeout))
            done, pending = await asyncio.wait(
                [*tasks.values(), timeout_task], return_when=asyncio.FIRST_COMPLETED
            )

            if timeout_task in done:
                raise TimeoutError()
        else:
            done, _pending = await asyncio.wait(tasks.values())

        results = {}
        for agent_name, task in tasks.items():
            if task.done() and not task.cancelled():
                try:
                    results[agent_name] = task.result()
                except Exception as e:
                    results[agent_name] = {"success": False, "error": str(e)}

        return results

    async def _wait_for_any(self, tasks: dict[str, asyncio.Task]) -> dict[str, Any]:
        """Wait for any agent to complete."""
        done, pending = await asyncio.wait(
            tasks.values(), return_when=asyncio.FIRST_COMPLETED, timeout=self.overall_timeout
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()

        results = {}
        for agent_name, task in tasks.items():
            if task in done:
                try:
                    results[agent_name] = task.result()
                except Exception as e:
                    results[agent_name] = {"success": False, "error": str(e)}

        return results

    async def _wait_for_majority(self, tasks: dict[str, asyncio.Task]) -> dict[str, Any]:
        """Wait for majority of agents to complete."""
        majority_count = len(tasks) // 2 + 1
        completed = 0
        results = {}

        _done, pending = await asyncio.wait(tasks.values(), timeout=self.overall_timeout)

        for agent_name, task in tasks.items():
            if task.done() and not task.cancelled():
                try:
                    results[agent_name] = task.result()
                    if results[agent_name].get("success"):
                        completed += 1
                except Exception as e:
                    results[agent_name] = {"success": False, "error": str(e)}

        # Cancel remaining if we have majority
        if completed >= majority_count:
            for task in pending:
                task.cancel()

        return results

    async def _wait_for_threshold(
        self, tasks: dict[str, asyncio.Task], threshold: float
    ) -> dict[str, Any]:
        """Wait until threshold of agents complete."""
        threshold_count = int(len(tasks) * threshold)
        results = {}

        _done, pending = await asyncio.wait(tasks.values(), timeout=self.overall_timeout)

        completed = 0
        for agent_name, task in tasks.items():
            if task.done() and not task.cancelled():
                try:
                    results[agent_name] = task.result()
                    if results[agent_name].get("success"):
                        completed += 1
                except Exception as e:
                    results[agent_name] = {"success": False, "error": str(e)}

        # Cancel remaining if threshold met
        if completed >= threshold_count:
            for task in pending:
                task.cancel()

        return results

    def _aggregate_results(self, results: dict[str, Any], initial_state: AgentState) -> AgentState:
        """Aggregate results based on aggregation strategy."""
        if self.aggregation_strategy == AggregationStrategy.MERGE:
            return self._merge_results(results, initial_state)
        elif self.aggregation_strategy == AggregationStrategy.VOTE:
            return self._vote_results(results, initial_state)
        elif self.aggregation_strategy == AggregationStrategy.BEST:
            return self._select_best_result(results, initial_state)
        elif self.aggregation_strategy == AggregationStrategy.CONSENSUS:
            return self._consensus_results(results, initial_state)
        elif self.aggregation_strategy == AggregationStrategy.ALL:
            # Return all results in state metadata
            state = initial_state.copy()
            state["parallel_results"] = results
            return state
        else:
            return initial_state

    def _merge_results(self, results: dict[str, Any], initial_state: AgentState) -> AgentState:
        """Merge all successful results into a single state."""
        merged_state = initial_state.copy()
        responses = []
        total_confidence = 0.0
        count = 0

        for agent_name, result in results.items():
            if result.get("success"):
                agent_state = result["state"]
                responses.append(f"**{agent_name}**: {agent_state.get('agent_response', '')}")
                total_confidence += agent_state.get("response_confidence", 0.0) * result.get(
                    "weight", 1.0
                )
                count += result.get("weight", 1.0)

        if responses:
            merged_state["agent_response"] = "\n\n".join(responses)
            merged_state["response_confidence"] = total_confidence / count if count > 0 else 0.0

        return merged_state

    def _vote_results(self, results: dict[str, Any], initial_state: AgentState) -> AgentState:
        """Select result based on weighted voting."""
        votes: dict[str, float] = {}

        for agent_name, result in results.items():
            if result.get("success"):
                result["state"].get("agent_response", "")
                weight = result.get("weight", 1.0)
                votes[agent_name] = votes.get(agent_name, 0.0) + weight

        if votes:
            winner = max(votes.items(), key=lambda x: x[1])[0]
            return results[winner]["state"]

        return initial_state

    def _select_best_result(self, results: dict[str, Any], initial_state: AgentState) -> AgentState:
        """Select the best result based on confidence score."""
        best_result = None
        best_score = -1.0

        for _agent_name, result in results.items():
            if result.get("success"):
                state = result["state"]
                confidence = state.get("response_confidence", 0.0)
                weight = result.get("weight", 1.0)
                score = confidence * weight

                if score > best_score:
                    best_score = score
                    best_result = state

        return best_result if best_result else initial_state

    def _consensus_results(self, results: dict[str, Any], initial_state: AgentState) -> AgentState:
        """Require consensus among agents - all must agree."""
        responses = set()

        for _agent_name, result in results.items():
            if result.get("success"):
                response = result["state"].get("agent_response", "")
                responses.add(response.strip())

        # If all agents agree, return that response
        if len(responses) == 1:
            state = initial_state.copy()
            state["agent_response"] = next(iter(responses))
            state["response_confidence"] = 0.95  # High confidence for consensus
            return state

        # No consensus - merge responses
        return self._merge_results(results, initial_state)


# Convenience function for quick parallel execution
async def execute_parallel(
    workflow_name: str,
    agent_names: list[str],
    initial_state: AgentState,
    agent_executor: Callable,
    **kwargs,
) -> ParallelResult:
    """
    Quick helper to execute agents in parallel.

    Args:
        workflow_name: Name of the workflow
        agent_names: List of agent names to execute in parallel
        initial_state: Initial state
        agent_executor: Function to execute agents
        **kwargs: Additional workflow configuration

    Returns:
        ParallelResult

    Example:
        result = await execute_parallel(
            "multi_specialist_analysis",
            ["sentiment_analyzer", "intent_classifier", "urgency_detector"],
            initial_state,
            executor
        )
    """
    agents = [ParallelAgent(agent_name=name) for name in agent_names]
    workflow = ParallelWorkflow(name=workflow_name, agents=agents, **kwargs)
    return await workflow.execute(initial_state, agent_executor)
