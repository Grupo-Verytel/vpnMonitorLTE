"""Tests for SnapshotService delta calculation and capture."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.snapshot import SnapshotDetail, SnapshotHeader
from app.services.snapshot_service import SnapshotService


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock FortiGateClient with default successful responses."""
    client = MagicMock()
    client.get_system_status.return_value = {
        "results": {"serial": "FGTEST", "version": "v7.4.0"}
    }
    client.get_ipsec_tunnels.return_value = {
        "results": [
            {
                "name": "site-tunnel-1",
                "rgwy": "192.168.1.1",
                "proxyid": [
                    {
                        "p2name": "p2-1",
                        "status": "up",
                        "incoming_bytes": 5000,
                        "outgoing_bytes": 3000,
                        "creation_time": 1700000000,
                        "connection_count": 1,
                    }
                ],
            }
        ]
    }
    return client


def test_calc_delta_normal() -> None:
    """Normal delta is current minus previous."""
    service = SnapshotService(MagicMock(), MagicMock())
    assert service._calc_delta(1000, 400, "t1", "incoming") == 600


def test_calc_delta_counter_reset() -> None:
    """Counter reset returns current value when current < previous."""
    service = SnapshotService(MagicMock(), MagicMock())
    assert service._calc_delta(200, 5000, "t1", "incoming") == 200


def test_calc_delta_first_snapshot() -> None:
    """First snapshot delta equals current value."""
    service = SnapshotService(MagicMock(), MagicMock())
    assert service._calc_delta(800, None, "t1", "outgoing") == 800


def test_take_snapshot_first_run(db_session: Session, mock_client: MagicMock) -> None:
    """First snapshot stores header and details with delta = current bytes."""
    service = SnapshotService(db_session, mock_client)
    header = service.take_snapshot()

    assert header.status == "success"
    assert header.total_tunnels == 1
    assert header.tunnels_up == 1
    assert header.tunnels_down == 0

    details = (
        db_session.query(SnapshotDetail)
        .filter(SnapshotDetail.snapshot_header_id == header.id)
        .all()
    )
    assert len(details) == 1
    assert details[0].incoming_bytes_delta == 5000
    assert details[0].outgoing_bytes_delta == 3000


def test_take_snapshot_with_delta(db_session: Session, mock_client: MagicMock) -> None:
    """Second snapshot calculates deltas from previous."""
    service = SnapshotService(db_session, mock_client)

    first = service.take_snapshot()
    assert first.status == "success"

    mock_client.get_ipsec_tunnels.return_value = {
        "results": [
            {
                "name": "site-tunnel-1",
                "rgwy": "192.168.1.1",
                "proxyid": [
                    {
                        "p2name": "p2-1",
                        "status": "up",
                        "incoming_bytes": 7000,
                        "outgoing_bytes": 4500,
                    }
                ],
            }
        ]
    }

    second = service.take_snapshot()
    details = (
        db_session.query(SnapshotDetail)
        .filter(SnapshotDetail.snapshot_header_id == second.id)
        .all()
    )
    assert details[0].incoming_bytes_delta == 2000
    assert details[0].outgoing_bytes_delta == 1500


def test_take_snapshot_counter_reset(db_session: Session, mock_client: MagicMock) -> None:
    """Counter reset uses current value as delta."""
    service = SnapshotService(db_session, mock_client)
    service.take_snapshot()

    mock_client.get_ipsec_tunnels.return_value = {
        "results": [
            {
                "name": "site-tunnel-1",
                "proxyid": [
                    {
                        "p2name": "p2-1",
                        "status": "up",
                        "incoming_bytes": 100,
                        "outgoing_bytes": 50,
                    }
                ],
            }
        ]
    }

    second = service.take_snapshot()
    details = (
        db_session.query(SnapshotDetail)
        .filter(SnapshotDetail.snapshot_header_id == second.id)
        .all()
    )
    assert details[0].incoming_bytes_delta == 100
    assert details[0].outgoing_bytes_delta == 50


def test_take_snapshot_with_proxy_selectors_as_lists(
    db_session: Session, mock_client: MagicMock
) -> None:
    """FortiGate proxy_src/proxy_dst are lists — must serialize to string for MySQL."""
    mock_client.get_ipsec_tunnels.return_value = {
        "results": [
            {
                "name": "site-tunnel-1",
                "rgwy": "10.0.0.1",
                "proxyid": [
                    {
                        "p2name": "p2-1",
                        "status": "up",
                        "incoming_bytes": 1000,
                        "outgoing_bytes": 2000,
                        "proxy_src": [{"name": "10.1.1.0/24", "q_origin_key": "src1"}],
                        "proxy_dst": [{"name": "192.168.1.0/24", "q_origin_key": "dst1"}],
                    }
                ],
            }
        ]
    }

    service = SnapshotService(db_session, mock_client)
    header = service.take_snapshot()

    assert header.status == "success"
    details = (
        db_session.query(SnapshotDetail)
        .filter(SnapshotDetail.snapshot_header_id == header.id)
        .all()
    )
    assert len(details) == 1
    assert details[0].proxy_src is not None
    assert details[0].proxy_src.startswith("[")
    assert details[0].proxy_dst is not None


def test_cleanup_old_snapshots(db_session: Session, mock_client: MagicMock) -> None:
    """Cleanup removes headers older than retention period."""
    old_header = SnapshotHeader(
        snapshot_time=datetime(2020, 1, 1, tzinfo=None),
        status="success",
        total_tunnels=0,
    )
    db_session.add(old_header)
    db_session.commit()

    service = SnapshotService(db_session, mock_client)
    deleted = service.cleanup_old_snapshots(days=60)

    assert deleted == 1
    remaining = db_session.query(SnapshotHeader).count()
    assert remaining == 0
