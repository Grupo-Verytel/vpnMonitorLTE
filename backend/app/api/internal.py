"""Internal protected endpoints for manual job triggers."""

from fastapi import APIRouter, Depends

from app.api.deps import verify_internal_token
from app.config import settings
from app.core.logging import get_logger
from app.database import SessionLocal
from app.jobs.scheduler import cleanup_job, take_snapshot_job
router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_internal_token)],
)

logger = get_logger(__name__)


@router.post("/trigger-snapshot")
def trigger_snapshot() -> dict[str, str | int]:
    """Manually trigger a VPN snapshot capture."""
    logger.info("manual_snapshot_triggered")
    take_snapshot_job()
    return {"status": "triggered", "message": "Snapshot job executed"}


@router.post("/cleanup")
def trigger_cleanup() -> dict[str, str | int]:
    """Manually trigger snapshot retention cleanup."""
    logger.info("manual_cleanup_triggered")
    deleted = cleanup_job()
    return {
        "status": "completed",
        "deleted_headers": deleted,
        "retention_days": settings.SNAPSHOT_RETENTION_DAYS,
    }
