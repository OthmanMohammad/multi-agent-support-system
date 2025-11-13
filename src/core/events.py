"""
Domain Events - Decouple components using events

This module implements the Observer pattern for domain events, enabling
loose coupling between components through event publishing and subscription.

Domain events represent things that have happened in the domain and are
always named in past tense (e.g., ConversationCreated, not CreateConversation).

Example:
    >>> from dataclasses import dataclass
    >>> from core.events import DomainEvent, get_event_bus
    >>> 
    >>> @dataclass
    >>> class ConversationStartedEvent(DomainEvent):
    ...     conversation_id: UUID
    ...     customer_id: UUID
    ...     initial_message: str
    >>> 
    >>> # Subscribe to events
    >>> def handle_conversation_started(event: ConversationStartedEvent):
    ...     print(f"New conversation: {event.conversation_id}")
    >>> 
    >>> bus = get_event_bus()
    >>> bus.subscribe(ConversationStartedEvent, handle_conversation_started)
    >>> 
    >>> # Publish events
    >>> event = ConversationStartedEvent(
    ...     conversation_id=uuid4(),
    ...     customer_id=uuid4(),
    ...     initial_message="Hello"
    ... )
    >>> bus.publish(event)
"""

from abc import ABC
from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Callable, Dict, Type, Any
from dataclasses import dataclass, field

from src.utils.logging.setup import get_logger

logger = get_logger(__name__)

__all__ = ["DomainEvent", "EventBus", "get_event_bus", "reset_event_bus"]


@dataclass
class DomainEvent(ABC):
    """
    Base class for all domain events
    
    Domain events are immutable records of things that have happened.
    They should be named in past tense and contain all relevant data.
    
    Attributes:
        event_id: Unique identifier for this event instance
        occurred_at: When the event occurred (UTC)
    
    Example:
        >>> @dataclass
        >>> class UserRegisteredEvent(DomainEvent):
        ...     user_id: UUID
        ...     email: str
        ...     plan: str
    """
    
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize event to dictionary for logging or persistence
        
        Returns:
            Dict representation of the event
        """
        result = {
            "event_type": self.__class__.__name__,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
        }
        
        # Add all fields except event_id and occurred_at
        for key, value in self.__dict__.items():
            if key not in ['event_id', 'occurred_at']:
                # Convert UUIDs to strings for serialization
                if isinstance(value, UUID):
                    result[key] = str(value)
                else:
                    result[key] = value
        
        return result
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}(event_id={self.event_id})"


class EventBus:
    """
    Event bus for publishing and subscribing to domain events
    
    Uses Observer pattern to decouple event publishers from subscribers.
    Subscribers are notified synchronously when events are published.
    
    Example:
        >>> bus = EventBus()
        >>> 
        >>> def handle_event(event):
        ...     print(f"Received: {event}")
        >>> 
        >>> bus.subscribe(MyEvent, handle_event)
        >>> bus.publish(MyEvent(...))
    """
    
    def __init__(self):
        """Initialize event bus"""
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = {}
        logger.debug("event_bus_initialized")
    
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Class of event to subscribe to
            handler: Function to call when event is published
        
        Example:
            >>> def my_handler(event: ConversationCreated):
            ...     print(f"New conversation: {event.conversation_id}")
            >>> 
            >>> bus.subscribe(ConversationCreated, my_handler)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        
        logger.debug(
            "event_subscription_added",
            event_type=event_type.__name__,
            handler=handler.__name__,
            total_subscribers=len(self._subscribers[event_type])
        )
    
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Unsubscribe from events
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(
                    "event_subscription_removed",
                    event_type=event_type.__name__,
                    handler=handler.__name__
                )
            except ValueError:
                logger.warning(
                    "handler_not_found_for_unsubscribe",
                    event_type=event_type.__name__,
                    handler=handler.__name__
                )
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all subscribers
        
        Notifies all handlers subscribed to this event type.
        Handlers are called synchronously in order of subscription.
        
        Args:
            event: Event instance to publish
        
        Example:
            >>> event = ConversationCreated(
            ...     conversation_id=uuid4(),
            ...     customer_id=uuid4()
            ... )
            >>> bus.publish(event)
        """
        event_type = type(event)
        
        logger.debug(
            "event_published",
            event_type=event_type.__name__,
            event_id=str(event.event_id)
        )
        
        # Get subscribers for this event type
        handlers = self._subscribers.get(event_type, [])
        
        if not handlers:
            logger.debug(
                "no_subscribers_for_event",
                event_type=event_type.__name__
            )
            return
        
        # Notify each subscriber
        for handler in handlers:
            try:
                handler(event)
                logger.debug(
                    "event_handler_executed",
                    event_type=event_type.__name__,
                    handler=handler.__name__
                )
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event_type.__name__,
                    handler=handler.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
    
    def clear(self) -> None:
        """Clear all subscriptions (useful for testing)"""
        logger.debug("event_bus_cleared")
        self._subscribers.clear()
    
    def get_subscribers(self, event_type: Type[DomainEvent]) -> List[Callable]:
        """
        Get list of subscribers for event type
        
        Args:
            event_type: Event type
        
        Returns:
            List of handler functions
        """
        return self._subscribers.get(event_type, []).copy()


# Global event bus instance
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """
    Get global event bus instance (singleton)
    
    Returns:
        Global EventBus instance
    
    Example:
        >>> bus = get_event_bus()
        >>> bus.publish(MyEvent(...))
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        logger.info("global_event_bus_created")
    return _event_bus


def reset_event_bus() -> None:
    """
    Reset global event bus (for testing)
    
    Creates a new EventBus instance, clearing all subscriptions.
    """
    global _event_bus
    _event_bus = EventBus()
    logger.debug("global_event_bus_reset")