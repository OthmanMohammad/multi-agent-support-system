"""
Log Formatters - Custom formatters for different environments

This module provides custom formatters for structlog to handle
different output requirements for development vs production.

Formatters:
- JSONFormatter: Structured JSON for production
- PrettyFormatter: Human-readable console for development
"""

from typing import Any

import structlog


class CustomJSONRenderer:
    """
    Custom JSON renderer with additional formatting

    Adds environment info and ensures consistent structure.
    """

    def __init__(self, environment: str = "production"):
        """
        Initialize renderer

        Args:
            environment: Environment name to include in logs
        """
        self.environment = environment
        self._json_renderer = structlog.processors.JSONRenderer()

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> str:
        """
        Render event dict as JSON

        Args:
            logger: Logger instance
            method_name: Method name
            event_dict: Event dictionary

        Returns:
            JSON string
        """
        # Add environment to every log
        event_dict["environment"] = self.environment

        # Use standard JSON renderer
        return self._json_renderer(logger, method_name, event_dict)


class CustomConsoleRenderer:
    """
    Custom console renderer with enhanced formatting

    Provides colorized, readable output for development.
    """

    def __init__(self):
        """Initialize renderer"""
        self._console_renderer = structlog.dev.ConsoleRenderer()

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> str:
        """
        Render event dict for console

        Args:
            logger: Logger instance
            method_name: Method name
            event_dict: Event dictionary

        Returns:
            Formatted string for console
        """
        return self._console_renderer(logger, method_name, event_dict)


def get_formatter(log_format: str, environment: str = "production"):
    """
    Get appropriate formatter for environment

    Args:
        log_format: Format type (json or pretty)
        environment: Environment name

    Returns:
        Formatter instance
    """
    if log_format == "json":
        return CustomJSONRenderer(environment=environment)
    else:
        return CustomConsoleRenderer()
