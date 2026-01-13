"""Celery application configuration."""

from celery import Celery

from talon.config import config

# Create Celery instance
celery = Celery("talon")

# Configure Celery
celery.conf.update(
    broker_url=config.celery.broker_url,
    result_backend=config.celery.result_backend,
    task_serializer=config.celery.task_serializer,
    result_serializer=config.celery.result_serializer,
    accept_content=config.celery.accept_content,
    timezone=config.celery.timezone,
    enable_utc=config.celery.enable_utc,
    task_track_started=config.celery.task_track_started,
    task_time_limit=config.celery.task_time_limit,
    worker_prefetch_multiplier=config.celery.worker_prefetch_multiplier,
    # Beat schedule for periodic tasks
    beat_schedule={
        "process-pending-notifications": {
            "task": "talon.tasks.notifications.process_pending_notifications",
            "schedule": 60.0,  # Every minute
        },
        "update-threat-scores": {
            "task": "talon.tasks.threat_scoring.update_threat_scores",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-old-scans": {
            "task": "talon.tasks.maintenance.cleanup_old_scans",
            "schedule": 86400.0,  # Daily
        },
    },
)


class ContextTask(celery.Task):
    """Celery task with Flask application context."""

    def __call__(self, *args, **kwargs):
        from talon.app import create_app
        
        app = create_app()
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

# Import tasks to register them
from talon.tasks import notifications, threat_scoring, maintenance  # noqa
