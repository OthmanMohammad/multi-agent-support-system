"""
Complexity Assessor - Assess query complexity and collaboration needs.

Scores query complexity on 1-10 scale and determines if multi-agent
collaboration is needed to resolve the query effectively.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-106)
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("complexity_assessor", tier="essential", category="routing")
class ComplexityAssessor(BaseAgent):
    """
    Complexity Assessor - Evaluate query complexity and collaboration needs.

    Assesses:
    - Complexity Score: 1-10 (1 = trivial, 10 = highly complex)
    - Multi-Agent Need: true/false (requires collaboration)
    - Estimated Resolution Time: quick/medium/long
    - Skill Requirements: list of required capabilities

    Complexity Factors:
    - Number of issues mentioned (multi-issue = complex)
    - Technical depth (deep technical = complex)
    - Cross-domain nature (billing + technical = complex)
    - Data requirements (needs analysis = complex)
    - Customization needed (custom solution = complex)
    """

    # Complexity levels
    COMPLEXITY_LEVELS = {
        (1, 3): "simple",      # Single issue, straightforward
        (4, 6): "moderate",    # Multiple factors, some investigation
        (7, 8): "complex",     # Cross-domain, deep analysis needed
        (9, 10): "very_complex"  # Multi-agent, extensive work
    }

    def __init__(self, **kwargs):
        """Initialize Complexity Assessor."""
        config = AgentConfig(
            name="complexity_assessor",
            type=AgentType.ANALYZER,
            temperature=0.2,  # Low but allows nuance
            max_tokens=300,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="complexity_assessor"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="complexity_assessor", agent_type="analyzer")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for complexity assessment.

        Returns:
            System prompt with assessment criteria
        """
        return """You are a query complexity assessment system. Evaluate the complexity of customer queries.

**Complexity Scoring (1-10):**

**Level 1-2: Trivial**
- Single, simple question
- Well-documented feature
- Self-service capable
- Examples: "How do I reset password?", "What's the pricing?"

**Level 3-4: Simple**
- Single issue, straightforward
- Common question with known solution
- Minimal investigation needed
- Examples: "How do I export data?", "Can I add more users?"

**Level 5-6: Moderate**
- Multiple factors to consider
- Some investigation required
- May need to check account/data
- Examples: "Why isn't sync working?", "Billing discrepancy"

**Level 7-8: Complex**
- Cross-domain issues (technical + billing)
- Deep investigation needed
- Multiple systems involved
- Custom solution required
- Examples: "Migration from competitor + training", "Performance issues affecting billing"

**Level 9-10: Very Complex**
- Multi-faceted problem
- Requires multiple specialists
- Strategic/architectural decisions
- High business impact
- Examples: "Enterprise deployment with custom SSO and data migration", "Critical bug affecting production"

**Multi-Agent Collaboration Indicators:**
- Cross-domain issues (technical + billing + account)
- Requires multiple skill sets
- Strategic decisions needed
- High-stakes situations (enterprise, churn risk)
- Complex integrations or migrations
- Customization + implementation

**Estimated Resolution Time:**
- quick: < 5 minutes (simple questions, self-service)
- medium: 5-30 minutes (moderate investigation)
- long: > 30 minutes (complex analysis, multi-step)

**Skill Requirements:**
(List capabilities needed to resolve)
- technical_support
- billing_specialist
- customer_success
- sales_specialist
- integration_expert
- security_specialist
- data_analyst

**Assessment Factors:**
1. Number of distinct issues mentioned
2. Technical depth required
3. Cross-domain nature
4. Data/analysis requirements
5. Customization needs
6. Business impact
7. Urgency vs. complexity (urgent simple = escalate, urgent complex = multi-agent)

**Context Considerations:**
- Plan tier: enterprise → higher priority, may need multi-agent
- Health score: low health + complex → definitely multi-agent
- Churn risk: high risk → escalate complexity
- Account value: high MRR → treat as more complex

**Output Format (JSON only, no extra text):**
{{
    "complexity_score": 7,
    "complexity_level": "complex",
    "multi_agent_needed": true,
    "estimated_resolution_time": "long",
    "skill_requirements": ["technical_support", "billing_specialist"],
    "complexity_factors": [
        "Cross-domain issue (technical + billing)",
        "Requires investigation",
        "Enterprise customer"
    ],
    "reasoning": "Technical issue affecting billing, enterprise customer, requires both technical and billing expertise"
}}

Output ONLY valid JSON."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Assess query complexity and collaboration needs.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with complexity assessment fields
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("complexity_assessor_empty_message")
                state.update(self._get_default_assessment())
                return state

            # Build rich context for assessment
            context_str = self._build_assessment_context(state)

            # Get conversation history for context
            conversation_history = self.get_conversation_context(state)

            # Call LLM for complexity assessment
            prompt = f"""Assess the complexity of this query.

