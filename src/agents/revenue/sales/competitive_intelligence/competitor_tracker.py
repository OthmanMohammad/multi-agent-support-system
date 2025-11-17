"""
Competitor Tracker Agent - TASK-1051

Tracks competitor mentions and activities, monitors wins and losses,
identifies competitive threats, and alerts on competitive deals.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("competitor_tracker", tier="revenue", category="sales")
class CompetitorTracker(BaseAgent):
    """
    Competitor Tracker Agent - Monitors competitor mentions and competitive activities.

    Handles:
    - Track competitor mentions in conversations
    - Monitor wins and losses against competitors
    - Identify competitive threats
    - Alert on competitive deals
    - Track competitive activity trends
    """

    # Competitor profiles
    COMPETITORS = {
        "salesforce": {
            "name": "Salesforce",
            "category": "CRM/Sales",
            "market_position": "market_leader",
            "threat_level": "high",
            "typical_deal_size": "enterprise",
            "win_rate_against_us": 0.35,
            "common_battle_grounds": ["enterprise", "financial_services", "healthcare"]
        },
        "hubspot": {
            "name": "HubSpot",
            "category": "Marketing/Sales",
            "market_position": "strong_challenger",
            "threat_level": "high",
            "typical_deal_size": "smb_mid_market",
            "win_rate_against_us": 0.42,
            "common_battle_grounds": ["smb", "marketing_teams", "saas"]
        },
        "zendesk": {
            "name": "Zendesk",
            "category": "Support",
            "market_position": "established_player",
            "threat_level": "medium",
            "typical_deal_size": "mid_market",
            "win_rate_against_us": 0.28,
            "common_battle_grounds": ["customer_support", "mid_market", "ecommerce"]
        },
        "intercom": {
            "name": "Intercom",
            "category": "Customer Messaging",
            "market_position": "niche_leader",
            "threat_level": "medium",
            "typical_deal_size": "smb_mid_market",
            "win_rate_against_us": 0.31,
            "common_battle_grounds": ["product_teams", "saas", "startups"]
        },
        "freshdesk": {
            "name": "Freshdesk",
            "category": "Support",
            "market_position": "value_player",
            "threat_level": "low",
            "typical_deal_size": "smb",
            "win_rate_against_us": 0.18,
            "common_battle_grounds": ["price_sensitive", "smb", "basic_support"]
        },
        "zoho": {
            "name": "Zoho CRM",
            "category": "CRM",
            "market_position": "value_player",
            "threat_level": "low",
            "typical_deal_size": "smb",
            "win_rate_against_us": 0.15,
            "common_battle_grounds": ["price_sensitive", "smb", "india_apac"]
        },
        "pipedrive": {
            "name": "Pipedrive",
            "category": "Sales CRM",
            "market_position": "niche_player",
            "threat_level": "low",
            "typical_deal_size": "smb",
            "win_rate_against_us": 0.22,
            "common_battle_grounds": ["sales_teams", "smb", "simple_crm"]
        }
    }

    # Competitive activity types
    ACTIVITY_TYPES = {
        "mention": {
            "weight": 1,
            "alert_threshold": 3,
            "description": "Competitor mentioned in conversation"
        },
        "evaluation": {
            "weight": 3,
            "alert_threshold": 2,
            "description": "Customer actively evaluating competitor"
        },
        "current_user": {
            "weight": 5,
            "alert_threshold": 1,
            "description": "Customer currently using competitor"
        },
        "win": {
            "weight": -10,
            "alert_threshold": 1,
            "description": "We won against competitor"
        },
        "loss": {
            "weight": 10,
            "alert_threshold": 1,
            "description": "We lost to competitor"
        },
        "churn_to_competitor": {
            "weight": 15,
            "alert_threshold": 1,
            "description": "Customer churned to competitor"
        }
    }

    # Alert severity levels
    ALERT_LEVELS = {
        "critical": {"min_score": 15, "action": "immediate_sales_escalation"},
        "high": {"min_score": 10, "action": "sales_team_notification"},
        "medium": {"min_score": 5, "action": "flag_for_review"},
        "low": {"min_score": 0, "action": "track_only"}
    }

    # Deal stage threat multipliers
    STAGE_MULTIPLIERS = {
        "discovery": 1.0,
        "qualification": 1.2,
        "demo": 1.5,
        "proposal": 2.0,
        "negotiation": 2.5,
        "closed_won": 0.0,
        "closed_lost": 3.0
    }

    def __init__(self):
        config = AgentConfig(
            name="competitor_tracker",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=1000,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process competitor tracking"""
        self.logger.info("competitor_tracker_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Identify competitor mentions
        mentioned_competitors = self._identify_competitors(message)

        # Determine activity type
        activity_type = self._determine_activity_type(message)

        # Calculate threat score
        threat_score = self._calculate_threat_score(
            mentioned_competitors,
            activity_type,
            customer_metadata,
            state
        )

        # Determine alert level
        alert_level = self._determine_alert_level(threat_score)

        # Track competitive activities
        competitive_activities = self._track_activities(
            mentioned_competitors,
            activity_type,
            message,
            customer_metadata
        )

        # Generate insights
        insights = self._generate_insights(
            mentioned_competitors,
            activity_type,
            threat_score,
            customer_metadata
        )

        # Determine if escalation is needed
        needs_escalation = alert_level in ["critical", "high"]

        # Generate alert if needed
        alert = None
        if needs_escalation:
            alert = self._generate_alert(
                mentioned_competitors,
                activity_type,
                threat_score,
                alert_level,
                customer_metadata
            )

        # Update state
        state["mentioned_competitors"] = mentioned_competitors
        state["competitor_activity_type"] = activity_type
        state["competitive_threat_score"] = threat_score
        state["alert_level"] = alert_level
        state["competitive_activities"] = competitive_activities
        state["competitive_insights"] = insights
        state["competitive_alert"] = alert
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"
        state["response_confidence"] = 0.88

        self.logger.info(
            "competitor_tracker_completed",
            competitors_count=len(mentioned_competitors),
            activity_type=activity_type,
            threat_score=threat_score,
            alert_level=alert_level
        )

        return state

    def _identify_competitors(self, message: str) -> List[str]:
        """Identify which competitors are mentioned"""
        message_lower = message.lower()
        mentioned = []

        for competitor_key, competitor_data in self.COMPETITORS.items():
            if competitor_key in message_lower or competitor_data["name"].lower() in message_lower:
                mentioned.append(competitor_key)

        return mentioned

    def _determine_activity_type(self, message: str) -> str:
        """Determine the type of competitive activity"""
        message_lower = message.lower()

        # Check for different activity patterns
        if any(phrase in message_lower for phrase in ["we lost", "chose", "went with", "selected"]):
            return "loss"
        elif any(phrase in message_lower for phrase in ["we won", "chose us", "selected us"]):
            return "win"
        elif any(phrase in message_lower for phrase in ["switched to", "moving to", "migrating to", "churned to"]):
            return "churn_to_competitor"
        elif any(phrase in message_lower for phrase in ["currently using", "been using", "have been with"]):
            return "current_user"
        elif any(phrase in message_lower for phrase in ["evaluating", "comparing", "looking at", "considering"]):
            return "evaluation"
        else:
            return "mention"

    def _calculate_threat_score(
        self,
        competitors: List[str],
        activity_type: str,
        customer_metadata: Dict,
        state: AgentState
    ) -> int:
        """Calculate competitive threat score"""
        base_score = 0

        # Base score from activity type
        activity_weight = self.ACTIVITY_TYPES.get(activity_type, {}).get("weight", 1)
        base_score += activity_weight

        # Add score per competitor mentioned
        for competitor in competitors:
            competitor_data = self.COMPETITORS.get(competitor, {})

            # High threat competitors add more
            if competitor_data.get("threat_level") == "high":
                base_score += 2
            elif competitor_data.get("threat_level") == "medium":
                base_score += 1

        # Apply deal stage multiplier
        deal_stage = customer_metadata.get("deal_stage", "discovery")
        stage_multiplier = self.STAGE_MULTIPLIERS.get(deal_stage, 1.0)

        threat_score = int(base_score * stage_multiplier)

        # Deal size adjustment
        deal_value = customer_metadata.get("deal_value", 0)
        if deal_value > 100000:
            threat_score = int(threat_score * 1.5)
        elif deal_value > 50000:
            threat_score = int(threat_score * 1.2)

        return max(threat_score, 0)

    def _determine_alert_level(self, threat_score: int) -> str:
        """Determine alert level based on threat score"""
        for level in ["critical", "high", "medium", "low"]:
            if threat_score >= self.ALERT_LEVELS[level]["min_score"]:
                return level
        return "low"

    def _track_activities(
        self,
        competitors: List[str],
        activity_type: str,
        message: str,
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Track competitive activities"""
        activities = []

        for competitor in competitors:
            competitor_data = self.COMPETITORS.get(competitor, {})

            activity = {
                "competitor": competitor,
                "competitor_name": competitor_data.get("name", competitor.title()),
                "activity_type": activity_type,
                "activity_description": self.ACTIVITY_TYPES.get(activity_type, {}).get("description", "Unknown activity"),
                "timestamp": datetime.now(UTC).isoformat(),
                "customer_id": customer_metadata.get("customer_id"),
                "company": customer_metadata.get("company"),
                "deal_value": customer_metadata.get("deal_value", 0),
                "deal_stage": customer_metadata.get("deal_stage", "unknown"),
                "industry": customer_metadata.get("industry"),
                "company_size": customer_metadata.get("company_size"),
                "message_snippet": message[:200]
            }

            activities.append(activity)

        return activities

    def _generate_insights(
        self,
        competitors: List[str],
        activity_type: str,
        threat_score: int,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate competitive insights"""
        insights = {
            "summary": self._generate_summary(competitors, activity_type, threat_score),
            "recommendations": self._generate_recommendations(competitors, activity_type, threat_score),
            "competitor_profiles": [],
            "win_rate_context": self._get_win_rate_context(competitors)
        }

        # Add competitor profiles
        for competitor in competitors:
            if competitor in self.COMPETITORS:
                competitor_data = self.COMPETITORS[competitor].copy()
                competitor_data["competitor_key"] = competitor
                insights["competitor_profiles"].append(competitor_data)

        return insights

    def _generate_summary(self, competitors: List[str], activity_type: str, threat_score: int) -> str:
        """Generate summary of competitive situation"""
        if not competitors:
            return "No specific competitors mentioned"

        competitor_names = [self.COMPETITORS.get(c, {}).get("name", c.title()) for c in competitors]

        if activity_type == "loss":
            return f"Deal lost to {', '.join(competitor_names)}. High priority for win/loss analysis."
        elif activity_type == "win":
            return f"Deal won against {', '.join(competitor_names)}. Capture success factors."
        elif activity_type == "churn_to_competitor":
            return f"Customer churned to {', '.join(competitor_names)}. Critical for retention analysis."
        elif activity_type == "current_user":
            return f"Customer currently using {', '.join(competitor_names)}. Displacement opportunity."
        elif activity_type == "evaluation":
            return f"Customer evaluating {', '.join(competitor_names)}. Active competitive situation."
        else:
            return f"Competitors mentioned: {', '.join(competitor_names)}"

    def _generate_recommendations(
        self,
        competitors: List[str],
        activity_type: str,
        threat_score: int
    ) -> List[str]:
        """Generate action recommendations"""
        recommendations = []

        if activity_type == "loss":
            recommendations.append("Schedule win/loss interview to understand decision factors")
            recommendations.append("Update competitive intelligence with loss insights")
            recommendations.append("Review and update battle cards for this competitor")

        elif activity_type == "win":
            recommendations.append("Document key differentiators that led to win")
            recommendations.append("Create case study/win story for sales enablement")
            recommendations.append("Share winning tactics with sales team")

        elif activity_type == "churn_to_competitor":
            recommendations.append("Conduct exit interview to understand churn reasons")
            recommendations.append("Analyze product/service gaps that led to churn")
            recommendations.append("Update retention playbook based on insights")

        elif activity_type == "current_user":
            recommendations.append("Provide competitive battle cards to sales rep")
            recommendations.append("Share migration success stories and support offerings")
            recommendations.append("Offer competitive comparison demo")

        elif activity_type == "evaluation":
            recommendations.append("Proactively share competitive differentiation materials")
            recommendations.append("Schedule head-to-head demo if appropriate")
            recommendations.append("Provide ROI comparison tools")

        if threat_score >= 10:
            recommendations.append("Escalate to sales leadership for strategic guidance")

        return recommendations

    def _get_win_rate_context(self, competitors: List[str]) -> Dict[str, Any]:
        """Get win rate context for mentioned competitors"""
        if not competitors:
            return {}

        win_rates = {}
        for competitor in competitors:
            if competitor in self.COMPETITORS:
                win_rates[competitor] = {
                    "name": self.COMPETITORS[competitor]["name"],
                    "our_win_rate": 1.0 - self.COMPETITORS[competitor]["win_rate_against_us"],
                    "their_win_rate": self.COMPETITORS[competitor]["win_rate_against_us"]
                }

        return win_rates

    def _generate_alert(
        self,
        competitors: List[str],
        activity_type: str,
        threat_score: int,
        alert_level: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate competitive alert"""
        competitor_names = [self.COMPETITORS.get(c, {}).get("name", c.title()) for c in competitors]

        alert = {
            "alert_level": alert_level,
            "alert_type": "competitive_threat",
            "threat_score": threat_score,
            "activity_type": activity_type,
            "competitors": competitor_names,
            "customer": customer_metadata.get("company", "Unknown"),
            "deal_value": customer_metadata.get("deal_value", 0),
            "deal_stage": customer_metadata.get("deal_stage", "unknown"),
            "action_required": self.ALERT_LEVELS[alert_level]["action"],
            "timestamp": datetime.now(UTC).isoformat(),
            "message": self._format_alert_message(competitors, activity_type, alert_level, customer_metadata)
        }

        return alert

    def _format_alert_message(
        self,
        competitors: List[str],
        activity_type: str,
        alert_level: str,
        customer_metadata: Dict
    ) -> str:
        """Format alert message"""
        competitor_names = [self.COMPETITORS.get(c, {}).get("name", c.title()) for c in competitors]
        company = customer_metadata.get("company", "Unknown customer")
        deal_value = customer_metadata.get("deal_value", 0)

        messages = {
            "loss": f"🚨 COMPETITIVE LOSS: {company} (${deal_value:,.0f}) chose {', '.join(competitor_names)}",
            "churn_to_competitor": f"🚨 CUSTOMER CHURN: {company} switched to {', '.join(competitor_names)}",
            "current_user": f"⚠️ DISPLACEMENT OPPORTUNITY: {company} currently using {', '.join(competitor_names)}",
            "evaluation": f"⚠️ ACTIVE EVALUATION: {company} comparing us to {', '.join(competitor_names)}",
            "win": f"✅ COMPETITIVE WIN: {company} chose us over {', '.join(competitor_names)}",
            "mention": f"ℹ️ COMPETITOR MENTIONED: {', '.join(competitor_names)} in {company} conversation"
        }

        return messages.get(activity_type, f"Competitive activity detected: {', '.join(competitor_names)}")


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing CompetitorTracker Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Current user (displacement opportunity)
        state1 = create_initial_state(
            "We're currently using Salesforce and it's been working okay for the past 2 years.",
            context={
                "customer_metadata": {
                    "customer_id": "CUST-001",
                    "company": "Enterprise Corp",
                    "company_size": 500,
                    "industry": "technology",
                    "deal_value": 75000,
                    "deal_stage": "qualification"
                }
            }
        )

        agent = CompetitorTracker()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Current Salesforce User")
        print(f"Competitors: {result1['mentioned_competitors']}")
        print(f"Activity Type: {result1['competitor_activity_type']}")
        print(f"Threat Score: {result1['competitive_threat_score']}")
        print(f"Alert Level: {result1['alert_level']}")
        print(f"Needs Escalation: {result1['needs_escalation']}")
        print(f"Summary: {result1['competitive_insights']['summary']}")
        print(f"Recommendations: {result1['competitive_insights']['recommendations']}")
        if result1.get('competitive_alert'):
            print(f"Alert: {result1['competitive_alert']['message']}\n")

        # Test case 2: Lost deal
        state2 = create_initial_state(
            "Unfortunately we lost this deal - they decided to go with HubSpot instead.",
            context={
                "customer_metadata": {
                    "customer_id": "CUST-002",
                    "company": "GrowthCo",
                    "company_size": 150,
                    "industry": "saas",
                    "deal_value": 45000,
                    "deal_stage": "closed_lost"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Lost Deal to HubSpot")
        print(f"Competitors: {result2['mentioned_competitors']}")
        print(f"Activity Type: {result2['competitor_activity_type']}")
        print(f"Threat Score: {result2['competitive_threat_score']}")
        print(f"Alert Level: {result2['alert_level']}")
        print(f"Needs Escalation: {result2['needs_escalation']}")
        print(f"Summary: {result2['competitive_insights']['summary']}")
        print(f"Recommendations: {result2['competitive_insights']['recommendations']}")
        if result2.get('competitive_alert'):
            print(f"Alert: {result2['competitive_alert']['message']}\n")

        # Test case 3: Active evaluation (multiple competitors)
        state3 = create_initial_state(
            "We're evaluating both Zendesk and Intercom as alternatives. Can you help us compare?",
            context={
                "customer_metadata": {
                    "customer_id": "CUST-003",
                    "company": "SupportCo",
                    "company_size": 200,
                    "industry": "ecommerce",
                    "deal_value": 60000,
                    "deal_stage": "demo"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Active Evaluation (Multiple Competitors)")
        print(f"Competitors: {result3['mentioned_competitors']}")
        print(f"Activity Type: {result3['competitor_activity_type']}")
        print(f"Threat Score: {result3['competitive_threat_score']}")
        print(f"Alert Level: {result3['alert_level']}")
        print(f"Needs Escalation: {result3['needs_escalation']}")
        print(f"Summary: {result3['competitive_insights']['summary']}")
        print(f"Win Rate Context: {result3['competitive_insights']['win_rate_context']}")
        print(f"Activities Tracked: {len(result3['competitive_activities'])}")

    asyncio.run(test())
