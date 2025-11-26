"""
Knowledge Base agents package.

This package contains all agents related to knowledge base management,
search, quality assurance, and continuous improvement.

Agents:
- KBSearcher: Semantic search across KB articles
- KBRanker: Re-ranks results by quality and relevance
- KBSynthesizer: Combines articles into coherent answers
- KBFeedbackTracker: Tracks article usage and effectiveness
- KBQualityChecker: Evaluates article quality
- KBUpdater: Detects outdated content
- KBGapDetector: Identifies missing KB content
- KBSuggester: Suggests new articles based on patterns
- FAQGenerator: Auto-generates FAQs from conversations
- KBEmbedder: Generates embeddings for articles
"""

from src.agents.essential.knowledge_base.embedder import KBEmbedder
from src.agents.essential.knowledge_base.faq_generator import FAQGenerator
from src.agents.essential.knowledge_base.feedback_tracker import KBFeedbackTracker
from src.agents.essential.knowledge_base.gap_detector import KBGapDetector
from src.agents.essential.knowledge_base.quality_checker import KBQualityChecker
from src.agents.essential.knowledge_base.ranker import KBRanker
from src.agents.essential.knowledge_base.searcher import KBSearcher
from src.agents.essential.knowledge_base.suggester import KBSuggester
from src.agents.essential.knowledge_base.synthesizer import KBSynthesizer
from src.agents.essential.knowledge_base.updater import KBUpdater

__all__ = [
    "FAQGenerator",
    "KBEmbedder",
    "KBFeedbackTracker",
    "KBGapDetector",
    "KBQualityChecker",
    "KBRanker",
    "KBSearcher",
    "KBSuggester",
    "KBSynthesizer",
    "KBUpdater",
]
