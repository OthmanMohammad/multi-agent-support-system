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
from src.workflow.patterns.sequential import (
    SequentialWorkflow,
    SequentialStep,
    SequentialResult,
    execute_sequential
)

# Parallel Pattern
from src.workflow.patterns.parallel import (
    ParallelWorkflow,
    ParallelAgent,
    ParallelResult,
    AggregationStrategy,
    CompletionStrategy,
    execute_parallel
)

# Debate Pattern
from src.workflow.patterns.debate import (
    DebateWorkflow,
    DebateParticipant,
    DebateRound,
    DebateResult,
    DebateFormat,
    ConsensusMethod,
    execute_debate
)

# Verification Pattern
from src.workflow.patterns.verification import (
    VerificationWorkflow,
    MultiVerifierWorkflow,
    VerificationCheck,
    VerificationFinding,
    VerificationResult,
    VerificationLevel,
    VerificationAction,
    execute_verification
)

# Expert Panel Pattern
from src.workflow.patterns.expert_panel import (
    ExpertPanelWorkflow,
    Expert,
    ExpertContribution,
    ExpertPanelResult,
    ExpertRole,
    SynthesisStrategy,
    execute_expert_panel
)


__all__ = [
    # Sequential
    "SequentialWorkflow",
    "SequentialStep",
    "SequentialResult",
    "execute_sequential",

    # Parallel
    "ParallelWorkflow",
    "ParallelAgent",
    "ParallelResult",
    "AggregationStrategy",
    "CompletionStrategy",
    "execute_parallel",

    # Debate
    "DebateWorkflow",
    "DebateParticipant",
    "DebateRound",
    "DebateResult",
    "DebateFormat",
    "ConsensusMethod",
    "execute_debate",

    # Verification
    "VerificationWorkflow",
    "MultiVerifierWorkflow",
    "VerificationCheck",
    "VerificationFinding",
    "VerificationResult",
    "VerificationLevel",
    "VerificationAction",
    "execute_verification",

    # Expert Panel
    "ExpertPanelWorkflow",
    "Expert",
    "ExpertContribution",
    "ExpertPanelResult",
    "ExpertRole",
    "SynthesisStrategy",
    "execute_expert_panel",
]
