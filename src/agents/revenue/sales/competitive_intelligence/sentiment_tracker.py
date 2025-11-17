"""
Sentiment Tracker Agent - TASK-1053

Tracks competitor sentiment on social media, monitors forums and communities,
identifies sentiment shifts, and generates sentiment reports.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("sentiment_tracker", tier="revenue", category="sales")
class SentimentTracker(BaseAgent):
    """
    Sentiment Tracker Agent - Monitors competitor sentiment across social media and communities.

    Handles:
    - Track competitor sentiment on social media
    - Monitor forums and communities
    - Identify sentiment shifts and trends
    - Generate sentiment reports
    - Alert on significant sentiment changes
    """

    # Social media and community platforms
    PLATFORMS = {
        "twitter": {
            "name": "Twitter/X",
            "weight": 1.3,
            "reach": "high",
            "real_time": True,
            "sentiment_volatility": "high"
        },
        "reddit": {
            "name": "Reddit",
            "weight": 1.5,
            "reach": "high",
            "real_time": False,
            "sentiment_volatility": "medium",
            "key_subreddits": ["r/saas", "r/sales", "r/startup", "r/entrepreneur"]
        },
        "linkedin": {
            "name": "LinkedIn",
            "weight": 1.2,
            "reach": "medium",
            "real_time": False,
            "sentiment_volatility": "low",
            "audience": "professional"
        },
        "hacker_news": {
            "name": "Hacker News",
            "weight": 1.6,
            "reach": "medium",
            "real_time": True,
            "sentiment_volatility": "medium",
            "audience": "technical"
        },
        "product_hunt": {
            "name": "Product Hunt",
            "weight": 1.4,
            "reach": "medium",
            "real_time": False,
            "sentiment_volatility": "medium",
            "audience": "product_makers"
        },
        "facebook": {
            "name": "Facebook",
            "weight": 1.0,
            "reach": "medium",
            "real_time": False,
            "sentiment_volatility": "low"
        }
    }

    # Sentiment categories
    SENTIMENT_CATEGORIES = {
        "very_positive": {"score": 5, "emoji": "🟢", "label": "Very Positive"},
        "positive": {"score": 4, "emoji": "🟢", "label": "Positive"},
        "neutral": {"score": 3, "emoji": "🟡", "label": "Neutral"},
        "negative": {"score": 2, "emoji": "🔴", "label": "Negative"},
        "very_negative": {"score": 1, "emoji": "🔴", "label": "Very Negative"}
    }

    # Competitor sentiment profiles (sample tracked data)
    COMPETITOR_SENTIMENT = {
        "salesforce": {
            "current_sentiment": "neutral",
            "sentiment_score": 3.2,
            "trend": "stable",
            "mentions_last_30d": 1250,
            "sentiment_breakdown": {
                "very_positive": 15,
                "positive": 30,
                "neutral": 35,
                "negative": 15,
                "very_negative": 5
            },
            "recent_topics": [
                {"topic": "pricing", "sentiment": "negative", "volume": "high"},
                {"topic": "features", "sentiment": "positive", "volume": "medium"},
                {"topic": "complexity", "sentiment": "negative", "volume": "high"},
                {"topic": "market_leader", "sentiment": "positive", "volume": "medium"}
            ],
            "viral_posts": [
                {
                    "platform": "twitter",
                    "summary": "Thread about Salesforce implementation costs",
                    "sentiment": "negative",
                    "reach": 50000,
                    "date": "2024-01-10"
                }
            ]
        },
        "hubspot": {
            "current_sentiment": "positive",
            "sentiment_score": 4.1,
            "trend": "declining",
            "mentions_last_30d": 980,
            "sentiment_breakdown": {
                "very_positive": 25,
                "positive": 40,
                "neutral": 25,
                "negative": 8,
                "very_negative": 2
            },
            "recent_topics": [
                {"topic": "ease_of_use", "sentiment": "positive", "volume": "high"},
                {"topic": "pricing_scale", "sentiment": "negative", "volume": "medium"},
                {"topic": "free_tier", "sentiment": "positive", "volume": "medium"},
                {"topic": "enterprise_features", "sentiment": "negative", "volume": "low"}
            ],
            "viral_posts": [
                {
                    "platform": "reddit",
                    "summary": "r/saas discussion about HubSpot pricing increases",
                    "sentiment": "negative",
                    "reach": 15000,
                    "date": "2024-01-12"
                }
            ]
        },
        "zendesk": {
            "current_sentiment": "neutral",
            "sentiment_score": 3.4,
            "trend": "stable",
            "mentions_last_30d": 450,
            "sentiment_breakdown": {
                "very_positive": 12,
                "positive": 35,
                "neutral": 38,
                "negative": 12,
                "very_negative": 3
            },
            "recent_topics": [
                {"topic": "product_suite", "sentiment": "neutral", "volume": "medium"},
                {"topic": "pricing", "sentiment": "negative", "volume": "low"},
                {"topic": "support", "sentiment": "positive", "volume": "medium"},
                {"topic": "ui_ux", "sentiment": "negative", "volume": "low"}
            ],
            "viral_posts": []
        },
        "intercom": {
            "current_sentiment": "mixed",
            "sentiment_score": 3.5,
            "trend": "declining",
            "mentions_last_30d": 380,
            "sentiment_breakdown": {
                "very_positive": 20,
                "positive": 30,
                "neutral": 25,
                "negative": 20,
                "very_negative": 5
            },
            "recent_topics": [
                {"topic": "modern_ui", "sentiment": "positive", "volume": "medium"},
                {"topic": "pricing", "sentiment": "very_negative", "volume": "very_high"},
                {"topic": "customer_messaging", "sentiment": "positive", "volume": "medium"},
                {"topic": "conversation_limits", "sentiment": "negative", "volume": "high"}
            ],
            "viral_posts": [
                {
                    "platform": "twitter",
                    "summary": "Tweet thread on Intercom pricing frustrations",
                    "sentiment": "very_negative",
                    "reach": 35000,
                    "date": "2024-01-08"
                }
            ]
        },
        "freshdesk": {
            "current_sentiment": "positive",
            "sentiment_score": 3.8,
            "trend": "improving",
            "mentions_last_30d": 220,
            "sentiment_breakdown": {
                "very_positive": 18,
                "positive": 42,
                "neutral": 30,
                "negative": 8,
                "very_negative": 2
            },
            "recent_topics": [
                {"topic": "value", "sentiment": "positive", "volume": "high"},
                {"topic": "simplicity", "sentiment": "positive", "volume": "medium"},
                {"topic": "limited_features", "sentiment": "negative", "volume": "low"},
                {"topic": "good_for_smb", "sentiment": "positive", "volume": "medium"}
            ],
            "viral_posts": []
        }
    }

    # Sentiment shift thresholds
    SHIFT_THRESHOLDS = {
        "major_positive": 0.5,  # +0.5 or more
        "minor_positive": 0.2,
        "stable": 0.2,
        "minor_negative": -0.2,
        "major_negative": -0.5  # -0.5 or more
    }

    # Alert triggers
    ALERT_TRIGGERS = {
        "viral_negative": {
            "threshold": 10000,
            "description": "Viral negative post about competitor"
        },
        "sentiment_crash": {
            "threshold": -0.5,
            "description": "Major negative sentiment shift"
        },
        "topic_spike": {
            "threshold": 100,
            "description": "Spike in mentions of specific topic"
        },
        "trend_reversal": {
            "description": "Sentiment trend reversal"
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="sentiment_tracker",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20240620",
            temperature=0.3,
            max_tokens=1200,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process sentiment tracking"""
        self.logger.info("sentiment_tracker_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify competitors to track
        competitors_to_track = self._identify_competitors(message, state)

        # Track sentiment for each competitor
        sentiment_reports = []
        for competitor in competitors_to_track:
            report = self._generate_sentiment_report(competitor)
            sentiment_reports.append(report)

        # Identify sentiment shifts
        sentiment_shifts = self._identify_shifts(sentiment_reports)

        # Identify trending topics
        trending_topics = self._identify_trending_topics(sentiment_reports)

        # Generate alerts
        alerts = self._generate_alerts(sentiment_reports, sentiment_shifts)

        # Generate insights
        insights = self._generate_insights(
            sentiment_reports,
            sentiment_shifts,
            trending_topics
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            sentiment_reports,
            sentiment_shifts,
            trending_topics
        )

        # Calculate confidence
        confidence = self._calculate_confidence(sentiment_reports)

        # Update state
        state["sentiment_reports"] = sentiment_reports
        state["sentiment_shifts"] = sentiment_shifts
        state["trending_topics"] = trending_topics
        state["sentiment_alerts"] = alerts
        state["sentiment_insights"] = insights
        state["sentiment_recommendations"] = recommendations
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "sentiment_tracker_completed",
            competitors_tracked=len(sentiment_reports),
            shifts_identified=len(sentiment_shifts),
            alerts_generated=len(alerts)
        )

        return state

    def _identify_competitors(self, message: str, state: AgentState) -> List[str]:
        """Identify which competitors to track"""
        message_lower = message.lower()
        competitors = []

        # Check for specific mentions
        for competitor in self.COMPETITOR_SENTIMENT.keys():
            if competitor in message_lower:
                competitors.append(competitor)

        # Use from state if available
        if not competitors:
            competitors = state.get("mentioned_competitors", [])

        # Default to tracking all major competitors
        if not competitors:
            competitors = list(self.COMPETITOR_SENTIMENT.keys())

        return competitors

    def _generate_sentiment_report(self, competitor: str) -> Dict[str, Any]:
        """Generate sentiment report for a competitor"""
        sentiment_data = self.COMPETITOR_SENTIMENT.get(competitor, {})

        if not sentiment_data:
            return {
                "competitor": competitor,
                "competitor_name": competitor.title(),
                "data_available": False
            }

        # Calculate weighted sentiment score
        breakdown = sentiment_data.get("sentiment_breakdown", {})
        total_mentions = sum(breakdown.values()) if breakdown else 0

        return {
            "competitor": competitor,
            "competitor_name": competitor.title(),
            "data_available": True,
            "current_sentiment": sentiment_data.get("current_sentiment", "neutral"),
            "sentiment_score": sentiment_data.get("sentiment_score", 3.0),
            "trend": sentiment_data.get("trend", "stable"),
            "mentions_last_30d": sentiment_data.get("mentions_last_30d", 0),
            "sentiment_breakdown": breakdown,
            "total_mentions": total_mentions,
            "recent_topics": sentiment_data.get("recent_topics", []),
            "viral_posts": sentiment_data.get("viral_posts", []),
            "platforms_tracked": len(self.PLATFORMS),
            "last_updated": datetime.now(UTC).isoformat()
        }

    def _identify_shifts(self, sentiment_reports: List[Dict]) -> List[Dict[str, Any]]:
        """Identify significant sentiment shifts"""
        shifts = []

        for report in sentiment_reports:
            if not report.get("data_available"):
                continue

            trend = report.get("trend", "stable")
            current_score = report.get("sentiment_score", 3.0)

            # In a real system, we'd compare to historical data
            # For demo, we'll use the trend indicator
            if trend == "declining":
                shift_magnitude = -0.3
                shift_type = "minor_negative"
            elif trend == "improving":
                shift_magnitude = 0.3
                shift_type = "minor_positive"
            else:
                shift_magnitude = 0.0
                shift_type = "stable"

            if abs(shift_magnitude) >= 0.2:
                shifts.append({
                    "competitor": report["competitor_name"],
                    "shift_type": shift_type,
                    "shift_magnitude": shift_magnitude,
                    "current_score": current_score,
                    "trend": trend,
                    "significance": "high" if abs(shift_magnitude) >= 0.5 else "medium"
                })

        return shifts

    def _identify_trending_topics(self, sentiment_reports: List[Dict]) -> List[Dict[str, Any]]:
        """Identify trending topics across competitors"""
        all_topics = []

        for report in sentiment_reports:
            if not report.get("data_available"):
                continue

            for topic in report.get("recent_topics", []):
                all_topics.append({
                    "competitor": report["competitor_name"],
                    "topic": topic["topic"],
                    "sentiment": topic["sentiment"],
                    "volume": topic["volume"],
                    "volume_score": self._volume_to_score(topic["volume"])
                })

        # Sort by volume and sentiment
        trending = sorted(
            all_topics,
            key=lambda x: x["volume_score"],
            reverse=True
        )

        return trending[:10]  # Top 10 trending topics

    def _volume_to_score(self, volume: str) -> int:
        """Convert volume description to numeric score"""
        volume_map = {
            "very_high": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "very_low": 1
        }
        return volume_map.get(volume, 3)

    def _generate_alerts(
        self,
        sentiment_reports: List[Dict],
        sentiment_shifts: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate alerts for significant sentiment events"""
        alerts = []

        # Check for viral posts
        for report in sentiment_reports:
            for viral_post in report.get("viral_posts", []):
                if viral_post["reach"] >= self.ALERT_TRIGGERS["viral_negative"]["threshold"]:
                    alerts.append({
                        "alert_type": "viral_negative",
                        "severity": "high",
                        "competitor": report["competitor_name"],
                        "description": f"Viral negative post about {report['competitor_name']}",
                        "details": viral_post,
                        "action": "Monitor and prepare response if customers ask"
                    })

        # Check for major sentiment shifts
        for shift in sentiment_shifts:
            if shift["significance"] == "high":
                alerts.append({
                    "alert_type": "sentiment_shift",
                    "severity": "medium",
                    "competitor": shift["competitor"],
                    "description": f"{shift['shift_type'].replace('_', ' ').title()} for {shift['competitor']}",
                    "details": shift,
                    "action": "Investigate cause and adjust positioning"
                })

        return alerts

    def _generate_insights(
        self,
        sentiment_reports: List[Dict],
        sentiment_shifts: List[Dict],
        trending_topics: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate insights from sentiment data"""
        insights = []

        # Overall sentiment landscape
        if sentiment_reports:
            avg_sentiment = sum(r.get("sentiment_score", 3.0) for r in sentiment_reports if r.get("data_available")) / len([r for r in sentiment_reports if r.get("data_available")])
            insights.append({
                "type": "landscape",
                "insight": f"Average competitor sentiment: {avg_sentiment:.1f}/5.0",
                "implication": "Overall competitive sentiment is neutral to positive"
            })

        # Negative trending topics are opportunities
        negative_trending = [t for t in trending_topics if t["sentiment"] in ["negative", "very_negative"]]
        if negative_trending:
            top_negative = negative_trending[0]
            insights.append({
                "type": "opportunity",
                "insight": f"{top_negative['competitor']} facing negative sentiment on '{top_negative['topic']}'",
                "implication": f"Opportunity to differentiate on {top_negative['topic'].replace('_', ' ')}"
            })

        # Declining sentiment
        declining = [s for s in sentiment_shifts if "negative" in s["shift_type"]]
        if declining:
            for shift in declining[:2]:  # Top 2
                insights.append({
                    "type": "competitive_weakness",
                    "insight": f"{shift['competitor']} sentiment declining",
                    "implication": "May indicate product/service issues - investigate and position accordingly"
                })

        # Improving competitor sentiment
        improving = [s for s in sentiment_shifts if "positive" in s["shift_type"]]
        if improving:
            for shift in improving[:2]:
                insights.append({
                    "type": "threat",
                    "insight": f"{shift['competitor']} sentiment improving",
                    "implication": "Monitor their recent changes - may need to respond"
                })

        return insights

    def _generate_recommendations(
        self,
        sentiment_reports: List[Dict],
        sentiment_shifts: List[Dict],
        trending_topics: List[Dict]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on negative trending topics
        negative_trending = [t for t in trending_topics[:5] if t["sentiment"] in ["negative", "very_negative"]]
        if negative_trending:
            topics = set(t["topic"] for t in negative_trending)
            recommendations.append(
                f"Emphasize our strengths in: {', '.join(t.replace('_', ' ') for t in topics)}"
            )

        # Based on viral posts
        viral_posts_count = sum(len(r.get("viral_posts", [])) for r in sentiment_reports)
        if viral_posts_count > 0:
            recommendations.append(
                f"Prepare FAQs for {viral_posts_count} viral competitor discussions"
            )

        # Based on sentiment shifts
        if sentiment_shifts:
            recommendations.append(
                "Update competitive intelligence with latest sentiment trends"
            )

        # General recommendations
        recommendations.append("Monitor social channels daily for competitor sentiment changes")
        recommendations.append("Use negative competitor sentiment in sales conversations tactfully")

        return recommendations

    def _calculate_confidence(self, sentiment_reports: List[Dict]) -> float:
        """Calculate confidence in sentiment analysis"""
        if not sentiment_reports:
            return 0.5

        # Confidence based on data availability and mention volume
        available_reports = [r for r in sentiment_reports if r.get("data_available")]
        if not available_reports:
            return 0.5

        total_mentions = sum(r.get("mentions_last_30d", 0) for r in available_reports)

        base_confidence = 0.80

        # More mentions = higher confidence
        if total_mentions > 2000:
            base_confidence += 0.10
        elif total_mentions > 1000:
            base_confidence += 0.05

        return min(base_confidence, 0.95)


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing SentimentTracker Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Track specific competitor sentiment
        state1 = create_initial_state(
            "What's the current sentiment around HubSpot on social media?",
            context={
                "customer_metadata": {
                    "company": "TechCorp",
                    "industry": "technology"
                }
            }
        )

        agent = SentimentTracker()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - HubSpot Sentiment Tracking")
        for report in result1['sentiment_reports']:
            if report['competitor'] == 'hubspot':
                print(f"\n{report['competitor_name']}:")
                print(f"  Current Sentiment: {report['current_sentiment'].upper()}")
                print(f"  Sentiment Score: {report['sentiment_score']:.1f}/5.0")
                print(f"  Trend: {report['trend'].upper()}")
                print(f"  Mentions (30d): {report['mentions_last_30d']:,}")
                print(f"  Sentiment Breakdown:")
                for sent, pct in report['sentiment_breakdown'].items():
                    print(f"    {sent}: {pct}%")
                print(f"  Recent Topics:")
                for topic in report['recent_topics'][:3]:
                    print(f"    - {topic['topic'].replace('_', ' ').title()}: {topic['sentiment']} ({topic['volume']} volume)")

        # Test case 2: Identify sentiment shifts
        state2 = create_initial_state(
            "Are there any major sentiment changes for our competitors?",
            context={}
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - Sentiment Shift Detection")
        print(f"Competitors Tracked: {len(result2['sentiment_reports'])}")
        print(f"Sentiment Shifts Identified: {len(result2['sentiment_shifts'])}")
        for shift in result2['sentiment_shifts']:
            print(f"\n  {shift['competitor']}:")
            print(f"    Shift Type: {shift['shift_type'].replace('_', ' ').title()}")
            print(f"    Magnitude: {shift['shift_magnitude']:+.1f}")
            print(f"    Current Score: {shift['current_score']:.1f}/5.0")
            print(f"    Significance: {shift['significance'].upper()}")

        print(f"\nAlerts Generated: {len(result2['sentiment_alerts'])}")
        for alert in result2['sentiment_alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['description']}")

        # Test case 3: Trending topics analysis
        state3 = create_initial_state(
            "What topics are trending in competitor discussions?",
            context={}
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - Trending Topics")
        print(f"Trending Topics (Top 5):")
        for i, topic in enumerate(result3['trending_topics'][:5], 1):
            emoji = "🔴" if "negative" in topic['sentiment'] else "🟢" if "positive" in topic['sentiment'] else "🟡"
            print(f"  {i}. {emoji} {topic['competitor']}: {topic['topic'].replace('_', ' ').title()}")
            print(f"     Sentiment: {topic['sentiment']}, Volume: {topic['volume']}")

        print(f"\nInsights:")
        for insight in result3['sentiment_insights']:
            print(f"  [{insight['type'].upper()}] {insight['insight']}")
            print(f"    → {insight['implication']}")

        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
