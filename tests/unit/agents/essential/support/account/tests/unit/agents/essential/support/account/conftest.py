"""Pytest fixtures for account agent tests."""

import pytest
from src.workflow.state import create_initial_state


@pytest.fixture
def base_state():
    """Create base state for testing."""
    return create_initial_state(
        "Test message",
        context={"customer_metadata": {"plan": "premium", "role": "admin", "team_size": 5}}
    )

