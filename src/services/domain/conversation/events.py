"""
Conversation Domain Events - Event definitions

These events represent things that have happened in the conversation domain.
They are created by domain services but published by application services.

NOTE: Domain services create these events but DO NOT publish them.
      Application services are responsible for publishing.
"""

from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional, List
from src.core.events import DomainEvent


@dataclass
class ConversationCreatedEvent(DomainEvent):
    """Conversation was created"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    initial_message: str = field(default="")
    customer_plan: str = field(default="free")


@dataclass
class ConversationResolvedEvent(DomainEvent):
    """Conversation was resolved"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    resolution_time_seconds: int = field(default=0)
    primary_intent: Optional[str] = field(default=None)
    agents_involved: List[str] = field(default_factory=list)
    sentiment_avg: Optional[float] = field(default=None)


@dataclass
class ConversationEscalatedEvent(DomainEvent):
    """Conversation was escalated to human"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    priority: str = field(default="medium")
    reason: str = field(default="")
    agents_involved: List[str] = field(default_factory=list)


@dataclass
class ConversationReopenedEvent(DomainEvent):
    """Resolved conversation was reopened"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    reason: str = field(default="")
    previous_status: str = field(default="resolved")


@dataclass
class MessageAddedEvent(DomainEvent):
    """Message was added to conversation"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    message_id: UUID = field(default=None)
    role: str = field(default="user")
    agent_name: Optional[str] = field(default=None)
    sentiment: Optional[float] = field(default=None)
    confidence: Optional[float] = field(default=None)


@dataclass
class LowConfidenceDetectedEvent(DomainEvent):
    """Low confidence response detected"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    message_id: UUID = field(default=None)
    confidence: float = field(default=0.0)
    agent_name: str = field(default="")
    threshold: float = field(default=0.5)


@dataclass
class NegativeSentimentDetectedEvent(DomainEvent):
    """Negative sentiment detected in conversation"""
    conversation_id: UUID = field(default=None)
    customer_id: UUID = field(default=None)
    message_id: UUID = field(default=None)
    sentiment: float = field(default=0.0)
    agent_name: Optional[str] = field(default=None)
    threshold: float = field(default=-0.5)