Message: {message}

{context_str if context_str else ""}

Provide complexity assessment in JSON format."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt,
                conversation_history=conversation_history
            )

            # Parse response
            assessment = self._parse_response(response)

            # Validate and normalize
            assessment = self._validate_assessment(assessment)

            # Apply context-based adjustments
            assessment = self._adjust_for_context(assessment, state)

            # Update state with complexity fields
            state["complexity_score"] = assessment["complexity_score"]
            state["complexity_level"] = assessment["complexity_level"]
            state["multi_agent_needed"] = assessment["multi_agent_needed"]
            state["estimated_resolution_time"] = assessment["estimated_resolution_time"]
            state["skill_requirements"] = assessment.get("skill_requirements", [])
            state["complexity_factors"] = assessment.get("complexity_factors", [])
            state["complexity_reasoning"] = assessment.get("reasoning", "")

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["complexity_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model
            }

            self.logger.info(
                "complexity_assessed",
                score=assessment["complexity_score"],
                level=assessment["complexity_level"],
                multi_agent=assessment["multi_agent_needed"],
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "complexity_assessment_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Fallback to moderate complexity
            state.update(self._get_default_assessment())
            return state

    def _build_assessment_context(self, state: AgentState) -> str:
        """
        Build rich context for complexity assessment.

        Args:
            state: Current state with routing and sentiment data

        Returns:
            Formatted context string
        """
        parts = []

        # Include routing decisions
        if state.get("intent_domain"):
            parts.append(f"Domain: {state['intent_domain']}")
            parts.append(f"Category: {state.get('intent_category', 'unknown')}")

        # Include sentiment
        if state.get("emotion"):
            parts.append(f"Emotion: {state['emotion']}")
            parts.append(f"Urgency: {state.get('urgency', 'medium')}")

        # Include customer context
        customer_metadata = state.get("customer_metadata", {})
        if customer_metadata.get("plan"):
            parts.append(f"Plan: {customer_metadata['plan']}")

        if customer_metadata.get("health_score"):
            parts.append(f"Health: {customer_metadata['health_score']}/100")

        if customer_metadata.get("churn_risk"):
            risk = int(customer_metadata['churn_risk'] * 100)
            parts.append(f"Churn Risk: {risk}%")

        # Include entities
        if state.get("extracted_entities"):
            entities = state["extracted_entities"]
            parts.append(f"Entities: {json.dumps(entities)}")

        if parts:
            return "Context:\n" + "\n".join(f"- {p}" for p in parts)

        return ""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into complexity assessment.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Dictionary with complexity assessment
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            # Parse JSON
            assessment = json.loads(cleaned_response)

            # Ensure it's a dict
            if not isinstance(assessment, dict):
                self.logger.warning(
                    "complexity_assessor_invalid_type",
                    type=type(assessment).__name__
                )
                return self._get_default_assessment()

            return assessment

        except json.JSONDecodeError as e:
            self.logger.warning(
                "complexity_assessor_invalid_json",
                response_preview=response[:100],
                error=str(e)
            )
            return self._get_default_assessment()

    def _validate_assessment(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize complexity assessment.

        Args:
            assessment: Raw complexity assessment

        Returns:
            Validated assessment
        """
        validated = {}

        # Validate complexity_score (1-10)
        score = assessment.get("complexity_score", 5)
        try:
            score = int(score)
            validated["complexity_score"] = max(1, min(10, score))
        except (ValueError, TypeError):
            validated["complexity_score"] = 5

        # Determine complexity level from score
        score = validated["complexity_score"]
        for (min_score, max_score), level in self.COMPLEXITY_LEVELS.items():
            if min_score <= score <= max_score:
                validated["complexity_level"] = level
                break
        else:
            validated["complexity_level"] = "moderate"

        # Validate multi_agent_needed
        multi_agent = assessment.get("multi_agent_needed", False)
        validated["multi_agent_needed"] = bool(multi_agent)

        # Auto-set multi-agent for very complex queries
        if validated["complexity_score"] >= 8:
            validated["multi_agent_needed"] = True

        # Validate estimated_resolution_time
        resolution_time = str(assessment.get("estimated_resolution_time", "medium")).lower()
        if resolution_time in ["quick", "medium", "long"]:
            validated["estimated_resolution_time"] = resolution_time
        else:
            # Derive from complexity
            if validated["complexity_score"] <= 3:
                validated["estimated_resolution_time"] = "quick"
            elif validated["complexity_score"] <= 6:
                validated["estimated_resolution_time"] = "medium"
            else:
                validated["estimated_resolution_time"] = "long"

        # Pass through other fields
        validated["skill_requirements"] = assessment.get("skill_requirements", [])
        validated["complexity_factors"] = assessment.get("complexity_factors", [])
        validated["reasoning"] = assessment.get("reasoning", "")

        return validated

    def _adjust_for_context(
        self,
        assessment: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Adjust complexity assessment based on context.

        Args:
            assessment: Validated assessment
            state: Current state

        Returns:
            Context-adjusted assessment
        """
        customer_metadata = state.get("customer_metadata", {})

        # Enterprise customers + complex issues → definitely multi-agent
        plan = customer_metadata.get("plan", "free")
        if plan == "enterprise" and assessment["complexity_score"] >= 6:
            assessment["multi_agent_needed"] = True

        # High churn risk + moderate complexity → escalate
        churn_risk = customer_metadata.get("churn_risk", 0.0)
        if churn_risk > 0.7 and assessment["complexity_score"] >= 5:
            assessment["complexity_score"] = min(10, assessment["complexity_score"] + 1)
            assessment["multi_agent_needed"] = True

        # Low health score → may need multi-agent support
        health_score = customer_metadata.get("health_score", 100)
        if health_score < 40 and assessment["complexity_score"] >= 5:
            assessment["multi_agent_needed"] = True

        # Critical urgency → may need multi-agent for faster resolution
        urgency = state.get("urgency", "medium")
        if urgency == "critical" and assessment["complexity_score"] >= 6:
            assessment["multi_agent_needed"] = True

        return assessment

    def _get_default_assessment(self) -> Dict[str, Any]:
        """
        Get default moderate complexity assessment.

        Returns:
            Default assessment values
        """
        return {
            "complexity_score": 5,
            "complexity_level": "moderate",
            "multi_agent_needed": False,
            "estimated_resolution_time": "medium",
            "skill_requirements": [],
            "complexity_factors": ["Default assessment (analysis failed)"],
            "complexity_reasoning": "Default moderate complexity",
            "complexity_metadata": {
                "latency_ms": 0,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model,
                "fallback": True
            }
        }


# Helper function to create instance
def create_complexity_assessor(**kwargs) -> ComplexityAssessor:
    """
    Create ComplexityAssessor instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured ComplexityAssessor instance
    """
    return ComplexityAssessor(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_complexity_assessor():
        """Test Complexity Assessor with sample queries."""
        print("=" * 60)
        print("TESTING COMPLEXITY ASSESSOR")
        print("=" * 60)

        assessor = ComplexityAssessor()

        # Test cases covering different complexity levels
        test_cases = [
            {
                "message": "How do I reset my password?",
                "context": {},
                "expected_level": "simple"
            },
            {
                "message": "The app isn't syncing properly, can you help?",
                "context": {},
                "expected_level": "moderate"
            },
            {
                "message": "We need to migrate from Asana, set up SSO, train our team of 100, and integrate with Salesforce",
                "context": {"plan": "enterprise", "team_size": 100},
                "expected_level": "very_complex"
            },
            {
                "message": "Billing error is blocking our production deployment - urgent!",
                "context": {"plan": "enterprise", "health_score": 30, "churn_risk": 0.8},
                "expected_level": "complex"
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message'][:60]}...")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test.get("context", {})}
            )

            result = await assessor.process(state)

            print(f"\n✓ Complexity Assessment:")
            print(f"  Score: {result['complexity_score']}/10")
            print(f"  Level: {result['complexity_level']}")
            print(f"  Multi-Agent Needed: {result['multi_agent_needed']}")
            print(f"  Est. Resolution: {result['estimated_resolution_time']}")
            print(f"  Skills Required: {result.get('skill_requirements', [])}")
            print(f"  Latency: {result['complexity_metadata']['latency_ms']}ms")

    # Run tests
    asyncio.run(test_complexity_assessor())
