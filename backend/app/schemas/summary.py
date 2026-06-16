"""Pydantic schemas for metrics and summary endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SummarySchema(BaseModel):
    """KPI summary from the latest successful snapshot."""

    snapshot_time: Optional[datetime] = None
    total_tunnels: int = 0
    tunnels_up: int = 0
    tunnels_down: int = 0
    availability_percent: float = 0.0
    fortigate_serial: Optional[str] = None
    fortigate_version: Optional[str] = None


class TopConsumerSchema(BaseModel):
    """Top traffic consumer in a time window."""

    tunnel_name: str
    site_name: Optional[str] = None
    total_incoming_delta: int
    total_outgoing_delta: int
    total_traffic_delta: int


class TopConsumersResponse(BaseModel):
    """Response wrapper for top consumers list."""

    minutes: int
    limit: int
    consumers: List[TopConsumerSchema]


class StatusChangeEventSchema(BaseModel):
    """Event representing a tunnel status change."""

    tunnel_name: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    changed_at: datetime
    site_name: Optional[str] = None


class StatusChangesResponse(BaseModel):
    """Response wrapper for status change events."""

    hours: int
    events: List[StatusChangeEventSchema]


class HealthResponse(BaseModel):
    """Health check response for Railway and monitoring."""

    status: str
    scheduler_running: bool
    active_jobs: List[str]
    next_snapshot: Optional[str] = None
    last_snapshot_time: Optional[str] = None
    last_snapshot_status: Optional[str] = None
    db_connected: bool


class ServiceInfoResponse(BaseModel):
    """Basic service information."""

    name: str
    version: str
    environment: str
