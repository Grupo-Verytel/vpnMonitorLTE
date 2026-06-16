"""Pydantic schemas for tunnel and catalog data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.snapshot import SnapshotDetailSchema


class TunnelCatalogSchema(BaseModel):
    """Schema for tunnel catalog metadata."""

    model_config = ConfigDict(from_attributes=True)

    tunnel_name: str
    site_name: Optional[str] = None
    site_address: Optional[str] = None
    locality: Optional[str] = None
    project_code: Optional[str] = None
    contact_person: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class ActiveTunnelSchema(BaseModel):
    """Tunnel with aggregated traffic in a time window."""

    tunnel_name: str
    total_incoming_delta: int
    total_outgoing_delta: int
    total_traffic_delta: int
    status: Optional[str] = None
    site_name: Optional[str] = None


class TunnelHistoryPointSchema(BaseModel):
    """Single point in a tunnel traffic history series."""

    snapshot_time: datetime
    status: Optional[str] = None
    incoming_bytes: Optional[int] = None
    outgoing_bytes: Optional[int] = None
    incoming_bytes_delta: Optional[int] = None
    outgoing_bytes_delta: Optional[int] = None


class TunnelHistorySchema(BaseModel):
    """Time series history for a tunnel."""

    tunnel_name: str
    hours: int
    points: List[TunnelHistoryPointSchema]


class TunnelDetailSchema(BaseModel):
    """Current tunnel state combined with catalog metadata."""

    tunnel_name: str
    current: Optional[SnapshotDetailSchema] = None
    catalog: Optional[TunnelCatalogSchema] = None
