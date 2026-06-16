"""Tests for FortiGateClient HTTP wrapper."""

from unittest.mock import patch

import httpx
import pytest
import respx

from app.core.exceptions import FortiGateAPIError
from app.services.fortigate_client import FortiGateClient

BASE_URL = "https://fortigate.test"


@pytest.fixture
def client() -> FortiGateClient:
    """Create a FortiGateClient pointed at the test host."""
    return FortiGateClient(
        host=BASE_URL,
        token="test-token",
        verify_ssl=False,
        timeout=5,
    )


@respx.mock
def test_get_ipsec_tunnels_success(client: FortiGateClient) -> None:
    """Parse successful IPsec tunnel response."""
    respx.get(f"{BASE_URL}/api/v2/monitor/vpn/ipsec").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "tunnel-a",
                        "rgwy": "10.0.0.1",
                        "proxyid": [
                            {
                                "p2name": "phase2-a",
                                "status": "up",
                                "incoming_bytes": 1000,
                                "outgoing_bytes": 2000,
                            }
                        ],
                    }
                ]
            },
        )
    )

    data = client.get_ipsec_tunnels()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "tunnel-a"
    client.close()


@respx.mock
def test_get_system_status_success(client: FortiGateClient) -> None:
    """Parse successful system status response."""
    respx.get(f"{BASE_URL}/api/v2/monitor/system/status").mock(
        return_value=httpx.Response(
            200,
            json={"results": {"serial": "FG70GTEST", "version": "v7.4.0"}},
        )
    )

    data = client.get_system_status()
    assert data["results"]["serial"] == "FG70GTEST"
    client.close()


@respx.mock
def test_retry_on_5xx(client: FortiGateClient) -> None:
    """Retry twice on 5xx before succeeding."""
    route = respx.get(f"{BASE_URL}/api/v2/monitor/vpn/ipsec")
    route.side_effect = [
        httpx.Response(503, text="Service Unavailable"),
        httpx.Response(503, text="Service Unavailable"),
        httpx.Response(200, json={"results": []}),
    ]

    data = client.get_ipsec_tunnels()
    assert data["results"] == []
    assert route.call_count == 3
    client.close()


@respx.mock
@patch("app.services.fortigate_client.time.sleep")
def test_retry_on_429(mock_sleep: object, client: FortiGateClient) -> None:
    """Retry twice on 429 before succeeding."""
    route = respx.get(f"{BASE_URL}/api/v2/monitor/vpn/ipsec")
    route.side_effect = [
        httpx.Response(429, text="Too Many Requests"),
        httpx.Response(429, text="Too Many Requests"),
        httpx.Response(200, json={"results": []}),
    ]

    data = client.get_ipsec_tunnels()
    assert data["results"] == []
    assert route.call_count == 3
    client.close()


@respx.mock
def test_raises_on_4xx(client: FortiGateClient) -> None:
    """Raise FortiGateAPIError on 4xx without retry."""
    respx.get(f"{BASE_URL}/api/v2/monitor/vpn/ipsec").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )

    with pytest.raises(FortiGateAPIError) as exc_info:
        client.get_ipsec_tunnels()

    assert exc_info.value.status_code == 401
    client.close()


@respx.mock
def test_context_manager() -> None:
    """Client works as context manager."""
    respx.get(f"{BASE_URL}/api/v2/monitor/system/status").mock(
        return_value=httpx.Response(200, json={"results": {}})
    )

    with FortiGateClient(host=BASE_URL, token="tok") as c:
        result = c.get_system_status()
        assert "results" in result
