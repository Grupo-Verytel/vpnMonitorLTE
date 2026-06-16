"""Pydantic schemas for site channel inference and dashboard endpoints."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tunnel import TunnelCatalogSchema

ChannelType = Literal["LTE", "FIBRA", "DOWN", "UNKNOWN"]


class ChannelInferenceSchema(BaseModel):
    """Result of channel inference for a single site."""

    tunnel_name: str
    channel: ChannelType
    current_status: str
    traffic_bytes_per_min: float
    total_bytes_in_window: int
    window_minutes: int
    snapshots_count: int
    data_complete: bool = True
    evaluated_at: str


class SitesSummarySchema(BaseModel):
    """KPI summary for the sites dashboard."""

    evaluated_at: str
    total_sites: int
    sites_lte: int
    sites_fibra: int
    sites_down: int
    pct_lte: float
    pct_fibra: float
    pct_down: float
    last_snapshot_time: Optional[str] = None


class SiteListItemSchema(BaseModel):
    """Single site row for the sites list view."""

    tunnel_name: str
    site_name: Optional[str] = None
    site_address: Optional[str] = None
    locality: Optional[str] = None
    project_code: Optional[str] = None
    channel: ChannelType
    current_status: str
    traffic_bytes_per_min: float
    traffic_last_5m_bytes: int
    last_lte_at: Optional[str] = None
    lte_minutes_today: int
    remote_gateway: Optional[str] = None


class SiteListResponse(BaseModel):
    """Paginated-style list wrapper for sites."""

    items: List[SiteListItemSchema]
    total: int


class LocalitiesResponse(BaseModel):
    """Distinct localities for filter dropdown."""

    localities: List[str]


class LteUsageTimelinePointSchema(BaseModel):
    """One point in the fleet-wide LTE usage timeline."""

    timestamp: str
    sites_lte: int
    sites_fibra: int
    sites_down: int
    pct_lte: float


class LteUsageTimelineResponse(BaseModel):
    """Fleet LTE usage over time."""

    hours: int
    points: List[LteUsageTimelinePointSchema]


class LteRankingItemSchema(BaseModel):
    """Site ranked by LTE usage."""

    tunnel_name: str
    site_name: Optional[str] = None
    lte_minutes: int
    fibra_minutes: int
    down_minutes: int
    total_minutes: int


class LteRankingResponse(BaseModel):
    """Top sites by LTE minutes."""

    days: int
    limit: int
    items: List[LteRankingItemSchema]


class SiteCurrentStateSchema(BaseModel):
    """Current channel and traffic state for site detail."""

    channel: ChannelType
    status: str
    traffic_bytes_per_min: float
    remote_gateway: Optional[str] = None
    proxy_destinations: List[str] = Field(default_factory=list)


class SitePeriodStatsSchema(BaseModel):
    """Channel time breakdown for a period."""

    lte_minutes: int
    fibra_minutes: int
    down_minutes: int
    channel_changes: int


class SiteDetailSchema(BaseModel):
    """Full site detail for the detail screen."""

    tunnel_name: str
    catalog: Optional[TunnelCatalogSchema] = None
    current: SiteCurrentStateSchema
    stats_today: SitePeriodStatsSchema
    stats_week: SitePeriodStatsSchema


class TrafficHistoryPointSchema(BaseModel):
    """Traffic data point with inferred channel."""

    timestamp: str
    incoming_bytes: int
    outgoing_bytes: int
    total_bytes: int
    bytes_per_min: float
    channel: ChannelType


class TrafficHistoryResponse(BaseModel):
    """Traffic history for a site."""

    tunnel_name: str
    hours: int
    points: List[TrafficHistoryPointSchema]


class ChannelTimelineBucketSchema(BaseModel):
    """One bucket in the channel timeline."""

    bucket_start: str
    bucket_end: str
    channel: ChannelType
    total_bytes: int
    bytes_per_min: float


class ChannelTimelineResponse(BaseModel):
    """Channel timeline for a site."""

    tunnel_name: str
    hours: int
    buckets: List[ChannelTimelineBucketSchema]


class ChannelEventSchema(BaseModel):
    """Channel transition event."""

    timestamp: str
    from_channel: ChannelType
    to_channel: ChannelType
    duration_minutes: Optional[int] = None


class ChannelEventsResponse(BaseModel):
    """Channel change events for a site."""

    tunnel_name: str
    hours: int
    events: List[ChannelEventSchema]
