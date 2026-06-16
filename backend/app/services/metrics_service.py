"""Aggregated metrics queries for the REST API."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models.catalog import TunnelCatalog
from app.models.snapshot import SnapshotDetail, SnapshotHeader
from app.schemas.summary import (
    StatusChangeEventSchema,
    SummarySchema,
    TopConsumerSchema,
)
from app.schemas.tunnel import (
    ActiveTunnelSchema,
    TunnelDetailSchema,
    TunnelHistoryPointSchema,
    TunnelHistorySchema,
)


def get_current_snapshot(db: Session) -> Optional[SnapshotHeader]:
    """Return the latest successful snapshot with all details loaded."""
    stmt = (
        select(SnapshotHeader)
        .where(SnapshotHeader.status == "success")
        .options(selectinload(SnapshotHeader.details))
        .order_by(desc(SnapshotHeader.snapshot_time))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_active_tunnels(db: Session, minutes: int = 5) -> List[ActiveTunnelSchema]:
    """Return tunnels with positive traffic delta sum in the given window."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)

    traffic_subq = (
        select(
            SnapshotDetail.tunnel_name,
            func.coalesce(func.sum(SnapshotDetail.incoming_bytes_delta), 0).label(
                "total_incoming"
            ),
            func.coalesce(func.sum(SnapshotDetail.outgoing_bytes_delta), 0).label(
                "total_outgoing"
            ),
        )
        .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
        .where(
            SnapshotHeader.status == "success",
            SnapshotHeader.snapshot_time >= cutoff,
        )
        .group_by(SnapshotDetail.tunnel_name)
        .having(
            func.coalesce(func.sum(SnapshotDetail.incoming_bytes_delta), 0)
            + func.coalesce(func.sum(SnapshotDetail.outgoing_bytes_delta), 0)
            > 0
        )
        .subquery()
    )

    latest_status_subq = (
        select(
            SnapshotDetail.tunnel_name,
            SnapshotDetail.status,
            func.row_number()
            .over(
                partition_by=SnapshotDetail.tunnel_name,
                order_by=desc(SnapshotHeader.snapshot_time),
            )
            .label("rn"),
        )
        .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
        .where(SnapshotHeader.status == "success")
        .subquery()
    )

    catalog_subq = select(TunnelCatalog).subquery()

    stmt = (
        select(
            traffic_subq.c.tunnel_name,
            traffic_subq.c.total_incoming,
            traffic_subq.c.total_outgoing,
            latest_status_subq.c.status,
            catalog_subq.c.site_name,
        )
        .join(
            latest_status_subq,
            (traffic_subq.c.tunnel_name == latest_status_subq.c.tunnel_name)
            & (latest_status_subq.c.rn == 1),
            isouter=True,
        )
        .join(
            catalog_subq,
            traffic_subq.c.tunnel_name == catalog_subq.c.tunnel_name,
            isouter=True,
        )
        .order_by(
            (traffic_subq.c.total_incoming + traffic_subq.c.total_outgoing).desc()
        )
    )

    rows = db.execute(stmt).all()
    return [
        ActiveTunnelSchema(
            tunnel_name=row.tunnel_name,
            total_incoming_delta=int(row.total_incoming or 0),
            total_outgoing_delta=int(row.total_outgoing or 0),
            total_traffic_delta=int((row.total_incoming or 0) + (row.total_outgoing or 0)),
            status=row.status,
            site_name=row.site_name,
        )
        for row in rows
    ]


