"""
Unit tests for domain events

Tests cover:
- DomainEvent base class
- EventBus subscription and publishing
- Event handler execution
- Error handling in handlers
- Global event bus singleton
"""

import pytest
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from src.core.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    reset_event_bus,
)


# Test event classes

@dataclass
class SampleEvent(DomainEvent):
    """Simple test event (renamed to avoid pytest collection)"""
    message: str = ""
    count: int = 0


@dataclass(kw_only=True)
class AnotherSampleEvent(DomainEvent):
    """Another test event for multiple subscriptions (renamed to avoid pytest collection)"""
    value: str


class TestDomainEvent:
    """Test suite for DomainEvent base class"""
    
    def test_event_has_id_and_timestamp(self):
        """Test that events get automatic ID and timestamp"""
        event = SampleEvent(message="Test", count=1)
        
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
    
    def test_event_id_is_unique(self):
        """Test that each event gets unique ID"""
        event1 = SampleEvent(message="Test1", count=1)
        event2 = SampleEvent(message="Test2", count=2)
        
        assert event1.event_id != event2.event_id
    
    def test_to_dict_includes_event_type(self):
        """Test to_dict includes event type name"""
        event = SampleEvent(message="Test", count=42)
        
        result = event.to_dict()
        
        assert result["event_type"] == "SampleEvent"
        assert result["message"] == "Test"
        assert result["count"] == 42
    
    def test_to_dict_includes_metadata(self):
        """Test to_dict includes event_id and occurred_at"""
        event = SampleEvent(message="Test", count=1)
        
        result = event.to_dict()
        
        assert "event_id" in result
        assert "occurred_at" in result
        assert isinstance(result["event_id"], str)
        assert isinstance(result["occurred_at"], str)
    
    def test_to_dict_converts_uuid_to_string(self):
        """Test that UUID fields are converted to strings"""
        from uuid import uuid4
        
        @dataclass(kw_only=True)
        class EventWithUUID(DomainEvent):
            user_id: UUID
        
        event = EventWithUUID(user_id=uuid4())
        result = event.to_dict()
        
        assert isinstance(result["user_id"], str)
    
    def test_repr_includes_event_id(self):
        """Test __repr__ includes event ID"""
        event = SampleEvent(message="Test", count=1)
        
        repr_str = repr(event)
        
        assert "SampleEvent" in repr_str
        assert str(event.event_id) in repr_str


class TestEventBus:
    """Test suite for EventBus"""
    
    def test_subscribe_registers_handler(self, event_bus):
        """Test that subscribe registers handler for event type"""
        called = []
        
        def handler(event):
            called.append(event)
        
        event_bus.subscribe(SampleEvent, handler)
        
        assert event_bus.handler_count(SampleEvent) == 1
    
    def test_publish_calls_subscribed_handler(self, event_bus):
        """Test that publish calls registered handlers"""
        called = []
        
        def handler(event):
            called.append(event)
        
        event_bus.subscribe(SampleEvent, handler)
        event = SampleEvent(message="Test", count=1)
        event_bus.publish(event)
        
        assert len(called) == 1
        assert called[0] == event
    
    def test_publish_calls_multiple_handlers(self, event_bus):
        """Test that all subscribed handlers are called"""
        called1 = []
        called2 = []
        
        event_bus.subscribe(SampleEvent, lambda e: called1.append(e))
        event_bus.subscribe(SampleEvent, lambda e: called2.append(e))
        
        event = SampleEvent(message="Test", count=1)
        event_bus.publish(event)
        
        assert len(called1) == 1
        assert len(called2) == 1
    
    def test_handlers_called_in_registration_order(self, event_bus):
        """Test that handlers are called in order registered"""
        order = []
        
        event_bus.subscribe(SampleEvent, lambda e: order.append(1))
        event_bus.subscribe(SampleEvent, lambda e: order.append(2))
        event_bus.subscribe(SampleEvent, lambda e: order.append(3))
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        
        assert order == [1, 2, 3]
    
    def test_publish_with_no_handlers(self, event_bus):
        """Test that publishing with no handlers doesn't error"""
        event = SampleEvent(message="Test", count=1)
        
        # Should not raise
        event_bus.publish(event)
    
    def test_different_event_types_isolated(self, event_bus):
        """Test that handlers only called for correct event type"""
        test_called = []
        another_called = []
        
        event_bus.subscribe(SampleEvent, lambda e: test_called.append(e))
        event_bus.subscribe(AnotherSampleEvent, lambda e: another_called.append(e))
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        
        assert len(test_called) == 1
        assert len(another_called) == 0
    
    def test_handler_exception_doesnt_stop_other_handlers(self, event_bus, caplog):
        """Test that exception in handler doesn't prevent other handlers"""
        called = []
        
        def failing_handler(event):
            raise ValueError("Handler failed")
        
        def working_handler(event):
            called.append(event)
        
        event_bus.subscribe(SampleEvent, failing_handler)
        event_bus.subscribe(SampleEvent, working_handler)
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        
        assert len(called) == 1  # Working handler still called
    
    def test_unsubscribe_removes_handler(self, event_bus):
        """Test that unsubscribe removes handler"""
        called = []
        
        def handler(event):
            called.append(event)
        
        event_bus.subscribe(SampleEvent, handler)
        result = event_bus.unsubscribe(SampleEvent, handler)
        
        assert result is True
        assert event_bus.handler_count(SampleEvent) == 0
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        assert len(called) == 0
    
    def test_unsubscribe_nonexistent_handler(self, event_bus):
        """Test unsubscribing handler that wasn't registered"""
        def handler(event):
            pass
        
        result = event_bus.unsubscribe(SampleEvent, handler)
        
        assert result is False
    
    def test_subscribe_to_all_receives_any_event(self, event_bus):
        """Test that subscribe_to_all receives all event types"""
        called = []
        
        event_bus.subscribe_to_all(lambda e: called.append(e))
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        event_bus.publish(AnotherSampleEvent(value="Another"))
        
        assert len(called) == 2
    
    def test_unsubscribe_from_all(self, event_bus):
        """Test unsubscribing global handler"""
        called = []
        
        def handler(event):
            called.append(event)
        
        event_bus.subscribe_to_all(handler)
        result = event_bus.unsubscribe_from_all(handler)
        
        assert result is True
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        assert len(called) == 0
    
    def test_clear_removes_all_handlers(self, event_bus):
        """Test that clear removes all handlers"""
        event_bus.subscribe(SampleEvent, lambda e: None)
        event_bus.subscribe(AnotherSampleEvent, lambda e: None)
        event_bus.subscribe_to_all(lambda e: None)
        
        event_bus.clear()
        
        assert event_bus.handler_count(SampleEvent) == 0
        assert event_bus.handler_count(AnotherSampleEvent) == 0
        assert event_bus.handler_count() == 0
    
    def test_handler_count_total(self, event_bus):
        """Test handler_count returns total when no type specified"""
        event_bus.subscribe(SampleEvent, lambda e: None)
        event_bus.subscribe(SampleEvent, lambda e: None)
        event_bus.subscribe(AnotherSampleEvent, lambda e: None)
        event_bus.subscribe_to_all(lambda e: None)
        
        assert event_bus.handler_count() == 4
    
    def test_handler_count_by_type(self, event_bus):
        """Test handler_count for specific event type"""
        event_bus.subscribe(SampleEvent, lambda e: None)
        event_bus.subscribe(SampleEvent, lambda e: None)
        event_bus.subscribe(AnotherSampleEvent, lambda e: None)
        
        assert event_bus.handler_count(SampleEvent) == 2
        assert event_bus.handler_count(AnotherSampleEvent) == 1
    
    def test_duplicate_subscription_adds_multiple_calls(self, event_bus):
        """Test that subscribing same handler twice calls it twice"""
        called = []
        
        def handler(event):
            called.append(event)
        
        event_bus.subscribe(SampleEvent, handler)
        event_bus.subscribe(SampleEvent, handler)
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        
        assert len(called) == 2


