"""
Conversation Domain Specifications - Business rules as composable objects
Specifications encapsulate business rules that can be combined using
boolean logic (AND, OR, NOT).
"""
from typing import TYPE_CHECKING
from src.core.specifications import Specification
if TYPE_CHECKING:
    from src.database.models import Conversation

class ConversationIsActive(Specification['Conversation']):
    """Conversation status is 'active'"""
    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return conversation.status == "active"

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return f"Conversation status is '{conversation.status}', not 'active'"

class ConversationIsResolved(Specification['Conversation']):
    """Conversation status is 'resolved'"""
    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return conversation.status == "resolved"

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return f"Conversation status is '{conversation.status}', not 'resolved'"

class ConversationIsEscalated(Specification['Conversation']):
    """Conversation status is 'escalated'"""
    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return conversation.status == "escalated"

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return f"Conversation status is '{conversation.status}', not 'escalated'"

class HasMinimumMessages(Specification['Conversation']):
    """Conversation has at least minimum number of messages"""
    def __init__(self, minimum: int = 2):
        self.minimum = minimum

    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return len(conversation.messages) >= self.minimum

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return (
            f"Conversation has {len(conversation.messages)} messages, "
            f"needs at least {self.minimum}"
        )

class HasAgentInteraction(Specification['Conversation']):
    """Conversation has at least one agent response"""
    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return any(
            msg.role == "assistant"
            for msg in conversation.messages
        )

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return "Conversation has no agent responses"

class HasValidSentiment(Specification['Conversation']):
    """Average sentiment is within valid range"""
    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        if conversation.sentiment_avg is None:
            return True  # Null is valid (no sentiment data yet)
        return -1.0 <= conversation.sentiment_avg <= 1.0

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return (
            f"Sentiment {conversation.sentiment_avg} is outside valid range [-1, 1]"
        )

class IsWithinMaxTurns(Specification['Conversation']):
    """Conversation hasn't exceeded maximum turns"""
    def __init__(self, max_turns: int = 50):
        self.max_turns = max_turns

    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return len(conversation.messages) <= self.max_turns

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return (
            f"Conversation has {len(conversation.messages)} messages, "
            f"exceeds maximum of {self.max_turns}"
        )

class CanResolveConversation(Specification['Conversation']):
    """
    Composite specification: Can conversation be resolved?
    Business Rules:
    - Must be active
    - Must have at least 2 messages (user + agent)
    - Must have agent interaction
    """

    def __init__(self):
        self.spec = (
            ConversationIsActive()
            .and_(HasMinimumMessages(minimum=2))
            .and_(HasAgentInteraction())
        )

    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return self.spec.is_satisfied_by(conversation)

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return self.spec.reason_not_satisfied(conversation)

class CanEscalateConversation(Specification['Conversation']):
    """
    Composite specification: Can conversation be escalated?
    Business Rules:
    - Must be active
    - Must not already be escalated
    """

    def __init__(self):
        self.spec = (
            ConversationIsActive()
            .and_(ConversationIsEscalated().not_())
        )

    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return self.spec.is_satisfied_by(conversation)

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return self.spec.reason_not_satisfied(conversation)

class CanReopenConversation(Specification['Conversation']):
    """
    Composite specification: Can conversation be reopened?
    Business Rules:
    - Must be resolved or escalated (not active)
    """

    def __init__(self):
        self.spec = (
            ConversationIsResolved()
            .or_(ConversationIsEscalated())
        )

    def is_satisfied_by(self, conversation: 'Conversation') -> bool:
        return self.spec.is_satisfied_by(conversation)

    def reason_not_satisfied(self, conversation: 'Conversation') -> str:
        return self.spec.reason_not_satisfied(conversation)