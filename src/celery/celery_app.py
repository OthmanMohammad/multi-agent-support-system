"""
Celery Application Configuration
Enterprise-grade background task processing with Redis broker

Features:
- Task routing (high/normal/low priority queues)
- Retry policies with exponential backoff
- Task monitoring and metrics
- Scheduled tasks (cron-like)
- Result backend for task state tracking
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)

# =============================================================================
# CELERY APP INITIALIZATION
# =============================================================================

celery_app = Celery(
    "multi_agent_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.celery.tasks.agent_tasks",
        "src.celery.tasks.analytics_tasks",
        "src.celery.tasks.maintenance_tasks",
        "src.celery.tasks.notification_tasks",
    ]
)

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

celery_app.conf.update(
    # =========================================================================
    # TIMEZONE & SERIALIZATION
    # =========================================================================
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # =========================================================================
    # TASK EXECUTION
    # =========================================================================
    task_acks_late=True,  # Acknowledge task after execution (safer)
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker crashes
    worker_prefetch_multiplier=1,  # One task per worker at a time (fairness)
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (memory leaks)

    # =========================================================================
    # RESULT BACKEND
    # =========================================================================
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True,
    },

    # =========================================================================
    # TASK RETRY POLICIES
    # =========================================================================
    task_default_retry_delay=60,  # Wait 60 seconds before retry
    task_max_retries=3,  # Max 3 retries
    task_retry_backoff=True,  # Exponential backoff (60s, 120s, 240s)
    task_retry_backoff_max=600,  # Max 10 minutes between retries

    # =========================================================================
    # TASK ROUTING (Priority Queues)
    # =========================================================================
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="topic",
    task_default_routing_key="task.default",

    task_queues=(
        # High priority (urgent customer requests)
        Queue(
            "high_priority",
            Exchange("tasks", type="topic"),
            routing_key="task.high",
            queue_arguments={"x-max-priority": 10},
        ),
        # Default queue (normal operations)
        Queue(
            "default",
            Exchange("tasks", type="topic"),
            routing_key="task.default",
            queue_arguments={"x-max-priority": 5},
        ),
        # Low priority (batch jobs, analytics)
        Queue(
            "low_priority",
            Exchange("tasks", type="topic"),
            routing_key="task.low",
            queue_arguments={"x-max-priority": 1},
        ),
    ),

    # =========================================================================
    # TASK ROUTES (Auto-route tasks to queues)
    # =========================================================================
    task_routes={
        # High priority
        "src.celery.tasks.agent_tasks.execute_urgent_agent": {
            "queue": "high_priority",
            "routing_key": "task.high",
        },
        "src.celery.tasks.notification_tasks.send_critical_alert": {
            "queue": "high_priority",
            "routing_key": "task.high",
        },

        # Default priority
        "src.celery.tasks.agent_tasks.*": {
            "queue": "default",
            "routing_key": "task.default",
        },
        "src.celery.tasks.notification_tasks.*": {
            "queue": "default",
            "routing_key": "task.default",
        },

        # Low priority
        "src.celery.tasks.analytics_tasks.*": {
            "queue": "low_priority",
            "routing_key": "task.low",
        },
        "src.celery.tasks.maintenance_tasks.*": {
            "queue": "low_priority",
            "routing_key": "task.low",
        },
    },

    # =========================================================================
    # SCHEDULED TASKS (Celery Beat)
    # =========================================================================
    beat_schedule={
        # Daily cleanup at 3 AM
        "cleanup-expired-conversations": {
            "task": "src.celery.tasks.maintenance_tasks.cleanup_expired_conversations",
            "schedule": crontab(hour=3, minute=0),
        },

        # Daily analytics report at 9 AM
        "generate-daily-analytics": {
            "task": "src.celery.tasks.analytics_tasks.generate_daily_analytics_report",
            "schedule": crontab(hour=9, minute=0),
        },

        # Hourly cost calculation
        "calculate-hourly-costs": {
            "task": "src.celery.tasks.analytics_tasks.calculate_usage_costs",
            "schedule": crontab(minute=0),  # Every hour
        },

        # Weekly knowledge base update (Sundays at 2 AM)
        "update-knowledge-base": {
            "task": "src.celery.tasks.maintenance_tasks.rebuild_vector_embeddings",
            "schedule": crontab(day_of_week=0, hour=2, minute=0),
        },
    },

    # =========================================================================
    # MONITORING & METRICS
    # =========================================================================
    worker_send_task_events=True,  # Enable task events for monitoring
    task_send_sent_event=True,  # Track task submission
    task_track_started=True,  # Track when tasks start

    # =========================================================================
    # LOGGING
    # =========================================================================
    worker_hijack_root_logger=False,  # Use our structured logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# =============================================================================
# TASK BASE CLASS (Custom Retry Logic)
# =============================================================================

class BaseTask(celery_app.Task):
    """
    Base task class with custom error handling and retry logic
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True  # Add randomness to retry delays

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries"""
        logger.error(
            "task_failed_after_retries",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            args=args,
            kwargs=kwargs,
        )

        # Send alert for critical tasks
        if self.name.startswith("src.celery.tasks.agent_tasks"):
            # TODO: Send Slack/email notification
            pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(
            "task_retry",
            task_id=task_id,
            task_name=self.name,
            exception=str(exc),
            retry_count=self.request.retries,
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(
            "task_success",
            task_id=task_id,
            task_name=self.name,
        )

# Set base task class
celery_app.Task = BaseTask

# =============================================================================
# STARTUP & SHUTDOWN HOOKS
# =============================================================================

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup additional periodic tasks dynamically"""
    logger.info("celery_beat_configured", schedule_count=len(sender.conf.beat_schedule))

@celery_app.on_after_finalize.connect
def setup_celery_monitoring(sender, **kwargs):
    """Initialize monitoring and metrics"""
    logger.info("celery_app_initialized", queues=["high_priority", "default", "low_priority"])

if __name__ == "__main__":
    celery_app.start()
