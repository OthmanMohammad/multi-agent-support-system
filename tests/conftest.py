"""
Pytest configuration and shared fixtures

This module configures pytest and provides shared fixtures used across
multiple test modules. It also handles path setup to ensure tests can
import from the src/ directory.
"""

import sys
from pathlib import Path
import pytest
from uuid import uuid4
from datetime import datetime, UTC

# Add src directory to Python path
# This allows tests to import from src/ regardless of where pytest is run
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# ===== Core Pattern Fixtures =====

@pytest.fixture
def sample_uuid():
    """Generate a sample UUID for testing"""
    return uuid4()


@pytest.fixture
def sample_timestamp():
    """Generate a sample timestamp for testing"""
    return datetime.now(UTC)


@pytest.fixture
def sample_email():
    """Generate a unique test email address"""
    return f"test_{uuid4().hex[:8]}@example.com"


# ===== Result Pattern Fixtures =====

@pytest.fixture
def sample_error():
    """Create a sample Error instance"""
    from core.result import Error
    return Error(
        code="TEST_ERROR",
        message="This is a test error",
        details={"field": "test_field", "value": "test_value"}
    )


@pytest.fixture
def sample_validation_error():
    """Create a sample validation error"""
    from core.errors import ValidationError
    return ValidationError(
        message="Email is required",
        field="email",
        constraint="required"
    )


# ===== Event Bus Fixtures =====

@pytest.fixture
def event_bus():
    """Create a fresh EventBus instance for each test"""
    from core.events import EventBus
    return EventBus()


@pytest.fixture
def reset_global_event_bus():
    """Reset global event bus before and after test"""
    from core.events import reset_event_bus
    reset_event_bus()
    yield
    reset_event_bus()


# ===== Test Helpers =====

@pytest.fixture
def captured_events():
    """
    Fixture that captures published events for testing
    
    Usage:
        def test_something(captured_events):
            bus = get_event_bus()
            bus.subscribe(MyEvent, captured_events)
            
            # ... trigger event ...
            
            assert len(captured_events.events) == 1
            assert isinstance(captured_events.events[0], MyEvent)
    """
    class EventCapture:
        def __init__(self):
            self.events = []
            self.__name__ = "EventCapture"  # For EventBus logging

        def __call__(self, event):
            self.events.append(event)

        def clear(self):
            self.events.clear()
    
    return EventCapture()


# ===== Async Test Helpers =====

@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests"""
    return 'asyncio'


# ===== Pytest Configuration =====

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location"""
    for item in items:
        # Add 'unit' marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add 'integration' marker to tests in integration/ directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)