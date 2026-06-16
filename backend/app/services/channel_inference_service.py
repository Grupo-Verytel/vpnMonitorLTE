"""LTE/Fibra channel inference from VPN snapshot traffic deltas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from cachetools import TTLCache
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.catalog import TunnelCatalog
from app.models.snapshot import SnapshotDetail, SnapshotHeader

# Module-level cache shared across requests (TTL 30s per frontend refresh cadence).
_ALL_SITES_CACHE: TTLCache = TTLCache(maxsize=4, ttl=30)

GAP_THRESHOLD_MINUTES = 5
CHANNEL_LTE = "LTE"
CHANNEL_FIBRA = "FIBRA"
CHANNEL_DOWN = "DOWN"
CHANNEL_UNKNOWN = "UNKNOWN"

BOGOTA_TZ = ZoneInfo("America/Bogota")


def _utc_now_naive() -> datetime:
    """Current UTC as naive datetime (consistent with DB storage)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_iso_utc(dt: datetime | None) -> str | None:
    """Serialize naive-UTC datetime to ISO 8601 with Z suffix."""
    if dt is None:
        return None
    aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    return aware.strftime("%Y-%m-%dT%H:%M:%SZ")


def _bogota_day_start_utc_naive() -> datetime:
    """Midnight today in Bogotá, converted to naive UTC for DB filters."""
    now_bogota = datetime.now(BOGOTA_TZ)
    start_bogota = now_bogota.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_bogota.astimezone(timezone.utc)
    return start_utc.replace(tzinfo=None)


def _tunnel_status_expr():
    """Aggregate proxyid rows: 'up' if any Phase-2 SA is up."""
    return case(
        (func.sum(case((SnapshotDetail.status == "up", 1), else_=0)) > 0, "up"),
        else_="down",
    )


def _has_snapshot_gaps(times: list[datetime], gap_minutes: int = GAP_THRESHOLD_MINUTES) -> bool:
    """True when consecutive snapshots are farther apart than the gap threshold."""
    if len(times) < 2:
        return False
    threshold_seconds = gap_minutes * 60
    for prev, curr in zip(times, times[1:]):
        if (curr - prev).total_seconds() > threshold_seconds:
            return True
    return False


def _elapsed_minutes(first: datetime | None, last: datetime | None) -> float:
    """Minutes between first and last snapshot; minimum 1 to avoid division by zero."""
    if first is None or last is None:
        return 1.0
    minutes = (last - first).total_seconds() / 60.0
    return max(minutes, 1.0)


def _classify_channel(
    status: str | None,
    bytes_per_min: float,
    threshold: int,
) -> str:
    if status is None:
        return CHANNEL_DOWN
    if status.lower() == "down":
        return CHANNEL_DOWN
    if status.lower() == "up":
        return CHANNEL_LTE if bytes_per_min >= threshold else CHANNEL_FIBRA
    return CHANNEL_DOWN


