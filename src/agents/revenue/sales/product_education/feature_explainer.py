"""
Feature Explainer Agent - TASK-1021

Explains product features clearly and tailors explanations to prospect's industry/role.
Provides demos, videos, screenshots, and competitor comparisons.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("feature_explainer", tier="revenue", category="sales")
class FeatureExplainer(BaseAgent):
    """
    Feature Explainer Agent - Specialist in product feature education.

    Handles:
    - Clear feature explanations tailored to industry/role
    - Demo materials (videos, screenshots, walkthroughs)
    - Competitor comparisons
    - Use case demonstrations
    - Technical depth adjustment based on audience
    """

    # Feature categories
    FEATURE_CATEGORIES = {
        "core": ["automation", "integration", "analytics", "reporting"],
        "advanced": ["api", "webhooks", "custom_workflows", "ai_powered"],
        "enterprise": ["sso", "audit_logs", "role_based_access", "dedicated_support"],
        "collaboration": ["team_workspaces", "shared_dashboards", "comments", "notifications"]
    }

    # Industry-specific feature mapping
    INDUSTRY_FEATURES = {
        "technology": ["api_integration", "developer_tools", "automation", "webhooks"],
        "healthcare": ["hipaa_compliance", "data_security", "audit_logs", "encryption"],
        "finance": ["sox_compliance", "audit_trails", "data_governance", "security"],
        "retail": ["inventory_tracking", "sales_analytics", "customer_insights", "pos_integration"],
        "manufacturing": ["supply_chain", "quality_control", "production_tracking", "iot_integration"]
    }

    # Role-based explanation depth
    ROLE_DEPTH = {
        "executive": "high_level",  # Focus on business value
        "manager": "balanced",       # Mix of value and functionality
        "technical": "detailed",     # Deep technical details
        "end_user": "practical"      # How-to and workflows
    }

    # Competitor comparison matrix
    COMPETITOR_ADVANTAGES = {
        "automation": "3x faster automation setup vs competitors",
        "integration": "200+ pre-built integrations vs avg 50",
        "analytics": "Real-time analytics vs hourly/daily updates",
        "pricing": "Transparent per-user pricing vs complex tiers",
        "support": "24/7 human support vs chatbot-only"
    }

    def __init__(self):
        config = AgentConfig(
            name="feature_explainer",
            type=AgentType.SPECIALIST,
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
        """Process feature explanation request"""
        self.logger.info("feature_explainer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify requested features
        requested_features = self._identify_requested_features(message)

        # Determine explanation approach
        explanation_approach = self._determine_approach(customer_metadata)

        # Get relevant demo materials
        demo_materials = self._get_demo_materials(requested_features, explanation_approach)

        # Generate competitor comparison if relevant
        competitor_comparison = self._generate_competitor_comparison(requested_features)

        # Search KB for feature documentation
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=5
        )
        state["kb_results"] = kb_results

        # Generate tailored explanation
        response = await self._generate_feature_explanation(
            message,
            requested_features,
            explanation_approach,
            demo_materials,
            competitor_comparison,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["requested_features"] = requested_features
        state["explanation_approach"] = explanation_approach
        state["demo_materials"] = demo_materials
        state["competitor_comparison"] = competitor_comparison
        state["status"] = "resolved"

        self.logger.info(
            "feature_explainer_completed",
            features_count=len(requested_features),
            approach=explanation_approach["depth"]
        )

        return state

    def _identify_requested_features(self, message: str) -> List[str]:
        """Identify which features are being asked about"""
        message_lower = message.lower()
        requested = []

        # Check all feature categories
        for category, features in self.FEATURE_CATEGORIES.items():
            for feature in features:
                if feature.replace("_", " ") in message_lower or feature in message_lower:
                    requested.append(feature)

        # If no specific features mentioned, assume general overview
        if not requested:
            requested = ["product_overview"]

        return list(set(requested))  # Remove duplicates

    def _determine_approach(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Determine how to explain based on prospect profile"""
        title = customer_metadata.get("title", "").lower()
        industry = customer_metadata.get("industry", "other").lower()

        # Determine role type
        role_type = "end_user"  # Default
        if any(exec_title in title for exec_title in ["ceo", "cto", "cfo", "president", "vp"]):
            role_type = "executive"
        elif "manager" in title or "director" in title or "head" in title:
            role_type = "manager"
        elif any(tech_title in title for tech_title in ["engineer", "developer", "architect", "admin"]):
            role_type = "technical"

        depth = self.ROLE_DEPTH.get(role_type, "balanced")

        # Get industry-relevant features
        industry_features = self.INDUSTRY_FEATURES.get(industry, [])

        return {
            "role_type": role_type,
            "depth": depth,
            "industry": industry,
            "industry_features": industry_features,
            "include_technical_details": role_type in ["technical", "manager"],
            "include_roi_metrics": role_type in ["executive", "manager"]
        }

    def _get_demo_materials(
        self,
        requested_features: List[str],
        approach: Dict
    ) -> Dict[str, List[str]]:
        """Get relevant demo materials for requested features"""
        materials = {
            "videos": [],
            "screenshots": [],
            "walkthroughs": [],
            "code_samples": []
        }

        for feature in requested_features:
            # Add video demos
            materials["videos"].append(f"demo_video_{feature}.mp4")

            # Add screenshots for visual learners
            if approach["depth"] in ["balanced", "practical"]:
                materials["screenshots"].append(f"screenshot_{feature}_overview.png")
                materials["screenshots"].append(f"screenshot_{feature}_config.png")

            # Add walkthroughs
            materials["walkthroughs"].append(f"walkthrough_{feature}_setup.pdf")

            # Add code samples for technical users
            if approach["include_technical_details"]:
                materials["code_samples"].append(f"code_sample_{feature}_integration.py")

        return materials

    def _generate_competitor_comparison(self, requested_features: List[str]) -> Dict[str, str]:
        """Generate competitor comparison for relevant features"""
        comparisons = {}

        for feature in requested_features:
            if feature in self.COMPETITOR_ADVANTAGES:
                comparisons[feature] = self.COMPETITOR_ADVANTAGES[feature]

        # Add general advantages if specific features not found
        if not comparisons and requested_features != ["product_overview"]:
            comparisons["overall"] = "Best-in-class performance and ease of use"

        return comparisons

    async def _generate_feature_explanation(
        self,
        message: str,
        requested_features: List[str],
        approach: Dict,
        demo_materials: Dict,
        competitor_comparison: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate tailored feature explanation"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant documentation:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build demo materials list
        demo_context = "\n\nAvailable demo materials:\n"
        if demo_materials["videos"]:
            demo_context += f"- Video demos: {len(demo_materials['videos'])} available\n"
        if demo_materials["screenshots"]:
            demo_context += f"- Screenshots: {len(demo_materials['screenshots'])} available\n"
        if demo_materials["walkthroughs"]:
            demo_context += f"- Interactive walkthroughs: {len(demo_materials['walkthroughs'])} available\n"

        # Build competitor comparison
        competitor_context = ""
        if competitor_comparison:
            competitor_context = "\n\nCompetitive advantages:\n"
            for feature, advantage in competitor_comparison.items():
                competitor_context += f"- {feature.replace('_', ' ').title()}: {advantage}\n"

        system_prompt = f"""You are a Feature Explainer specialist helping prospects understand our product.

Prospect Profile:
- Role: {approach['role_type'].replace('_', ' ').title()}
- Industry: {approach['industry'].title()}
- Explanation Depth: {approach['depth']}
- Include Technical Details: {approach['include_technical_details']}
- Include ROI Metrics: {approach['include_roi_metrics']}

Requested Features: {', '.join(requested_features)}

Industry-Relevant Features: {', '.join(approach['industry_features'])}

Tailor your explanation to:
1. Match the prospect's technical level and role
2. Highlight industry-specific benefits
3. Reference available demo materials
4. Include competitor advantages when relevant
5. Use clear, jargon-free language unless technical depth is needed
6. Focus on business value for executives, functionality for managers, implementation for technical users"""

        user_prompt = f"""Customer message: {message}

{kb_context}
{demo_context}
{competitor_context}

Generate a clear, tailored feature explanation that addresses their question."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    """Test harness for FeatureExplainer"""
    import asyncio
    from src.workflow.state import AgentState

    async def test_feature_explainer():
        agent = FeatureExplainer()

        # Test case 1: Executive asking about automation
        state1 = AgentState(
            current_message="Can you explain your automation capabilities?",
            customer_metadata={
                "title": "CEO",
                "industry": "technology",
                "company_size": 500
            },
            messages=[],
            status="pending"
        )

        result1 = await agent.process(state1)
        print("Test 1 - Executive Automation Query:")
        print(f"Approach: {result1['explanation_approach']}")
        print(f"Features: {result1['requested_features']}")
        print(f"Response: {result1['agent_response'][:200]}...")
        print()

        # Test case 2: Technical user asking about API
        state2 = AgentState(
            current_message="How does your API integration work? Do you have webhooks?",
            customer_metadata={
                "title": "Software Engineer",
                "industry": "finance",
                "company_size": 200
            },
            messages=[],
            status="pending"
        )

        result2 = await agent.process(state2)
        print("Test 2 - Technical API Query:")
        print(f"Approach: {result2['explanation_approach']}")
        print(f"Features: {result2['requested_features']}")
        print(f"Demo Materials: {len(result2['demo_materials']['code_samples'])} code samples")
        print()

    asyncio.run(test_feature_explainer())
