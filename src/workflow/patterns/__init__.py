"""
Workflow patterns for multi-agent collaboration.

This module provides production-ready patterns for coordinating multiple agents:

- **Sequential**: Execute agents one after another in a defined order
- **Parallel**: Execute multiple agents simultaneously and aggregate results
- **Debate**: Agents engage in structured debate to reach consensus
- **Verification**: One agent verifies and improves another's output
- **Expert Panel**: Multiple expert agents contribute specialized knowledge

Each pattern is fully implemented with:
- Comprehensive error handling and timeouts
- Configurable execution strategies
- Detailed logging and monitoring
- Production-grade quality assurance

Example usage:
    from src.workflow.patterns import execute_sequential, SequentialStep

    workflow = SequentialWorkflow(
        name="customer_onboarding",
        steps=[
            SequentialStep("data_collector", required=True),
            SequentialStep("account_setup", required=True),
            SequentialStep("welcome_tour", required=False)
        ]
    )

    result = await workflow.execute(initial_state, agent_executor)

Part of: EPIC-006 Advanced Workflow Patterns
"""

# Sequential Pattern
# Debate Pattern
from src.workflow.patterns.debate import (
    ConsensusMethod,
    DebateFormat,
    DebateParticipant,
    DebateResult,
    DebateRound,
    DebateWorkflow,
    execute_debate,
)

# Expert Panel Pattern
from src.workflow.patterns.expert_panel import (
    Expert,
    ExpertContribution,
    ExpertPanelResult,
    ExpertPanelWorkflow,
    ExpertRole,
    SynthesisStrategy,
    execute_expert_panel,
)

# Parallel Pattern
from src.workflow.patterns.parallel import (
    AggregationStrategy,
    CompletionStrategy,
    ParallelAgent,
    ParallelResult,
    ParallelWorkflow,
    execute_parallel,
)
from src.workflow.patterns.sequential import (
    SequentialResult,
    SequentialStep,
    SequentialWorkflow,
    execute_sequential,
)

# Verification Pattern
from src.workflow.patterns.verification import (
    MultiVerifierWorkflow,
    VerificationAction,
    VerificationCheck,
    VerificationFinding,
    VerificationLevel,
    VerificationResult,
    VerificationWorkflow,
    execute_verification,
)

__all__ = [
    "AggregationStrategy",
    "CompletionStrategy",
    "ConsensusMethod",
    "DebateFormat",
    "DebateParticipant",
    "DebateResult",
    "DebateRound",
    # Debate
    "DebateWorkflow",
    "Expert",
    "ExpertContribution",
    "ExpertPanelResult",
    # Expert Panel
    "ExpertPanelWorkflow",
    "ExpertRole",
    "MultiVerifierWorkflow",
    "ParallelAgent",
    "ParallelResult",
    # Parallel
    "ParallelWorkflow",
    "SequentialResult",
    "SequentialStep",
    # Sequential
    "SequentialWorkflow",
    "SynthesisStrategy",
    "VerificationAction",
    "VerificationCheck",
    "VerificationFinding",
    "VerificationLevel",
    "VerificationResult",
    # Verification
    "VerificationWorkflow",
    "execute_debate",
    "execute_expert_panel",
    "execute_parallel",
    "execute_sequential",
    "execute_verification",
]
