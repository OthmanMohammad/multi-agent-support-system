"""
Customer intelligence provider.

Fetches customer profile data, business metrics, and key indicators.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider


class CustomerIntelligenceProvider(BaseContextProvider):
    """
    Provides customer profile and business intelligence.

    Fetches:
    - Company information
    - Plan and revenue metrics
    - Health score and churn risk
    - NPS score
    - Customer tenure
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch customer intelligence from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)

        Returns:
            Customer intelligence data
        """
        self.logger.debug("fetching_customer_intelligence", customer_id=customer_id)

        # TODO: Replace with actual database query
        # For now, return reasonable defaults with some variation based on customer_id
        # This allows the system to work while database integration is in progress

        # Simple hash to create variation
        customer_hash = sum(ord(c) for c in customer_id) % 100

        # Determine plan based on hash
        if customer_hash < 20:
            plan = "free"
            mrr = 0
        elif customer_hash < 60:
            plan = "basic"
            mrr = 10 * ((customer_hash % 10) + 1)
        else:
            plan = "premium"
            mrr = 25 * ((customer_hash % 10) + 1)

        # Calculate LTV (simple estimate: 12 months of MRR)
        ltv = mrr * 12

        # Health score (60-95 range)
        health_score = 60 + (customer_hash % 35)

        # Churn risk (inverse of health, with some randomness)
        churn_risk = max(0.1, min(0.9, (100 - health_score) / 100))

        # NPS (1-10, higher for higher health)
        nps_score = min(10, max(1, health_score // 10))

        # Customer since (30-365 days ago)
        days_ago = 30 + (customer_hash % 335)
        customer_since = datetime.utcnow() - timedelta(days=days_ago)

        return {
            "company_name": f"Customer {customer_id[:8]}",
            "industry": self._get_industry(customer_hash),
            "company_size": self._get_company_size(customer_hash),
            "plan": plan,
            "mrr": float(mrr),
            "ltv": float(ltv),
            "health_score": health_score,
            "churn_risk": churn_risk,
            "nps_score": nps_score,
            "customer_since": customer_since
        }

    def _get_industry(self, hash_val: int) -> Optional[str]:
        """Get industry based on hash"""
        industries = [
            "Technology", "Healthcare", "Finance", "Education",
            "Retail", "Manufacturing", "Professional Services", "Media"
        ]
        if hash_val % 10 < 8:  # 80% have industry set
            return industries[hash_val % len(industries)]
        return None

    def _get_company_size(self, hash_val: int) -> Optional[int]:
        """Get company size based on hash"""
        if hash_val % 10 < 7:  # 70% have size set
            # 1-1000 employees
            return (hash_val % 10 + 1) * (10 ** (hash_val % 3))
        return None
