"""
Disqualification Agent - TASK-1015

Identifies bad-fit leads and disqualifies them politely.
Routes to nurture, self-serve, or reject based on reason.
"""

from datetime import datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("disqualification_agent", tier="revenue", category="sales")
class DisqualificationAgent(BaseAgent):
    """
    Disqualification Agent - Specialist in identifying and handling bad-fit leads.

    Handles:
    - Identify bad-fit leads (wrong ICP, no budget, etc.)
    - Disqualify politely with helpful alternatives
    - Route to nurture/self-serve/reject
    - Schedule re-qualification if temporary
    - Track disqualification reasons
    """

    # Disqualification reasons
    DISQUALIFICATION_REASONS = {
        "no_budget": {
            "category": "budget",
            "severity": "medium",
            "route_to": "self_serve",
            "re_qualify_in_days": 90,
        },
        "wrong_company_size": {
            "category": "firmographic",
            "severity": "high",
            "route_to": "reject",
            "re_qualify_in_days": None,
        },
        "no_authority": {
            "category": "authority",
            "severity": "low",
            "route_to": "nurture",
            "re_qualify_in_days": 60,
        },
        "wrong_industry": {
            "category": "firmographic",
            "severity": "medium",
            "route_to": "reject",
            "re_qualify_in_days": None,
        },
        "no_timeline": {
            "category": "timeline",
            "severity": "low",
            "route_to": "nurture",
            "re_qualify_in_days": 180,
        },
        "competitor": {
            "category": "other",
            "severity": "high",
            "route_to": "reject",
            "re_qualify_in_days": None,
        },
        "student_personal": {
            "category": "other",
            "severity": "high",
            "route_to": "reject",
            "re_qualify_in_days": None,
        },
        "spam": {
            "category": "other",
            "severity": "critical",
            "route_to": "reject",
            "re_qualify_in_days": None,
        },
    }

    # Minimum viable thresholds
    MIN_COMPANY_SIZE = 10  # Minimum 10 employees
    MIN_LEAD_SCORE = 20  # Below 20 is auto-disqualify

    # Competitor domains
    COMPETITOR_DOMAINS = ["salesforce.com", "hubspot.com", "zoho.com", "pipedrive.com"]

    # Self-serve resources
    SELF_SERVE_RESOURCES = {
        "no_budget": [
            "Free tier/trial",
            "Product documentation",
            "Video tutorials",
            "Community forum",
        ],
        "no_timeline": ["Product roadmap", "Case studies", "ROI calculator", "Monthly newsletter"],
        "wrong_company_size": ["Starter plan information", "Small business resources"],
    }

    def __init__(self):
        config = AgentConfig(
            name="disqualification_agent",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=600,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE,
            ],
            kb_category="sales",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process lead disqualification.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with disqualification results
        """
        self.logger.info("disqualification_agent_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        lead_score = state.get("lead_score", 0)
        qualification_status = state.get("qualification_status", "Unknown")

        # Detect disqualification reasons
        disqualification_analysis = self._analyze_disqualification_signals(
            message, customer_metadata, lead_score, qualification_status
        )

        if not disqualification_analysis["should_disqualify"]:
            # Lead is qualified, no disqualification needed
            state["disqualification_status"] = "qualified"
            state["disqualification_reason"] = None
            state["next_action"] = "continue_qualification"
            state["status"] = "resolved"
            state["response_confidence"] = 0.88

            self.logger.info("lead_qualified_not_disqualifying")
            return state

        # Lead should be disqualified
        primary_reason = disqualification_analysis["primary_reason"]
        all_reasons = disqualification_analysis["all_reasons"]
        route_to = self._determine_routing(primary_reason)
        re_qualify_date = self._calculate_requalification_date(primary_reason)

        # Search KB for relevant resources
        kb_results = await self.search_knowledge_base(
            f"alternatives for {primary_reason}", category="sales", limit=3
        )
        state["kb_results"] = kb_results

        # Generate polite disqualification response
        response = await self._generate_disqualification_response(
            message, primary_reason, route_to, customer_metadata, kb_results, state
        )

        # Get recommended resources
        recommended_resources = self._get_recommended_resources(primary_reason)

        # Update state
        state["agent_response"] = response
        state["disqualification_status"] = "disqualified"
        state["disqualification_reason"] = primary_reason
        state["all_disqualification_reasons"] = all_reasons
        state["route_to"] = route_to
        state["re_qualification_date"] = re_qualify_date
        state["recommended_resources"] = recommended_resources
        state["next_action"] = f"route_to_{route_to}"
        state["status"] = "resolved"
        state["response_confidence"] = 0.89
        state["disqualified_at"] = datetime.now().isoformat()

        self.logger.info(
            "disqualification_completed",
            reason=primary_reason,
            route=route_to,
            re_qualify_date=re_qualify_date,
        )

        return state

    def _analyze_disqualification_signals(
        self, message: str, customer_metadata: dict, lead_score: int, qualification_status: str
    ) -> dict[str, Any]:
        """
        Analyze signals to determine if lead should be disqualified.

        Returns:
            Dict with should_disqualify, primary_reason, all_reasons
        """
        reasons = []
        message_lower = message.lower()

        # 1. Check lead score
        if lead_score < self.MIN_LEAD_SCORE:
            reasons.append("low_score")

        # 2. Check company size
        company_size = customer_metadata.get("company_size", 0)
        if company_size > 0 and company_size < self.MIN_COMPANY_SIZE:
            reasons.append("wrong_company_size")

        # 3. Check for budget signals
        if any(
            phrase in message_lower for phrase in ["no budget", "can't afford", "too expensive"]
        ):
            reasons.append("no_budget")

        # 4. Check for competitor
        email = customer_metadata.get("email", "").lower()
        if any(domain in email for domain in self.COMPETITOR_DOMAINS):
            reasons.append("competitor")

        # 5. Check for student/personal
        if any(
            word in message_lower for word in ["student", "school", "university", "personal use"]
        ):
            reasons.append("student_personal")

        # 6. Check for spam signals
        spam_signals = ["test", "testing", "asdfasdf", "qwerty", "fake"]
        if any(signal in message_lower for signal in spam_signals):
            company = customer_metadata.get("company", "").lower()
            if any(signal in company for signal in spam_signals):
                reasons.append("spam")

        # 7. Check for no authority
        title = customer_metadata.get("title", "").lower()
        if any(word in title for word in ["intern", "student", "assistant"]):
            reasons.append("no_authority")

        # 8. Check for no timeline
        if qualification_status == "Unqualified" and lead_score < 40:
            if any(
                phrase in message_lower for phrase in ["just looking", "exploring", "researching"]
            ):
                reasons.append("no_timeline")

        # Determine if should disqualify
        should_disqualify = len(reasons) > 0

        # Determine primary reason (most severe)
        primary_reason = None
        if reasons:
            # Prioritize by severity
            severity_order = ["critical", "high", "medium", "low"]
            for severity in severity_order:
                for reason in reasons:
                    if reason in self.DISQUALIFICATION_REASONS:
                        if self.DISQUALIFICATION_REASONS[reason]["severity"] == severity:
                            primary_reason = reason
                            break
                if primary_reason:
                    break

            # Fallback to first reason if no match
            if not primary_reason:
                primary_reason = reasons[0]

        return {
            "should_disqualify": should_disqualify,
            "primary_reason": primary_reason,
            "all_reasons": reasons,
        }

    def _determine_routing(self, reason: str) -> str:
        """
        Determine where to route the disqualified lead.

        Returns:
            "nurture", "self_serve", or "reject"
        """
        if reason in self.DISQUALIFICATION_REASONS:
            return self.DISQUALIFICATION_REASONS[reason]["route_to"]
        return "reject"

    def _calculate_requalification_date(self, reason: str) -> str | None:
        """
        Calculate when to re-qualify this lead (if applicable).

        Returns:
            ISO datetime string or None
        """
        if reason not in self.DISQUALIFICATION_REASONS:
            return None

        days = self.DISQUALIFICATION_REASONS[reason]["re_qualify_in_days"]
        if days is None:
            return None

        re_qualify_date = datetime.now() + timedelta(days=days)
        return re_qualify_date.isoformat()

    def _get_recommended_resources(self, reason: str) -> list[str]:
        """Get recommended self-serve resources based on disqualification reason"""
        return self.SELF_SERVE_RESOURCES.get(
            reason, ["Product documentation", "Knowledge base", "Community forum"]
        )

    async def _generate_disqualification_response(
        self,
        message: str,
        reason: str,
        route_to: str,
        customer_metadata: dict,
        kb_results: list[dict],
        state: AgentState,
    ) -> str:
        """Generate polite disqualification response using Claude"""

        # Get conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        resources = self._get_recommended_resources(reason)
        resources_text = "\n".join([f"- {r}" for r in resources])

        system_prompt = f"""You are a Lead Qualification Specialist handling a disqualification.

