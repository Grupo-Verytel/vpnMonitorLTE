"""Snapshot header and detail ORM models."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# BigInteger in MySQL; Integer variant for SQLite tests (autoincrement quirk)
_pk_type = BigInteger().with_variant(Integer, "sqlite")


class SnapshotHeader(Base):
    """Represents a single VPN monitoring snapshot taken from FortiGate."""

    __tablename__ = "vpn_snapshot_headers"

    id: Mapped[int] = mapped_column(_pk_type, primary_key=True, autoincrement=True)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, server_default=func.now()
    )
    fortigate_serial: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fortigate_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    total_tunnels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tunnels_up: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tunnels_down: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fetch_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    details: Mapped[List["SnapshotDetail"]] = relationship(
        "SnapshotDetail",
        back_populates="header",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_vpn_snapshot_headers_snapshot_time_desc", snapshot_time.desc()),
    )


class SnapshotDetail(Base):
    """Per-tunnel/proxy detail row within a snapshot."""

    __tablename__ = "vpn_snapshot_details"

    id: Mapped[int] = mapped_column(_pk_type, primary_key=True, autoincrement=True)
    snapshot_header_id: Mapped[int] = mapped_column(
        _pk_type,
        ForeignKey("vpn_snapshot_headers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tunnel_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    p2name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    remote_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    proxy_src: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    proxy_dst: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    incoming_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    outgoing_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    incoming_bytes_delta: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    outgoing_bytes_delta: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    creation_time: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    connection_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    header: Mapped["SnapshotHeader"] = relationship(
        "SnapshotHeader", back_populates="details"
    )

    __table_args__ = (
        Index(
            "ix_vpn_snapshot_details_tunnel_header",
            "tunnel_name",
            "snapshot_header_id",
        ),
    )
