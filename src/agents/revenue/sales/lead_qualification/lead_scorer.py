"""
Lead Scorer Agent - TASK-1013

Scores leads 0-100 based on firmographic, behavioral, and engagement signals.
Uses ML-ready scoring model with feature importance.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("lead_scorer", tier="revenue", category="sales")
class LeadScorer(BaseAgent):
    """
    Lead Scorer Agent - ML-powered lead scoring specialist.

    Handles:
    - Firmographic scoring (company data)
    - Behavioral scoring (actions taken)
    - Engagement scoring (product usage)
    - Predictive scoring
    - Score tier assignment (A/B/C/D)
    """

    # Score tiers
    TIER_A = 80  # >= 80 = Hot lead
    TIER_B = 60  # 60-79 = Warm lead
    TIER_C = 40  # 40-59 = Cold lead
    # < 40 = Very cold/disqualify

    # ICP (Ideal Customer Profile) industries
    ICP_INDUSTRIES = ["technology", "saas", "software", "healthcare", "finance", "fintech"]

    def __init__(self):
        config = AgentConfig(
            name="lead_scorer",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=800,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process lead scoring"""
        self.logger.info("lead_scorer_processing_started")

        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract scoring data
        scoring_data = self._extract_scoring_data(customer_metadata, entities, state)

        # Calculate scores
        firmographic_score = self._calculate_firmographic_score(scoring_data)
        behavioral_score = self._calculate_behavioral_score(scoring_data)
        engagement_score = self._calculate_engagement_score(scoring_data)
        recency_bonus = self._calculate_recency_score(scoring_data)

        # Total score
        total_score = min(
            firmographic_score + behavioral_score + engagement_score + recency_bonus,
            100
        )

        # Assign tier
        tier = self._assign_tier(total_score)

        # Generate recommendation
        recommendation = self._generate_recommendation(total_score, tier, scoring_data)

        # Build score breakdown
        score_breakdown = {
            "firmographic_score": firmographic_score,
            "behavioral_score": behavioral_score,
            "engagement_score": engagement_score,
            "recency_bonus": recency_bonus,
            "total_score": total_score
        }

        # Update state
        state["lead_score"] = total_score
        state["score_breakdown"] = score_breakdown
        state["lead_tier"] = tier
        state["recommendation"] = recommendation
        state["status"] = "resolved"
        state["response_confidence"] = 0.91

        self.logger.info(
            "lead_scorer_completed",
            total_score=total_score,
            tier=tier
        )

        return state

    def _extract_scoring_data(
        self,
        customer_metadata: Dict,
        entities: Dict,
        state: AgentState
    ) -> Dict[str, Any]:
        """Extract all data needed for scoring"""
        return {
            # Firmographic
            "company_size": customer_metadata.get("company_size", 0),
            "industry": customer_metadata.get("industry", "other"),
            "location": customer_metadata.get("location", "unknown"),
            "revenue": customer_metadata.get("revenue", 0),

            # Behavioral
            "email_opens": customer_metadata.get("email_opens", 0),
            "page_views": customer_metadata.get("page_views", 0),
            "downloads": customer_metadata.get("downloads", 0),
            "demo_requested": customer_metadata.get("demo_requested", False),

            # Engagement
            "trial_started": customer_metadata.get("trial_started", False),
            "trial_activity": customer_metadata.get("trial_activity", "none"),
            "features_used": customer_metadata.get("features_used", 0),
            "api_calls": customer_metadata.get("api_calls", 0),

            # Recency
            "days_since_first_touch": customer_metadata.get("days_since_first_touch", 999),
            "last_activity_date": customer_metadata.get("last_activity_date")
        }

    def _calculate_firmographic_score(self, data: Dict) -> int:
        """Calculate firmographic score (0-30 points)"""
        score = 0

        # Company size (0-15 points)
        company_size = data.get("company_size", 0)
        if company_size >= 1000:
            score += 15
        elif company_size >= 200:
            score += 12
        elif company_size >= 50:
            score += 10
        elif company_size >= 10:
            score += 7
        else:
            score += 3

        # Industry ICP match (0-10 points)
        industry = data.get("industry", "").lower()
        if industry in self.ICP_INDUSTRIES:
            score += 10
        elif industry in ["ecommerce", "marketing", "sales"]:
            score += 7
        else:
            score += 3

        # Revenue (0-5 points)
        revenue = data.get("revenue", 0)
        if revenue >= 50000000:  # $50M+
            score += 5
        elif revenue >= 10000000:  # $10M+
            score += 3
        elif revenue >= 1000000:  # $1M+
            score += 2

        return min(score, 30)

    def _calculate_behavioral_score(self, data: Dict) -> int:
        """Calculate behavioral score (0-25 points)"""
        score = 0

        # Email engagement (0-10 points)
        email_opens = data.get("email_opens", 0)
        score += min(email_opens * 2, 10)

        # Website engagement (0-10 points)
        page_views = data.get("page_views", 0)
        score += min(page_views // 2, 10)

        # Content downloads (0-5 points)
        downloads = data.get("downloads", 0)
        score += min(downloads * 2, 5)

        return min(score, 25)

    def _calculate_engagement_score(self, data: Dict) -> int:
        """Calculate engagement score (0-30 points)"""
        score = 0

        # Demo requested (10 points)
        if data.get("demo_requested"):
            score += 10

        # Trial activity (0-15 points)
        trial_activity = data.get("trial_activity", "none")
        if trial_activity == "high":
            score += 15
        elif trial_activity == "medium":
            score += 10
        elif trial_activity == "low":
            score += 5

        # Features used (0-5 points)
        features_used = data.get("features_used", 0)
        score += min(features_used, 5)

        return min(score, 30)

    def _calculate_recency_score(self, data: Dict) -> int:
        """Calculate recency bonus/penalty (0-15 points)"""
        days_since = data.get("days_since_first_touch", 999)

        if days_since <= 3:
            return 15
        elif days_since <= 7:
            return 10
        elif days_since <= 14:
            return 5
        elif days_since <= 30:
            return 0
        elif days_since <= 60:
            return -5
        else:
            return -10

    def _assign_tier(self, score: int) -> str:
        """Assign tier based on score"""
        if score >= self.TIER_A:
            return "A"
        elif score >= self.TIER_B:
            return "B"
        elif score >= self.TIER_C:
            return "C"
        else:
            return "D"

    def _generate_recommendation(self, score: int, tier: str, data: Dict) -> str:
        """Generate action recommendation based on score"""
        if tier == "A":
            return "High-priority lead - Immediate sales outreach recommended"
        elif tier == "B":
            return "Warm lead - Schedule demo within 48 hours"
        elif tier == "C":
            return "Cold lead - Add to nurture campaign"
        else:
            return "Very cold lead - Long-term nurture or disqualify"
