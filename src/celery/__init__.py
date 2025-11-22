"""
Celery Task Processing Module
Background task execution for multi-agent system
"""

from src.celery.celery_app import celery_app

__all__ = ["celery_app"]
