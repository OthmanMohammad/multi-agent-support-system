"""
Conversation domain services package
"""

from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.domain.conversation.events import (
    ConversationCreatedEvent,
    ConversationEscalatedEvent,
    ConversationReopenedEvent,
    ConversationResolvedEvent,
    LowConfidenceDetectedEvent,
    MessageAddedEvent,
    NegativeSentimentDetectedEvent,
)
from src.services.domain.conversation.specifications import (
    CanEscalateConversation,
    CanReopenConversation,
    CanResolveConversation,
    ConversationIsActive,
    ConversationIsEscalated,
    ConversationIsResolved,
    HasAgentInteraction,
    HasMinimumMessages,
    HasValidSentiment,
    IsWithinMaxTurns,
)
from src.services.domain.conversation.validators import ConversationValidators

__all__ = [
    "CanEscalateConversation",
    "CanReopenConversation",
    "CanResolveConversation",
    # Events
    "ConversationCreatedEvent",
    # Service
    "ConversationDomainService",
    "ConversationEscalatedEvent",
    # Specifications
    "ConversationIsActive",
    "ConversationIsEscalated",
    "ConversationIsResolved",
    "ConversationReopenedEvent",
    "ConversationResolvedEvent",
    # Validators
    "ConversationValidators",
    "HasAgentInteraction",
    "HasMinimumMessages",
    "HasValidSentiment",
    "IsWithinMaxTurns",
    "LowConfidenceDetectedEvent",
    "MessageAddedEvent",
    "NegativeSentimentDetectedEvent",
]
