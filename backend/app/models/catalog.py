"""Tunnel catalog ORM model for site metadata."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TunnelCatalog(Base, TimestampMixin):
    """Metadata catalog for VPN tunnels (sites, contacts, etc.)."""

    __tablename__ = "vpn_tunnels_catalog"

    tunnel_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    site_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    site_address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    locality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
