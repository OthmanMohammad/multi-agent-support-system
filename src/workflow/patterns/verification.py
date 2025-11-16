"""
Verification Workflow Pattern - One agent verifies another's output.

This pattern implements a verify-and-improve cycle where one or more agents
review, validate, and potentially correct the output of other agents. Essential
for quality assurance, compliance checking, and error detection.

Example use cases:
- Response quality assurance: QA agent verifies support agent responses
- Code review: Senior agent reviews junior agent's code suggestions
- Compliance checking: Compliance agent verifies marketing content
- Fact-checking: Fact-checker verifies research agent's findings
- Security review: Security agent verifies technical solutions
- Policy enforcement: Policy agent verifies agent decisions comply with rules

Part of: EPIC-006 Advanced Workflow Patterns
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from src.workflow.state import AgentState
from src.workflow.exceptions import WorkflowException

# Alias for backward compatibility
WorkflowExecutionError = WorkflowException

logger = structlog.get_logger(__name__)


class VerificationLevel(str, Enum):
    """Level of verification rigor."""
    BASIC = "basic"  # Quick sanity check
    STANDARD = "standard"  # Normal verification
    THOROUGH = "thorough"  # Comprehensive review
    CRITICAL = "critical"  # Maximum scrutiny for critical decisions


class VerificationAction(str, Enum):
    """Action to take based on verification result."""
    APPROVE = "approve"  # Output is good, no changes needed
    APPROVE_WITH_NOTES = "approve_with_notes"  # Good but has suggestions
    REQUEST_REVISION = "request_revision"  # Needs changes
    REJECT = "reject"  # Output is unacceptable
    ESCALATE = "escalate"  # Needs human review


@dataclass
class VerificationCheck:
    """
    A specific verification check to perform.

    Attributes:
        name: Name of the check
        description: What this check validates
        required: Whether this check must pass
        weight: Importance weight (0.0-1.0)
        criteria: Specific criteria to check
    """
    name: str
    description: str
    required: bool = True
    weight: float = 1.0
    criteria: List[str] = field(default_factory=list)


@dataclass
class VerificationFinding:
    """
    A single verification finding.

    Attributes:
        check_name: Which check produced this finding
        severity: Severity level (critical, high, medium, low, info)
        finding: Description of what was found
        recommendation: Suggested fix
        location: Where the issue was found (optional)
    """
    check_name: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    finding: str
    recommendation: str
    location: Optional[str] = None


@dataclass
class VerificationResult:
    """
    Result of verification workflow.

    Attributes:
        success: Whether verification workflow completed
        action: Recommended action
        original_output: Original agent output
        verified_output: Final verified/corrected output
        findings: List of verification findings
        verification_score: Overall quality score (0.0-1.0)
        verifier_confidence: Verifier's confidence (0.0-1.0)
        iterations: Number of verify-revise iterations
        execution_time: Total verification time in seconds
        error: Error message if workflow failed
    """
    success: bool
    action: VerificationAction
    original_output: str
    verified_output: str
    findings: List[VerificationFinding]
    verification_score: float
    verifier_confidence: float
    iterations: int
    execution_time: float
    error: Optional[str] = None


class VerificationWorkflow:
    """
    Verification workflow pattern for quality assurance.

    This pattern implements a verify-and-improve cycle where verifier agents
    check the output of producer agents and provide feedback. Supports multiple
    verification rounds with iterative improvement.

    Example:
        workflow = VerificationWorkflow(
            name="response_qa",
            producer_agent="support_specialist",
            verifier_agent="qa_agent",
            checks=[
                VerificationCheck("accuracy", "Check factual accuracy", required=True),
                VerificationCheck("tone", "Check appropriate tone", required=True),
                VerificationCheck("completeness", "Check all questions answered", required=True),
            ],
            verification_level=VerificationLevel.STANDARD,
            max_iterations=3
        )

        result = await workflow.execute(initial_state, executor)
    """

    def __init__(
        self,
        name: str,
        producer_agent: str,
        verifier_agent: str,
        checks: List[VerificationCheck],
        verification_level: VerificationLevel = VerificationLevel.STANDARD,
        max_iterations: int = 3,
        auto_correct: bool = True,
        quality_threshold: float = 0.8,
        overall_timeout: Optional[int] = None
    ):
        """
        Initialize verification workflow.

        Args:
            name: Workflow name
            producer_agent: Agent that produces initial output
            verifier_agent: Agent that verifies output
            checks: List of verification checks to perform
            verification_level: Rigor level for verification
            max_iterations: Maximum verify-revise iterations
            auto_correct: Whether verifier can auto-correct issues
            quality_threshold: Minimum quality score to approve
            overall_timeout: Maximum time for entire workflow (seconds)
        """
        self.name = name
        self.producer_agent = producer_agent
        self.verifier_agent = verifier_agent
        self.checks = checks
        self.verification_level = verification_level
        self.max_iterations = max_iterations
        self.auto_correct = auto_correct
        self.quality_threshold = quality_threshold
        self.overall_timeout = overall_timeout
        self.logger = logger.bind(workflow=name, pattern="verification")

        # Validate configuration
        self._validate_workflow()

    def _validate_workflow(self):
        """Validate workflow configuration."""
        if not self.checks:
            raise ValueError("Verification workflow must have at least one check")

        if self.max_iterations < 1:
            raise ValueError("Must allow at least 1 iteration")

        if not 0.0 <= self.quality_threshold <= 1.0:
            raise ValueError("Quality threshold must be between 0.0 and 1.0")

        # Validate check weights
        for check in self.checks:
            if not 0.0 <= check.weight <= 1.0:
                raise ValueError(f"Check weight must be between 0.0 and 1.0: {check.name}")

    async def execute(
        self,
        initial_state: AgentState,
        agent_executor: Callable[[str, AgentState], Any]
    ) -> VerificationResult:
        """
        Execute the verification workflow.

        Args:
            initial_state: Initial state with task
            agent_executor: Function to execute an agent

        Returns:
            VerificationResult with verification outcome
        """
        start_time = datetime.utcnow()
        all_findings: List[VerificationFinding] = []
        current_state = initial_state.copy()
        original_output = None

        self.logger.info(
            "verification_started",
            producer=self.producer_agent,
            verifier=self.verifier_agent,
            checks=len(self.checks),
            level=self.verification_level.value
        )

        try:
            # Step 1: Producer creates initial output
            self.logger.debug("producer_executing", agent=self.producer_agent)

            producer_result = await asyncio.wait_for(
                agent_executor(self.producer_agent, current_state),
                timeout=60
            )

            original_output = producer_result.get("agent_response", "")
            current_output = original_output

            self.logger.info(
                "producer_completed",
                output_length=len(original_output)
            )

            # Step 2: Iterative verification and improvement
            iteration = 0
            final_action = VerificationAction.APPROVE

            while iteration < self.max_iterations:
                iteration += 1

                self.logger.debug(
                    "verification_iteration",
                    iteration=iteration,
                    max_iterations=self.max_iterations
                )

                # Verify current output
                verification_state = current_state.copy()
                verification_state["output_to_verify"] = current_output
                verification_state["verification_checks"] = [
                    {
                        "name": check.name,
                        "description": check.description,
                        "required": check.required,
                        "criteria": check.criteria
                    }
                    for check in self.checks
                ]
                verification_state["verification_level"] = self.verification_level.value
                verification_state["iteration"] = iteration

                verifier_result = await asyncio.wait_for(
                    agent_executor(self.verifier_agent, verification_state),
                    timeout=60
                )

                # Parse verification results
                findings, score, confidence, action = self._parse_verification_result(
                    verifier_result
                )

                all_findings.extend(findings)

                self.logger.info(
                    "verification_completed",
                    iteration=iteration,
                    score=score,
                    findings=len(findings),
                    action=action.value
                )

                # Determine next action
                if action == VerificationAction.APPROVE:
                    final_action = VerificationAction.APPROVE
                    break

                elif action == VerificationAction.APPROVE_WITH_NOTES:
                    final_action = VerificationAction.APPROVE_WITH_NOTES
                    break

                elif action == VerificationAction.REJECT:
                    final_action = VerificationAction.REJECT
                    break

                elif action == VerificationAction.ESCALATE:
                    final_action = VerificationAction.ESCALATE
                    break

                elif action == VerificationAction.REQUEST_REVISION:
                    # Check if we can auto-correct
                    if self.auto_correct and iteration < self.max_iterations:
                        # Request producer to revise
                        revision_state = current_state.copy()
                        revision_state["previous_output"] = current_output
                        revision_state["verification_findings"] = [
                            {
                                "check": f.check_name,
                                "severity": f.severity,
                                "finding": f.finding,
                                "recommendation": f.recommendation
                            }
                            for f in findings
                        ]

                        self.logger.debug("requesting_revision", iteration=iteration)

                        revision_result = await asyncio.wait_for(
                            agent_executor(self.producer_agent, revision_state),
                            timeout=60
                        )

                        current_output = revision_result.get("agent_response", current_output)

                        self.logger.info(
                            "revision_completed",
                            iteration=iteration,
                            output_length=len(current_output)
                        )
                    else:
                        # Can't auto-correct or max iterations reached
                        final_action = VerificationAction.REQUEST_REVISION
                        break

            # Calculate final verification score
            final_score = self._calculate_final_score(all_findings)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                "workflow_completed",
                action=final_action.value,
                iterations=iteration,
                score=final_score,
                execution_time=execution_time
            )

            return VerificationResult(
                success=True,
                action=final_action,
                original_output=original_output or "",
                verified_output=current_output,
                findings=all_findings,
                verification_score=final_score,
                verifier_confidence=confidence,
                iterations=iteration,
                execution_time=execution_time
            )

        except asyncio.TimeoutError:
            error = f"Verification exceeded timeout of {self.overall_timeout}s"
            self.logger.error("verification_timeout", error=error)

            return VerificationResult(
                success=False,
                action=VerificationAction.ESCALATE,
                original_output=original_output or "",
                verified_output=original_output or "",
                findings=all_findings,
                verification_score=0.0,
                verifier_confidence=0.0,
                iterations=0,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                error=error
            )

        except Exception as e:
            self.logger.error("verification_error", error=str(e), exc_info=True)

            return VerificationResult(
                success=False,
                action=VerificationAction.ESCALATE,
                original_output=original_output or "",
                verified_output=original_output or "",
                findings=all_findings,
                verification_score=0.0,
                verifier_confidence=0.0,
                iterations=0,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                error=f"Verification error: {str(e)}"
            )

    def _parse_verification_result(
        self,
        verifier_result: AgentState
    ) -> tuple[List[VerificationFinding], float, float, VerificationAction]:
        """
        Parse verification result from verifier agent.

        Returns:
            Tuple of (findings, score, confidence, action)
        """
        findings: List[VerificationFinding] = []

        # Extract findings from verifier response
        # In a real implementation, this would parse structured output
        response = verifier_result.get("agent_response", "")

        # For now, create a simple finding based on response
        if "APPROVE" in response.upper():
            action = VerificationAction.APPROVE
            score = 0.95
        elif "REJECT" in response.upper():
            action = VerificationAction.REJECT
            score = 0.3
            findings.append(VerificationFinding(
                check_name="overall",
                severity="critical",
                finding="Output did not meet quality standards",
                recommendation="Review and revise output"
            ))
        elif "REVISION" in response.upper() or "REVISE" in response.upper():
            action = VerificationAction.REQUEST_REVISION
            score = 0.6
            findings.append(VerificationFinding(
                check_name="overall",
                severity="medium",
                finding="Output needs improvement",
                recommendation="Address verification feedback and revise"
            ))
        else:
            action = VerificationAction.APPROVE_WITH_NOTES
            score = 0.8

        confidence = verifier_result.get("response_confidence", 0.7)

        # Check against quality threshold
        if score < self.quality_threshold and action == VerificationAction.APPROVE:
            action = VerificationAction.REQUEST_REVISION

        return findings, score, confidence, action

    def _calculate_final_score(self, findings: List[VerificationFinding]) -> float:
        """Calculate final quality score based on findings."""
        if not findings:
            return 1.0

        # Severity weights
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
            "info": 0.1
        }

        # Calculate penalty
        total_penalty = sum(
            severity_weights.get(f.severity, 0.5)
            for f in findings
        )

        # Normalize to 0-1 score
        max_possible_penalty = len(self.checks) * 1.0
        score = max(0.0, 1.0 - (total_penalty / max(max_possible_penalty, 1.0)))

        return score


class MultiVerifierWorkflow:
    """
    Multi-verifier workflow with multiple verification agents.

    This pattern uses multiple specialized verifiers to check different aspects
    of the output (e.g., accuracy verifier, tone verifier, compliance verifier).

    Example:
        workflow = MultiVerifierWorkflow(
            name="comprehensive_qa",
            producer_agent="content_writer",
            verifiers=[
                ("fact_checker", [VerificationCheck("facts", "Check accuracy")]),
                ("tone_checker", [VerificationCheck("tone", "Check appropriate tone")]),
                ("compliance_checker", [VerificationCheck("compliance", "Check policy compliance")])
            ]
        )
    """

    def __init__(
        self,
        name: str,
        producer_agent: str,
        verifiers: List[tuple[str, List[VerificationCheck]]],
        require_all_pass: bool = True,
        overall_timeout: Optional[int] = None
    ):
        """
        Initialize multi-verifier workflow.

        Args:
            name: Workflow name
            producer_agent: Agent that produces output
            verifiers: List of (verifier_agent, checks) tuples
            require_all_pass: Whether all verifiers must approve
            overall_timeout: Maximum time for entire workflow
        """
        self.name = name
        self.producer_agent = producer_agent
        self.verifiers = verifiers
        self.require_all_pass = require_all_pass
        self.overall_timeout = overall_timeout
        self.logger = logger.bind(workflow=name, pattern="multi_verification")

    async def execute(
        self,
        initial_state: AgentState,
        agent_executor: Callable[[str, AgentState], Any]
    ) -> VerificationResult:
        """Execute multi-verifier workflow."""
        start_time = datetime.utcnow()

        # Step 1: Producer creates output
        producer_result = await agent_executor(self.producer_agent, initial_state)
        output = producer_result.get("agent_response", "")

        # Step 2: Run all verifiers in parallel
        all_findings: List[VerificationFinding] = []
        verification_results = []

        for verifier_agent, checks in self.verifiers:
            workflow = VerificationWorkflow(
                name=f"{self.name}_{verifier_agent}",
                producer_agent=self.producer_agent,
                verifier_agent=verifier_agent,
                checks=checks,
                max_iterations=1,  # Single pass for multi-verifier
                auto_correct=False
            )

            # Run verification
            state = initial_state.copy()
            state["output_to_verify"] = output

            result = await workflow.execute(state, agent_executor)
            verification_results.append((verifier_agent, result))
            all_findings.extend(result.findings)

        # Step 3: Aggregate results
        if self.require_all_pass:
            # All must approve
            all_approved = all(
                r.action in [VerificationAction.APPROVE, VerificationAction.APPROVE_WITH_NOTES]
                for _, r in verification_results
            )
            final_action = VerificationAction.APPROVE if all_approved else VerificationAction.REQUEST_REVISION
        else:
            # Majority must approve
            approved_count = sum(
                1 for _, r in verification_results
                if r.action in [VerificationAction.APPROVE, VerificationAction.APPROVE_WITH_NOTES]
            )
            final_action = (
                VerificationAction.APPROVE
                if approved_count > len(verification_results) / 2
                else VerificationAction.REQUEST_REVISION
            )

        # Calculate aggregate score
        avg_score = sum(r.verification_score for _, r in verification_results) / len(verification_results)

        return VerificationResult(
            success=True,
            action=final_action,
            original_output=output,
            verified_output=output,
            findings=all_findings,
            verification_score=avg_score,
            verifier_confidence=0.8,
            iterations=1,
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )


# Convenience function for quick verification
async def execute_verification(
    producer_agent: str,
    verifier_agent: str,
    checks: List[str],
    initial_state: AgentState,
    agent_executor: Callable,
    **kwargs
) -> VerificationResult:
    """
    Quick helper to execute verification workflow.

    Args:
        producer_agent: Agent that produces output
        verifier_agent: Agent that verifies output
        checks: List of check names
        initial_state: Initial state
        agent_executor: Function to execute agents
        **kwargs: Additional workflow configuration

    Returns:
        VerificationResult

    Example:
        result = await execute_verification(
            "support_specialist",
            "qa_agent",
            ["accuracy", "tone", "completeness"],
            initial_state,
            executor
        )
    """
    check_objects = [
        VerificationCheck(name=check, description=f"Check {check}")
        for check in checks
    ]

    workflow = VerificationWorkflow(
        name="quick_verification",
        producer_agent=producer_agent,
        verifier_agent=verifier_agent,
        checks=check_objects,
        **kwargs
    )

    return await workflow.execute(initial_state, agent_executor)
