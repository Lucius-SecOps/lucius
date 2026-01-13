"""Maintenance Celery tasks."""

from datetime import datetime, timedelta

from shared.logging import get_logger
from talon.celery_app import celery
from talon.extensions import db
from talon.models import Notification, ScanResult

logger = get_logger(__name__)


@celery.task
def cleanup_old_scans(days_to_keep: int = 90) -> dict:
    """
    Clean up old scan results.

    Args:
        days_to_keep: Number of days of scans to retain

    Returns:
        Cleanup summary
    """
    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

    # Count before deletion
    old_scans = ScanResult.query.filter(
        ScanResult.created_at < cutoff
    ).count()

    if old_scans == 0:
        return {"deleted": 0}

    logger.info(f"Cleaning up {old_scans} scans older than {days_to_keep} days")

    # Delete in batches to avoid long transactions
    deleted = 0
    batch_size = 100

    while True:
        batch = ScanResult.query.filter(
            ScanResult.created_at < cutoff
        ).limit(batch_size).all()

        if not batch:
            break

        for scan in batch:
            db.session.delete(scan)

        db.session.commit()
        deleted += len(batch)

    logger.info(f"Deleted {deleted} old scans")

    return {"deleted": deleted}


@celery.task
def cleanup_old_notifications(days_to_keep: int = 30) -> dict:
    """
    Clean up old notification records.

    Args:
        days_to_keep: Number of days of notifications to retain

    Returns:
        Cleanup summary
    """
    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

    # Only clean up sent/failed notifications, keep pending
    deleted = Notification.query.filter(
        Notification.created_at < cutoff,
        Notification.status.in_(["sent", "failed"]),
    ).delete(synchronize_session=False)

    db.session.commit()

    if deleted > 0:
        logger.info(f"Deleted {deleted} old notifications")

    return {"deleted": deleted}


@celery.task
def database_vacuum() -> dict:
    """
    Run PostgreSQL VACUUM ANALYZE for optimization.

    Returns:
        Status
    """
    try:
        from sqlalchemy import text

        # Analyze tables for query optimization
        tables = ["vulnerabilities", "scan_results", "scan_vulnerabilities", "notifications"]

        for table in tables:
            db.session.execute(text(f"ANALYZE {table}"))

        db.session.commit()

        logger.info("Database ANALYZE completed")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return {"status": "error", "message": str(e)}


@celery.task
def retry_failed_notifications(max_age_hours: int = 24) -> dict:
    """
    Retry recently failed notifications.

    Args:
        max_age_hours: Maximum age of notifications to retry

    Returns:
        Retry summary
    """
    from talon.tasks.notifications import send_notification_task

    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    failed = Notification.query.filter(
        Notification.status == "failed",
        Notification.created_at >= cutoff,
        Notification.retry_count < 3,  # Don't retry too many times
    ).all()

    if not failed:
        return {"retried": 0}

    logger.info(f"Retrying {len(failed)} failed notifications")

    for notification in failed:
        send_notification_task.delay(str(notification.id))

    return {"retried": len(failed)}