class TestGlobalEventBus:
    """Test suite for global event bus singleton"""
    
    def test_get_event_bus_returns_singleton(self, reset_global_event_bus):
        """Test that get_event_bus returns same instance"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
    
    def test_reset_creates_new_instance(self, reset_global_event_bus):
        """Test that reset_event_bus creates fresh instance"""
        bus1 = get_event_bus()
        bus1.subscribe(SampleEvent, lambda e: None)
        
        reset_event_bus()
        bus2 = get_event_bus()
        
        assert bus2 is not bus1
        assert bus2.handler_count(SampleEvent) == 0
    
    def test_global_bus_isolated_between_tests(self, reset_global_event_bus):
        """Test that reset fixture isolates tests"""
        bus = get_event_bus()
        
        # Should be clean
        assert bus.handler_count() == 0


class TestEventBusIntegration:
    """Integration tests for complex event scenarios"""
    
    def test_event_chain_propagation(self, event_bus, captured_events):
        """Test that events can trigger other events"""
        
        @dataclass(kw_only=True)
        class FirstEvent(DomainEvent):
            value: int

        @dataclass(kw_only=True)
        class SecondEvent(DomainEvent):
            doubled: int
        
        def handle_first(event: FirstEvent):
            # Handler publishes another event
            event_bus.publish(SecondEvent(doubled=event.value * 2))
        
        event_bus.subscribe(FirstEvent, handle_first)
        event_bus.subscribe(SecondEvent, captured_events)
        
        event_bus.publish(FirstEvent(value=5))
        
        assert len(captured_events.events) == 1
        assert captured_events.events[0].doubled == 10
    
    def test_multiple_event_types_same_handler(self, event_bus):
        """Test same handler can be registered for multiple event types"""
        called = []
        
        def handler(event):
            called.append(event.__class__.__name__)
        
        event_bus.subscribe(SampleEvent, handler)
        event_bus.subscribe(AnotherSampleEvent, handler)
        
        event_bus.publish(SampleEvent(message="Test", count=1))
        event_bus.publish(AnotherSampleEvent(value="Value"))
        
        assert called == ["SampleEvent", "AnotherSampleEvent"]


@pytest.mark.parametrize("handler_count", [1, 3, 5, 10])
def test_multiple_handlers_all_called(event_bus, handler_count):
    """Parametrized test that all handlers are called"""
    called = []
    
    for i in range(handler_count):
        event_bus.subscribe(SampleEvent, lambda e, i=i: called.append(i))
    
    event_bus.publish(SampleEvent(message="Test", count=1))
    
    assert len(called) == handler_count