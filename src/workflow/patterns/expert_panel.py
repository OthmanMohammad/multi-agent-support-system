"""
Expert Panel Workflow Pattern - Multiple expert agents contribute specialized knowledge.

This pattern assembles a panel of expert agents, each contributing their specialized
knowledge to a problem. A coordinator synthesizes their inputs into a comprehensive
solution. Ideal for complex problems requiring diverse expertise.

Example use cases:
- Medical diagnosis: Multiple medical specialists analyze a case
- Technical architecture: Multiple engineers contribute to system design
- Investment decisions: Finance, risk, market experts collaborate
- Legal review: Multiple legal specialists review complex contracts
- Product launches: PM, engineering, marketing, sales experts plan launch
- Customer escalations: Multiple departments contribute to resolution

Part of: EPIC-006 Advanced Workflow Patterns
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
import structlog

from src.workflow.state import AgentState
from src.workflow.exceptions import WorkflowException

# Alias for backward compatibility
WorkflowExecutionError = WorkflowException

logger = structlog.get_logger(__name__)


class ExpertRole(str, Enum):
    """Role of an expert in the panel."""
    PRIMARY = "primary"  # Primary expert - highest weight
    SPECIALIST = "specialist"  # Specialized expert in subdomain
    ADVISOR = "advisor"  # Advisory role - provides context
    REVIEWER = "reviewer"  # Reviews and critiques solutions


class SynthesisStrategy(str, Enum):
    """Strategy for synthesizing expert contributions."""
    COORDINATOR = "coordinator"  # Coordinator agent synthesizes
    CONSENSUS = "consensus"  # Require consensus among experts
    WEIGHTED_MERGE = "weighted_merge"  # Merge with expert weights
    SEQUENTIAL_BUILD = "sequential_build"  # Each expert builds on previous
    BEST_SOLUTION = "best_solution"  # Select single best contribution


@dataclass
class Expert:
    """
    Configuration for an expert in the panel.

    Attributes:
        agent_name: Name of the expert agent
        role: Role in the expert panel
        expertise_area: Specific area of expertise
        weight: Importance weight (0.0-2.0)
        required: Whether this expert must contribute
        execution_order: Order for sequential strategies (optional)
        metadata: Additional expert metadata
    """
    agent_name: str
    role: ExpertRole = ExpertRole.SPECIALIST
    expertise_area: str = ""
    weight: float = 1.0
    required: bool = True
    execution_order: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertContribution:
    """
    A single expert's contribution.

    Attributes:
        expert_name: Name of the expert
        expertise_area: Their area of expertise
        contribution: Their contribution text
        confidence: Confidence in their contribution
        key_insights: Key insights provided
        recommendations: Specific recommendations
        timestamp: When contribution was made
    """
    expert_name: str
    expertise_area: str
    contribution: str
    confidence: float
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExpertPanelResult:
    """
    Result of expert panel workflow.

    Attributes:
        success: Whether workflow completed successfully
        final_solution: Synthesized final solution
        expert_contributions: All expert contributions
        synthesis_method: How contributions were synthesized
        confidence: Confidence in final solution
        consensus_level: Level of agreement among experts (0.0-1.0)
        primary_expert: Primary expert who led (if any)
        execution_time: Total workflow time in seconds
        error: Error message if workflow failed
    """
    success: bool
    final_solution: Optional[str]
    expert_contributions: List[ExpertContribution]
    synthesis_method: SynthesisStrategy
    confidence: float
    consensus_level: float
    primary_expert: Optional[str]
    execution_time: float
    error: Optional[str] = None


class ExpertPanelWorkflow:
    """
    Expert Panel workflow pattern for collaborative problem-solving.

    This pattern assembles multiple expert agents to tackle complex problems
    requiring diverse expertise. Experts contribute their specialized knowledge,
    which is then synthesized into a comprehensive solution.

    Example:
        workflow = ExpertPanelWorkflow(
            name="technical_architecture_review",
            experts=[
                Expert("backend_architect", role=ExpertRole.PRIMARY, weight=1.5),
                Expert("frontend_architect", role=ExpertRole.SPECIALIST, weight=1.2),
                Expert("security_expert", role=ExpertRole.SPECIALIST, weight=1.3),
                Expert("devops_engineer", role=ExpertRole.ADVISOR, weight=1.0),
                Expert("tech_lead", role=ExpertRole.REVIEWER, weight=1.1),
            ],
            coordinator_agent="senior_architect",
            synthesis_strategy=SynthesisStrategy.COORDINATOR
        )

        result = await workflow.execute(initial_state, executor)
    """

    def __init__(
        self,
        name: str,
        experts: List[Expert],
        coordinator_agent: Optional[str] = None,
        synthesis_strategy: SynthesisStrategy = SynthesisStrategy.COORDINATOR,
        parallel_execution: bool = True,
        consensus_threshold: float = 0.7,
        overall_timeout: Optional[int] = None
    ):
        """
        Initialize expert panel workflow.

        Args:
            name: Workflow name
            experts: List of expert agents
            coordinator_agent: Agent that synthesizes expert input
            synthesis_strategy: How to combine expert contributions
            parallel_execution: Execute experts in parallel vs sequential
            consensus_threshold: Threshold for consensus (0.0-1.0)
            overall_timeout: Maximum time for entire workflow (seconds)
        """
        self.name = name
        self.experts = experts
        self.coordinator_agent = coordinator_agent
        self.synthesis_strategy = synthesis_strategy
        self.parallel_execution = parallel_execution
        self.consensus_threshold = consensus_threshold
        self.overall_timeout = overall_timeout
        self.logger = logger.bind(workflow=name, pattern="expert_panel")

        # Validate configuration
        self._validate_workflow()

    def _validate_workflow(self):
        """Validate workflow configuration."""
        if not self.experts:
            raise ValueError("Expert panel must have at least one expert")

        if len(self.experts) > 15:
            self.logger.warning(
                "many_experts",
                count=len(self.experts),
                message="Large expert panel may be difficult to coordinate"
            )

        if not 0.0 <= self.consensus_threshold <= 1.0:
            raise ValueError("Consensus threshold must be between 0.0 and 1.0")

        # Validate weights
        for expert in self.experts:
            if not 0.0 <= expert.weight <= 2.0:
                raise ValueError(f"Expert weight must be between 0.0 and 2.0: {expert.agent_name}")

        # Require coordinator for COORDINATOR strategy
        if self.synthesis_strategy == SynthesisStrategy.COORDINATOR and not self.coordinator_agent:
            raise ValueError("COORDINATOR synthesis strategy requires coordinator_agent")

    async def execute(
        self,
        initial_state: AgentState,
        agent_executor: Callable[[str, AgentState], Any]
    ) -> ExpertPanelResult:
        """
        Execute the expert panel workflow.

        Args:
            initial_state: Initial state with problem/question
            agent_executor: Function to execute an agent

        Returns:
            ExpertPanelResult with synthesized solution
        """
        start_time = datetime.now(UTC)
        contributions: List[ExpertContribution] = []

        self.logger.info(
            "expert_panel_started",
            experts=len(self.experts),
            parallel=self.parallel_execution,
            synthesis=self.synthesis_strategy.value
        )

        try:
            # Step 1: Gather expert contributions
            if self.parallel_execution:
                contributions = await self._gather_parallel_contributions(
                    initial_state,
                    agent_executor
                )
            else:
                contributions = await self._gather_sequential_contributions(
                    initial_state,
                    agent_executor
                )

            self.logger.info(
                "contributions_gathered",
                count=len(contributions),
                average_confidence=sum(c.confidence for c in contributions) / len(contributions) if contributions else 0
            )

            # Step 2: Synthesize contributions
            final_solution, confidence, consensus_level = await self._synthesize_contributions(
                contributions,
                initial_state,
                agent_executor
            )

            # Step 3: Identify primary expert (if any)
            primary_expert = self._identify_primary_expert()

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            self.logger.info(
                "expert_panel_completed",
                confidence=confidence,
                consensus=consensus_level,
                execution_time=execution_time
            )

            return ExpertPanelResult(
                success=True,
                final_solution=final_solution,
                expert_contributions=contributions,
                synthesis_method=self.synthesis_strategy,
                confidence=confidence,
                consensus_level=consensus_level,
                primary_expert=primary_expert,
                execution_time=execution_time
            )

        except asyncio.TimeoutError:
            error = f"Expert panel exceeded timeout of {self.overall_timeout}s"
            self.logger.error("expert_panel_timeout", error=error)

            return ExpertPanelResult(
                success=False,
                final_solution=None,
                expert_contributions=contributions,
                synthesis_method=self.synthesis_strategy,
                confidence=0.0,
                consensus_level=0.0,
                primary_expert=None,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=error
            )

        except Exception as e:
            self.logger.error("expert_panel_error", error=str(e), exc_info=True)

            return ExpertPanelResult(
                success=False,
                final_solution=None,
                expert_contributions=contributions,
                synthesis_method=self.synthesis_strategy,
                confidence=0.0,
                consensus_level=0.0,
                primary_expert=None,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=f"Expert panel error: {str(e)}"
            )

    async def _gather_parallel_contributions(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[ExpertContribution]:
        """Gather expert contributions in parallel."""
        contributions: List[ExpertContribution] = []

        # Create tasks for all experts
        tasks = {}
        for expert in self.experts:
            expert_state = state.copy()
            expert_state["expert_role"] = expert.role.value
            expert_state["expertise_area"] = expert.expertise_area

            tasks[expert.agent_name] = asyncio.create_task(
                self._get_expert_contribution(expert, expert_state, agent_executor)
            )

        # Wait for all contributions
        timeout_task = None
        if self.overall_timeout:
            timeout_task = asyncio.create_task(asyncio.sleep(self.overall_timeout))
            done, pending = await asyncio.wait(
                [*tasks.values(), timeout_task],
                return_when=asyncio.ALL_COMPLETED
            )

            if timeout_task in done and not all(t.done() for t in tasks.values()):
                # Timeout occurred
                for task in tasks.values():
                    if not task.done():
                        task.cancel()
                raise asyncio.TimeoutError()
        else:
            await asyncio.wait(tasks.values())

        # Collect results
        for expert_name, task in tasks.items():
            if task.done() and not task.cancelled():
                try:
                    contribution = task.result()
                    if contribution:
                        contributions.append(contribution)
                except Exception as e:
                    self.logger.warning(
                        "expert_failed",
                        expert=expert_name,
                        error=str(e)
                    )

        return contributions

    async def _gather_sequential_contributions(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[ExpertContribution]:
        """Gather expert contributions sequentially."""
        contributions: List[ExpertContribution] = []

        # Sort by execution order if specified
        sorted_experts = sorted(
            self.experts,
            key=lambda e: e.execution_order if e.execution_order is not None else float('inf')
        )

        for expert in sorted_experts:
            expert_state = state.copy()
            expert_state["expert_role"] = expert.role.value
            expert_state["expertise_area"] = expert.expertise_area

            # Provide previous contributions as context
            expert_state["previous_contributions"] = [
                {
                    "expert": c.expert_name,
                    "area": c.expertise_area,
                    "contribution": c.contribution
                }
                for c in contributions
            ]

            contribution = await self._get_expert_contribution(
                expert,
                expert_state,
                agent_executor
            )

            if contribution:
                contributions.append(contribution)

        return contributions

    async def _get_expert_contribution(
        self,
        expert: Expert,
        state: AgentState,
        agent_executor: Callable
    ) -> Optional[ExpertContribution]:
        """Get contribution from a single expert."""
        try:
            self.logger.debug(
                "expert_executing",
                expert=expert.agent_name,
                area=expert.expertise_area
            )

            result = await asyncio.wait_for(
                agent_executor(expert.agent_name, state),
                timeout=60
            )

            contribution_text = result.get("agent_response", "")
            confidence = result.get("response_confidence", 0.5)

            # Extract key insights and recommendations
            # In a real implementation, this would parse structured output
            key_insights = []
            recommendations = []

            contribution = ExpertContribution(
                expert_name=expert.agent_name,
                expertise_area=expert.expertise_area,
                contribution=contribution_text,
                confidence=confidence,
                key_insights=key_insights,
                recommendations=recommendations,
                timestamp=datetime.now(UTC)
            )

            self.logger.info(
                "expert_contributed",
                expert=expert.agent_name,
                confidence=confidence,
                length=len(contribution_text)
            )

            return contribution

        except asyncio.TimeoutError:
            self.logger.warning(
                "expert_timeout",
                expert=expert.agent_name
            )
            if expert.required:
                raise
            return None

        except Exception as e:
            self.logger.warning(
                "expert_error",
                expert=expert.agent_name,
                error=str(e)
            )
            if expert.required:
                raise
            return None

    async def _synthesize_contributions(
        self,
        contributions: List[ExpertContribution],
        state: AgentState,
        agent_executor: Callable
    ) -> tuple[str, float, float]:
        """
        Synthesize expert contributions into final solution.

        Returns:
            Tuple of (solution, confidence, consensus_level)
        """
        if self.synthesis_strategy == SynthesisStrategy.COORDINATOR:
            return await self._coordinator_synthesis(contributions, state, agent_executor)

        elif self.synthesis_strategy == SynthesisStrategy.CONSENSUS:
            return self._consensus_synthesis(contributions)

        elif self.synthesis_strategy == SynthesisStrategy.WEIGHTED_MERGE:
            return self._weighted_merge_synthesis(contributions)

        elif self.synthesis_strategy == SynthesisStrategy.SEQUENTIAL_BUILD:
            return self._sequential_build_synthesis(contributions)

        elif self.synthesis_strategy == SynthesisStrategy.BEST_SOLUTION:
            return self._best_solution_synthesis(contributions)

        else:
            # Default to weighted merge
            return self._weighted_merge_synthesis(contributions)

    async def _coordinator_synthesis(
        self,
        contributions: List[ExpertContribution],
        state: AgentState,
        agent_executor: Callable
    ) -> tuple[str, float, float]:
        """Let coordinator agent synthesize contributions."""
        coordinator_state = state.copy()
        coordinator_state["expert_contributions"] = [
            {
                "expert": c.expert_name,
                "area": c.expertise_area,
                "contribution": c.contribution,
                "confidence": c.confidence
            }
            for c in contributions
        ]
        coordinator_state["synthesis_task"] = "synthesize_expert_panel"

        try:
            result = await asyncio.wait_for(
                agent_executor(self.coordinator_agent, coordinator_state),
                timeout=60
            )

            solution = result.get("agent_response", "")
            confidence = result.get("response_confidence", 0.7)
            consensus = self._calculate_consensus(contributions)

            return solution, confidence, consensus

        except Exception as e:
            self.logger.error("coordinator_synthesis_failed", error=str(e))
            # Fallback to weighted merge
            return self._weighted_merge_synthesis(contributions)

    def _consensus_synthesis(
        self,
        contributions: List[ExpertContribution]
    ) -> tuple[str, float, float]:
        """Synthesize based on consensus."""
        # Calculate consensus level
        consensus = self._calculate_consensus(contributions)

        if consensus >= self.consensus_threshold:
            # Strong consensus - merge contributions
            merged = "\n\n".join([
                f"**{c.expert_name} ({c.expertise_area})**:\n{c.contribution}"
                for c in contributions
            ])
            avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
            return merged, avg_confidence, consensus
        else:
            # No consensus - highlight disagreements
            solution = "**Expert panel could not reach consensus.**\n\n"
            solution += "**Divergent perspectives:**\n\n"
            for c in contributions:
                solution += f"- {c.expert_name}: {c.contribution[:200]}...\n"

            return solution, 0.5, consensus

    def _weighted_merge_synthesis(
        self,
        contributions: List[ExpertContribution]
    ) -> tuple[str, float, float]:
        """Merge contributions with expert weights."""
        # Get expert weights
        expert_weights = {e.agent_name: e.weight for e in self.experts}

        # Sort by weight (highest first)
        sorted_contributions = sorted(
            contributions,
            key=lambda c: expert_weights.get(c.expert_name, 1.0),
            reverse=True
        )

        # Merge with weighted emphasis
        merged = "**Expert Panel Analysis:**\n\n"
        total_weight = sum(expert_weights.get(c.expert_name, 1.0) for c in contributions)
        weighted_confidence = 0.0

        for c in sorted_contributions:
            weight = expert_weights.get(c.expert_name, 1.0)
            emphasis = "PRIMARY" if weight > 1.2 else "SPECIALIST" if weight > 0.8 else "ADVISOR"
            merged += f"**{c.expert_name}** ({c.expertise_area}) [{emphasis}]:\n"
            merged += f"{c.contribution}\n\n"
            weighted_confidence += c.confidence * weight

        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.5
        consensus = self._calculate_consensus(contributions)

        return merged, final_confidence, consensus

    def _sequential_build_synthesis(
        self,
        contributions: List[ExpertContribution]
    ) -> tuple[str, float, float]:
        """Each expert builds on previous (for sequential execution)."""
        if not contributions:
            return "No expert contributions received", 0.0, 0.0

        # Last contribution is the most complete (builds on all others)
        final_contribution = contributions[-1]

        solution = f"**Final Synthesized Solution** (by {final_contribution.expert_name}):\n\n"
        solution += final_contribution.contribution

        # Include earlier contributions as context
        if len(contributions) > 1:
            solution += "\n\n**Built upon contributions from:**\n"
            for c in contributions[:-1]:
                solution += f"- {c.expert_name} ({c.expertise_area})\n"

        consensus = self._calculate_consensus(contributions)

        return solution, final_contribution.confidence, consensus

    def _best_solution_synthesis(
        self,
        contributions: List[ExpertContribution]
    ) -> tuple[str, float, float]:
        """Select single best contribution."""
        if not contributions:
            return "No expert contributions received", 0.0, 0.0

        # Get expert weights
        expert_weights = {e.agent_name: e.weight for e in self.experts}

        # Calculate score = confidence * weight
        best_contribution = max(
            contributions,
            key=lambda c: c.confidence * expert_weights.get(c.expert_name, 1.0)
        )

        solution = f"**Best Solution** (by {best_contribution.expert_name}, {best_contribution.expertise_area}):\n\n"
        solution += best_contribution.contribution

        consensus = self._calculate_consensus(contributions)

        return solution, best_contribution.confidence, consensus

    def _calculate_consensus(self, contributions: List[ExpertContribution]) -> float:
        """Calculate consensus level among experts (simplified)."""
        if len(contributions) < 2:
            return 1.0

        # In a real implementation, this would use semantic similarity
        # For now, use average confidence as proxy
        avg_confidence = sum(c.confidence for c in contributions) / len(contributions)
        confidence_variance = sum(
            (c.confidence - avg_confidence) ** 2 for c in contributions
        ) / len(contributions)

        # Low variance = high consensus
        consensus = max(0.0, 1.0 - confidence_variance)

        return consensus

    def _identify_primary_expert(self) -> Optional[str]:
        """Identify the primary expert (if any)."""
        primary_experts = [e for e in self.experts if e.role == ExpertRole.PRIMARY]
        if primary_experts:
            # Return highest weighted primary expert
            return max(primary_experts, key=lambda e: e.weight).agent_name
        return None


# Convenience function for quick expert panel execution
async def execute_expert_panel(
    workflow_name: str,
    expert_names: List[str],
    coordinator: Optional[str],
    initial_state: AgentState,
    agent_executor: Callable,
    **kwargs
) -> ExpertPanelResult:
    """
    Quick helper to execute expert panel workflow.

    Args:
        workflow_name: Name of the workflow
        expert_names: List of expert agent names
        coordinator: Coordinator agent name (optional)
        initial_state: Initial state with problem
        agent_executor: Function to execute agents
        **kwargs: Additional workflow configuration

    Returns:
        ExpertPanelResult

    Example:
        result = await execute_expert_panel(
            "architecture_review",
            ["backend_architect", "frontend_architect", "security_expert"],
            "senior_architect",
            initial_state,
            executor,
            synthesis_strategy=SynthesisStrategy.COORDINATOR
        )
    """
    experts = [Expert(agent_name=name) for name in expert_names]
    workflow = ExpertPanelWorkflow(
        name=workflow_name,
        experts=experts,
        coordinator_agent=coordinator,
        **kwargs
    )
    return await workflow.execute(initial_state, agent_executor)
