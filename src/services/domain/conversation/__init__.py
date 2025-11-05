"""
Conversation domain services package
"""

from services.domain.conversation.domain_service import ConversationDomainService
from services.domain.conversation.specifications import (
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
from services.domain.conversation.events import (
    ConversationCreatedEvent,
    ConversationResolvedEvent,
    ConversationEscalatedEvent,
    ConversationReopenedEvent,
    MessageAddedEvent,
    LowConfidenceDetectedEvent,
    NegativeSentimentDetectedEvent,
)
from services.domain.conversation.validators import ConversationValidators

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