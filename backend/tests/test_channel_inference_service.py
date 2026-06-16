"""Tests for LTE/Fibra channel inference service."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.catalog import TunnelCatalog
from app.models.snapshot import SnapshotDetail, SnapshotHeader
from app.services.channel_inference_service import (
    CHANNEL_DOWN,
    CHANNEL_FIBRA,
    CHANNEL_LTE,
    CHANNEL_UNKNOWN,
    ChannelInferenceService,
    _ALL_SITES_CACHE,
)

THRESHOLD = 10240
WINDOW = 15


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _seed_catalog(db: Session, tunnel_name: str = "TUNNEL-01") -> None:
    db.add(
        TunnelCatalog(
            tunnel_name=tunnel_name,
            site_name="Sitio Test",
            is_active=True,
        )
    )
    db.commit()


def _seed_snapshot(
    db: Session,
    tunnel_name: str,
    *,
    status: str = "up",
    incoming_delta: int = 0,
    outgoing_delta: int = 0,
    minutes_ago: int = 0,
    p2name: str | None = None,
) -> SnapshotHeader:
    snap_time = _utc_now() - timedelta(minutes=minutes_ago)
    header = SnapshotHeader(
        snapshot_time=snap_time,
        status="success",
        total_tunnels=1,
        tunnels_up=1 if status == "up" else 0,
        tunnels_down=0 if status == "up" else 1,
    )
    db.add(header)
    db.flush()
    db.add(
        SnapshotDetail(
            snapshot_header_id=header.id,
            tunnel_name=tunnel_name,
            p2name=p2name,
            status=status,
            incoming_bytes_delta=incoming_delta,
            outgoing_bytes_delta=outgoing_delta,
            remote_gateway="10.0.0.1",
        )
    )
    db.commit()
    return header


@pytest.fixture(autouse=True)
def clear_inference_cache() -> None:
    _ALL_SITES_CACHE.clear()
    yield
    _ALL_SITES_CACHE.clear()


@pytest.fixture
def service(db_session: Session) -> ChannelInferenceService:
    return ChannelInferenceService(
        db=db_session,
        threshold_bytes_per_min=THRESHOLD,
        window_minutes=WINDOW,
    )


def test_no_snapshots_returns_down(service: ChannelInferenceService, db_session: Session) -> None:
    _seed_catalog(db_session)
    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["channel"] == CHANNEL_DOWN
    assert result["current_status"] == "down"
    assert result["snapshots_count"] == 0


def test_status_down_returns_down(service: ChannelInferenceService, db_session: Session) -> None:
    _seed_catalog(db_session)
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="down",
        incoming_delta=50000,
        outgoing_delta=50000,
        minutes_ago=1,
    )
    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["channel"] == CHANNEL_DOWN
    assert result["current_status"] == "down"


def test_status_up_high_traffic_returns_lte(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    # 20 KB total over ~1 min → above 10 KB/min threshold
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="up",
        incoming_delta=10000,
        outgoing_delta=10000,
        minutes_ago=2,
    )
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="up",
        incoming_delta=10000,
        outgoing_delta=10000,
        minutes_ago=1,
    )
    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["channel"] == CHANNEL_LTE
    assert result["current_status"] == "up"
    assert result["traffic_bytes_per_min"] >= THRESHOLD


def test_status_up_low_traffic_returns_fibra(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="up",
        incoming_delta=100,
        outgoing_delta=100,
        minutes_ago=2,
    )
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="up",
        incoming_delta=100,
        outgoing_delta=100,
        minutes_ago=1,
    )
    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["channel"] == CHANNEL_FIBRA
    assert result["current_status"] == "up"
    assert result["traffic_bytes_per_min"] < THRESHOLD


def test_multiple_proxyids_aggregated(
    service: ChannelInferenceService, db_session: Session
) -> None:
    """Two Phase-2 rows in the same snapshot should sum deltas."""
    _seed_catalog(db_session)
    snap_time = _utc_now() - timedelta(minutes=1)
    header = SnapshotHeader(snapshot_time=snap_time, status="success")
    db_session.add(header)
    db_session.flush()
    for p2, delta in [("p2-a", 6000), ("p2-b", 6000)]:
        db_session.add(
            SnapshotDetail(
                snapshot_header_id=header.id,
                tunnel_name="TUNNEL-01",
                p2name=p2,
                status="up",
                incoming_bytes_delta=delta,
                outgoing_bytes_delta=0,
            )
        )
    db_session.commit()

    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["channel"] == CHANNEL_LTE
    assert result["total_bytes_in_window"] == 12000


def test_timeline_groups_by_buckets(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    base = _utc_now().replace(second=0, microsecond=0) - timedelta(hours=2)

    for i in range(4):
        header = SnapshotHeader(
            snapshot_time=base + timedelta(minutes=i * 15),
            status="success",
        )
        db_session.add(header)
        db_session.flush()
        db_session.add(
            SnapshotDetail(
                snapshot_header_id=header.id,
                tunnel_name="TUNNEL-01",
                status="up",
                incoming_bytes_delta=15000,
                outgoing_bytes_delta=0,
            )
        )
    db_session.commit()

    timeline = service.get_channel_timeline("TUNNEL-01", hours=3, bucket_minutes=15)
    assert len(timeline) >= 1
    channels = {b["channel"] for b in timeline if b["total_bytes"] > 0}
    assert CHANNEL_LTE in channels


def test_timeline_empty_bucket_is_unknown(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    _seed_snapshot(
        db_session,
        "TUNNEL-01",
        status="up",
        incoming_delta=500,
        minutes_ago=30,
    )
    timeline = service.get_channel_timeline("TUNNEL-01", hours=2, bucket_minutes=15)
    unknown_buckets = [b for b in timeline if b["channel"] == CHANNEL_UNKNOWN]
    assert len(unknown_buckets) >= 1


def test_events_detect_channel_changes(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    base = _utc_now().replace(second=0, microsecond=0) - timedelta(hours=3)

    # First hour: low traffic (FIBRA), second hour: high traffic (LTE)
    scenarios = [
        (0, 100, "up"),
        (15, 100, "up"),
        (60, 20000, "up"),
        (75, 20000, "up"),
    ]
    for offset_min, delta, st in scenarios:
        header = SnapshotHeader(
            snapshot_time=base + timedelta(minutes=offset_min),
            status="success",
        )
        db_session.add(header)
        db_session.flush()
        db_session.add(
            SnapshotDetail(
                snapshot_header_id=header.id,
                tunnel_name="TUNNEL-01",
                status=st,
                incoming_bytes_delta=delta,
                outgoing_bytes_delta=0,
            )
        )
    db_session.commit()

    events = service.get_lte_events("TUNNEL-01", hours=4)
    transitions = {(e["from_channel"], e["to_channel"]) for e in events}
    assert (CHANNEL_FIBRA, CHANNEL_LTE) in transitions


def test_gap_marks_data_incomplete(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session)
    _seed_snapshot(db_session, "TUNNEL-01", status="up", incoming_delta=100, minutes_ago=10)
    _seed_snapshot(db_session, "TUNNEL-01", status="up", incoming_delta=100, minutes_ago=1)
    result = service.infer_channel_for_site("TUNNEL-01")
    assert result["data_complete"] is False


def test_infer_all_sites_cached(
    service: ChannelInferenceService, db_session: Session
) -> None:
    _seed_catalog(db_session, "TUNNEL-A")
    _seed_catalog(db_session, "TUNNEL-B")
    _seed_snapshot(db_session, "TUNNEL-A", status="up", incoming_delta=500, minutes_ago=1)

    first = service.infer_channel_for_all_sites()
    second = service.infer_channel_for_all_sites()
    assert first is second  # same cached list object
    assert len(first) == 2
