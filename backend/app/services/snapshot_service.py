"""Snapshot capture and retention logic."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import FortiGateAPIError
from app.core.logging import get_logger
from app.models.catalog import TunnelCatalog
from app.models.snapshot import SnapshotDetail, SnapshotHeader
from app.services.fortigate_client import FortiGateClient

logger = get_logger(__name__)


class SnapshotService:
    """Orchestrates VPN snapshot capture, delta calculation, and cleanup."""

    def __init__(self, db: Session, fortigate_client: FortiGateClient) -> None:
        self._db = db
        self._client = fortigate_client

    def take_snapshot(self) -> SnapshotHeader:
        """Capture a VPN snapshot from FortiGate and persist to database.

        Returns:
            The created SnapshotHeader (success or error status).
        """
        start = datetime.now(timezone.utc)
        fetch_start = datetime.now(timezone.utc)

        try:
            system_status = self._client.get_system_status()
            tunnel_data = self._client.get_ipsec_tunnels()
            fetch_duration_ms = int(
                (datetime.now(timezone.utc) - fetch_start).total_seconds() * 1000
            )

            serial = self._safe_str(system_status.get("results", {}).get("serial"), max_len=50)
            version = self._safe_str(system_status.get("results", {}).get("version"), max_len=20)
            tunnels = tunnel_data.get("results", [])

            tunnels_up, tunnels_down = self._count_tunnel_statuses(tunnels)
            catalog_created = self._sync_catalog_from_tunnels(tunnels)

            header = SnapshotHeader(
                snapshot_time=start.replace(tzinfo=None),
                fortigate_serial=serial,
                fortigate_version=version,
                total_tunnels=len(tunnels),
                tunnels_up=tunnels_up,
                tunnels_down=tunnels_down,
                fetch_duration_ms=fetch_duration_ms,
                status="success",
            )
            self._db.add(header)
            self._db.flush()

            previous_details = self._get_previous_snapshot_details(exclude_header_id=header.id)
            detail_rows = self._build_detail_rows(header.id, tunnels, previous_details)
            self._db.add_all(detail_rows)
            self._db.commit()
            self._db.refresh(header)

            logger.info(
                "snapshot_completed",
                tunnels=len(tunnels),
                tunnels_up=tunnels_up,
                tunnels_down=tunnels_down,
                catalog_created=catalog_created,
                duration_ms=fetch_duration_ms,
                snapshot_id=header.id,
            )
            return header

        except FortiGateAPIError as exc:
            return self._save_error_snapshot(start, str(exc.message))
        except Exception as exc:
            logger.exception("snapshot_unexpected_error", error=str(exc))
            return self._save_error_snapshot(start, str(exc))

    def _save_error_snapshot(
        self, start: datetime, error_message: str
    ) -> SnapshotHeader:
        """Persist a snapshot header with error status."""
        self._db.rollback()
        header = SnapshotHeader(
            snapshot_time=start.replace(tzinfo=None),
            status="error",
            error_message=error_message,
        )
        self._db.add(header)
        self._db.commit()
        self._db.refresh(header)
        logger.error("snapshot_failed", error=error_message, snapshot_id=header.id)
        return header

    def _count_tunnel_statuses(self, tunnels: list[dict[str, Any]]) -> tuple[int, int]:
        """Count up/down proxy entries across all tunnels."""
        up = 0
        down = 0
        for tunnel in tunnels:
            for proxy in tunnel.get("proxyid", []):
                if proxy.get("status") == "up":
                    up += 1
                else:
                    down += 1
        return up, down

    def _sync_catalog_from_tunnels(self, tunnels: list[dict[str, Any]]) -> int:
        """Create catalog entries for FortiGate tunnels not yet in vpn_tunnels_catalog."""
        tunnel_meta: dict[str, dict[str, Any]] = {}
        for tunnel in tunnels:
            name = self._safe_str(tunnel.get("name"), max_len=100)
            if not name:
                continue
            tunnel_meta[name] = tunnel

        if not tunnel_meta:
            return 0

        tunnel_names = list(tunnel_meta.keys())
        existing = set(
            self._db.execute(
                select(TunnelCatalog.tunnel_name).where(
                    TunnelCatalog.tunnel_name.in_(tunnel_names)
                )
            ).scalars()
        )

        new_rows: list[TunnelCatalog] = []
        for name, tunnel in tunnel_meta.items():
            if name in existing:
                continue
            new_rows.append(
                TunnelCatalog(
                    tunnel_name=name,
                    site_name=name,
                    site_address=self._safe_str(tunnel.get("comments"), max_len=300),
                    is_active=True,
                    notes="Auto-creado desde FortiGate",
                )
            )

        if new_rows:
            self._db.add_all(new_rows)
            logger.info(
                "catalog_sync_completed",
                created=len(new_rows),
                tunnel_names=[row.tunnel_name for row in new_rows],
            )

        return len(new_rows)

    def _get_previous_snapshot(self, exclude_header_id: int | None = None) -> Optional[SnapshotHeader]:
        """Return the most recent successful snapshot header, optionally excluding one."""
        stmt = select(SnapshotHeader).where(SnapshotHeader.status == "success")
        if exclude_header_id is not None:
            stmt = stmt.where(SnapshotHeader.id != exclude_header_id)
        stmt = stmt.order_by(desc(SnapshotHeader.snapshot_time)).limit(1)
        return self._db.execute(stmt).scalar_one_or_none()

    def _get_previous_snapshot_details(
        self, exclude_header_id: int | None = None
    ) -> dict[str, SnapshotDetail]:
        """Map previous snapshot details by composite key tunnel|p2name."""
        previous = self._get_previous_snapshot(exclude_header_id=exclude_header_id)
        if not previous:
            return {}

        stmt = select(SnapshotDetail).where(
            SnapshotDetail.snapshot_header_id == previous.id
        )
        details = self._db.execute(stmt).scalars().all()
        return {
            f"{d.tunnel_name}|{d.p2name or ''}": d
            for d in details
        }

    def _build_detail_rows(
        self,
        header_id: int,
        tunnels: list[dict[str, Any]],
        previous_details: dict[str, SnapshotDetail],
    ) -> list[SnapshotDetail]:
        """Build detail rows with delta calculations for each proxy."""
        rows: list[SnapshotDetail] = []

        for tunnel in tunnels:
            tunnel_name = self._safe_str(tunnel.get("name"), max_len=100) or "unknown"
            proxy_list = tunnel.get("proxyid", [])

            if not proxy_list:
                rows.append(
                    SnapshotDetail(
                        snapshot_header_id=header_id,
                        tunnel_name=tunnel_name,
                        status=self._safe_str(tunnel.get("status"), max_len=10),
                        remote_gateway=self._safe_str(tunnel.get("rgwy"), max_len=50),
                    )
                )
                continue

            for proxy in proxy_list:
                p2name = self._safe_str(proxy.get("p2name"), max_len=100)
                key = f"{tunnel_name}|{p2name or ''}"
                prev = previous_details.get(key)

                incoming = self._safe_int(proxy.get("incoming_bytes"))
                outgoing = self._safe_int(proxy.get("outgoing_bytes"))
                prev_incoming = prev.incoming_bytes if prev else None
                prev_outgoing = prev.outgoing_bytes if prev else None

                incoming_delta = self._calc_delta(
                    incoming, prev_incoming, tunnel_name, "incoming"
                )
                outgoing_delta = self._calc_delta(
                    outgoing, prev_outgoing, tunnel_name, "outgoing"
                )

                rows.append(
                    SnapshotDetail(
                        snapshot_header_id=header_id,
                        tunnel_name=tunnel_name,
                        p2name=p2name,
                        status=self._safe_str(proxy.get("status"), max_len=10),
                        remote_gateway=self._safe_str(tunnel.get("rgwy"), max_len=50),
                        proxy_src=self._safe_str(proxy.get("proxy_src")),
                        proxy_dst=self._safe_str(proxy.get("proxy_dst")),
                        incoming_bytes=incoming,
                        outgoing_bytes=outgoing,
                        incoming_bytes_delta=incoming_delta,
                        outgoing_bytes_delta=outgoing_delta,
                        creation_time=self._safe_int(proxy.get("creation_time")),
                        connection_count=self._safe_int(proxy.get("connection_count")),
                    )
                )

        return rows

    def _calc_delta(
        self,
        current: Optional[int],
        previous: Optional[int],
        tunnel_name: str,
        counter_type: str,
    ) -> Optional[int]:
        """Calculate byte delta, handling FortiGate counter resets.

        If current < previous, the counter was reset (Phase 2 renegotiation)
        and we treat the delta as the current value.
        """
        if current is None:
            return None
        if previous is None:
            return current

        if current < previous:
            logger.warning(
                "counter_reset_detected",
                tunnel=tunnel_name,
                counter_type=counter_type,
                current=current,
                previous=previous,
            )
            return current

        return current - previous

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert a value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_str(value: Any, max_len: int = 255) -> Optional[str]:
        """Coerce FortiGate field values to a DB-safe string.

        FortiGate returns proxy_src/proxy_dst as lists of selector objects;
        PyMySQL cannot bind dict/list values to VARCHAR columns.
        """
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        else:
            text = str(value)
        if not text:
            return None
        return text[:max_len]

    def cleanup_old_snapshots(self, days: int) -> int:
        """Delete snapshot headers older than N days (details cascade).

        Returns:
            Number of deleted headers.
        """
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        stmt = (
            delete(SnapshotHeader)
            .where(SnapshotHeader.snapshot_time < cutoff)
            .execution_options(synchronize_session=False)
        )
        result = self._db.execute(stmt)
        self._db.commit()
        deleted = result.rowcount or 0
        logger.info("snapshot_cleanup_completed", deleted=deleted, retention_days=days)
        return deleted
