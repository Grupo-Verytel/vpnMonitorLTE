"""Site list and dashboard queries built on channel inference."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.catalog import TunnelCatalog
from app.schemas.site import (
    ChannelEventsResponse,
    ChannelEventSchema,
    ChannelTimelineBucketSchema,
    ChannelTimelineResponse,
    LocalitiesResponse,
    LteRankingItemSchema,
    LteRankingResponse,
    LteUsageTimelinePointSchema,
    LteUsageTimelineResponse,
    SiteCurrentStateSchema,
    SiteDetailSchema,
    SiteListItemSchema,
    SiteListResponse,
    SitePeriodStatsSchema,
    SitesSummarySchema,
    TrafficHistoryPointSchema,
    TrafficHistoryResponse,
)
from app.schemas.tunnel import TunnelCatalogSchema
from app.services.channel_inference_service import (
    _bogota_day_start_utc_naive,
    _to_iso_utc,
    _utc_now_naive,
    get_inference_service,
)
from app.services.metrics_service import get_current_snapshot


def _get_last_snapshot_time(db: Session) -> datetime | None:
    snapshot = get_current_snapshot(db)
    return snapshot.snapshot_time if snapshot else None


def get_sites_summary(db: Session) -> SitesSummarySchema:
    """Aggregate KPIs from cached inference for all active sites."""
    service = get_inference_service(db)
    inferences = service.infer_channel_for_all_sites()
    total = len(inferences)
    sites_lte = sum(1 for i in inferences if i["channel"] == "LTE")
    sites_fibra = sum(1 for i in inferences if i["channel"] == "FIBRA")
    sites_down = sum(1 for i in inferences if i["channel"] == "DOWN")

    evaluated_at = inferences[0]["evaluated_at"] if inferences else _to_iso_utc(_utc_now_naive())
    last_snapshot = _get_last_snapshot_time(db)

    def pct(n: int) -> float:
        return round(n / total * 100, 1) if total else 0.0

    return SitesSummarySchema(
        evaluated_at=evaluated_at,
        total_sites=total,
        sites_lte=sites_lte,
        sites_fibra=sites_fibra,
        sites_down=sites_down,
        pct_lte=pct(sites_lte),
        pct_fibra=pct(sites_fibra),
        pct_down=pct(sites_down),
        last_snapshot_time=_to_iso_utc(last_snapshot),
    )


def _fetch_catalog_sites(db: Session) -> list[TunnelCatalog]:
    """Active catalog entries (base for v_sites_current equivalent)."""
    return list(
        db.execute(
            select(TunnelCatalog).where(TunnelCatalog.is_active.is_(True))
        ).scalars()
    )


def list_sites(
    db: Session,
    channel: str | None = None,
    locality: str | None = None,
    search: str | None = None,
) -> SiteListResponse:
    """List sites with current channel, catalog info and traffic metrics."""
    service = get_inference_service(db)
    inference_map = {
        item["tunnel_name"]: item for item in service.infer_channel_for_all_sites()
    }
    latest_states = service.get_all_latest_tunnel_states()
    traffic_5m = service.get_all_traffic_last_n_minutes(minutes=5)
    lte_today = service.get_all_lte_minutes_today()
    last_lte_map = service.get_all_last_lte_at()

    catalog_sites = _fetch_catalog_sites(db)
    items: list[SiteListItemSchema] = []

    for catalog in catalog_sites:
        inference = inference_map.get(catalog.tunnel_name, {})
        latest = latest_states.get(catalog.tunnel_name)

        item = SiteListItemSchema(
            tunnel_name=catalog.tunnel_name,
            site_name=catalog.site_name,
            site_address=catalog.site_address,
            locality=catalog.locality,
            project_code=catalog.project_code,
            channel=inference.get("channel", "DOWN"),
            current_status=inference.get("current_status", "down"),
            traffic_bytes_per_min=inference.get("traffic_bytes_per_min", 0.0),
            traffic_last_5m_bytes=traffic_5m.get(catalog.tunnel_name, 0),
            last_lte_at=last_lte_map.get(catalog.tunnel_name),
            lte_minutes_today=lte_today.get(catalog.tunnel_name, 0),
            remote_gateway=latest["remote_gateway"] if latest else None,
        )
        items.append(item)

    if channel:
        items = [i for i in items if i.channel == channel.upper()]

    if locality:
        loc_lower = locality.lower()
        items = [
            i for i in items if i.locality and i.locality.lower() == loc_lower
        ]

    if search:
        term = search.lower()
        items = [
            i
            for i in items
            if term in i.tunnel_name.lower()
            or (i.site_name and term in i.site_name.lower())
        ]

    return SiteListResponse(items=items, total=len(items))


def get_localities(db: Session) -> LocalitiesResponse:
    """Distinct non-null localities from active catalog."""
    rows = db.execute(
        select(TunnelCatalog.locality)
        .where(
            TunnelCatalog.is_active.is_(True),
            TunnelCatalog.locality.isnot(None),
            TunnelCatalog.locality != "",
        )
        .distinct()
        .order_by(TunnelCatalog.locality)
    ).all()
    return LocalitiesResponse(localities=[r[0] for r in rows])


def lte_usage_timeline(db: Session, hours: int = 24) -> LteUsageTimelineResponse:
    """Fleet-wide LTE usage percentage over time."""
    service = get_inference_service(db)
    points = service.get_lte_usage_timeline(hours=hours, bucket_minutes=15)
    return LteUsageTimelineResponse(
        hours=hours,
        points=[LteUsageTimelinePointSchema(**p) for p in points],
    )


def lte_ranking(db: Session, days: int = 7, limit: int = 20) -> LteRankingResponse:
    """Top sites by LTE minutes in the last N days."""
    service = get_inference_service(db)
    items = service.get_lte_ranking(days=days, limit=limit)
    return LteRankingResponse(
        days=days,
        limit=limit,
        items=[LteRankingItemSchema(**item) for item in items],
    )


def _period_stats(
    service,
    tunnel_name: str,
    start: datetime,
    end: datetime,
) -> SitePeriodStatsSchema:
    counts = service.get_channel_minutes_in_range(tunnel_name, start, end, bucket_minutes=15)
    events = service.get_lte_events(
        tunnel_name,
        hours=max(1, int((end - start).total_seconds() / 3600) + 1),
    )
    return SitePeriodStatsSchema(
        lte_minutes=counts["LTE"],
        fibra_minutes=counts["FIBRA"],
        down_minutes=counts["DOWN"] + counts.get("UNKNOWN", 0),
        channel_changes=len(events),
    )


def get_site_detail(db: Session, tunnel_name: str) -> SiteDetailSchema:
    """Full detail for a single site."""
    catalog = db.get(TunnelCatalog, tunnel_name)
    if catalog is None or not catalog.is_active:
        raise NotFoundError(f"Site '{tunnel_name}' not found")

    service = get_inference_service(db)
    inference = service.infer_channel_for_site(tunnel_name)
    latest = service.get_latest_tunnel_state(tunnel_name)

    now = _utc_now_naive()
    day_start = _bogota_day_start_utc_naive()
    week_start = now - timedelta(days=7)

    return SiteDetailSchema(
        tunnel_name=tunnel_name,
        catalog=TunnelCatalogSchema.model_validate(catalog),
        current=SiteCurrentStateSchema(
            channel=inference["channel"],
            status=inference["current_status"],
            traffic_bytes_per_min=inference["traffic_bytes_per_min"],
            remote_gateway=latest["remote_gateway"] if latest else None,
            proxy_destinations=service.get_proxy_destinations(tunnel_name),
        ),
        stats_today=_period_stats(service, tunnel_name, day_start, now),
        stats_week=_period_stats(service, tunnel_name, week_start, now),
    )


def get_site_traffic_history(
    db: Session, tunnel_name: str, hours: int = 24
) -> TrafficHistoryResponse:
    """Traffic time series with per-point channel inference."""
    catalog = db.get(TunnelCatalog, tunnel_name)
    if catalog is None:
        raise NotFoundError(f"Site '{tunnel_name}' not found")

    service = get_inference_service(db)
    points = service.get_traffic_history(tunnel_name, hours=hours)
    return TrafficHistoryResponse(
        tunnel_name=tunnel_name,
        hours=hours,
        points=[TrafficHistoryPointSchema(**p) for p in points],
    )


def get_site_channel_timeline(
    db: Session, tunnel_name: str, hours: int = 24
) -> ChannelTimelineResponse:
    """Channel timeline buckets for a site."""
    catalog = db.get(TunnelCatalog, tunnel_name)
    if catalog is None:
        raise NotFoundError(f"Site '{tunnel_name}' not found")

    service = get_inference_service(db)
    buckets = service.get_channel_timeline(tunnel_name, hours=hours, bucket_minutes=15)
    return ChannelTimelineResponse(
        tunnel_name=tunnel_name,
        hours=hours,
        buckets=[ChannelTimelineBucketSchema(**b) for b in buckets],
    )


def get_site_events(
    db: Session, tunnel_name: str, hours: int = 24
) -> ChannelEventsResponse:
    """Channel change events for a site."""
    catalog = db.get(TunnelCatalog, tunnel_name)
    if catalog is None:
        raise NotFoundError(f"Site '{tunnel_name}' not found")

    service = get_inference_service(db)
    events = service.get_lte_events(tunnel_name, hours=hours)
    return ChannelEventsResponse(
        tunnel_name=tunnel_name,
        hours=hours,
        events=[ChannelEventSchema(**e) for e in events],
    )
