"""Metrics and KPI API endpoints."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.summary import (
    StatusChangesResponse,
    SummarySchema,
    TopConsumersResponse,
)
from app.services import metrics_service

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/summary", response_model=SummarySchema)
def get_summary(db: DbSession) -> SummarySchema:
    """Return KPI summary from the latest successful snapshot."""
    return metrics_service.get_summary(db)


@router.get("/top-consumers", response_model=TopConsumersResponse)
def get_top_consumers(
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=100),
    minutes: int = Query(default=5, ge=1, le=1440),
) -> TopConsumersResponse:
    """Return top tunnels by traffic consumption."""
    consumers = metrics_service.get_top_consumers(db, limit=limit, minutes=minutes)
    return TopConsumersResponse(minutes=minutes, limit=limit, consumers=consumers)


@router.get("/status-changes", response_model=StatusChangesResponse)
def get_status_changes(
    db: DbSession,
    hours: int = Query(default=24, ge=1, le=720),
) -> StatusChangesResponse:
    """Return tunnel status change events in the given window."""
    events = metrics_service.get_status_changes(db, hours=hours)
    return StatusChangesResponse(hours=hours, events=events)