def get_tunnel_history(
    db: Session, tunnel_name: str, hours: int = 24
) -> TunnelHistorySchema:
    """Return time series data for a tunnel over the given hours."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)

    stmt = (
        select(
            SnapshotHeader.snapshot_time,
            SnapshotDetail.status,
            SnapshotDetail.incoming_bytes,
            SnapshotDetail.outgoing_bytes,
            SnapshotDetail.incoming_bytes_delta,
            SnapshotDetail.outgoing_bytes_delta,
        )
        .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
        .where(
            SnapshotDetail.tunnel_name == tunnel_name,
            SnapshotHeader.status == "success",
            SnapshotHeader.snapshot_time >= cutoff,
        )
        .order_by(SnapshotHeader.snapshot_time.asc())
    )

    rows = db.execute(stmt).all()
    points = [
        TunnelHistoryPointSchema(
            snapshot_time=row.snapshot_time,
            status=row.status,
            incoming_bytes=row.incoming_bytes,
            outgoing_bytes=row.outgoing_bytes,
            incoming_bytes_delta=row.incoming_bytes_delta,
            outgoing_bytes_delta=row.outgoing_bytes_delta,
        )
        for row in rows
    ]

    return TunnelHistorySchema(tunnel_name=tunnel_name, hours=hours, points=points)


def get_tunnel_detail(db: Session, tunnel_name: str) -> TunnelDetailSchema:
    """Return current tunnel state plus catalog metadata."""
    snapshot = get_current_snapshot(db)
    current_detail = None
    if snapshot:
        for detail in snapshot.details:
            if detail.tunnel_name == tunnel_name:
                current_detail = detail
                break

    catalog = db.get(TunnelCatalog, tunnel_name)

    if current_detail is None and catalog is None:
        raise NotFoundError(f"Tunnel '{tunnel_name}' not found")

    from app.schemas.snapshot import SnapshotDetailSchema
    from app.schemas.tunnel import TunnelCatalogSchema

    return TunnelDetailSchema(
        tunnel_name=tunnel_name,
        current=SnapshotDetailSchema.model_validate(current_detail)
        if current_detail
        else None,
        catalog=TunnelCatalogSchema.model_validate(catalog) if catalog else None,
    )


def get_summary(db: Session) -> SummarySchema:
    """Return KPI summary from the latest successful snapshot."""
    snapshot = get_current_snapshot(db)
    if not snapshot:
        return SummarySchema()

    total = snapshot.total_tunnels or 0
    up = snapshot.tunnels_up or 0
    down = snapshot.tunnels_down or 0
    availability = (up / (up + down) * 100) if (up + down) > 0 else 0.0

    return SummarySchema(
        snapshot_time=snapshot.snapshot_time,
        total_tunnels=total,
        tunnels_up=up,
        tunnels_down=down,
        availability_percent=round(availability, 2),
        fortigate_serial=snapshot.fortigate_serial,
        fortigate_version=snapshot.fortigate_version,
    )


def get_top_consumers(
    db: Session, limit: int = 10, minutes: int = 5
) -> List[TopConsumerSchema]:
    """Return top tunnels by traffic consumption in a time window."""
    active = get_active_tunnels(db, minutes=minutes)
    active.sort(key=lambda t: t.total_traffic_delta, reverse=True)
    return [
        TopConsumerSchema(
            tunnel_name=t.tunnel_name,
            site_name=t.site_name,
            total_incoming_delta=t.total_incoming_delta,
            total_outgoing_delta=t.total_outgoing_delta,
            total_traffic_delta=t.total_traffic_delta,
        )
        for t in active[:limit]
    ]


def get_status_changes(
    db: Session, hours: int = 24
) -> List[StatusChangeEventSchema]:
    """Detect tunnel status changes (up↔down) within the time window."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)

    stmt = (
        select(
            SnapshotDetail.tunnel_name,
            SnapshotDetail.status,
            SnapshotHeader.snapshot_time,
        )
        .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
        .where(
            SnapshotHeader.status == "success",
            SnapshotHeader.snapshot_time >= cutoff,
        )
        .order_by(SnapshotDetail.tunnel_name, SnapshotHeader.snapshot_time.asc())
    )

    rows = db.execute(stmt).all()
    events: list[StatusChangeEventSchema] = []
    last_status: dict[str, str | None] = {}

    catalog_cache: dict[str, str | None] = {}

    for row in rows:
        prev = last_status.get(row.tunnel_name)
        if prev is not None and prev != row.status:
            if row.tunnel_name not in catalog_cache:
                cat = db.get(TunnelCatalog, row.tunnel_name)
                catalog_cache[row.tunnel_name] = cat.site_name if cat else None

            events.append(
                StatusChangeEventSchema(
                    tunnel_name=row.tunnel_name,
                    previous_status=prev,
                    new_status=row.status,
                    changed_at=row.snapshot_time,
                    site_name=catalog_cache.get(row.tunnel_name),
                )
            )
        last_status[row.tunnel_name] = row.status

    events.sort(key=lambda e: e.changed_at, reverse=True)
    return events
