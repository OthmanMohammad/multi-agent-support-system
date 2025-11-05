"""
Test suite for multi-agent support system

This package contains unit tests, integration tests, and fixtures for testing
the application. Tests are organized by layer (core, services, database, etc.)

Structure:
    tests/
    ├── __init__.py           # This file
    ├── conftest.py           # Shared pytest fixtures
    └── unit/                 # Unit tests
        ├── core/             # Core pattern tests
        ├── services/         # Service layer tests
        └── database/         # Database layer tests

Running tests:
    # All tests
    pytest tests/
    
    # Specific test file
    pytest tests/unit/core/test_result.py
    
    # With coverage
    pytest tests/ --cov=src --cov-report=html
    
    # Verbose output
    pytest tests/ -v
    
    # Stop on first failure
    pytest tests/ -x
"""

__version__ = "1.0.0"