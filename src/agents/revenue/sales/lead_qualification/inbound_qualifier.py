"""
Inbound Qualifier Agent - TASK-1011

Qualifies inbound leads from demo requests, trials, website forms.
Handles initial qualification using BANT framework and scores leads.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("inbound_qualifier", tier="revenue", category="sales")
class InboundQualifier(BaseAgent):
    """
    Inbound Qualifier Agent - Specialist in qualifying inbound leads.

    Handles:
    - Demo requests from website forms
    - Trial signup qualification
    - Initial BANT assessment
    - Lead scoring (0-100)
    - Routing to sales or nurture
    """

    # Class-level constants
    LEAD_SOURCES = {
        "website_form": "Website demo request form",
        "trial_signup": "Product trial signup",
        "pricing_page": "Pricing page inquiry",
        "content_download": "Whitepaper/ebook download",
        "webinar": "Webinar registration/attendance",
        "referral": "Customer referral"
    }

    QUALIFICATION_QUESTIONS = {
        "budget": [
            "What's your budget range for this type of solution?",
            "Have you allocated budget for this initiative?",
            "When does your budget cycle reset?"
        ],
        "authority": [
            "Who else will be involved in the decision?",
            "What's the approval process at your company?",
            "Are you the decision maker for this purchase?"
        ],
        "need": [
            "What's driving your interest in our product?",
            "What tools are you using today?",
            "What would success look like for you?"
        ],
        "timeline": [
            "When are you looking to make a decision?",
            "What's your timeline for implementation?",
            "Is there a specific deadline driving this?"
        ]
    }

    # Scoring thresholds
    SCORE_SALES_READY = 70  # >= 70 = route to sales (SQL)
    SCORE_NURTURE = 40      # 40-69 = nurture (MQL)
    SCORE_DISQUALIFY = 39   # < 40 = disqualify or self-serve

    # Title scoring (Authority signals)
    TITLE_SCORES = {
        "c_level": 20,      # CEO, CTO, CFO, COO
        "vp": 15,           # VP, Vice President
        "director": 12,     # Director
        "manager": 10,      # Manager
        "lead": 8,          # Team Lead
        "specialist": 5,    # Specialist, Analyst
        "other": 3          # Other titles
    }

    # Company size scoring
    COMPANY_SIZE_SCORES = {
        "enterprise": 20,   # 1000+ employees
        "mid_market": 15,   # 200-999 employees
        "smb": 10,          # 50-199 employees
        "small": 5,         # 10-49 employees
        "micro": 2          # 1-9 employees
    }

    def __init__(self):
        config = AgentConfig(
            name="inbound_qualifier",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20241022",
            temperature=0.4,
            max_tokens=600,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process inbound lead qualification.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with qualification results
        """
        self.logger.info("inbound_qualifier_processing_started")

        # Update state (adds to history, increments turn count)
        state = self.update_state(state)

        # Extract context
        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        self.logger.debug(
            "inbound_qualifier_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Extract lead information from message and entities
        lead_info = self._extract_lead_info(message, entities, customer_metadata)

        # Calculate lead score
        lead_score = self._calculate_lead_score(lead_info)

        # Determine qualification status
        qualification_status = self._determine_qualification_status(lead_score)

        # Search knowledge base for relevant resources
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate appropriate response
        response = await self._generate_qualification_response(
            message,
            lead_info,
            lead_score,
            qualification_status,
            kb_results
        )

        # Determine next action
        next_action = self._determine_next_action(qualification_status, lead_score)

        # Update state with results
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["lead_score"] = lead_score
        state["qualification_status"] = qualification_status
        state["next_action"] = next_action
        state["lead_info"] = lead_info
        state["status"] = "resolved"

        self.logger.info(
            "inbound_qualifier_completed",
            lead_score=lead_score,
            qualification_status=qualification_status,
            next_action=next_action
        )

        return state

    def _extract_lead_info(
        self,
        message: str,
        entities: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract lead information from message and metadata"""
        lead_info = {
            "company": customer_metadata.get("company", entities.get("company", "Unknown")),
            "title": customer_metadata.get("title", entities.get("title", "Unknown")),
            "company_size": customer_metadata.get("company_size", entities.get("company_size", 0)),
            "email": customer_metadata.get("email", entities.get("email", "")),
            "lead_source": customer_metadata.get("lead_source", "website_form"),
            "industry": customer_metadata.get("industry", entities.get("industry", "Unknown")),
            "current_tool": None,
            "pain_points": [],
            "timeline": None
        }

        # Extract pain points from message
        message_lower = message.lower()
        pain_point_keywords = {
            "slow": "Slow processes",
            "manual": "Manual work",
            "expensive": "High costs",
            "difficult": "Usability issues",
            "integration": "Integration challenges",
            "scale": "Scaling problems"
        }

        for keyword, pain_point in pain_point_keywords.items():
            if keyword in message_lower:
                lead_info["pain_points"].append(pain_point)

        # Extract timeline signals
        timeline_keywords = {
            "asap": "Immediate",
            "urgent": "Immediate",
            "this week": "This week",
            "this month": "This month",
            "this quarter": "This quarter",
            "next quarter": "Next quarter",
            "exploring": "6+ months"
        }

        for keyword, timeline in timeline_keywords.items():
            if keyword in message_lower:
                lead_info["timeline"] = timeline
                break

        # Extract current tool
        competitor_keywords = ["salesforce", "hubspot", "zendesk", "freshdesk", "intercom"]
        for competitor in competitor_keywords:
            if competitor in message_lower:
                lead_info["current_tool"] = competitor.capitalize()
                break

        return lead_info

    def _calculate_lead_score(self, lead_info: Dict[str, Any]) -> int:
        """
        Calculate lead score (0-100) based on firmographic and behavioral signals.

        Scoring breakdown:
        - Title/Authority: 0-20 points
        - Company Size: 0-20 points
        - Lead Source: 0-20 points
        - Pain Points: 0-20 points
        - Timeline: 0-20 points
        """
        score = 0

        # 1. Title/Authority scoring (0-20 points)
        title = lead_info.get("title", "").lower()
        if any(word in title for word in ["ceo", "cto", "cfo", "coo", "chief"]):
            score += self.TITLE_SCORES["c_level"]
        elif "vp" in title or "vice president" in title:
            score += self.TITLE_SCORES["vp"]
        elif "director" in title:
            score += self.TITLE_SCORES["director"]
        elif "manager" in title:
            score += self.TITLE_SCORES["manager"]
        elif "lead" in title:
            score += self.TITLE_SCORES["lead"]
        elif any(word in title for word in ["specialist", "analyst", "coordinator"]):
            score += self.TITLE_SCORES["specialist"]
        else:
            score += self.TITLE_SCORES["other"]

        # 2. Company Size scoring (0-20 points)
        company_size = lead_info.get("company_size", 0)
        if company_size >= 1000:
            score += self.COMPANY_SIZE_SCORES["enterprise"]
        elif company_size >= 200:
            score += self.COMPANY_SIZE_SCORES["mid_market"]
        elif company_size >= 50:
            score += self.COMPANY_SIZE_SCORES["smb"]
        elif company_size >= 10:
            score += self.COMPANY_SIZE_SCORES["small"]
        else:
            score += self.COMPANY_SIZE_SCORES["micro"]

        # 3. Lead Source scoring (0-20 points)
        lead_source = lead_info.get("lead_source", "")
        source_scores = {
            "referral": 20,
            "trial_signup": 18,
            "website_form": 15,
            "webinar": 15,
            "pricing_page": 12,
            "content_download": 10
        }
        score += source_scores.get(lead_source, 10)

        # 4. Pain Points scoring (0-20 points)
        pain_points = lead_info.get("pain_points", [])
        pain_point_score = min(len(pain_points) * 7, 20)  # 7 points per pain, max 20
        score += pain_point_score

        # 5. Timeline scoring (0-20 points)
        timeline = lead_info.get("timeline", "")
        timeline_scores = {
            "Immediate": 20,
            "This week": 18,
            "This month": 15,
            "This quarter": 12,
            "Next quarter": 8,
            "6+ months": 5
        }
        score += timeline_scores.get(timeline, 10)

        # Ensure score is between 0 and 100
        return min(max(score, 0), 100)

    def _determine_qualification_status(self, lead_score: int) -> str:
        """
        Determine qualification status based on lead score.

        Returns:
            - "SQL" (Sales Qualified Lead): score >= 70
            - "MQL" (Marketing Qualified Lead): score 40-69
            - "Unqualified": score < 40
        """
        if lead_score >= self.SCORE_SALES_READY:
            return "SQL"
        elif lead_score >= self.SCORE_NURTURE:
            return "MQL"
        else:
            return "Unqualified"

    def _determine_next_action(self, qualification_status: str, lead_score: int) -> str:
        """Determine the next action based on qualification status"""
        if qualification_status == "SQL":
            return "assign_to_sales"
        elif qualification_status == "MQL":
            return "nurture_campaign"
        else:
            return "self_serve_or_disqualify"

    async def _generate_qualification_response(
        self,
        message: str,
        lead_info: Dict[str, Any],
        lead_score: int,
        qualification_status: str,
        kb_results: List[Dict]
    ) -> str:
        """Generate personalized qualification response using Claude"""

        # Build knowledge base context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant resources:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"{i}. {article.get('title', 'Resource')}\n"

        # Build system prompt
        system_prompt = f"""You are an Inbound Lead Qualifier for a SaaS product.
Your goal is to qualify leads using the BANT framework (Budget, Authority, Need, Timeline).

Current lead information:
- Company: {lead_info.get('company', 'Unknown')}
- Title: {lead_info.get('title', 'Unknown')}
- Company Size: {lead_info.get('company_size', 'Unknown')}
- Lead Source: {lead_info.get('lead_source', 'Unknown')}
- Lead Score: {lead_score}/100
- Qualification Status: {qualification_status}

Be consultative, not pushy. Build trust and gather information.
Ask 2-3 qualifying questions to understand their needs better.
Be enthusiastic about helping them succeed."""

        # Build user prompt based on qualification status
        if qualification_status == "SQL":
            user_prompt = f"""Customer message: {message}

This is a high-quality lead (score: {lead_score}/100).

Your response should:
1. Acknowledge their interest warmly
2. Ask 2-3 BANT questions to understand their specific needs
3. Mention that we'd love to schedule a personalized demo
4. Be professional and helpful

{kb_context}

Generate a warm, professional response."""

        elif qualification_status == "MQL":
            user_prompt = f"""Customer message: {message}

This is a medium-quality lead (score: {lead_score}/100).

Your response should:
1. Acknowledge their interest
2. Ask qualifying questions about their situation
3. Offer helpful resources (case studies, product tours)
4. Gauge their timeline and urgency

{kb_context}

Generate a helpful response."""

        else:  # Unqualified
            user_prompt = f"""Customer message: {message}

This is a lower-quality lead (score: {lead_score}/100).

Your response should:
1. Thank them for their interest
2. Ask about their use case to better understand fit
3. Suggest self-serve options (free trial, resources)
4. Keep door open for future engagement

{kb_context}

Generate a friendly, helpful response."""

        # Call Claude
        response = await self.call_llm(system_prompt, user_prompt)

        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing InboundQualifier Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: High-quality lead (enterprise, demo request)
        state1 = create_initial_state(
            "I'd like to request a demo of your product for our team",
            context={
                "customer_metadata": {
                    "company": "Acme Corp",
                    "title": "CTO",
                    "company_size": 500,
                    "email": "cto@acmecorp.com",
                    "lead_source": "website_form"
                }
            }
        )

        agent = InboundQualifier()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Enterprise CTO Demo Request")
        print(f"Lead Score: {result1['lead_score']}/100")
        print(f"Qualification Status: {result1['qualification_status']}")
        print(f"Next Action: {result1['next_action']}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Medium-quality lead (small company, trial signup)
        state2 = create_initial_state(
            "Just signed up for trial, want to learn more",
            context={
                "customer_metadata": {
                    "company": "Startup Inc",
                    "title": "Product Manager",
                    "company_size": 15,
                    "lead_source": "trial_signup"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Small Company Trial Signup")
        print(f"Lead Score: {result2['lead_score']}/100")
        print(f"Qualification Status: {result2['qualification_status']}")
        print(f"Next Action: {result2['next_action']}")
        print(f"Response:\n{result2['agent_response']}\n")

    asyncio.run(test())
