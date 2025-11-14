"""
Router Agent - Classifies intent and routes to specialist agents.

DEPRECATED: This module is kept for backward compatibility.
Please import from src.agents.essential.routing.meta_router instead.
"""

# Import from new location
from src.agents.essential.routing.meta_router import (
    MetaRouterAgent as RouterAgent,
    IntentClassification
)

# For backward compatibility
__all__ = ["RouterAgent", "IntentClassification"]
