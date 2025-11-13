"""
Conversation domain services package
"""

from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.domain.conversation.specifications import (
    ConversationIsActive,
    ConversationIsResolved,
    ConversationIsEscalated,
    HasMinimumMessages,
    HasAgentInteraction,
    HasValidSentiment,
    IsWithinMaxTurns,
    CanResolveConversation,
    CanEscalateConversation,
    CanReopenConversation,
)
from src.services.domain.conversation.events import (
    ConversationCreatedEvent,
    ConversationResolvedEvent,
    ConversationEscalatedEvent,
    ConversationReopenedEvent,
    MessageAddedEvent,
    LowConfidenceDetectedEvent,
    NegativeSentimentDetectedEvent,
)
from src.services.domain.conversation.validators import ConversationValidators

__all__ = [
    # Service
    "ConversationDomainService",
    # Specifications
    "ConversationIsActive",
    "ConversationIsResolved",
    "ConversationIsEscalated",
    "HasMinimumMessages",
    "HasAgentInteraction",
    "HasValidSentiment",
    "IsWithinMaxTurns",
    "CanResolveConversation",
    "CanEscalateConversation",
    "CanReopenConversation",
    # Events
    "ConversationCreatedEvent",
    "ConversationResolvedEvent",
    "ConversationEscalatedEvent",
    "ConversationReopenedEvent",
    "MessageAddedEvent",
    "LowConfidenceDetectedEvent",
    "NegativeSentimentDetectedEvent",
    # Validators
    "ConversationValidators",
]