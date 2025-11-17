"""
Debate Workflow Pattern - Agents discuss and reach consensus.

This pattern enables multiple agents to engage in structured debate, exchange
arguments, challenge each other's reasoning, and converge on a final decision.
Useful for complex decisions requiring multiple perspectives and critical analysis.

Example use cases:
- Complex technical decisions: Multiple engineers debate solution approaches
- Pricing decisions: Finance, sales, CS agents debate optimal pricing
- Policy decisions: Legal, compliance, security agents debate policy changes
- Product roadmap: PM, engineering, design agents debate feature prioritization
- Customer escalations: Multiple specialists debate resolution approach
- Risk assessment: Multiple risk experts debate risk mitigation strategies

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


class DebateFormat(str, Enum):
    """Format for the debate."""
    ROUND_ROBIN = "round_robin"  # Each agent speaks in turn
    FREE_FORM = "free_form"  # Agents can respond to each other freely
    STRUCTURED = "structured"  # Opening ??? Rebuttals ??? Closing
    SOCRATIC = "socratic"  # Question-driven dialogue


class ConsensusMethod(str, Enum):
    """Method for reaching consensus."""
    UNANIMOUS = "unanimous"  # All agents must agree
    MAJORITY = "majority"  # Majority vote wins
    WEIGHTED_VOTE = "weighted_vote"  # Weighted by agent expertise
    MODERATOR = "moderator"  # Moderator makes final decision
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Consensus when confidence threshold met


@dataclass
class DebateParticipant:
    """
    A participant in the debate.

    Attributes:
        agent_name: Name of the agent
        role: Role in debate (advocate, critic, moderator, neutral)
        expertise_weight: Weight for voting (0.0-1.0)
        speaking_order: Order in structured debates (optional)
        max_turns: Maximum turns this agent can take
    """
    agent_name: str
    role: Literal["advocate", "critic", "moderator", "neutral"] = "neutral"
    expertise_weight: float = 1.0
    speaking_order: Optional[int] = None
    max_turns: int = 3


@dataclass
class DebateRound:
    """
    A single round of debate.

    Attributes:
        round_number: Round number
        speaker: Agent who spoke
        statement: What was said
        confidence: Confidence in the statement
        timestamp: When the statement was made
        response_to: Which agent this responds to (optional)
    """
    round_number: int
    speaker: str
    statement: str
    confidence: float
    timestamp: datetime
    response_to: Optional[str] = None


@dataclass
class DebateResult:
    """
    Result of debate workflow.

    Attributes:
        success: Whether consensus was reached
        final_decision: The agreed-upon decision
        confidence: Confidence in the final decision
        rounds: All debate rounds
        participants: Agents who participated
        consensus_method: How consensus was reached
        execution_time: Total debate time in seconds
        votes: Final vote tally (if applicable)
        error: Error message if debate failed
    """
    success: bool
    final_decision: Optional[str]
    confidence: float
    rounds: List[DebateRound]
    participants: List[str]
    consensus_method: ConsensusMethod
    execution_time: float
    votes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DebateWorkflow:
    """
    Debate workflow pattern for multi-agent deliberation.

    This pattern facilitates structured debate between multiple agents, allowing
    them to exchange arguments, challenge assumptions, and converge on a decision.
    Particularly useful for complex, high-stakes decisions.

    Example:
        workflow = DebateWorkflow(
            name="pricing_decision",
            participants=[
                DebateParticipant("finance_analyst", role="advocate", expertise_weight=1.2),
                DebateParticipant("sales_director", role="neutral", expertise_weight=1.0),
                DebateParticipant("cs_manager", role="critic", expertise_weight=0.9),
            ],
            format=DebateFormat.STRUCTURED,
            consensus_method=ConsensusMethod.WEIGHTED_VOTE,
            max_rounds=5
        )

        result = await workflow.execute(initial_state, executor)
    """

    def __init__(
        self,
        name: str,
        participants: List[DebateParticipant],
        format: DebateFormat = DebateFormat.ROUND_ROBIN,
        consensus_method: ConsensusMethod = ConsensusMethod.MAJORITY,
        max_rounds: int = 5,
        confidence_threshold: float = 0.8,
        overall_timeout: Optional[int] = None,
        moderator_agent: Optional[str] = None
    ):
        """
        Initialize debate workflow.

        Args:
            name: Workflow name
            participants: Agents participating in debate
            format: Debate format
            consensus_method: How to reach consensus
            max_rounds: Maximum debate rounds
            confidence_threshold: Confidence needed for consensus
            overall_timeout: Maximum time for entire debate (seconds)
            moderator_agent: Optional moderator agent name
        """
        self.name = name
        self.participants = participants
        self.format = format
        self.consensus_method = consensus_method
        self.max_rounds = max_rounds
        self.confidence_threshold = confidence_threshold
        self.overall_timeout = overall_timeout
        self.moderator_agent = moderator_agent
        self.logger = logger.bind(workflow=name, pattern="debate")

        # Validate configuration
        self._validate_workflow()

    def _validate_workflow(self):
        """Validate workflow configuration."""
        if len(self.participants) < 2:
            raise ValueError("Debate requires at least 2 participants")

        if len(self.participants) > 10:
            self.logger.warning(
                "many_participants",
                count=len(self.participants),
                message="Large number of participants may make consensus difficult"
            )

        if self.max_rounds < 1:
            raise ValueError("Debate must allow at least 1 round")

        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")

        # Validate expertise weights
        for participant in self.participants:
            if not 0.0 <= participant.expertise_weight <= 2.0:
                raise ValueError(f"Expertise weight must be between 0.0 and 2.0: {participant.agent_name}")

    async def execute(
        self,
        initial_state: AgentState,
        agent_executor: Callable[[str, AgentState], Any]
    ) -> DebateResult:
        """
        Execute the debate workflow.

        Args:
            initial_state: Initial state with debate topic/question
            agent_executor: Function to execute an agent

        Returns:
            DebateResult with final decision and debate transcript
        """
        start_time = datetime.now(UTC)
        rounds: List[DebateRound] = []
        current_state = initial_state.copy()

        self.logger.info(
            "debate_started",
            participants=len(self.participants),
            format=self.format.value,
            max_rounds=self.max_rounds
        )

        try:
            # Execute debate based on format
            if self.format == DebateFormat.ROUND_ROBIN:
                rounds = await self._round_robin_debate(current_state, agent_executor)
            elif self.format == DebateFormat.STRUCTURED:
                rounds = await self._structured_debate(current_state, agent_executor)
            elif self.format == DebateFormat.FREE_FORM:
                rounds = await self._free_form_debate(current_state, agent_executor)
            elif self.format == DebateFormat.SOCRATIC:
                rounds = await self._socratic_debate(current_state, agent_executor)
            else:
                raise ValueError(f"Unknown debate format: {self.format}")

            # Reach consensus
            decision, confidence, votes = await self._reach_consensus(
                rounds,
                current_state,
                agent_executor
            )

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            self.logger.info(
                "debate_completed",
                rounds=len(rounds),
                decision_confidence=confidence,
                execution_time=execution_time
            )

            return DebateResult(
                success=True,
                final_decision=decision,
                confidence=confidence,
                rounds=rounds,
                participants=[p.agent_name for p in self.participants],
                consensus_method=self.consensus_method,
                execution_time=execution_time,
                votes=votes
            )

        except asyncio.TimeoutError:
            error = f"Debate exceeded timeout of {self.overall_timeout}s"
            self.logger.error("debate_timeout", error=error)

            return DebateResult(
                success=False,
                final_decision=None,
                confidence=0.0,
                rounds=rounds,
                participants=[p.agent_name for p in self.participants],
                consensus_method=self.consensus_method,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=error
            )

        except Exception as e:
            self.logger.error("debate_error", error=str(e), exc_info=True)

            return DebateResult(
                success=False,
                final_decision=None,
                confidence=0.0,
                rounds=rounds,
                participants=[p.agent_name for p in self.participants],
                consensus_method=self.consensus_method,
                execution_time=(datetime.now(UTC) - start_time).total_seconds(),
                error=f"Debate error: {str(e)}"
            )

    async def _round_robin_debate(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[DebateRound]:
        """Execute round-robin debate where each agent speaks in turn."""
        rounds: List[DebateRound] = []
        debate_history = []

        for round_num in range(1, self.max_rounds + 1):
            self.logger.debug("debate_round_started", round=round_num)

            for participant in self.participants:
                # Skip if participant exceeded max turns
                participant_turns = sum(
                    1 for r in rounds if r.speaker == participant.agent_name
                )
                if participant_turns >= participant.max_turns:
                    continue

                # Build context with debate history
                debate_state = state.copy()
                debate_state["debate_history"] = debate_history
                debate_state["debate_round"] = round_num
                debate_state["participant_role"] = participant.role

                # Execute agent
                try:
                    result = await asyncio.wait_for(
                        agent_executor(participant.agent_name, debate_state),
                        timeout=30
                    )

                    statement = result.get("agent_response", "")
                    confidence = result.get("response_confidence", 0.5)

                    debate_round = DebateRound(
                        round_number=round_num,
                        speaker=participant.agent_name,
                        statement=statement,
                        confidence=confidence,
                        timestamp=datetime.now(UTC)
                    )

                    rounds.append(debate_round)
                    debate_history.append({
                        "speaker": participant.agent_name,
                        "statement": statement,
                        "confidence": confidence
                    })

                    self.logger.debug(
                        "agent_spoke",
                        agent=participant.agent_name,
                        round=round_num,
                        confidence=confidence
                    )

                except Exception as e:
                    self.logger.warning(
                        "agent_failed_to_speak",
                        agent=participant.agent_name,
                        error=str(e)
                    )

            # Check for early consensus
            if await self._check_early_consensus(rounds):
                self.logger.info("early_consensus_reached", round=round_num)
                break

        return rounds

    async def _structured_debate(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[DebateRound]:
        """Execute structured debate: Opening ??? Rebuttals ??? Closing."""
        rounds: List[DebateRound] = []

        # Phase 1: Opening statements
        self.logger.debug("debate_phase", phase="opening_statements")
        for participant in self.participants:
            debate_state = state.copy()
            debate_state["debate_phase"] = "opening"
            debate_state["participant_role"] = participant.role

            try:
                result = await agent_executor(participant.agent_name, debate_state)
                rounds.append(DebateRound(
                    round_number=1,
                    speaker=participant.agent_name,
                    statement=result.get("agent_response", ""),
                    confidence=result.get("response_confidence", 0.5),
                    timestamp=datetime.now(UTC)
                ))
            except Exception as e:
                self.logger.warning("opening_failed", agent=participant.agent_name, error=str(e))

        # Phase 2: Rebuttals (2-3 rounds)
        for round_num in range(2, min(self.max_rounds, 4)):
            self.logger.debug("debate_phase", phase=f"rebuttals_round_{round_num}")

            for participant in self.participants:
                debate_state = state.copy()
                debate_state["debate_phase"] = "rebuttal"
                debate_state["debate_history"] = [
                    {"speaker": r.speaker, "statement": r.statement}
                    for r in rounds
                ]

                try:
                    result = await agent_executor(participant.agent_name, debate_state)
                    rounds.append(DebateRound(
                        round_number=round_num,
                        speaker=participant.agent_name,
                        statement=result.get("agent_response", ""),
                        confidence=result.get("response_confidence", 0.5),
                        timestamp=datetime.now(UTC)
                    ))
                except Exception as e:
                    self.logger.warning("rebuttal_failed", agent=participant.agent_name, error=str(e))

        # Phase 3: Closing statements
        self.logger.debug("debate_phase", phase="closing_statements")
        for participant in self.participants:
            debate_state = state.copy()
            debate_state["debate_phase"] = "closing"
            debate_state["debate_history"] = [
                {"speaker": r.speaker, "statement": r.statement}
                for r in rounds
            ]

            try:
                result = await agent_executor(participant.agent_name, debate_state)
                rounds.append(DebateRound(
                    round_number=self.max_rounds,
                    speaker=participant.agent_name,
                    statement=result.get("agent_response", ""),
                    confidence=result.get("response_confidence", 0.5),
                    timestamp=datetime.now(UTC)
                ))
            except Exception as e:
                self.logger.warning("closing_failed", agent=participant.agent_name, error=str(e))

        return rounds

    async def _free_form_debate(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[DebateRound]:
        """Execute free-form debate where agents respond to each other."""
        rounds: List[DebateRound] = []
        last_speaker = None

        for round_num in range(1, self.max_rounds + 1):
            # Select next speaker (different from last)
            available_participants = [
                p for p in self.participants
                if p.agent_name != last_speaker and
                sum(1 for r in rounds if r.speaker == p.agent_name) < p.max_turns
            ]

            if not available_participants:
                break

            # Let agent with strongest disagreement speak
            participant = available_participants[0]

            debate_state = state.copy()
            debate_state["debate_history"] = [
                {"speaker": r.speaker, "statement": r.statement}
                for r in rounds
            ]
            debate_state["last_speaker"] = last_speaker

            try:
                result = await agent_executor(participant.agent_name, debate_state)
                rounds.append(DebateRound(
                    round_number=round_num,
                    speaker=participant.agent_name,
                    statement=result.get("agent_response", ""),
                    confidence=result.get("response_confidence", 0.5),
                    timestamp=datetime.now(UTC),
                    response_to=last_speaker
                ))
                last_speaker = participant.agent_name
            except Exception as e:
                self.logger.warning("free_form_failed", agent=participant.agent_name, error=str(e))

        return rounds

    async def _socratic_debate(
        self,
        state: AgentState,
        agent_executor: Callable
    ) -> List[DebateRound]:
        """Execute Socratic debate (question-driven dialogue)."""
        rounds: List[DebateRound] = []

        # Questioner and responder alternate
        questioner = self.participants[0]
        responders = self.participants[1:]

        for round_num in range(1, self.max_rounds + 1):
            # Questioner asks
            debate_state = state.copy()
            debate_state["debate_mode"] = "question"
            debate_state["debate_history"] = [
                {"speaker": r.speaker, "statement": r.statement}
                for r in rounds
            ]

            try:
                result = await agent_executor(questioner.agent_name, debate_state)
                rounds.append(DebateRound(
                    round_number=round_num,
                    speaker=questioner.agent_name,
                    statement=result.get("agent_response", ""),
                    confidence=result.get("response_confidence", 0.5),
                    timestamp=datetime.now(UTC)
                ))
            except Exception as e:
                self.logger.warning("question_failed", error=str(e))

            # Responders answer
            for responder in responders:
                debate_state["debate_mode"] = "answer"
                debate_state["debate_history"] = [
                    {"speaker": r.speaker, "statement": r.statement}
                    for r in rounds
                ]

                try:
                    result = await agent_executor(responder.agent_name, debate_state)
                    rounds.append(DebateRound(
                        round_number=round_num,
                        speaker=responder.agent_name,
                        statement=result.get("agent_response", ""),
                        confidence=result.get("response_confidence", 0.5),
                        timestamp=datetime.now(UTC),
                        response_to=questioner.agent_name
                    ))
                except Exception as e:
                    self.logger.warning("answer_failed", agent=responder.agent_name, error=str(e))

        return rounds

    async def _check_early_consensus(self, rounds: List[DebateRound]) -> bool:
        """Check if early consensus has been reached."""
        if len(rounds) < len(self.participants):
            return False

        # Get last statement from each participant
        last_statements = {}
        for participant in self.participants:
            participant_rounds = [r for r in rounds if r.speaker == participant.agent_name]
            if participant_rounds:
                last_statements[participant.agent_name] = participant_rounds[-1]

        # Check if all have high confidence and similar statements
        if len(last_statements) == len(self.participants):
            avg_confidence = sum(r.confidence for r in last_statements.values()) / len(last_statements)
            return avg_confidence >= self.confidence_threshold

        return False

    async def _reach_consensus(
        self,
        rounds: List[DebateRound],
        state: AgentState,
        agent_executor: Callable
    ) -> tuple[Optional[str], float, Optional[Dict]]:
        """Reach consensus based on configured method."""
        if self.consensus_method == ConsensusMethod.MAJORITY:
            return self._majority_vote(rounds)
        elif self.consensus_method == ConsensusMethod.WEIGHTED_VOTE:
            return self._weighted_vote(rounds)
        elif self.consensus_method == ConsensusMethod.UNANIMOUS:
            return self._unanimous_decision(rounds)
        elif self.consensus_method == ConsensusMethod.MODERATOR:
            return await self._moderator_decision(rounds, state, agent_executor)
        elif self.consensus_method == ConsensusMethod.CONFIDENCE_THRESHOLD:
            return self._confidence_consensus(rounds)
        else:
            return None, 0.0, None

    def _majority_vote(self, rounds: List[DebateRound]) -> tuple[str, float, Dict]:
        """Simple majority vote from last round statements."""
        last_round = max(r.round_number for r in rounds)
        final_statements = [r for r in rounds if r.round_number == last_round]

        # Count votes (simplified - in reality would need semantic similarity)
        votes = {}
        for statement in final_statements:
            key = statement.statement[:50]  # Simplified
            votes[key] = votes.get(key, 0) + 1

        if votes:
            winner = max(votes.items(), key=lambda x: x[1])
            confidence = winner[1] / len(final_statements)
            return winner[0], confidence, {"votes": votes}

        return "No consensus reached", 0.0, {"votes": {}}

    def _weighted_vote(self, rounds: List[DebateRound]) -> tuple[str, float, Dict]:
        """Weighted vote based on participant expertise."""
        last_round = max(r.round_number for r in rounds)
        final_statements = [r for r in rounds if r.round_number == last_round]

        # Weight votes by expertise
        weighted_votes = {}
        for statement in final_statements:
            participant = next(
                (p for p in self.participants if p.agent_name == statement.speaker),
                None
            )
            weight = participant.expertise_weight if participant else 1.0
            key = statement.statement[:50]
            weighted_votes[key] = weighted_votes.get(key, 0.0) + weight

        if weighted_votes:
            winner = max(weighted_votes.items(), key=lambda x: x[1])
            total_weight = sum(p.expertise_weight for p in self.participants)
            confidence = min(winner[1] / total_weight, 1.0)
            return winner[0], confidence, {"weighted_votes": weighted_votes}

        return "No consensus reached", 0.0, {"weighted_votes": {}}

    def _unanimous_decision(self, rounds: List[DebateRound]) -> tuple[str, float, Dict]:
        """Check for unanimous agreement."""
        last_round = max(r.round_number for r in rounds)
        final_statements = [r for r in rounds if r.round_number == last_round]

        unique_statements = set(s.statement[:50] for s in final_statements)

        if len(unique_statements) == 1:
            return list(unique_statements)[0], 1.0, {"unanimous": True}

        return "No unanimous consensus", 0.0, {"unanimous": False}

    async def _moderator_decision(
        self,
        rounds: List[DebateRound],
        state: AgentState,
        agent_executor: Callable
    ) -> tuple[Optional[str], float, Dict]:
        """Let moderator make final decision."""
        if not self.moderator_agent:
            return self._majority_vote(rounds)

        moderator_state = state.copy()
        moderator_state["debate_history"] = [
            {"speaker": r.speaker, "statement": r.statement, "confidence": r.confidence}
            for r in rounds
        ]
        moderator_state["role"] = "moderator"

        try:
            result = await agent_executor(self.moderator_agent, moderator_state)
            decision = result.get("agent_response", "")
            confidence = result.get("response_confidence", 0.5)
            return decision, confidence, {"moderator": self.moderator_agent}
        except Exception as e:
            self.logger.error("moderator_failed", error=str(e))
            return None, 0.0, {"error": str(e)}

    def _confidence_consensus(self, rounds: List[DebateRound]) -> tuple[str, float, Dict]:
        """Consensus when average confidence exceeds threshold."""
        last_round = max(r.round_number for r in rounds)
        final_statements = [r for r in rounds if r.round_number == last_round]

        avg_confidence = sum(s.confidence for s in final_statements) / len(final_statements)

        if avg_confidence >= self.confidence_threshold:
            # Return highest confidence statement
            best = max(final_statements, key=lambda x: x.confidence)
            return best.statement, best.confidence, {"average_confidence": avg_confidence}

        return "Confidence threshold not met", avg_confidence, {"threshold": self.confidence_threshold}


# Convenience function for quick debate execution
async def execute_debate(
    workflow_name: str,
    agent_names: List[str],
    initial_state: AgentState,
    agent_executor: Callable,
    **kwargs
) -> DebateResult:
    """
    Quick helper to execute a debate.

    Args:
        workflow_name: Name of the debate
        agent_names: List of agent names to participate
        initial_state: Initial state with debate topic
        agent_executor: Function to execute agents
        **kwargs: Additional workflow configuration

    Returns:
        DebateResult

    Example:
        result = await execute_debate(
            "pricing_decision",
            ["finance_analyst", "sales_director", "cs_manager"],
            initial_state,
            executor,
            format=DebateFormat.STRUCTURED,
            consensus_method=ConsensusMethod.WEIGHTED_VOTE
        )
    """
    participants = [DebateParticipant(agent_name=name) for name in agent_names]
    workflow = DebateWorkflow(name=workflow_name, participants=participants, **kwargs)
    return await workflow.execute(initial_state, agent_executor)
