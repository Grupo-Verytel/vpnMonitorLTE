"""Health and root endpoints."""

from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, Request
from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.config import settings
from app.models.snapshot import SnapshotHeader
from app.schemas.summary import HealthResponse, ServiceInfoResponse

router = APIRouter(tags=["health"])


@router.get("/", response_model=ServiceInfoResponse)
def root() -> ServiceInfoResponse:
    """Return basic service information."""
    return ServiceInfoResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


def _get_next_snapshot_time(scheduler: Optional[BackgroundScheduler]) -> Optional[str]:
    """Extract next run time for the snapshot job."""
    if not scheduler:
        return None
    job = scheduler.get_job("vpn_snapshot_job")
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None


def _get_active_job_ids(scheduler: Optional[BackgroundScheduler]) -> list[str]:
    """List IDs of scheduled jobs."""
    if not scheduler:
        return []
    return [job.id for job in scheduler.get_jobs()]


@router.get("/health", response_model=HealthResponse)
def health(request: Request, db: DbSession) -> HealthResponse:
    """Health check endpoint for Railway and monitoring."""
    scheduler: Optional[BackgroundScheduler] = getattr(
        request.app.state, "scheduler", None
    )
    scheduler_running = scheduler.running if scheduler else False

    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    last_snapshot_time: Optional[str] = None
    last_snapshot_status: Optional[str] = None
    try:
        stmt = (
            select(SnapshotHeader)
            .order_by(desc(SnapshotHeader.snapshot_time))
            .limit(1)
        )
        last = db.execute(stmt).scalar_one_or_none()
        if last:
            last_snapshot_time = last.snapshot_time.isoformat()
            last_snapshot_status = last.status
    except Exception:
        pass

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        scheduler_running=scheduler_running,
        active_jobs=_get_active_job_ids(scheduler),
        next_snapshot=_get_next_snapshot_time(scheduler),
        last_snapshot_time=last_snapshot_time,
        last_snapshot_status=last_snapshot_status,
        db_connected=db_connected,
    )
