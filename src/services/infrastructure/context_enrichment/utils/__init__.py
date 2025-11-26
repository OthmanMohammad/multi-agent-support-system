"""
Context enrichment utilities.

Provides scoring, filtering, and monitoring utilities for the context enrichment system.
"""

from src.services.infrastructure.context_enrichment.utils.filtering import (
    PIIFilter,
    filter_pii,
    mask_credit_card,
    mask_email,
    mask_phone,
    mask_ssn,
)
from src.services.infrastructure.context_enrichment.utils.monitoring import (
    ContextMetrics,
    get_metrics,
    record_cache_hit,
    record_cache_miss,
    record_enrichment,
    record_provider_execution,
)
from src.services.infrastructure.context_enrichment.utils.scoring import (
    RelevanceScorer,
    score_context,
    score_with_breakdown,
)

__all__ = [
    # Monitoring
    "ContextMetrics",
    # Filtering
    "PIIFilter",
    # Scoring
    "RelevanceScorer",
    "filter_pii",
    "get_metrics",
    "mask_credit_card",
    "mask_email",
    "mask_phone",
    "mask_ssn",
    "record_cache_hit",
    "record_cache_miss",
    "record_enrichment",
    "record_provider_execution",
    "score_context",
    "score_with_breakdown",
]
