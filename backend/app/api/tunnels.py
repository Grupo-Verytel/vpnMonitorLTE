"""Tunnel monitoring API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.core.exceptions import NotFoundError
from app.schemas.snapshot import SnapshotHeaderSchema
from app.schemas.tunnel import ActiveTunnelSchema, TunnelDetailSchema, TunnelHistorySchema
from app.services import metrics_service

router = APIRouter(prefix="/api/tunnels", tags=["tunnels"])


@router.get("/current", response_model=SnapshotHeaderSchema)
def get_current_tunnels(db: DbSession) -> SnapshotHeaderSchema:
    """Return the latest successful snapshot with all tunnel details."""
    snapshot = metrics_service.get_current_snapshot(db)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No successful snapshot available",
        )
    return SnapshotHeaderSchema.model_validate(snapshot)


@router.get("/active", response_model=list[ActiveTunnelSchema])
def get_active_tunnels(
    db: DbSession,
    minutes: int = Query(default=5, ge=1, le=1440),
) -> list[ActiveTunnelSchema]:
    """Return tunnels with positive traffic in the given time window."""
    return metrics_service.get_active_tunnels(db, minutes=minutes)


@router.get("/{tunnel_name}/history", response_model=TunnelHistorySchema)
def get_tunnel_history(
    tunnel_name: str,
    db: DbSession,
    hours: int = Query(default=24, ge=1, le=720),
) -> TunnelHistorySchema:
    """Return traffic history time series for a tunnel."""
    return metrics_service.get_tunnel_history(db, tunnel_name, hours=hours)


@router.get("/{tunnel_name}/detail", response_model=TunnelDetailSchema)
def get_tunnel_detail(tunnel_name: str, db: DbSession) -> TunnelDetailSchema:
    """Return current tunnel state combined with catalog metadata."""
    try:
        return metrics_service.get_tunnel_detail(db, tunnel_name)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