Disqualification Reason: {reason}
Routing Decision: {route_to}

Your response must:
1. Be empathetic and professional
2. Thank them for their interest
3. Explain why it may not be the right fit (gently)
4. Offer helpful alternatives (self-serve resources, future contact, etc.)
5. Keep the door open for future engagement if appropriate
6. Be brief (3-4 sentences)

Never be negative or dismissive. Focus on being helpful."""

        user_prompt = f"""Customer message: {message}

Recommended resources to mention:
{resources_text}

{kb_context}

Generate a polite, helpful disqualification response."""

        response = await self.call_llm(
            system_prompt, user_prompt, conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing DisqualificationAgent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Student with no budget
        state1 = create_initial_state(
            "I'm a student looking to use this for my personal project, no budget",
            context={
                "customer_metadata": {
                    "company": "University",
                    "title": "Student",
                    "company_size": 0,
                    "email": "student@university.edu",
                },
                "lead_score": 15,
                "qualification_status": "Unqualified",
            },
        )

        agent = DisqualificationAgent()
        result1 = await agent.process(state1)

        print("\nTest 1 - Student Lead")
        print(f"Disqualification Status: {result1['disqualification_status']}")
        if result1["disqualification_status"] == "disqualified":
            print(f"Reason: {result1['disqualification_reason']}")
            print(f"Route To: {result1['route_to']}")
            print(f"Re-qualification Date: {result1['re_qualification_date']}")
            print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: No timeline, low urgency
        state2 = create_initial_state(
            "Just exploring options, no rush, maybe in a year or so",
            context={
                "customer_metadata": {
                    "company": "Small Corp",
                    "title": "Manager",
                    "company_size": 25,
                },
                "lead_score": 35,
                "qualification_status": "Unqualified",
            },
        )

        result2 = await agent.process(state2)

        print("\nTest 2 - No Timeline Lead")
        print(f"Disqualification Status: {result2['disqualification_status']}")
        if result2["disqualification_status"] == "disqualified":
            print(f"Reason: {result2['disqualification_reason']}")
            print(f"Route To: {result2['route_to']}")
            print(f"Re-qualification Date: {result2['re_qualification_date']}")
            print(f"Response:\n{result2['agent_response']}\n")

    asyncio.run(test())
