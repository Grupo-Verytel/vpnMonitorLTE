"""Pydantic schemas for snapshot data."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SnapshotDetailSchema(BaseModel):
    """Schema for a single tunnel detail within a snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    snapshot_header_id: int
    tunnel_name: str
    p2name: Optional[str] = None
    status: Optional[str] = None
    remote_gateway: Optional[str] = None
    proxy_src: Optional[str] = None
    proxy_dst: Optional[str] = None
    incoming_bytes: Optional[int] = None
    outgoing_bytes: Optional[int] = None
    incoming_bytes_delta: Optional[int] = None
    outgoing_bytes_delta: Optional[int] = None
    creation_time: Optional[int] = None
    connection_count: Optional[int] = None


class SnapshotHeaderSchema(BaseModel):
    """Schema for a snapshot header with optional details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    snapshot_time: datetime
    fortigate_serial: Optional[str] = None
    fortigate_version: Optional[str] = None
    total_tunnels: Optional[int] = None
    tunnels_up: Optional[int] = None
    tunnels_down: Optional[int] = None
    fetch_duration_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    details: List[SnapshotDetailSchema] = Field(default_factory=list)


class SnapshotHeaderBriefSchema(BaseModel):
    """Brief snapshot header without details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    snapshot_time: datetime
    fortigate_serial: Optional[str] = None
    fortigate_version: Optional[str] = None
    total_tunnels: Optional[int] = None
    tunnels_up: Optional[int] = None
    tunnels_down: Optional[int] = None
    fetch_duration_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