class ChannelInferenceService:
    """Determina si un sitio está usando LTE o Fibra basado en deltas de tráfico."""

    def __init__(
        self,
        db: Session,
        threshold_bytes_per_min: int,
        window_minutes: int,
    ) -> None:
        self._db = db
        self._threshold = threshold_bytes_per_min
        self._window = window_minutes

    def _aggregated_snapshots_stmt(
        self,
        cutoff: datetime,
        tunnel_name: str | None = None,
    ):
        """Per-snapshot aggregates for one or all tunnels since cutoff."""
        status_expr = _tunnel_status_expr().label("status")
        incoming_delta_expr = func.coalesce(
            func.sum(SnapshotDetail.incoming_bytes_delta), 0
        ).label("incoming_delta")
        outgoing_delta_expr = func.coalesce(
            func.sum(SnapshotDetail.outgoing_bytes_delta), 0
        ).label("outgoing_delta")
        total_delta_expr = (incoming_delta_expr + outgoing_delta_expr).label("total_delta")

        stmt = (
            select(
                SnapshotDetail.tunnel_name,
                SnapshotHeader.id.label("header_id"),
                SnapshotHeader.snapshot_time,
                status_expr,
                incoming_delta_expr,
                outgoing_delta_expr,
                total_delta_expr,
            )
            .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
            .where(
                SnapshotHeader.status == "success",
                SnapshotHeader.snapshot_time >= cutoff,
            )
            .group_by(
                SnapshotDetail.tunnel_name,
                SnapshotHeader.id,
                SnapshotHeader.snapshot_time,
            )
            .order_by(SnapshotDetail.tunnel_name, SnapshotHeader.snapshot_time)
        )
        if tunnel_name is not None:
            stmt = stmt.where(SnapshotDetail.tunnel_name == tunnel_name)
        return stmt

    def _infer_from_rows(
        self,
        tunnel_name: str,
        rows: list[Any],
        evaluated_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Apply inference rules to pre-fetched per-snapshot rows for one tunnel."""
        evaluated_at = evaluated_at or _utc_now_naive()

        if not rows:
            return {
                "tunnel_name": tunnel_name,
                "channel": CHANNEL_DOWN,
                "current_status": "down",
                "traffic_bytes_per_min": 0.0,
                "total_bytes_in_window": 0,
                "window_minutes": self._window,
                "snapshots_count": 0,
                "data_complete": False,
                "evaluated_at": _to_iso_utc(evaluated_at),
            }

        times = [r.snapshot_time for r in rows]
        total_bytes = sum(int(r.total_delta or 0) for r in rows)
        latest = rows[-1]
        data_complete = not _has_snapshot_gaps(times)
        bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
        channel = _classify_channel(latest.status, bytes_per_min, self._threshold)

        return {
            "tunnel_name": tunnel_name,
            "channel": channel,
            "current_status": (latest.status or "down").lower(),
            "traffic_bytes_per_min": round(bytes_per_min, 2),
            "total_bytes_in_window": total_bytes,
            "window_minutes": self._window,
            "snapshots_count": len(rows),
            "data_complete": data_complete,
            "evaluated_at": _to_iso_utc(evaluated_at),
        }

    def infer_channel_for_site(self, tunnel_name: str) -> dict[str, Any]:
        """Infer channel for a single tunnel_name (all proxyids aggregated per snapshot)."""
        cutoff = _utc_now_naive() - timedelta(minutes=self._window)
        stmt = self._aggregated_snapshots_stmt(cutoff, tunnel_name=tunnel_name)
        rows = list(self._db.execute(stmt).all())
        return self._infer_from_rows(tunnel_name, rows)

    def infer_channel_for_all_sites(self) -> list[dict[str, Any]]:
        """Infer channel for every active catalog tunnel (cached 30s)."""
        cache_key = (self._threshold, self._window)
        cached = _ALL_SITES_CACHE.get(cache_key)
        if cached is not None:
            return cached

        evaluated_at = _utc_now_naive()
        cutoff = evaluated_at - timedelta(minutes=self._window)

        catalog_tunnels = list(
            self._db.execute(
                select(TunnelCatalog.tunnel_name).where(TunnelCatalog.is_active.is_(True))
            ).scalars()
        )

        stmt = self._aggregated_snapshots_stmt(cutoff)
        all_rows = self._db.execute(stmt).all()

        by_tunnel: dict[str, list[Any]] = {name: [] for name in catalog_tunnels}
        for row in all_rows:
            if row.tunnel_name in by_tunnel:
                by_tunnel[row.tunnel_name].append(row)

        results = [
            self._infer_from_rows(name, by_tunnel[name], evaluated_at=evaluated_at)
            for name in catalog_tunnels
        ]
        _ALL_SITES_CACHE[cache_key] = results
        return results

    def get_channel_timeline(
        self,
        tunnel_name: str,
        hours: int = 24,
        bucket_minutes: int = 15,
    ) -> list[dict[str, Any]]:
        """Time series of inferred channel per fixed-width bucket."""
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        stmt = self._aggregated_snapshots_stmt(cutoff, tunnel_name=tunnel_name)
        rows = list(self._db.execute(stmt).all())

        if not rows:
            return []

        bucket_delta = timedelta(minutes=bucket_minutes)
        start = rows[0].snapshot_time
        # Align first bucket to snapshot start (floor to bucket boundary).
        start = start.replace(second=0, microsecond=0)
        start = start - timedelta(minutes=start.minute % bucket_minutes)

        end = _utc_now_naive()
        timeline: list[dict[str, Any]] = []
        bucket_start = start

        while bucket_start < end:
            bucket_end = bucket_start + bucket_delta
            bucket_rows = [
                r for r in rows if bucket_start <= r.snapshot_time < bucket_end
            ]

            if not bucket_rows:
                timeline.append(
                    {
                        "bucket_start": _to_iso_utc(bucket_start),
                        "bucket_end": _to_iso_utc(bucket_end),
                        "channel": CHANNEL_UNKNOWN,
                        "total_bytes": 0,
                        "bytes_per_min": 0.0,
                    }
                )
            else:
                times = [r.snapshot_time for r in bucket_rows]
                total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                latest = bucket_rows[-1]
                channel = _classify_channel(latest.status, bytes_per_min, self._threshold)
                timeline.append(
                    {
                        "bucket_start": _to_iso_utc(bucket_start),
                        "bucket_end": _to_iso_utc(bucket_end),
                        "channel": channel,
                        "total_bytes": total_bytes,
                        "bytes_per_min": round(bytes_per_min, 2),
                    }
                )

            bucket_start = bucket_end

        return timeline

    def get_lte_events(self, tunnel_name: str, hours: int = 24) -> list[dict[str, Any]]:
        """Detect channel transitions between consecutive timeline buckets."""
        timeline = self.get_channel_timeline(
            tunnel_name, hours=hours, bucket_minutes=15
        )
        events: list[dict[str, Any]] = []
        prev_channel: str | None = None
        prev_timestamp: datetime | None = None

        for bucket in timeline:
            channel = bucket["channel"]
            if channel == CHANNEL_UNKNOWN:
                continue
            ts = datetime.strptime(
                bucket["bucket_start"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            ts_naive = ts.replace(tzinfo=None)

            if prev_channel is not None and channel != prev_channel:
                duration_minutes: int | None = None
                if prev_timestamp is not None:
                    duration_minutes = int(
                        (ts_naive - prev_timestamp).total_seconds() / 60
                    )
                events.append(
                    {
                        "timestamp": bucket["bucket_start"],
                        "from_channel": prev_channel,
                        "to_channel": channel,
                        "duration_minutes": duration_minutes,
                    }
                )

            prev_channel = channel
            prev_timestamp = ts_naive

        return events

    def get_lte_total_minutes_today(self, tunnel_name: str) -> int:
        """Minutes in LTE today (midnight Bogotá → now), 1-minute bucket resolution."""
        day_start = _bogota_day_start_utc_naive()
        now = _utc_now_naive()
        hours = max(1, int((now - day_start).total_seconds() / 3600) + 1)

        stmt = self._aggregated_snapshots_stmt(day_start, tunnel_name=tunnel_name)
        rows = list(self._db.execute(stmt).all())
        if not rows:
            return 0

        bucket_minutes = 1
        bucket_delta = timedelta(minutes=bucket_minutes)
        lte_minutes = 0
        bucket_start = day_start.replace(second=0, microsecond=0)

        while bucket_start < now:
            bucket_end = bucket_start + bucket_delta
            bucket_rows = [
                r for r in rows if bucket_start <= r.snapshot_time < bucket_end
            ]
            if bucket_rows:
                times = [r.snapshot_time for r in bucket_rows]
                total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                channel = _classify_channel(
                    bucket_rows[-1].status, bytes_per_min, self._threshold
                )
                if channel == CHANNEL_LTE:
                    lte_minutes += bucket_minutes
            bucket_start = bucket_end

        return lte_minutes

    def get_channel_minutes_in_range(
        self,
        tunnel_name: str,
        start: datetime,
        end: datetime,
        bucket_minutes: int = 1,
    ) -> dict[str, int]:
        """Count minutes per channel between start and end (inclusive start)."""
        stmt = self._aggregated_snapshots_stmt(start, tunnel_name=tunnel_name)
        rows = [r for r in self._db.execute(stmt).all() if r.snapshot_time < end]

        counts = {CHANNEL_LTE: 0, CHANNEL_FIBRA: 0, CHANNEL_DOWN: 0, CHANNEL_UNKNOWN: 0}
        if not rows:
            counts[CHANNEL_DOWN] = int((end - start).total_seconds() / 60)
            return counts

        bucket_delta = timedelta(minutes=bucket_minutes)
        bucket_start = start.replace(second=0, microsecond=0)

        while bucket_start < end:
            bucket_end = min(bucket_start + bucket_delta, end)
            bucket_rows = [
                r for r in rows if bucket_start <= r.snapshot_time < bucket_end
            ]
            minutes_in_bucket = int((bucket_end - bucket_start).total_seconds() / 60)
            if minutes_in_bucket <= 0:
                bucket_start = bucket_end
                continue

            if not bucket_rows:
                counts[CHANNEL_UNKNOWN] += minutes_in_bucket
            else:
                times = [r.snapshot_time for r in bucket_rows]
                total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                channel = _classify_channel(
                    bucket_rows[-1].status, bytes_per_min, self._threshold
                )
                counts[channel] += minutes_in_bucket

            bucket_start = bucket_end

        return counts

    def get_last_lte_at(self, tunnel_name: str, hours: int = 168) -> str | None:
        """Last bucket_start where channel was LTE within the lookback window."""
        timeline = self.get_channel_timeline(tunnel_name, hours=hours, bucket_minutes=15)
        for bucket in reversed(timeline):
            if bucket["channel"] == CHANNEL_LTE:
                return bucket["bucket_start"]
        return None

    def get_traffic_last_n_minutes(self, tunnel_name: str, minutes: int = 5) -> int:
        """Sum of traffic deltas in the last N minutes."""
        cutoff = _utc_now_naive() - timedelta(minutes=minutes)
        stmt = (
            select(
                func.coalesce(func.sum(SnapshotDetail.incoming_bytes_delta), 0)
                + func.coalesce(func.sum(SnapshotDetail.outgoing_bytes_delta), 0)
            )
            .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
            .where(
                SnapshotDetail.tunnel_name == tunnel_name,
                SnapshotHeader.status == "success",
                SnapshotHeader.snapshot_time >= cutoff,
            )
        )
        total = self._db.execute(stmt).scalar_one()
        return int(total or 0)

    def get_all_latest_tunnel_states(self) -> dict[str, dict[str, Any]]:
        """Latest aggregated state for every tunnel in one query."""
        latest_header_id = (
            select(func.max(SnapshotHeader.id))
            .where(SnapshotHeader.status == "success")
            .scalar_subquery()
        )

        stmt = (
            select(
                SnapshotHeader.snapshot_time,
                SnapshotDetail.tunnel_name,
                _tunnel_status_expr().label("status"),
                func.max(SnapshotDetail.remote_gateway).label("remote_gateway"),
            )
            .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
            .where(SnapshotHeader.id == latest_header_id)
            .group_by(SnapshotHeader.snapshot_time, SnapshotDetail.tunnel_name)
        )
        return {
            row.tunnel_name: {
                "snapshot_time": row.snapshot_time,
                "status": row.status,
                "remote_gateway": row.remote_gateway,
            }
            for row in self._db.execute(stmt).all()
        }

    def get_all_traffic_last_n_minutes(self, minutes: int = 5) -> dict[str, int]:
        """Sum of traffic deltas per tunnel in the last N minutes (single query)."""
        cutoff = _utc_now_naive() - timedelta(minutes=minutes)
        stmt = (
            select(
                SnapshotDetail.tunnel_name,
                (
                    func.coalesce(func.sum(SnapshotDetail.incoming_bytes_delta), 0)
                    + func.coalesce(func.sum(SnapshotDetail.outgoing_bytes_delta), 0)
                ).label("total"),
            )
            .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
            .where(
                SnapshotHeader.status == "success",
                SnapshotHeader.snapshot_time >= cutoff,
            )
            .group_by(SnapshotDetail.tunnel_name)
        )
        return {row.tunnel_name: int(row.total or 0) for row in self._db.execute(stmt).all()}

    def get_all_lte_minutes_today(self) -> dict[str, int]:
        """LTE minutes today per tunnel (single query + in-memory bucket classification)."""
        day_start = _bogota_day_start_utc_naive()
        now = _utc_now_naive()
        stmt = self._aggregated_snapshots_stmt(day_start)
        all_rows = self._db.execute(stmt).all()

        by_tunnel: dict[str, list[Any]] = {}
        for row in all_rows:
            by_tunnel.setdefault(row.tunnel_name, []).append(row)

        result: dict[str, int] = {}
        bucket_delta = timedelta(minutes=1)
        bucket_start = day_start.replace(second=0, microsecond=0)

        for tunnel_name, rows in by_tunnel.items():
            lte_minutes = 0
            current = bucket_start
            while current < now:
                bucket_end = current + bucket_delta
                bucket_rows = [r for r in rows if current <= r.snapshot_time < bucket_end]
                if bucket_rows:
                    times = [r.snapshot_time for r in bucket_rows]
                    total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                    bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                    if (
                        _classify_channel(
                            bucket_rows[-1].status, bytes_per_min, self._threshold
                        )
                        == CHANNEL_LTE
                    ):
                        lte_minutes += 1
                current = bucket_end
            result[tunnel_name] = lte_minutes

        return result

    def get_all_last_lte_at(self, hours: int = 168) -> dict[str, str | None]:
        """Last LTE bucket timestamp per tunnel from a single data fetch."""
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        stmt = self._aggregated_snapshots_stmt(cutoff)
        all_rows = self._db.execute(stmt).all()

        by_tunnel: dict[str, list[Any]] = {}
        for row in all_rows:
            by_tunnel.setdefault(row.tunnel_name, []).append(row)

        bucket_minutes = 15
        bucket_delta = timedelta(minutes=bucket_minutes)
        result: dict[str, str | None] = {}

        for tunnel_name, rows in by_tunnel.items():
            if not rows:
                result[tunnel_name] = None
                continue

            start = rows[0].snapshot_time.replace(second=0, microsecond=0)
            start = start - timedelta(minutes=start.minute % bucket_minutes)
            end = _utc_now_naive()
            last_lte: str | None = None
            bucket_start = start

            while bucket_start < end:
                bucket_end = bucket_start + bucket_delta
                bucket_rows = [
                    r for r in rows if bucket_start <= r.snapshot_time < bucket_end
                ]
                if bucket_rows:
                    times = [r.snapshot_time for r in bucket_rows]
                    total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                    bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                    channel = _classify_channel(
                        bucket_rows[-1].status, bytes_per_min, self._threshold
                    )
                    if channel == CHANNEL_LTE:
                        last_lte = _to_iso_utc(bucket_start)
                bucket_start = bucket_end

            result[tunnel_name] = last_lte

        return result

    def get_latest_tunnel_state(self, tunnel_name: str) -> dict[str, Any] | None:
        """Latest aggregated tunnel row (equivalent to v_latest_tunnel_state)."""
        latest_header_id = (
            select(func.max(SnapshotHeader.id))
            .where(SnapshotHeader.status == "success")
            .scalar_subquery()
        )

        stmt = (
            select(
                SnapshotHeader.snapshot_time,
                SnapshotDetail.tunnel_name,
                _tunnel_status_expr().label("status"),
                func.coalesce(func.sum(SnapshotDetail.incoming_bytes), 0).label(
                    "incoming_bytes"
                ),
                func.coalesce(func.sum(SnapshotDetail.outgoing_bytes), 0).label(
                    "outgoing_bytes"
                ),
                func.max(SnapshotDetail.remote_gateway).label("remote_gateway"),
            )
            .join(SnapshotHeader, SnapshotDetail.snapshot_header_id == SnapshotHeader.id)
            .where(
                SnapshotHeader.id == latest_header_id,
                SnapshotDetail.tunnel_name == tunnel_name,
            )
            .group_by(
                SnapshotHeader.snapshot_time,
                SnapshotDetail.tunnel_name,
            )
        )
        row = self._db.execute(stmt).first()
        if row is None:
            return None
        return {
            "snapshot_time": row.snapshot_time,
            "tunnel_name": row.tunnel_name,
            "status": row.status,
            "incoming_bytes": int(row.incoming_bytes or 0),
            "outgoing_bytes": int(row.outgoing_bytes or 0),
            "remote_gateway": row.remote_gateway,
        }

    def get_proxy_destinations(self, tunnel_name: str) -> list[str]:
        """Distinct proxy_dst values from the latest snapshot for a tunnel."""
        latest_header_id = (
            select(func.max(SnapshotHeader.id))
            .where(SnapshotHeader.status == "success")
            .scalar_subquery()
        )
        stmt = (
            select(SnapshotDetail.proxy_dst)
            .where(
                SnapshotDetail.snapshot_header_id == latest_header_id,
                SnapshotDetail.tunnel_name == tunnel_name,
                SnapshotDetail.proxy_dst.isnot(None),
            )
            .distinct()
        )
        return [row[0] for row in self._db.execute(stmt).all() if row[0]]

    def get_traffic_history(
        self, tunnel_name: str, hours: int = 24
    ) -> list[dict[str, Any]]:
        """Per-snapshot traffic series with inferred channel."""
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        stmt = self._aggregated_snapshots_stmt(cutoff, tunnel_name=tunnel_name)
        rows = list(self._db.execute(stmt).all())

        history: list[dict[str, Any]] = []
        for i, row in enumerate(rows):
            total_delta = int(row.total_delta or 0)
            # bytes_per_min for this point: delta vs previous snapshot interval.
            if i > 0:
                prev = rows[i - 1]
                minutes = _elapsed_minutes(prev.snapshot_time, row.snapshot_time)
                bytes_per_min = total_delta / minutes
            else:
                bytes_per_min = float(total_delta)

            incoming = int(row.incoming_delta or 0)
            outgoing = int(row.outgoing_delta or 0)
            channel = _classify_channel(row.status, bytes_per_min, self._threshold)
            history.append(
                {
                    "timestamp": _to_iso_utc(row.snapshot_time),
                    "incoming_bytes": incoming,
                    "outgoing_bytes": outgoing,
                    "total_bytes": incoming + outgoing,
                    "bytes_per_min": round(bytes_per_min, 2),
                    "channel": channel,
                }
            )
        return history

    def get_lte_usage_timeline(self, hours: int = 24, bucket_minutes: int = 15) -> list[dict]:
        """Percentage of active catalog sites per channel over time buckets."""
        cutoff = _utc_now_naive() - timedelta(hours=hours)
        catalog_tunnels = list(
            self._db.execute(
                select(TunnelCatalog.tunnel_name).where(TunnelCatalog.is_active.is_(True))
            ).scalars()
        )
        total_sites = len(catalog_tunnels)
        if total_sites == 0:
            return []

        stmt = self._aggregated_snapshots_stmt(cutoff)
        all_rows = self._db.execute(stmt).all()
        by_tunnel: dict[str, list[Any]] = {name: [] for name in catalog_tunnels}
        for row in all_rows:
            if row.tunnel_name in by_tunnel:
                by_tunnel[row.tunnel_name].append(row)

        bucket_delta = timedelta(minutes=bucket_minutes)
        start = cutoff.replace(second=0, microsecond=0)
        start = start - timedelta(minutes=start.minute % bucket_minutes)
        end = _utc_now_naive()

        timeline: list[dict] = []
        bucket_start = start

        while bucket_start < end:
            bucket_end = bucket_start + bucket_delta
            sites_lte = sites_fibra = sites_down = 0

            for tunnel_name in catalog_tunnels:
                tunnel_rows = by_tunnel[tunnel_name]
                bucket_rows = [
                    r for r in tunnel_rows if bucket_start <= r.snapshot_time < bucket_end
                ]
                if not bucket_rows:
                    sites_down += 1
                    continue

                times = [r.snapshot_time for r in bucket_rows]
                total_bytes = sum(int(r.total_delta or 0) for r in bucket_rows)
                bytes_per_min = total_bytes / _elapsed_minutes(times[0], times[-1])
                channel = _classify_channel(
                    bucket_rows[-1].status, bytes_per_min, self._threshold
                )
                if channel == CHANNEL_LTE:
                    sites_lte += 1
                elif channel == CHANNEL_FIBRA:
                    sites_fibra += 1
                else:
                    sites_down += 1

            pct_lte = round(sites_lte / total_sites * 100, 1) if total_sites else 0.0
            timeline.append(
                {
                    "timestamp": _to_iso_utc(bucket_start),
                    "sites_lte": sites_lte,
                    "sites_fibra": sites_fibra,
                    "sites_down": sites_down,
                    "pct_lte": pct_lte,
                }
            )
            bucket_start = bucket_end

        return timeline

    def get_lte_ranking(self, days: int = 7, limit: int = 20) -> list[dict[str, Any]]:
        """Top tunnels by LTE minutes in the last N days."""
        cutoff = _utc_now_naive() - timedelta(days=days)
        catalog_rows = self._db.execute(
            select(TunnelCatalog.tunnel_name, TunnelCatalog.site_name).where(
                TunnelCatalog.is_active.is_(True)
            )
        ).all()

        rankings: list[dict[str, Any]] = []
        for tunnel_name, site_name in catalog_rows:
            counts = self.get_channel_minutes_in_range(
                tunnel_name, cutoff, _utc_now_naive(), bucket_minutes=15
            )
            rankings.append(
                {
                    "tunnel_name": tunnel_name,
                    "site_name": site_name,
                    "lte_minutes": counts[CHANNEL_LTE],
                    "fibra_minutes": counts[CHANNEL_FIBRA],
                    "down_minutes": counts[CHANNEL_DOWN],
                    "total_minutes": sum(counts.values()),
                }
            )

        rankings.sort(key=lambda r: r["lte_minutes"], reverse=True)
        return rankings[:limit]


def get_inference_service(db: Session) -> ChannelInferenceService:
    """Factory using application settings."""
    from app.config import settings

    return ChannelInferenceService(
        db=db,
        threshold_bytes_per_min=settings.LTE_TRAFFIC_THRESHOLD_BYTES_PER_MIN,
        window_minutes=settings.LTE_EVALUATION_WINDOW_MINUTES,
    )
