"""
Pytest fixtures for account agent tests.
"""

import pytest
from src.workflow.state import create_initial_state


@pytest.fixture
def base_state():
    """Create base state for testing."""
    return create_initial_state(
        "Test message",
        context={
            "customer_metadata": {
                "plan": "premium",
                "role": "admin",
                "team_size": 5
            }
        }
    )


@pytest.fixture
def enterprise_state():
    """Create enterprise state for testing."""
    return create_initial_state(
        "Test message",
        context={
            "customer_metadata": {
                "plan": "enterprise",
                "role": "owner",
                "team_size": 20
            }
        }
    )


@pytest.fixture
def free_state():
    """Create free plan state for testing."""
    return create_initial_state(
        "Test message",
        context={
            "customer_metadata": {
                "plan": "free",
                "role": "member",
                "team_size": 1
            }
        }
    )
