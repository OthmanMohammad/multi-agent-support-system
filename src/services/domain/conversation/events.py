"""
Conversation Domain Events - Event definitions

These events represent things that have happened in the conversation domain.
They are created by domain services but published by application services.

NOTE: Domain services create these events but DO NOT publish them.
      Application services are responsible for publishing.
"""

from dataclasses import dataclass
from uuid import UUID
from typing import Optional, List
from core.events import DomainEvent


@dataclass
class ConversationCreatedEvent(DomainEvent):
    """Conversation was created"""
    conversation_id: UUID
    customer_id: UUID
    initial_message: str
    customer_plan: str


@dataclass
class ConversationResolvedEvent(DomainEvent):
    """Conversation was resolved"""
    conversation_id: UUID
    customer_id: UUID
    resolution_time_seconds: int
    primary_intent: Optional[str]
    agents_involved: List[str]
    sentiment_avg: Optional[float]


@dataclass
class ConversationEscalatedEvent(DomainEvent):
    """Conversation was escalated to human"""
    conversation_id: UUID
    customer_id: UUID
    priority: str  # low, medium, high, critical
    reason: str
    agents_involved: List[str]


@dataclass
class ConversationReopenedEvent(DomainEvent):
    """Resolved conversation was reopened"""
    conversation_id: UUID
    customer_id: UUID
    reason: str
    previous_status: str


@dataclass
class MessageAddedEvent(DomainEvent):
    """Message was added to conversation"""
    conversation_id: UUID
    customer_id: UUID
    message_id: UUID
    role: str  # user, assistant, system
    agent_name: Optional[str]
    sentiment: Optional[float]
    confidence: Optional[float]


@dataclass
class LowConfidenceDetectedEvent(DomainEvent):
    """Low confidence response detected"""
    conversation_id: UUID
    customer_id: UUID
    message_id: UUID
    confidence: float
    agent_name: str
    threshold: float = 0.5


@dataclass
class NegativeSentimentDetectedEvent(DomainEvent):
    """Negative sentiment detected in conversation"""
    conversation_id: UUID
    customer_id: UUID
    message_id: UUID
    sentiment: float
    agent_name: Optional[str]
    threshold: float = -0.5