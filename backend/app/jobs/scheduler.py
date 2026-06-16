"""APScheduler background jobs for snapshot capture and cleanup."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.core.logging import get_logger
from app.database import SessionLocal
from app.services.fortigate_client import FortiGateClient
from app.services.snapshot_service import SnapshotService

logger = get_logger(__name__)

SCHEDULER_TIMEZONE = "America/Bogota"


def take_snapshot_job() -> None:
    """Execute a VPN snapshot capture in its own DB session.

    Wrapped in broad try/except so failures never crash the scheduler.
    """
    start_msg = "snapshot_job_started"
    logger.info(start_msg)
    db = SessionLocal()
    client = FortiGateClient(
        host=settings.fortigate_base_url,
        token=settings.FORTIGATE_TOKEN,
        verify_ssl=settings.FORTIGATE_VERIFY_SSL,
        timeout=settings.FORTIGATE_TIMEOUT_SECONDS,
    )
    try:
        service = SnapshotService(db, client)
        header = service.take_snapshot()
        logger.info(
            "snapshot_job_finished",
            snapshot_id=header.id,
            status=header.status,
        )
    except Exception as exc:
        logger.exception("snapshot_job_crashed", error=str(exc))
    finally:
        client.close()
        db.close()


def cleanup_job() -> int:
    """Execute snapshot retention cleanup in its own DB session."""
    logger.info("cleanup_job_started")
    db = SessionLocal()
    deleted = 0
    try:
        client = FortiGateClient(
            host=settings.fortigate_base_url,
            token=settings.FORTIGATE_TOKEN,
            verify_ssl=settings.FORTIGATE_VERIFY_SSL,
            timeout=settings.FORTIGATE_TIMEOUT_SECONDS,
        )
        service = SnapshotService(db, client)
        deleted = service.cleanup_old_snapshots(settings.SNAPSHOT_RETENTION_DAYS)
        logger.info("cleanup_job_finished", deleted=deleted)
    except Exception as exc:
        logger.exception("cleanup_job_crashed", error=str(exc))
    finally:
        db.close()
    return deleted


def start_scheduler() -> BackgroundScheduler:
    """Create and start the background scheduler with snapshot and cleanup jobs.

    Uses max_instances=1 and coalesce=True to prevent overlapping snapshot
    jobs when FortiGate API responses are slow.
    """
    scheduler = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE)

    scheduler.add_job(
        take_snapshot_job,
        trigger=IntervalTrigger(
            minutes=settings.SCHEDULER_INTERVAL_MINUTES,
            timezone=SCHEDULER_TIMEZONE,
        ),
        id="vpn_snapshot_job",
        name="VPN Snapshot Job",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
        replace_existing=True,
    )

    scheduler.add_job(
        cleanup_job,
        trigger=CronTrigger(
            hour=3,
            minute=0,
            timezone=SCHEDULER_TIMEZONE,
        ),
        id="cleanup_job",
        name="Snapshot Cleanup Job",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        interval_minutes=settings.SCHEDULER_INTERVAL_MINUTES,
        timezone=SCHEDULER_TIMEZONE,
    )
    return scheduler
