"""
Monitoring infrastructure - Error tracking and performance monitoring

This package provides production-grade monitoring using Sentry.

Features:
- Error tracking with full stack traces
- Performance monitoring and transaction tracking
- Real-time alerts via email
- Built-in dashboards for errors and performance
- PII filtering for GDPR/CCPA compliance
- Correlation ID tracking for debugging
- Context enrichment (customer, conversation, agent)

Quick Start:
    from utils.monitoring import init_sentry, capture_exception
    
    # Initialize once at startup
    init_sentry()
    
    # Manually capture exceptions with context
    try:
        process_payment()
    except PaymentError as e:
        capture_exception(
            e,
            customer_id=customer.id,
            amount=100.00
        )

Automatic Capture:
    Sentry automatically captures:
    - Unhandled exceptions in FastAPI routes
    - Database errors from SQLAlchemy
    - Slow requests (performance monitoring)
    - All with correlation IDs attached
"""

from utils.monitoring.sentry_config import (
    init_sentry,
    capture_exception,
    capture_message,
)

__version__ = "1.0.0"

__all__ = [
    "init_sentry",
    "capture_exception",
    "capture_message",
]