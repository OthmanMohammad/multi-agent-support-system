"""
Context enrichment utilities.

Provides scoring, filtering, and monitoring utilities for the context enrichment system.
"""

from src.services.infrastructure.context_enrichment.utils.scoring import (
    RelevanceScorer,
    score_context,
    score_with_breakdown
)
from src.services.infrastructure.context_enrichment.utils.filtering import (
    PIIFilter,
    filter_pii,
    mask_email,
    mask_phone,
    mask_ssn,
    mask_credit_card
)
from src.services.infrastructure.context_enrichment.utils.monitoring import (
    ContextMetrics,
    get_metrics,
    record_enrichment,
    record_provider_execution,
    record_cache_hit,
    record_cache_miss
)

__all__ = [
    # Scoring
    "RelevanceScorer",
    "score_context",
    "score_with_breakdown",
    # Filtering
    "PIIFilter",
    "filter_pii",
    "mask_email",
    "mask_phone",
    "mask_ssn",
    "mask_credit_card",
    # Monitoring
    "ContextMetrics",
    "get_metrics",
    "record_enrichment",
    "record_provider_execution",
    "record_cache_hit",
    "record_cache_miss",
]
