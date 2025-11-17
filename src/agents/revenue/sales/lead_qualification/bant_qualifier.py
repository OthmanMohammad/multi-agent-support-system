"""
BANT Qualifier Agent - TASK-1012

Deep BANT assessment (Budget, Authority, Need, Timeline).
Converts MQL to SQL through comprehensive qualification.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("bant_qualifier", tier="revenue", category="sales")
class BANTQualifier(BaseAgent):
    """
    BANT Qualifier Agent - Specialist in comprehensive BANT assessment.

    Handles:
    - Budget assessment and estimation
    - Authority identification (decision makers)
    - Need analysis and pain point discovery
    - Timeline determination
    - MQL to SQL conversion
    """

    # BANT scoring thresholds
    BANT_SCORE_SQL = 70  # >= 70 = SQL
    BANT_SCORE_MQL = 40  # 40-69 = MQL

    # Budget signals
    BUDGET_SIGNALS = {
        "high": ["approved", "allocated", "budgeted", "funded"],
        "medium": ["exploring", "looking at", "considering budget"],
        "low": ["no budget", "tight budget", "limited budget"],
        "unknown": []
    }

    # Authority indicators
    DECISION_MAKER_TITLES = [
        "ceo", "cto", "cfo", "coo", "president", "founder",
        "vp", "vice president", "head of", "director"
    ]

    # Urgency indicators
    URGENCY_KEYWORDS = {
        "critical": ["asap", "urgent", "critical", "immediately", "emergency"],
        "high": ["soon", "this month", "this quarter", "quickly"],
        "medium": ["next quarter", "this year", "few months"],
        "low": ["eventually", "someday", "exploring", "researching"]
    }

    def __init__(self):
        config = AgentConfig(
            name="bant_qualifier",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.3,
            max_tokens=800,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process BANT qualification"""
        self.logger.info("bant_qualifier_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        conversation_history = state.get("messages", [])

        # Perform BANT assessment
        bant_assessment = self._assess_bant(
            message,
            customer_metadata,
            conversation_history
        )

        # Calculate overall BANT score
        overall_score = self._calculate_bant_score(bant_assessment)

        # Determine qualification status
        qualification_status = self._determine_status(overall_score)

        # Search KB
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_bant_response(
            message,
            bant_assessment,
            overall_score,
            qualification_status,
            kb_results
        )

        # Determine next steps
        next_steps = self._determine_next_steps(qualification_status, bant_assessment)

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.82
        state["bant_assessment"] = bant_assessment
        state["overall_bant_score"] = overall_score
        state["qualification_status"] = qualification_status
        state["next_steps"] = next_steps
        state["status"] = "resolved"

        self.logger.info(
            "bant_qualifier_completed",
            bant_score=overall_score,
            qualification=qualification_status
        )

        return state

    def _assess_bant(
        self,
        message: str,
        customer_metadata: Dict,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Assess all BANT dimensions"""
        message_lower = message.lower()

        # Combine all conversation text for better analysis
        all_text = message_lower
        for msg in conversation_history:
            if msg.get("content"):
                all_text += " " + msg["content"].lower()

        # Budget assessment
        budget_assessment = self._assess_budget(all_text, customer_metadata)

        # Authority assessment
        authority_assessment = self._assess_authority(all_text, customer_metadata)

        # Need assessment
        need_assessment = self._assess_need(all_text, customer_metadata)

        # Timeline assessment
        timeline_assessment = self._assess_timeline(all_text, customer_metadata)

        return {
            "budget": budget_assessment,
            "authority": authority_assessment,
            "need": need_assessment,
            "timeline": timeline_assessment
        }

    def _assess_budget(self, text: str, metadata: Dict) -> Dict[str, Any]:
        """Assess budget dimension (0-10 score)"""
        score = 5  # Default neutral score
        signals = []
        estimated_range = "Unknown"
        confidence = 0.5

        # Check for budget signals
        for level, keywords in self.BUDGET_SIGNALS.items():
            if any(keyword in text for keyword in keywords):
                if level == "high":
                    score = 9
                    signals.append("Budget approved/allocated")
                    confidence = 0.9
                elif level == "medium":
                    score = 6
                    signals.append("Exploring budget options")
                    confidence = 0.6
                elif level == "low":
                    score = 3
                    signals.append("Budget constraints mentioned")
                    confidence = 0.8

        # Estimate budget based on company size
        company_size = metadata.get("company_size", 0)
        if company_size >= 1000:
            estimated_range = "$50k-$200k/year"
            score = min(score + 1, 10)
        elif company_size >= 200:
            estimated_range = "$25k-$75k/year"
        elif company_size >= 50:
            estimated_range = "$10k-$30k/year"
        else:
            estimated_range = "$5k-$15k/year"

        return {
            "score": score,
            "signals": signals,
            "estimated_budget": estimated_range,
            "confidence": confidence
        }

    def _assess_authority(self, text: str, metadata: Dict) -> Dict[str, Any]:
        """Assess authority dimension (0-10 score)"""
        score = 5
        signals = []
        decision_maker = False
        needs_to_involve = []
        confidence = 0.5

        title = metadata.get("title", "").lower()

        # Check if decision maker based on title
        if any(dm_title in title for dm_title in self.DECISION_MAKER_TITLES):
            score = 9
            decision_maker = True
            signals.append(f"Decision maker title: {metadata.get('title')}")
            confidence = 0.9
        elif "manager" in title:
            score = 7
            signals.append("Manager-level, may need approval")
            needs_to_involve = ["Director", "VP"]
            confidence = 0.7
        else:
            score = 4
            signals.append("Individual contributor, needs approval")
            needs_to_involve = ["Manager", "Director"]
            confidence = 0.6

        # Check for mentions of approval process
        if "need approval" in text or "need to check" in text:
            score = max(score - 2, 1)
            signals.append("Approval required")

        return {
            "score": score,
            "signals": signals,
            "decision_maker": decision_maker,
            "needs_to_involve": needs_to_involve,
            "confidence": confidence
        }

    def _assess_need(self, text: str, metadata: Dict) -> Dict[str, Any]:
        """Assess need dimension (0-10 score)"""
        score = 5
        pain_points = []
        urgency = "medium"
        confidence = 0.5

        # Identify pain points
        pain_keywords = {
            "efficiency": ["slow", "manual", "time-consuming", "inefficient"],
            "cost": ["expensive", "costly", "budget", "save money"],
            "quality": ["errors", "mistakes", "quality", "accuracy"],
            "scale": ["growth", "scaling", "capacity", "overwhelmed"],
            "integration": ["disconnected", "silos", "integration", "consolidate"]
        }

        for pain_type, keywords in pain_keywords.items():
            if any(keyword in text for keyword in keywords):
                pain_points.append(pain_type.capitalize())
                score += 1

        score = min(score, 10)

        # Assess urgency
        for urgency_level, keywords in self.URGENCY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                urgency = urgency_level
                if urgency_level == "critical":
                    score = min(score + 2, 10)
                    confidence = 0.9
                elif urgency_level == "high":
                    score = min(score + 1, 10)
                    confidence = 0.8
                break

        return {
            "score": score,
            "pain_points": pain_points,
            "urgency": urgency,
            "confidence": confidence
        }

    def _assess_timeline(self, text: str, metadata: Dict) -> Dict[str, Any]:
        """Assess timeline dimension (0-10 score)"""
        score = 5
        timeframe = "Unknown"
        signals = []
        confidence = 0.5

        # Timeline keywords
        if any(word in text for word in ["asap", "immediately", "urgent", "this week"]):
            score = 10
            timeframe = "Immediate (< 2 weeks)"
            signals.append("Urgent timeline")
            confidence = 0.9
        elif any(word in text for word in ["this month", "soon", "quickly"]):
            score = 8
            timeframe = "This month"
            signals.append("Short timeline")
            confidence = 0.8
        elif any(word in text for word in ["this quarter", "q1", "q2", "q3", "q4"]):
            score = 7
            timeframe = "This quarter"
            signals.append("Quarterly timeline")
            confidence = 0.7
        elif any(word in text for word in ["next quarter", "few months"]):
            score = 5
            timeframe = "Next quarter"
            confidence = 0.6
        elif any(word in text for word in ["this year", "2024", "2025"]):
            score = 4
            timeframe = "This year"
            confidence = 0.5
        elif any(word in text for word in ["exploring", "researching", "someday"]):
            score = 2
            timeframe = "Exploratory (6+ months)"
            signals.append("Long timeline")
            confidence = 0.8

        return {
            "score": score,
            "timeframe": timeframe,
            "signals": signals,
            "confidence": confidence
        }

    def _calculate_bant_score(self, bant_assessment: Dict) -> int:
        """Calculate overall BANT score (0-100)"""
        # Average of all BANT dimensions (each 0-10) * 10 = 0-100
        budget_score = bant_assessment["budget"]["score"]
        authority_score = bant_assessment["authority"]["score"]
        need_score = bant_assessment["need"]["score"]
        timeline_score = bant_assessment["timeline"]["score"]

        overall = (budget_score + authority_score + need_score + timeline_score) / 4
        return int(overall * 10)

    def _determine_status(self, score: int) -> str:
        """Determine qualification status based on BANT score"""
        if score >= self.BANT_SCORE_SQL:
            return "SQL"
        elif score >= self.BANT_SCORE_MQL:
            return "MQL"
        else:
            return "Unqualified"

    def _determine_next_steps(
        self,
        qualification_status: str,
        bant_assessment: Dict
    ) -> List[str]:
        """Determine recommended next steps"""
        next_steps = []

        if qualification_status == "SQL":
            next_steps.append("Assign to sales representative")
            next_steps.append("Schedule discovery call")
            if bant_assessment["authority"]["decision_maker"]:
                next_steps.append("Fast-track to demo")
        elif qualification_status == "MQL":
            next_steps.append("Continue nurture sequence")
            next_steps.append("Share relevant case studies")
            next_steps.append("Schedule follow-up in 2 weeks")
        else:
            next_steps.append("Add to long-term nurture")
            next_steps.append("Provide self-serve resources")

        return next_steps

    async def _generate_bant_response(
        self,
        message: str,
        bant_assessment: Dict,
        overall_score: int,
        qualification_status: str,
        kb_results: List[Dict]
    ) -> str:
        """Generate BANT qualification response"""

        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a BANT Qualifier using the BANT framework.

Lead BANT Assessment:
- Budget Score: {bant_assessment['budget']['score']}/10 ({bant_assessment['budget']['estimated_budget']})
- Authority Score: {bant_assessment['authority']['score']}/10 (Decision Maker: {bant_assessment['authority']['decision_maker']})
- Need Score: {bant_assessment['need']['score']}/10 (Pain Points: {', '.join(bant_assessment['need']['pain_points'])})
- Timeline Score: {bant_assessment['timeline']['score']}/10 ({bant_assessment['timeline']['timeframe']})
- Overall BANT Score: {overall_score}/100
- Qualification: {qualification_status}

Ask questions to assess dimensions with low scores.
Be consultative and build rapport.
For high-scoring leads, move toward demo/next steps."""

        user_prompt = f"""Customer message: {message}

{kb_context}

Generate appropriate response based on BANT assessment."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
