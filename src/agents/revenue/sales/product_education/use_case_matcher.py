"""
Use Case Matcher Agent - TASK-1022

Matches prospect's needs to relevant use cases and customer stories.
Recommends features and provides implementation approaches.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("use_case_matcher", tier="revenue", category="sales")
class UseCaseMatcher(BaseAgent):
    """
    Use Case Matcher Agent - Specialist in matching needs to use cases.

    Handles:
    - Matching prospect needs to relevant use cases
    - Finding similar customer success stories
    - Recommending relevant features for their scenario
    - Providing implementation approaches
    - ROI projections based on similar customers
    """

    # Use case library organized by industry
    USE_CASE_LIBRARY = {
        "technology": [
            {
                "name": "Developer Workflow Automation",
                "pain_points": ["manual_deployments", "slow_ci_cd", "integration_gaps"],
                "features": ["api_integration", "webhooks", "automation", "ci_cd_tools"],
                "roi_impact": "60% faster deployment cycles",
                "customer_example": "TechCorp reduced deployment time by 65%"
            },
            {
                "name": "Customer Data Integration",
                "pain_points": ["data_silos", "disconnected_tools", "reporting_delays"],
                "features": ["data_sync", "real_time_analytics", "unified_dashboard"],
                "roi_impact": "80% reduction in data consolidation time",
                "customer_example": "DataCo unified 12 data sources into one platform"
            }
        ],
        "healthcare": [
            {
                "name": "Patient Data Management",
                "pain_points": ["compliance_burden", "manual_records", "security_concerns"],
                "features": ["hipaa_compliance", "encryption", "audit_logs", "access_control"],
                "roi_impact": "95% compliance accuracy, zero breaches",
                "customer_example": "HealthPlus secured 500k patient records seamlessly"
            },
            {
                "name": "Appointment Automation",
                "pain_points": ["no_shows", "manual_scheduling", "staff_overhead"],
                "features": ["automated_reminders", "smart_scheduling", "patient_portal"],
                "roi_impact": "40% reduction in no-shows",
                "customer_example": "CareClinic reduced no-shows by 45% in 3 months"
            }
        ],
        "finance": [
            {
                "name": "Regulatory Compliance Automation",
                "pain_points": ["compliance_overhead", "audit_preparation", "reporting_burden"],
                "features": ["sox_compliance", "audit_trails", "automated_reporting", "data_governance"],
                "roi_impact": "70% faster compliance reporting",
                "customer_example": "FinanceFirst cut audit prep time from 2 weeks to 3 days"
            },
            {
                "name": "Fraud Detection & Prevention",
                "pain_points": ["fraud_risk", "manual_review", "false_positives"],
                "features": ["ai_detection", "real_time_alerts", "pattern_analysis"],
                "roi_impact": "85% fraud detection rate with 50% fewer false positives",
                "customer_example": "SecureBank prevented $2M in fraud in first quarter"
            }
        ],
        "retail": [
            {
                "name": "Inventory Optimization",
                "pain_points": ["stockouts", "overstock", "manual_tracking", "shrinkage"],
                "features": ["inventory_tracking", "predictive_analytics", "auto_reorder"],
                "roi_impact": "30% reduction in carrying costs",
                "customer_example": "RetailCo reduced stockouts by 75% and overstock by 40%"
            }
        ],
        "manufacturing": [
            {
                "name": "Production Quality Control",
                "pain_points": ["defect_rates", "manual_inspection", "recall_risk"],
                "features": ["quality_tracking", "iot_sensors", "predictive_maintenance"],
                "roi_impact": "50% reduction in defect rates",
                "customer_example": "ManufacturePro reduced defects by 60% using AI inspection"
            }
        ]
    }

    # Pain point keywords for matching
    PAIN_POINT_KEYWORDS = {
        "manual_deployments": ["manual", "deploy", "release", "slow"],
        "data_silos": ["silos", "disconnected", "fragmented", "separate systems"],
        "compliance_burden": ["compliance", "regulatory", "audit", "sox", "hipaa"],
        "stockouts": ["out of stock", "inventory", "stockout", "shortage"],
        "fraud_risk": ["fraud", "security", "risk", "breach"],
        "slow_ci_cd": ["slow", "ci/cd", "pipeline", "build time"],
        "manual_scheduling": ["scheduling", "calendar", "appointments", "manual"],
        "defect_rates": ["defects", "quality", "errors", "failures"]
    }

    # Match confidence thresholds
    MATCH_CONFIDENCE_HIGH = 0.8
    MATCH_CONFIDENCE_MEDIUM = 0.5

    def __init__(self):
        config = AgentConfig(
            name="use_case_matcher",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",
            temperature=0.4,
            max_tokens=1200,
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
        """Process use case matching request"""
        self.logger.info("use_case_matcher_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        conversation_history = state.get("messages", [])

        # Extract pain points from conversation
        pain_points = self._extract_pain_points(message, conversation_history)

        # Find matching use cases
        matched_use_cases = self._match_use_cases(
            pain_points,
            customer_metadata
        )

        # Get recommended features
        recommended_features = self._get_recommended_features(matched_use_cases)

        # Generate implementation approach
        implementation_approach = self._generate_implementation_approach(
            matched_use_cases,
            customer_metadata
        )

        # Search KB for case studies
        kb_results = await self.search_knowledge_base(
            f"case study {customer_metadata.get('industry', '')} {' '.join(pain_points)}",
            category="sales",
            limit=5
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_use_case_response(
            message,
            pain_points,
            matched_use_cases,
            recommended_features,
            implementation_approach,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["identified_pain_points"] = pain_points
        state["matched_use_cases"] = matched_use_cases
        state["recommended_features"] = recommended_features
        state["implementation_approach"] = implementation_approach
        state["status"] = "resolved"

        self.logger.info(
            "use_case_matcher_completed",
            pain_points_count=len(pain_points),
            matches_count=len(matched_use_cases)
        )

        return state

    def _extract_pain_points(
        self,
        message: str,
        conversation_history: List[Dict]
    ) -> List[str]:
        """Extract pain points from conversation"""
        pain_points = []

        # Combine all text
        all_text = message.lower()
        for msg in conversation_history:
            if msg.get("content"):
                all_text += " " + msg["content"].lower()

        # Match against pain point keywords
        for pain_point, keywords in self.PAIN_POINT_KEYWORDS.items():
            if any(keyword in all_text for keyword in keywords):
                pain_points.append(pain_point)

        # If no specific pain points found, add generic
        if not pain_points:
            pain_points.append("general_efficiency")

        return pain_points

    def _match_use_cases(
        self,
        pain_points: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Match prospect to relevant use cases"""
        matches = []
        industry = customer_metadata.get("industry", "other").lower()

        # Get use cases for prospect's industry
        industry_use_cases = self.USE_CASE_LIBRARY.get(industry, [])

        # Also check general/cross-industry use cases
        all_use_cases = industry_use_cases.copy()
        for other_industry, cases in self.USE_CASE_LIBRARY.items():
            if other_industry != industry:
                all_use_cases.extend(cases)

        # Score each use case based on pain point overlap
        for use_case in all_use_cases:
            use_case_pain_points = set(use_case["pain_points"])
            prospect_pain_points = set(pain_points)

            # Calculate overlap
            overlap = len(use_case_pain_points & prospect_pain_points)
            total = len(use_case_pain_points | prospect_pain_points)

            if total > 0:
                match_score = overlap / total
            else:
                match_score = 0.0

            if match_score >= self.MATCH_CONFIDENCE_MEDIUM:
                matches.append({
                    "use_case": use_case,
                    "match_score": match_score,
                    "matched_pain_points": list(use_case_pain_points & prospect_pain_points),
                    "is_industry_match": use_case in industry_use_cases
                })

        # Sort by match score (highest first)
        matches.sort(key=lambda x: (x["is_industry_match"], x["match_score"]), reverse=True)

        # Return top 3 matches
        return matches[:3]

    def _get_recommended_features(self, matched_use_cases: List[Dict]) -> List[str]:
        """Extract recommended features from matched use cases"""
        features = set()

        for match in matched_use_cases:
            use_case = match["use_case"]
            features.update(use_case["features"])

        return list(features)

    def _generate_implementation_approach(
        self,
        matched_use_cases: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate implementation approach based on matches"""
        if not matched_use_cases:
            return {
                "timeline": "4-6 weeks",
                "phases": ["Discovery", "Setup", "Training", "Go-live"],
                "complexity": "Medium"
            }

        # Use the highest-scoring match
        top_match = matched_use_cases[0]
        use_case = top_match["use_case"]

        # Determine complexity based on company size and features
        company_size = customer_metadata.get("company_size", 0)
        feature_count = len(use_case["features"])

        if company_size > 500 or feature_count > 5:
            complexity = "High"
            timeline = "8-12 weeks"
            phases = ["Discovery", "Architecture", "Phased Rollout", "Integration", "Training", "Go-live"]
        elif company_size > 100 or feature_count > 3:
            complexity = "Medium"
            timeline = "4-6 weeks"
            phases = ["Discovery", "Setup", "Integration", "Training", "Go-live"]
        else:
            complexity = "Low"
            timeline = "2-3 weeks"
            phases = ["Quick Setup", "Training", "Go-live"]

        return {
            "timeline": timeline,
            "phases": phases,
            "complexity": complexity,
            "primary_use_case": use_case["name"]
        }

    async def _generate_use_case_response(
        self,
        message: str,
        pain_points: List[str],
        matched_use_cases: List[Dict],
        recommended_features: List[str],
        implementation_approach: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate use case matching response"""

        # Build matched use cases context
        use_case_context = "\n\nMatched Use Cases:\n"
        for idx, match in enumerate(matched_use_cases, 1):
            use_case = match["use_case"]
            use_case_context += f"{idx}. {use_case['name']} (Match: {match['match_score']:.0%})\n"
            use_case_context += f"   - ROI Impact: {use_case['roi_impact']}\n"
            use_case_context += f"   - Customer Example: {use_case['customer_example']}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant case studies:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Case Study')}\n"

        # Build implementation context
        impl_context = f"\n\nImplementation Approach:\n"
        impl_context += f"- Timeline: {implementation_approach['timeline']}\n"
        impl_context += f"- Complexity: {implementation_approach['complexity']}\n"
        impl_context += f"- Phases: {', '.join(implementation_approach['phases'])}\n"

        system_prompt = f"""You are a Use Case Matcher specialist helping prospects see how our product solves their specific challenges.

Prospect Profile:
- Industry: {customer_metadata.get('industry', 'Unknown').title()}
- Company Size: {customer_metadata.get('company_size', 'Unknown')}
- Identified Pain Points: {', '.join(pain_points)}

Recommended Features: {', '.join(recommended_features)}

Your response should:
1. Acknowledge their specific pain points
2. Present the most relevant use case(s) with customer examples
3. Explain how recommended features address their needs
4. Provide realistic implementation timeline
5. Build confidence through similar customer success stories
6. Be specific and actionable, not generic"""

        user_prompt = f"""Customer message: {message}

{use_case_context}
{kb_context}
{impl_context}

Generate a compelling response that matches their needs to our solutions."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    """Test harness for UseCaseMatcher"""
    import asyncio
    from src.workflow.state import AgentState

    async def test_use_case_matcher():
        agent = UseCaseMatcher()

        # Test case 1: Healthcare compliance
        state1 = AgentState(
            current_message="We're struggling with HIPAA compliance and manual patient records. It's taking too much time.",
            customer_metadata={
                "title": "IT Director",
                "industry": "healthcare",
                "company_size": 300
            },
            messages=[],
            status="pending"
        )

        result1 = await agent.process(state1)
        print("Test 1 - Healthcare Compliance:")
        print(f"Pain Points: {result1['identified_pain_points']}")
        print(f"Matched Use Cases: {len(result1['matched_use_cases'])}")
        print(f"Implementation: {result1['implementation_approach']}")
        print()

        # Test case 2: Retail inventory
        state2 = AgentState(
            current_message="We keep running out of stock on popular items and have too much of slow-moving inventory.",
            customer_metadata={
                "title": "Operations Manager",
                "industry": "retail",
                "company_size": 150
            },
            messages=[],
            status="pending"
        )

        result2 = await agent.process(state2)
        print("Test 2 - Retail Inventory:")
        print(f"Pain Points: {result2['identified_pain_points']}")
        print(f"Recommended Features: {result2['recommended_features']}")
        print()

    asyncio.run(test_use_case_matcher())
