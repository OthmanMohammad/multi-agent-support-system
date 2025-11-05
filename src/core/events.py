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
import logging

logger = logging.getLogger(__name__)

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
    Simple in-memory event bus implementing the Observer pattern
    
    Features:
    - Type-safe event subscription
    - Synchronous event publishing
    - Global event handlers (subscribe to all events)
    - Automatic error handling (handlers don't crash the bus)
    - Event handler registration/unregistration
    
    Example:
        >>> bus = EventBus()
        >>> 
        >>> def handler(event: ConversationStartedEvent):
        ...     print(f"Conversation started: {event.conversation_id}")
        >>> 
        >>> bus.subscribe(ConversationStartedEvent, handler)
        >>> bus.publish(ConversationStartedEvent(...))
    """
    
    def __init__(self):
        """Initialize empty event bus"""
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}
        self._global_handlers: List[Callable] = []
        logger.debug("EventBus initialized")
    
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Subscribe handler to specific event type
        
        The handler will be called synchronously when events of this type
        are published. Handlers are called in registration order.
        
        Args:
            event_type: Type of event to listen for
            handler: Callable that accepts the event
        
        Example:
            >>> def on_user_registered(event: UserRegisteredEvent):
            ...     send_welcome_email(event.email)
            >>> 
            >>> bus.subscribe(UserRegisteredEvent, on_user_registered)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.info(
                f"Subscribed {handler.__name__} to {event_type.__name__}"
            )
    
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> bool:
        """
        Unsubscribe handler from event type
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
        
        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(
                    f"Unsubscribed {handler.__name__} from {event_type.__name__}"
                )
                return True
            except ValueError:
                pass
        return False
    
    def subscribe_to_all(self, handler: Callable[[DomainEvent], None]) -> None:
        """
        Subscribe handler to all events
        
        Global handlers are called for every event, regardless of type.
        Useful for logging, monitoring, or event persistence.
        
        Args:
            handler: Callable that accepts any DomainEvent
        
        Example:
            >>> def log_all_events(event: DomainEvent):
            ...     logger.info(f"Event: {event.to_dict()}")
            >>> 
            >>> bus.subscribe_to_all(log_all_events)
        """
        if handler not in self._global_handlers:
            self._global_handlers.append(handler)
            logger.info(f"Subscribed {handler.__name__} to all events")
    
    def unsubscribe_from_all(self, handler: Callable[[DomainEvent], None]) -> bool:
        """
        Unsubscribe handler from all events
        
        Args:
            handler: Handler to remove
        
        Returns:
            True if handler was found and removed, False otherwise
        """
        try:
            self._global_handlers.remove(handler)
            logger.info(f"Unsubscribed {handler.__name__} from all events")
            return True
        except ValueError:
            return False
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all subscribers
        
        Events are delivered synchronously in the order handlers were registered.
        If a handler raises an exception, it is logged but does not prevent
        other handlers from executing.
        
        Args:
            event: Event to publish
        
        Example:
            >>> event = ConversationStartedEvent(
            ...     conversation_id=uuid4(),
            ...     customer_id=uuid4(),
            ...     initial_message="Hello"
            ... )
            >>> bus.publish(event)
        """
        event_type = type(event)
        logger.debug(
            f"Publishing {event_type.__name__}: {event.event_id}"
        )
        
        # Call type-specific handlers
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in event handler {handler.__name__} "
                        f"for {event_type.__name__}: {e}",
                        exc_info=True
                    )
        
        # Call global handlers
        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in global event handler {handler.__name__} "
                    f"for {event_type.__name__}: {e}",
                    exc_info=True
                )
    
    def clear(self) -> None:
        """
        Clear all handlers
        
        Useful for testing or resetting the event bus.
        """
        self._handlers.clear()
        self._global_handlers.clear()
        logger.info("EventBus cleared")
    
    def handler_count(self, event_type: Type[DomainEvent] = None) -> int:
        """
        Get number of registered handlers
        
        Args:
            event_type: Count handlers for specific type, or all if None
        
        Returns:
            Number of handlers
        """
        if event_type is None:
            # Count all handlers (type-specific + global)
            type_specific = sum(len(h) for h in self._handlers.values())
            return type_specific + len(self._global_handlers)
        
        return len(self._handlers.get(event_type, []))


# ===== Global Event Bus Singleton =====

_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """
    Get or create global event bus singleton
    
    This provides a single shared event bus for the entire application.
    Use this in production code.
    
    Returns:
        Global EventBus instance
    
    Example:
        >>> from core.events import get_event_bus
        >>> 
        >>> bus = get_event_bus()
        >>> bus.subscribe(MyEvent, my_handler)
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        logger.info("Global event bus created")
    return _event_bus


def reset_event_bus() -> None:
    """
    Reset global event bus
    
    Creates a fresh event bus with no handlers.
    Useful for testing to ensure test isolation.
    
    Example:
        >>> def test_something():
        ...     reset_event_bus()  # Clean slate
        ...     bus = get_event_bus()
        ...     # ... test code ...
    """
    global _event_bus
    _event_bus = EventBus()
    logger.info("Global event bus reset")


if __name__ == "__main__":
    # Self-test
    print("=" * 70)
    print("DOMAIN EVENTS - SELF TEST")
    print("=" * 70)
    
    @dataclass
    class TestEvent(DomainEvent):
        """Test event for demonstration"""
        message: str
        count: int
    
    # Test event creation
    print("\n1. Testing event creation...")
    event = TestEvent(message="Hello", count=42)
    assert event.event_id is not None
    assert event.occurred_at is not None
    print(f"   ✓ {event}")
    
    # Test to_dict
    print("\n2. Testing serialization...")
    event_dict = event.to_dict()
    assert event_dict["event_type"] == "TestEvent"
    assert event_dict["message"] == "Hello"
    assert event_dict["count"] == 42
    print(f"   ✓ {event_dict}")
    
    # Test EventBus subscription
    print("\n3. Testing event subscription...")
    bus = EventBus()
    called = []
    
    def handler(e: TestEvent):
        called.append(e.message)
    
    bus.subscribe(TestEvent, handler)
    assert bus.handler_count(TestEvent) == 1
    print(f"   ✓ Handler subscribed")
    
    # Test event publishing
    print("\n4. Testing event publishing...")
    bus.publish(TestEvent(message="Test1", count=1))
    bus.publish(TestEvent(message="Test2", count=2))
    assert len(called) == 2
    assert called == ["Test1", "Test2"]
    print(f"   ✓ Events published and handled")
    
    # Test global handlers
    print("\n5. Testing global handlers...")
    global_called = []
    
    def global_handler(e: DomainEvent):
        global_called.append(e.__class__.__name__)
    
    bus.subscribe_to_all(global_handler)
    bus.publish(TestEvent(message="Global", count=3))
    assert "TestEvent" in global_called
    print(f"   ✓ Global handler called")
    
    # Test handler removal
    print("\n6. Testing unsubscribe...")
    bus.unsubscribe(TestEvent, handler)
    assert bus.handler_count(TestEvent) == 0
    print(f"   ✓ Handler unsubscribed")
    
    # Test global singleton
    print("\n7. Testing global event bus...")
    global_bus = get_event_bus()
    assert global_bus is not None
    reset_event_bus()
    new_bus = get_event_bus()
    assert new_bus is not global_bus
    print(f"   ✓ Global bus working")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)