"""
Learning & Improvement Swarm - EPIC-004 STORY-405

10 learning agents that continuously improve the entire system.

Agents: Conversation Analyzer, Mistake Detector, Feedback Processor, Improvement Suggester,
A/B Test Designer, Model Fine-tuner, Prompt Optimizer, Knowledge Gap Identifier,
Routing Optimizer, Performance Tracker (TASK-4050 to TASK-4059)
"""

from src.agents.advanced.learning.conversation_analyzer import ConversationAnalyzerAgent
from src.agents.advanced.learning.mistake_detector import MistakeDetectorAgent
from src.agents.advanced.learning.feedback_processor import FeedbackProcessorAgent
from src.agents.advanced.learning.improvement_suggester import ImprovementSuggesterAgent
from src.agents.advanced.learning.ab_test_designer import ABTestDesignerAgent
from src.agents.advanced.learning.model_fine_tuner import ModelFineTunerAgent
from src.agents.advanced.learning.prompt_optimizer import PromptOptimizerAgent
from src.agents.advanced.learning.knowledge_gap_identifier import KnowledgeGapIdentifierAgent
from src.agents.advanced.learning.routing_optimizer import RoutingOptimizerAgent
from src.agents.advanced.learning.performance_tracker import PerformanceTrackerAgent

__all__ = ["ConversationAnalyzerAgent", "MistakeDetectorAgent", "FeedbackProcessorAgent", "ImprovementSuggesterAgent", "ABTestDesignerAgent", "ModelFineTunerAgent", "PromptOptimizerAgent", "KnowledgeGapIdentifierAgent", "RoutingOptimizerAgent", "PerformanceTrackerAgent"]
