"""
Relationship Health Agent - TASK-2064

Assesses relationship strength with customers, identifies engagement gaps,
and tracks relationship metrics to ensure strong customer partnerships.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("relationship_health", tier="revenue", category="customer_success")
class RelationshipHealthAgent(BaseAgent):
    """
    Relationship Health Agent.

    Monitors relationship health by:
    - Assessing relationship strength across multiple dimensions
    - Tracking engagement frequency and quality
    - Identifying relationship gaps and risks
    - Measuring stakeholder coverage and depth
    - Monitoring communication sentiment
    - Generating relationship improvement recommendations
    """

    # Relationship health dimensions and weights
    HEALTH_DIMENSIONS = {
        "engagement_frequency": {"weight": 25, "target": 85},
        "stakeholder_coverage": {"weight": 25, "target": 75},
        "communication_quality": {"weight": 20, "target": 80},
        "relationship_depth": {"weight": 15, "target": 70},
        "executive_alignment": {"weight": 15, "target": 65}
    }

    # Engagement frequency targets (by tier)
    ENGAGEMENT_TARGETS = {
        "enterprise": {"touchpoints_per_month": 8, "exec_touchpoints_per_quarter": 3},
        "premium": {"touchpoints_per_month": 4, "exec_touchpoints_per_quarter": 2},
        "growth": {"touchpoints_per_month": 2, "exec_touchpoints_per_quarter": 1},
        "standard": {"touchpoints_per_month": 1, "exec_touchpoints_per_quarter": 0}
    }

    # Relationship health tiers
    HEALTH_TIERS = {
        "excellent": {"score_min": 85, "description": "Strong, multi-threaded relationship"},
        "good": {"score_min": 70, "description": "Solid relationship with room to deepen"},
        "fair": {"score_min": 55, "description": "Adequate relationship needing attention"},
        "at_risk": {"score_min": 40, "description": "Weak relationship requiring intervention"},
        "critical": {"score_min": 0, "description": "Relationship in jeopardy"}
    }

    def __init__(self):
        config = AgentConfig(
            name="relationship_health",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=700,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="customer_success",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Assess relationship health.

        Args:
            state: Current agent state with relationship data

        Returns:
            Updated state with relationship health assessment
        """
        self.logger.info("relationship_health_assessment_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        contact_data = state.get("entities", {}).get("contact_data", {})
        communication_data = state.get("entities", {}).get("communication_data", {})

        self.logger.debug(
            "relationship_health_details",
            customer_id=customer_id,
            tier=customer_metadata.get("tier", "standard")
        )

        # Assess relationship health
        health_assessment = self._assess_relationship_health(
            engagement_data,
            contact_data,
            communication_data,
            customer_metadata
        )

        # Identify relationship gaps
        relationship_gaps = self._identify_relationship_gaps(
            health_assessment,
            contact_data,
            customer_metadata
        )

        # Analyze stakeholder coverage
        stakeholder_analysis = self._analyze_stakeholder_coverage(
            contact_data,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_relationship_recommendations(
            health_assessment,
            relationship_gaps,
            stakeholder_analysis
        )

        # Create action plan
        action_plan = self._create_relationship_action_plan(
            health_assessment,
            relationship_gaps
        )

        # Format response
        response = self._format_relationship_health_report(
            health_assessment,
            relationship_gaps,
            stakeholder_analysis,
            recommendations,
            action_plan
        )

        state["agent_response"] = response
        state["relationship_health_score"] = health_assessment["overall_score"]
        state["relationship_status"] = health_assessment["health_tier"]
        state["stakeholder_coverage"] = stakeholder_analysis.get("coverage_score", 0)
        state["relationship_risk_level"] = health_assessment.get("risk_level", "medium")
        state["response_confidence"] = 0.86
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "relationship_health_assessment_completed",
            customer_id=customer_id,
            health_score=health_assessment["overall_score"],
            health_tier=health_assessment["health_tier"]
        )

        return state

    def _assess_relationship_health(
        self,
        engagement_data: Dict[str, Any],
        contact_data: Dict[str, Any],
        communication_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess overall relationship health.

        Args:
            engagement_data: Customer engagement metrics
            contact_data: Contact and stakeholder information
            communication_data: Communication history and sentiment
            customer_metadata: Customer profile data

        Returns:
            Comprehensive relationship health assessment
        """
        scores = {}

        # 1. Engagement frequency (0-25 points)
        scores["engagement_frequency"] = self._score_engagement_frequency(
            engagement_data,
            customer_metadata
        )

        # 2. Stakeholder coverage (0-25 points)
        scores["stakeholder_coverage"] = self._score_stakeholder_coverage(
            contact_data
        )

        # 3. Communication quality (0-20 points)
        scores["communication_quality"] = self._score_communication_quality(
            communication_data,
            engagement_data
        )

        # 4. Relationship depth (0-15 points)
        scores["relationship_depth"] = self._score_relationship_depth(
            engagement_data,
            contact_data
        )

        # 5. Executive alignment (0-15 points)
        scores["executive_alignment"] = self._score_executive_alignment(
            contact_data,
            engagement_data
        )

        # Calculate overall score
        overall_score = sum(scores.values())
        overall_score = min(int(overall_score), 100)

        # Determine health tier
        health_tier = self._determine_health_tier(overall_score)

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score, scores)

        # Calculate trend
        previous_score = customer_metadata.get("previous_relationship_score")
        trend = self._calculate_trend(overall_score, previous_score)

        return {
            "overall_score": overall_score,
            "health_tier": health_tier,
            "dimension_scores": {k: int(v) for k, v in scores.items()},
            "risk_level": risk_level,
            "trend": trend,
            "score_change": int(overall_score - previous_score) if previous_score else 0,
            "assessed_at": datetime.now(UTC).isoformat()
        }

    def _score_engagement_frequency(
        self,
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> float:
        """Score engagement frequency (0-25)."""
        tier = customer_metadata.get("tier", "standard")
        targets = self.ENGAGEMENT_TARGETS.get(tier, self.ENGAGEMENT_TARGETS["standard"])

        touchpoints_last_30d = engagement_data.get("touchpoints_last_30d", 0)
        target_touchpoints = targets["touchpoints_per_month"]

        if target_touchpoints == 0:
            return 20  # Default for no target

        # Calculate score based on target achievement
        achievement_pct = (touchpoints_last_30d / target_touchpoints) * 100
        score = min((achievement_pct / 100) * 25, 25)

        return score

    def _score_stakeholder_coverage(self, contact_data: Dict[str, Any]) -> float:
        """Score stakeholder coverage (0-25)."""
        contacts = contact_data.get("all_contacts", [])
        engaged_contacts = contact_data.get("engaged_contacts_last_90d", [])

        if len(contacts) == 0:
            return 0

        # Coverage percentage
        coverage_pct = (len(engaged_contacts) / len(contacts)) * 100

        # Department diversity
        departments = set(c.get("department", "Unknown") for c in engaged_contacts)
        department_score = min(len(departments) * 3, 10)

        # Seniority levels
        has_exec = any(
            any(term in c.get("title", "").lower() for term in ["vp", "ceo", "cto", "cfo", "chief"])
            for c in engaged_contacts
        )
        seniority_score = 5 if has_exec else 2

        total_score = (coverage_pct / 100) * 10 + department_score + seniority_score
        return min(total_score, 25)

    def _score_communication_quality(
        self,
        communication_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> float:
        """Score communication quality (0-20)."""
        score = 0

        # Response time
        avg_response_hours = communication_data.get("avg_response_time_hours", 48)
        if avg_response_hours <= 4:
            score += 8
        elif avg_response_hours <= 24:
            score += 5
        elif avg_response_hours <= 48:
            score += 2

        # Sentiment
        sentiment = communication_data.get("overall_sentiment", "neutral")
        if sentiment == "positive":
            score += 7
        elif sentiment == "neutral":
            score += 4
        else:
            score += 1

        # Engagement quality
        qbr_attended = engagement_data.get("qbr_attended_last_quarter", False)
        if qbr_attended:
            score += 5

        return min(score, 20)

    def _score_relationship_depth(
        self,
        engagement_data: Dict[str, Any],
        contact_data: Dict[str, Any]
    ) -> float:
        """Score relationship depth (0-15)."""
        score = 0

        # Multi-threading (multiple engaged contacts)
        engaged_contacts = len(contact_data.get("engaged_contacts_last_90d", []))
        if engaged_contacts >= 5:
            score += 7
        elif engaged_contacts >= 3:
            score += 5
        elif engaged_contacts >= 1:
            score += 3

        # Relationship tenure
        customer_since = contact_data.get("customer_since_date")
        if customer_since:
            try:
                since_date = datetime.fromisoformat(customer_since.replace('Z', '+00:00'))
                days_active = (datetime.now(UTC) - since_date).days
                if days_active > 365:
                    score += 5
                elif days_active > 180:
                    score += 3
                else:
                    score += 1
            except:
                score += 1

        # Proactive engagement
        feature_requests = engagement_data.get("feature_requests_submitted", 0)
        if feature_requests > 0:
            score += 3

        return min(score, 15)

    def _score_executive_alignment(
        self,
        contact_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> float:
        """Score executive alignment (0-15)."""
        score = 0

        # Executive sponsor identified
        has_sponsor = bool(contact_data.get("executive_sponsor", {}).get("name"))
        if has_sponsor:
            score += 8

            # Recent executive engagement
            last_exec_contact = contact_data.get("executive_sponsor", {}).get("last_contact_date")
            if last_exec_contact:
                try:
                    last_contact = datetime.fromisoformat(last_exec_contact.replace('Z', '+00:00'))
                    days_since = (datetime.now(UTC) - last_contact).days
                    if days_since <= 30:
                        score += 7
                    elif days_since <= 60:
                        score += 4
                    elif days_since <= 90:
                        score += 2
                except:
                    pass
        else:
            score += 2  # Some baseline points

        return min(score, 15)

    def _determine_health_tier(self, score: int) -> str:
        """Determine health tier from overall score."""
        for tier, config in sorted(
            self.HEALTH_TIERS.items(),
            key=lambda x: x[1]["score_min"],
            reverse=True
        ):
            if score >= config["score_min"]:
                return tier
        return "critical"

    def _determine_risk_level(self, overall_score: int, dimension_scores: Dict[str, float]) -> str:
        """Determine relationship risk level."""
        if overall_score >= 75:
            return "low"
        elif overall_score >= 60:
            return "medium"
        elif overall_score >= 45:
            return "high"
        else:
            return "critical"

    def _calculate_trend(self, current_score: int, previous_score: Optional[int]) -> str:
        """Calculate relationship health trend."""
        if not previous_score:
            return "new"

        change = current_score - previous_score

        if change > 8:
            return "improving"
        elif change < -8:
            return "declining"
        else:
            return "stable"

    def _identify_relationship_gaps(
        self,
        health_assessment: Dict[str, Any],
        contact_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify gaps in relationship health."""
        gaps = []
        dimension_scores = health_assessment["dimension_scores"]

        # Check each dimension against targets
        for dimension, config in self.HEALTH_DIMENSIONS.items():
            actual_score = dimension_scores.get(dimension, 0)
            max_score = config["weight"]
            score_pct = (actual_score / max_score * 100) if max_score > 0 else 0

            if score_pct < 60:  # Below 60% of max
                gaps.append({
                    "dimension": dimension,
                    "actual_score": int(actual_score),
                    "max_score": max_score,
                    "gap_severity": "high" if score_pct < 40 else "medium",
                    "recommendation": self._get_gap_recommendation(dimension, score_pct)
                })

        return gaps

    def _get_gap_recommendation(self, dimension: str, score_pct: float) -> str:
        """Get recommendation for a specific gap."""
        recommendations = {
            "engagement_frequency": "Increase touchpoint frequency - schedule regular check-ins",
            "stakeholder_coverage": "Expand stakeholder network - engage additional departments",
            "communication_quality": "Improve response times and communication sentiment",
            "relationship_depth": "Deepen relationships through strategic discussions",
            "executive_alignment": "Establish or strengthen executive sponsor relationship"
        }
        return recommendations.get(dimension, "Address this relationship gap")

    def _analyze_stakeholder_coverage(
        self,
        contact_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze stakeholder coverage."""
        all_contacts = contact_data.get("all_contacts", [])
        engaged_contacts = contact_data.get("engaged_contacts_last_90d", [])

        # Department coverage
        departments = set(c.get("department", "Unknown") for c in engaged_contacts)

        # Seniority coverage
        exec_contacts = sum(
            1 for c in engaged_contacts
            if any(term in c.get("title", "").lower() for term in ["vp", "ceo", "cto", "cfo", "chief", "president"])
        )

        manager_contacts = sum(
            1 for c in engaged_contacts
            if any(term in c.get("title", "").lower() for term in ["manager", "director"])
        )

        # Calculate coverage score
        if len(all_contacts) > 0:
            coverage_pct = (len(engaged_contacts) / len(all_contacts)) * 100
            coverage_score = int(coverage_pct)
        else:
            coverage_score = 0

        return {
            "total_contacts": len(all_contacts),
            "engaged_contacts": len(engaged_contacts),
            "coverage_score": coverage_score,
            "departments_covered": len(departments),
            "executive_contacts": exec_contacts,
            "manager_contacts": manager_contacts,
            "multi_threaded": len(engaged_contacts) >= 3
        }

    def _generate_relationship_recommendations(
        self,
        health_assessment: Dict[str, Any],
        relationship_gaps: List[Dict[str, Any]],
        stakeholder_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations to improve relationship health."""
        recommendations = []

        # Address critical gaps
        for gap in relationship_gaps:
            if gap["gap_severity"] == "high":
                recommendations.append({
                    "area": gap["dimension"].replace("_", " ").title(),
                    "action": gap["recommendation"],
                    "priority": "high"
                })

        # Stakeholder expansion
        if not stakeholder_analysis["multi_threaded"]:
            recommendations.append({
                "area": "Stakeholder Network",
                "action": "Expand to 3+ engaged stakeholders for relationship resilience",
                "priority": "high"
            })

        # Executive alignment
        if stakeholder_analysis["executive_contacts"] == 0:
            recommendations.append({
                "area": "Executive Engagement",
                "action": "Identify and engage executive sponsor",
                "priority": "high"
            })

        return recommendations[:5]

    def _create_relationship_action_plan(
        self,
        health_assessment: Dict[str, Any],
        relationship_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Create action plan to improve relationship health."""
        actions = []

        risk_level = health_assessment["risk_level"]

        if risk_level in ["high", "critical"]:
            actions.append({
                "action": "Schedule urgent executive business review",
                "owner": "VP Customer Success",
                "timeline": "Within 1 week",
                "priority": "critical"
            })

        # Address top gaps
        for gap in relationship_gaps[:2]:
            actions.append({
                "action": gap["recommendation"],
                "owner": "CSM",
                "timeline": "Within 2 weeks",
                "priority": "high" if gap["gap_severity"] == "high" else "medium"
            })

        # Regular touchpoint
        if health_assessment["overall_score"] < 75:
            actions.append({
                "action": "Establish regular weekly or bi-weekly touchpoint cadence",
                "owner": "CSM",
                "timeline": "This week",
                "priority": "medium"
            })

        return actions[:5]

    def _format_relationship_health_report(
        self,
        health_assessment: Dict[str, Any],
        relationship_gaps: List[Dict[str, Any]],
        stakeholder_analysis: Dict[str, Any],
        recommendations: List[Dict[str, str]],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format relationship health report."""
        tier = health_assessment["health_tier"]
        score = health_assessment["overall_score"]
        risk = health_assessment["risk_level"]

        tier_emoji = {
            "excellent": "????",
            "good": "???",
            "fair": "??????",
            "at_risk": "????",
            "critical": "????"
        }

        risk_emoji = {
            "low": "????",
            "medium": "????",
            "high": "????",
            "critical": "????"
        }

        report = f"""**???? Relationship Health Assessment**

**Overall Score:** {score}/100 {tier_emoji.get(tier, '???')}
**Health Status:** {tier.replace('_', ' ').title()}
**Risk Level:** {risk.upper()} {risk_emoji.get(risk, '???')}
**Trend:** {health_assessment['trend'].capitalize()} ({health_assessment['score_change']:+d} points)

**Dimension Scores:**
"""

        for dimension, score_val in health_assessment["dimension_scores"].items():
            max_score = self.HEALTH_DIMENSIONS[dimension]["weight"]
            pct = int((score_val / max_score * 100))
            bar = "???" * int(pct / 10) + "???" * (10 - int(pct / 10))
            report += f"- {dimension.replace('_', ' ').title()}: {score_val}/{max_score} {bar}\n"

        # Stakeholder analysis
        report += f"\n**???? Stakeholder Coverage:**\n"
        report += f"- Engaged Contacts: {stakeholder_analysis['engaged_contacts']}/{stakeholder_analysis['total_contacts']}\n"
        report += f"- Coverage Score: {stakeholder_analysis['coverage_score']}%\n"
        report += f"- Departments: {stakeholder_analysis['departments_covered']}\n"
        report += f"- Executive Contacts: {stakeholder_analysis['executive_contacts']}\n"
        report += f"- Multi-threaded: {'Yes ???' if stakeholder_analysis['multi_threaded'] else 'No ??????'}\n"

        # Relationship gaps
        if relationship_gaps:
            report += "\n**?????? Relationship Gaps:**\n"
            for i, gap in enumerate(relationship_gaps[:3], 1):
                severity_icon = "????" if gap["gap_severity"] == "high" else "????"
                report += f"{i}. **{gap['dimension'].replace('_', ' ').title()}** {severity_icon}\n"
                report += f"   Score: {gap['actual_score']}/{gap['max_score']}\n"
                report += f"   Action: {gap['recommendation']}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommendations:**\n"
            for i, rec in enumerate(recommendations[:4], 1):
                priority_icon = "????" if rec["priority"] == "high" else "????"
                report += f"{i}. **{rec['area']}** {priority_icon}\n"
                report += f"   {rec['action']}\n"

        # Action plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Relationship Health Agent (TASK-2064)")
        print("=" * 70)

        agent = RelationshipHealthAgent()

        # Test 1: Excellent relationship health
        print("\n\nTest 1: Excellent Relationship Health")
        print("-" * 70)

        state1 = create_initial_state(
            "Assess relationship health",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "previous_relationship_score": 80
                }
            }
        )
        state1["entities"] = {
            "engagement_data": {
                "touchpoints_last_30d": 10,
                "qbr_attended_last_quarter": True,
                "feature_requests_submitted": 5
            },
            "contact_data": {
                "executive_sponsor": {
                    "name": "Sarah Johnson",
                    "last_contact_date": (datetime.now(UTC) - timedelta(days=15)).isoformat()
                },
                "all_contacts": [
                    {"name": "Contact 1", "department": "Engineering", "title": "VP Engineering"},
                    {"name": "Contact 2", "department": "Operations", "title": "Director Operations"},
                    {"name": "Contact 3", "department": "IT", "title": "IT Manager"},
                    {"name": "Contact 4", "department": "Engineering", "title": "Engineer"}
                ],
                "engaged_contacts_last_90d": [
                    {"name": "Contact 1", "department": "Engineering", "title": "VP Engineering"},
                    {"name": "Contact 2", "department": "Operations", "title": "Director Operations"},
                    {"name": "Contact 3", "department": "IT", "title": "IT Manager"}
                ],
                "customer_since_date": (datetime.now(UTC) - timedelta(days=500)).isoformat()
            },
            "communication_data": {
                "avg_response_time_hours": 3,
                "overall_sentiment": "positive"
            }
        }

        result1 = await agent.process(state1)

        print(f"Relationship Health Score: {result1['relationship_health_score']}")
        print(f"Status: {result1['relationship_status']}")
        print(f"Risk Level: {result1['relationship_risk_level']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: At-risk relationship
        print("\n\n" + "=" * 70)
        print("Test 2: At-Risk Relationship")
        print("-" * 70)

        state2 = create_initial_state(
            "Check relationship health",
            context={
                "customer_id": "cust_growth_002",
                "customer_metadata": {
                    "tier": "growth",
                    "previous_relationship_score": 60
                }
            }
        )
        state2["entities"] = {
            "engagement_data": {
                "touchpoints_last_30d": 1,
                "qbr_attended_last_quarter": False,
                "feature_requests_submitted": 0
            },
            "contact_data": {
                "executive_sponsor": {},
                "all_contacts": [
                    {"name": "Contact 1", "department": "IT", "title": "IT Manager"}
                ],
                "engaged_contacts_last_90d": [
                    {"name": "Contact 1", "department": "IT", "title": "IT Manager"}
                ],
                "customer_since_date": (datetime.now(UTC) - timedelta(days=120)).isoformat()
            },
            "communication_data": {
                "avg_response_time_hours": 72,
                "overall_sentiment": "neutral"
            }
        }

        result2 = await agent.process(state2)

        print(f"Relationship Health Score: {result2['relationship_health_score']}")
        print(f"Status: {result2['relationship_status']}")
        print(f"Risk Level: {result2['relationship_risk_level']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
