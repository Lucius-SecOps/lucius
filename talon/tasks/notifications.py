"""Notification Celery tasks."""

from shared.logging import get_logger
from talon.celery_app import celery
from talon.models import Notification
from talon.services.notification_service import NotificationService

logger = get_logger(__name__)


@celery.task(bind=True, max_retries=3)
def send_notification_task(self, notification_id: str) -> dict:
    """
    Send a single notification.

    Args:
        notification_id: UUID of the notification to send

    Returns:
        Result dict with status
    """
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            logger.error(f"Notification not found: {notification_id}")
            return {"status": "error", "message": "Notification not found"}

        service = NotificationService()
        success = service.send_notification(notification)

        return {
            "status": "sent" if success else "failed",
            "notification_id": notification_id,
        }

    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}")

        # Retry with exponential backoff
        try:
            self.retry(countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for notification {notification_id}")
            return {"status": "failed", "message": str(e)}


@celery.task
def process_pending_notifications() -> dict:
    """
    Process all pending notifications.

    This task runs periodically via Celery Beat.

    Returns:
        Summary of processed notifications
    """
    pending = Notification.query.filter_by(status="pending").limit(100).all()

    if not pending:
        return {"processed": 0}

    logger.info(f"Processing {len(pending)} pending notifications")

    sent = 0

    for notification in pending:
        send_notification_task.delay(str(notification.id))
        sent += 1

    return {"queued": sent}


@celery.task
def send_critical_alert(
    project_name: str,
    critical_count: int,
    scan_id: str,
) -> dict:
    """
    Send alert for critical vulnerabilities.

    Args:
        project_name: Name of the affected project
        critical_count: Number of critical vulnerabilities
        scan_id: ID of the scan

    Returns:
        Alert result
    """
    service = NotificationService()

    title = f"🚨 Critical Vulnerabilities in {project_name}"
    message = (
        f"*{critical_count} critical vulnerabilities* detected in `{project_name}`.\n\n"
        f"Scan ID: `{scan_id}`\n\n"
        f"Immediate review recommended."
    )

    results = service.send_alert(
        title=title,
        message=message,
        severity="critical",
        channels=["slack"],
    )

    logger.info(f"Critical alert sent for {project_name}: {results}")

    return {"status": "sent", "results": results}


@celery.task
def send_daily_summary() -> dict:
    """
    Send daily vulnerability summary.

    Returns:
        Summary result
    """
    from datetime import datetime, timedelta

    from talon.models import ScanResult

    # Get stats for last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)

    scans = ScanResult.query.filter(ScanResult.created_at >= yesterday).all()

    if not scans:
        return {"status": "skipped", "reason": "No scans in last 24 hours"}

    total_scans = len(scans)
    total_critical = sum(s.critical_count for s in scans)
    total_high = sum(s.high_count for s in scans)

    title = "📊 Daily Vulnerability Summary"
    message = (
        f"*Scans in last 24 hours:* {total_scans}\n"
        f"*Critical vulnerabilities:* {total_critical}\n"
        f"*High vulnerabilities:* {total_high}\n"
    )

    if total_critical > 0:
        message += "\n⚠️ *Action required:* Critical vulnerabilities detected."

    service = NotificationService()
    results = service.send_alert(
        title=title,
        message=message,
        severity="medium" if total_critical == 0 else "high",
        channels=["slack"],
    )

    return {"status": "sent", "results": results}
