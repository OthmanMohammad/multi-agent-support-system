"""
Review Analyzer Agent - TASK-1052

Analyzes competitor reviews from G2, Capterra, TrustRadius and other platforms.
Extracts key themes, identifies strengths and weaknesses, generates competitive insights.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("review_analyzer", tier="revenue", category="sales")
class ReviewAnalyzer(BaseAgent):
    """
    Review Analyzer Agent - Analyzes competitor reviews for competitive intelligence.

    Handles:
    - Analyze competitor reviews from multiple platforms
    - Extract key themes and patterns
    - Identify competitor strengths and weaknesses
    - Generate competitive insights
    - Track review sentiment trends
    """

    # Review platforms
    REVIEW_PLATFORMS = {
        "g2": {
            "name": "G2",
            "weight": 1.5,
            "credibility": "high",
            "typical_review_count": "high",
            "focus": "software_buyers"
        },
        "capterra": {
            "name": "Capterra",
            "weight": 1.3,
            "credibility": "high",
            "typical_review_count": "medium",
            "focus": "smb_buyers"
        },
        "trustradius": {
            "name": "TrustRadius",
            "weight": 1.4,
            "credibility": "high",
            "typical_review_count": "medium",
            "focus": "enterprise_buyers"
        },
        "gartner": {
            "name": "Gartner Peer Insights",
            "weight": 1.8,
            "credibility": "very_high",
            "typical_review_count": "low",
            "focus": "enterprise_buyers"
        },
        "software_advice": {
            "name": "Software Advice",
            "weight": 1.2,
            "credibility": "medium",
            "typical_review_count": "medium",
            "focus": "smb_buyers"
        }
    }

    # Common review themes
    REVIEW_THEMES = {
        "ease_of_use": {
            "keywords": ["easy to use", "intuitive", "user-friendly", "simple", "straightforward", "learning curve"],
            "category": "usability",
            "importance": "high"
        },
        "features": {
            "keywords": ["features", "functionality", "capabilities", "feature-rich", "limited features", "missing"],
            "category": "product",
            "importance": "high"
        },
        "pricing": {
            "keywords": ["expensive", "pricing", "cost", "value for money", "affordable", "overpriced", "cheap"],
            "category": "commercial",
            "importance": "high"
        },
        "support": {
            "keywords": ["customer support", "help desk", "responsive", "support team", "documentation", "unhelpful"],
            "category": "service",
            "importance": "high"
        },
        "reliability": {
            "keywords": ["reliable", "uptime", "stable", "bugs", "crashes", "downtime", "performance"],
            "category": "technical",
            "importance": "high"
        },
        "integration": {
            "keywords": ["integration", "api", "connects", "third-party", "ecosystem", "compatibility"],
            "category": "technical",
            "importance": "medium"
        },
        "customization": {
            "keywords": ["customizable", "flexible", "configure", "rigid", "inflexible", "limited options"],
            "category": "product",
            "importance": "medium"
        },
        "onboarding": {
            "keywords": ["onboarding", "setup", "implementation", "getting started", "training", "ramp-up"],
            "category": "service",
            "importance": "medium"
        },
        "scalability": {
            "keywords": ["scalable", "grows with us", "enterprise-ready", "performance at scale", "limitations"],
            "category": "technical",
            "importance": "medium"
        },
        "reporting": {
            "keywords": ["reports", "analytics", "dashboards", "insights", "data visualization", "metrics"],
            "category": "product",
            "importance": "medium"
        }
    }

    # Competitor review profiles (sample data)
    COMPETITOR_REVIEWS = {
        "salesforce": {
            "overall_rating": 4.2,
            "total_reviews": 15420,
            "common_positives": [
                "Comprehensive feature set",
                "Industry standard / market leader",
                "Strong ecosystem and integrations",
                "Powerful for large enterprises",
                "Extensive customization options"
            ],
            "common_negatives": [
                "Very expensive, especially with add-ons",
                "Steep learning curve",
                "Complex setup requiring consultants",
                "Can be overwhelming for smaller teams",
                "Frequent UI changes confusing"
            ],
            "key_themes": {
                "ease_of_use": {"score": 3.5, "sentiment": "negative"},
                "features": {"score": 4.6, "sentiment": "positive"},
                "pricing": {"score": 2.8, "sentiment": "negative"},
                "support": {"score": 3.9, "sentiment": "neutral"},
                "reliability": {"score": 4.1, "sentiment": "positive"}
            }
        },
        "hubspot": {
            "overall_rating": 4.4,
            "total_reviews": 9850,
            "common_positives": [
                "Very user-friendly and intuitive",
                "Great for marketing and sales alignment",
                "Good free tier to get started",
                "Excellent educational content",
                "Clean, modern interface"
            ],
            "common_negatives": [
                "Pricing scales up very quickly",
                "Contact-based pricing gets expensive",
                "Some enterprise features missing",
                "Limited customization compared to competitors",
                "Reporting could be more robust"
            ],
            "key_themes": {
                "ease_of_use": {"score": 4.7, "sentiment": "positive"},
                "features": {"score": 4.2, "sentiment": "positive"},
                "pricing": {"score": 3.2, "sentiment": "negative"},
                "support": {"score": 4.3, "sentiment": "positive"},
                "reliability": {"score": 4.4, "sentiment": "positive"}
            }
        },
        "zendesk": {
            "overall_rating": 4.3,
            "total_reviews": 5420,
            "common_positives": [
                "Good for customer support teams",
                "Decent ticketing system",
                "Multiple product options",
                "Integration capabilities",
                "Established platform"
            ],
            "common_negatives": [
                "Need multiple products for complete solution",
                "Pricing structure confusing",
                "UI feels dated",
                "Limited automation capabilities",
                "Reporting not intuitive"
            ],
            "key_themes": {
                "ease_of_use": {"score": 3.9, "sentiment": "neutral"},
                "features": {"score": 4.0, "sentiment": "neutral"},
                "pricing": {"score": 3.3, "sentiment": "negative"},
                "support": {"score": 4.1, "sentiment": "positive"},
                "reliability": {"score": 4.2, "sentiment": "positive"}
            }
        },
        "intercom": {
            "overall_rating": 4.5,
            "total_reviews": 2890,
            "common_positives": [
                "Great for customer messaging",
                "Beautiful, modern interface",
                "Good for product-led companies",
                "Easy to implement",
                "Strong mobile experience"
            ],
            "common_negatives": [
                "Extremely expensive at scale",
                "Conversation limits frustrating",
                "Support ticketing features lacking",
                "Pricing not transparent",
                "Limited for traditional support teams"
            ],
            "key_themes": {
                "ease_of_use": {"score": 4.6, "sentiment": "positive"},
                "features": {"score": 4.2, "sentiment": "positive"},
                "pricing": {"score": 2.5, "sentiment": "very_negative"},
                "support": {"score": 4.0, "sentiment": "neutral"},
                "reliability": {"score": 4.4, "sentiment": "positive"}
            }
        },
        "freshdesk": {
            "overall_rating": 4.5,
            "total_reviews": 2640,
            "common_positives": [
                "Affordable pricing",
                "Easy to set up",
                "Good for small teams",
                "Clean interface",
                "Decent feature set"
            ],
            "common_negatives": [
                "Basic automation",
                "Limited advanced features",
                "Performance issues at scale",
                "Fewer integrations than competitors",
                "Reporting capabilities limited"
            ],
            "key_themes": {
                "ease_of_use": {"score": 4.4, "sentiment": "positive"},
                "features": {"score": 3.8, "sentiment": "neutral"},
                "pricing": {"score": 4.6, "sentiment": "positive"},
                "support": {"score": 4.2, "sentiment": "positive"},
                "reliability": {"score": 4.0, "sentiment": "neutral"}
            }
        }
    }

    # Insight categories
    INSIGHT_CATEGORIES = {
        "opportunity": "Areas where competitors are weak and we can win",
        "threat": "Areas where competitors excel and we need to match",
        "trend": "Emerging patterns in customer feedback",
        "positioning": "How to position against specific weaknesses"
    }

    def __init__(self):
        config = AgentConfig(
            name="review_analyzer",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            max_tokens=1500,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process review analysis"""
        self.logger.info("review_analyzer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify which competitors to analyze
        competitors_to_analyze = self._identify_competitors(message, state)

        # Analyze reviews for each competitor
        review_analyses = []
        for competitor in competitors_to_analyze:
            analysis = self._analyze_competitor_reviews(competitor)
            review_analyses.append(analysis)

        # Generate comparative insights
        comparative_insights = self._generate_comparative_insights(review_analyses)

        # Extract opportunities and threats
        opportunities = self._extract_opportunities(review_analyses)
        threats = self._extract_threats(review_analyses)

        # Generate battle card recommendations
        battle_card_points = self._generate_battle_card_points(review_analyses)

        # Generate positioning recommendations
        positioning_recommendations = self._generate_positioning(
            review_analyses,
            opportunities,
            threats
        )

        # Calculate insight confidence
        confidence = self._calculate_confidence(review_analyses)

        # Update state
        state["review_analyses"] = review_analyses
        state["comparative_insights"] = comparative_insights
        state["competitive_opportunities"] = opportunities
        state["competitive_threats"] = threats
        state["battle_card_points"] = battle_card_points
        state["positioning_recommendations"] = positioning_recommendations
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "review_analyzer_completed",
            competitors_analyzed=len(review_analyses),
            opportunities_found=len(opportunities),
            threats_identified=len(threats)
        )

        return state

    def _identify_competitors(self, message: str, state: AgentState) -> List[str]:
        """Identify which competitors to analyze"""
        message_lower = message.lower()
        competitors = []

        # Check if specific competitors mentioned
        for competitor_key in self.COMPETITOR_REVIEWS.keys():
            if competitor_key in message_lower:
                competitors.append(competitor_key)

        # If no specific competitors mentioned, use from state or analyze all major ones
        if not competitors:
            competitors = state.get("mentioned_competitors", [])

        # If still empty, analyze top 3 competitors
        if not competitors:
            competitors = ["salesforce", "hubspot", "zendesk"]

        return competitors

    def _analyze_competitor_reviews(self, competitor: str) -> Dict[str, Any]:
        """Analyze reviews for a specific competitor"""
        review_data = self.COMPETITOR_REVIEWS.get(competitor, {})

        if not review_data:
            # Return generic analysis if competitor not in database
            return {
                "competitor": competitor,
                "competitor_name": competitor.title(),
                "overall_rating": 4.0,
                "total_reviews": 1000,
                "common_positives": ["Established solution", "Decent features"],
                "common_negatives": ["Limited information available"],
                "key_themes": {},
                "strengths": [],
                "weaknesses": []
            }

        # Analyze strengths (high-scoring themes)
        strengths = []
        weaknesses = []

        for theme, theme_data in review_data.get("key_themes", {}).items():
            theme_score = theme_data.get("score", 0)
            theme_sentiment = theme_data.get("sentiment", "neutral")

            if theme_score >= 4.3:
                strengths.append({
                    "theme": theme.replace("_", " ").title(),
                    "score": theme_score,
                    "sentiment": theme_sentiment,
                    "insight": f"Strong performance in {theme.replace('_', ' ')}"
                })
            elif theme_score <= 3.5:
                weaknesses.append({
                    "theme": theme.replace("_", " ").title(),
                    "score": theme_score,
                    "sentiment": theme_sentiment,
                    "insight": f"Weakness in {theme.replace('_', ' ')}"
                })

        return {
            "competitor": competitor,
            "competitor_name": review_data.get("competitor_name", competitor.title()),
            "overall_rating": review_data.get("overall_rating", 0),
            "total_reviews": review_data.get("total_reviews", 0),
            "review_credibility": "high" if review_data.get("total_reviews", 0) > 1000 else "medium",
            "common_positives": review_data.get("common_positives", []),
            "common_negatives": review_data.get("common_negatives", []),
            "key_themes": review_data.get("key_themes", {}),
            "strengths": strengths,
            "weaknesses": weaknesses
        }

    def _generate_comparative_insights(self, review_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate comparative insights across competitors"""
        insights = []

        # Compare ratings
        avg_competitor_rating = sum(r["overall_rating"] for r in review_analyses) / len(review_analyses) if review_analyses else 0

        insights.append({
            "category": "overall_satisfaction",
            "insight": f"Average competitor rating: {avg_competitor_rating:.1f}/5.0",
            "implication": "Our target is to maintain 4.5+ rating to stay competitive"
        })

        # Identify common weaknesses across competitors
        weakness_themes = {}
        for analysis in review_analyses:
            for weakness in analysis.get("weaknesses", []):
                theme = weakness["theme"]
                weakness_themes[theme] = weakness_themes.get(theme, 0) + 1

        # Common weaknesses are opportunities
        for theme, count in weakness_themes.items():
            if count >= 2:  # Weakness shared by multiple competitors
                insights.append({
                    "category": "opportunity",
                    "insight": f"Multiple competitors struggle with {theme}",
                    "implication": f"Opportunity to differentiate on {theme}"
                })

        # Identify common strengths
        strength_themes = {}
        for analysis in review_analyses:
            for strength in analysis.get("strengths", []):
                theme = strength["theme"]
                strength_themes[theme] = strength_themes.get(theme, 0) + 1

        # Common strengths are table stakes
        for theme, count in strength_themes.items():
            if count >= 2:
                insights.append({
                    "category": "table_stakes",
                    "insight": f"Multiple competitors excel at {theme}",
                    "implication": f"Must match or exceed competitor performance on {theme}"
                })

        return insights

    def _extract_opportunities(self, review_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Extract competitive opportunities from review analysis"""
        opportunities = []

        for analysis in review_analyses:
            competitor = analysis["competitor_name"]

            # Each weakness is an opportunity
            for weakness in analysis.get("weaknesses", []):
                opportunities.append({
                    "type": "weakness_exploitation",
                    "competitor": competitor,
                    "theme": weakness["theme"],
                    "description": f"{competitor} struggles with {weakness['theme']} (score: {weakness['score']:.1f}/5)",
                    "our_positioning": f"Emphasize our superior {weakness['theme']}",
                    "priority": "high" if weakness["score"] < 3.0 else "medium"
                })

            # Specific negatives from reviews
            for i, negative in enumerate(analysis.get("common_negatives", [])[:3]):  # Top 3
                opportunities.append({
                    "type": "pain_point_addressing",
                    "competitor": competitor,
                    "pain_point": negative,
                    "description": f"Common complaint: '{negative}'",
                    "our_positioning": f"We solve this by...",
                    "priority": "high" if i == 0 else "medium"
                })

        return opportunities

    def _extract_threats(self, review_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Extract competitive threats from review analysis"""
        threats = []

        for analysis in review_analyses:
            competitor = analysis["competitor_name"]

            # Each strength is a potential threat
            for strength in analysis.get("strengths", []):
                threats.append({
                    "type": "competitor_strength",
                    "competitor": competitor,
                    "theme": strength["theme"],
                    "description": f"{competitor} excels at {strength['theme']} (score: {strength['score']:.1f}/5)",
                    "mitigation": f"Ensure we match or explain our approach to {strength['theme']}",
                    "severity": "high" if strength["score"] > 4.5 else "medium"
                })

        return threats

    def _generate_battle_card_points(self, review_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Generate battle card talking points from review analysis"""
        battle_points = []

        for analysis in review_analyses:
            competitor = analysis["competitor_name"]

            # Create battle card section for this competitor
            battle_card = {
                "competitor": competitor,
                "overall_rating": analysis["overall_rating"],
                "when_to_use": f"When competing against {competitor}",
                "their_strengths": [p for p in analysis.get("common_positives", [])[:3]],
                "their_weaknesses": [n for n in analysis.get("common_negatives", [])[:3]],
                "our_talking_points": [],
                "objection_handlers": []
            }

            # Generate talking points based on their weaknesses
            for weakness in analysis.get("weaknesses", [])[:3]:
                battle_card["our_talking_points"].append(
                    f"While {competitor} {weakness['insight'].lower()}, we excel in this area"
                )

            # Generate objection handlers for their strengths
            for strength in analysis.get("strengths", [])[:2]:
                battle_card["objection_handlers"].append({
                    "objection": f"But {competitor} is known for {strength['theme']}",
                    "response": f"Yes, they do well there. We match their capabilities and also provide..."
                })

            battle_points.append(battle_card)

        return battle_points

    def _generate_positioning(
        self,
        review_analyses: List[Dict],
        opportunities: List[Dict],
        threats: List[Dict]
    ) -> List[str]:
        """Generate positioning recommendations"""
        recommendations = []

        # Based on common weaknesses
        common_weaknesses = {}
        for analysis in review_analyses:
            for negative in analysis.get("common_negatives", []):
                common_weaknesses[negative] = common_weaknesses.get(negative, 0) + 1

        for weakness, count in sorted(common_weaknesses.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count >= 2:
                recommendations.append(
                    f"Position as solving: '{weakness}' (common complaint across {count} competitors)"
                )

        # Based on opportunities
        high_priority_opps = [o for o in opportunities if o.get("priority") == "high"]
        if high_priority_opps:
            recommendations.append(
                f"Emphasize {len(high_priority_opps)} high-priority differentiators in competitive situations"
            )

        # Based on threats
        high_severity_threats = [t for t in threats if t.get("severity") == "high"]
        if high_severity_threats:
            recommendations.append(
                f"Prepare responses for {len(high_severity_threats)} areas where competitors excel"
            )

        # General positioning
        recommendations.append("Lead with ease of use and value - common pain points across competitors")
        recommendations.append("Use third-party review data to validate competitive claims")

        return recommendations

    def _calculate_confidence(self, review_analyses: List[Dict]) -> float:
        """Calculate confidence in review analysis"""
        if not review_analyses:
            return 0.5

        # Higher confidence with more reviews analyzed
        total_reviews = sum(a.get("total_reviews", 0) for a in review_analyses)

        base_confidence = 0.75

        # Boost confidence based on review volume
        if total_reviews > 10000:
            base_confidence += 0.15
        elif total_reviews > 5000:
            base_confidence += 0.10
        elif total_reviews > 1000:
            base_confidence += 0.05

        return min(base_confidence, 0.95)


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing ReviewAnalyzer Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Analyze specific competitor
        state1 = create_initial_state(
            "What do customers say about Salesforce in reviews? Any common complaints?",
            context={
                "customer_metadata": {
                    "company": "TechCorp",
                    "industry": "technology"
                }
            }
        )

        agent = ReviewAnalyzer()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Salesforce Review Analysis")
        print(f"Competitors Analyzed: {len(result1['review_analyses'])}")
        for analysis in result1['review_analyses']:
            print(f"\n{analysis['competitor_name']}:")
            print(f"  Overall Rating: {analysis['overall_rating']}/5.0")
            print(f"  Total Reviews: {analysis['total_reviews']:,}")
            print(f"  Strengths: {len(analysis['strengths'])}")
            print(f"  Weaknesses: {len(analysis['weaknesses'])}")
            print(f"  Top Weaknesses:")
            for weakness in analysis['weaknesses'][:3]:
                print(f"    - {weakness['insight']} ({weakness['score']:.1f}/5)")

        print(f"\nOpportunities Found: {len(result1['competitive_opportunities'])}")
        for opp in result1['competitive_opportunities'][:3]:
            print(f"  - {opp['description']}")

        # Test case 2: Compare multiple competitors
        state2 = create_initial_state(
            "How do HubSpot and Intercom compare based on customer reviews?",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "industry": "saas"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - HubSpot vs Intercom Review Comparison")
        print(f"Competitors Analyzed: {len(result2['review_analyses'])}")
        print(f"\nComparative Insights:")
        for insight in result2['comparative_insights'][:4]:
            print(f"  [{insight['category'].upper()}] {insight['insight']}")
            print(f"    → {insight['implication']}")

        print(f"\nBattle Card Points Generated: {len(result2['battle_card_points'])}")
        for bc in result2['battle_card_points']:
            print(f"\n  {bc['competitor']}:")
            print(f"    Weaknesses to exploit: {len(bc['their_weaknesses'])}")
            print(f"    Talking points: {len(bc['our_talking_points'])}")

        # Test case 3: General competitive review analysis
        state3 = create_initial_state(
            "I want to understand the competitive landscape based on customer reviews",
            context={}
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - General Competitive Landscape")
        print(f"Competitors Analyzed: {len(result3['review_analyses'])}")
        print(f"\nPositioning Recommendations:")
        for rec in result3['positioning_recommendations']:
            print(f"  • {rec}")
        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
