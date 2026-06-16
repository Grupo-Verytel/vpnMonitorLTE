"""FortiGate REST API HTTP client."""

import time
from typing import Any

import httpx

from app.core.exceptions import FortiGateAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 2
BACKOFF_SECONDS = (1, 2)
RATE_LIMIT_BACKOFF_SECONDS = (5, 15)


class FortiGateClient:
    """Wrapper around httpx for FortiGate REST API calls."""

    def __init__(
        self,
        host: str,
        token: str,
        verify_ssl: bool = False,
        timeout: int = 15,
    ) -> None:
        base_url = host if host.startswith("http") else f"https://{host}"
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {token}"},
            verify=verify_ssl,
            timeout=timeout,
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an HTTP request with retry on 5xx, 429, and timeout."""
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            start = time.perf_counter()
            try:
                response = self._client.request(method, path, **kwargs)
                duration_ms = int((time.perf_counter() - start) * 1000)

                logger.info(
                    "fortigate_request",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    attempt=attempt + 1,
                )

                if response.status_code == 429 and attempt < MAX_RETRIES:
                    wait = RATE_LIMIT_BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "fortigate_rate_limited",
                        path=path,
                        attempt=attempt + 1,
                        retry_in_seconds=wait,
                    )
                    time.sleep(wait)
                    continue

                if response.status_code >= 500 and attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue

                if response.status_code >= 400:
                    raise FortiGateAPIError(
                        f"FortiGate API error {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code,
                    )

                return response.json()

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                duration_ms = int((time.perf_counter() - start) * 1000)
                logger.warning(
                    "fortigate_request_failed",
                    method=method,
                    path=path,
                    duration_ms=duration_ms,
                    attempt=attempt + 1,
                    error=str(exc),
                )
                last_error = exc
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue
                raise FortiGateAPIError(
                    f"FortiGate connection failed after retries: {exc}"
                ) from exc

        raise FortiGateAPIError(
            f"FortiGate request failed: {last_error}"
        ) from last_error

    def get_ipsec_tunnels(self) -> dict[str, Any]:
        """Fetch IPsec tunnel monitor data from FortiGate."""
        return self._request(
            "GET",
            "/api/v2/monitor/vpn/ipsec",
        )

    def get_system_status(self) -> dict[str, Any]:
        """Fetch FortiGate system status (serial, version)."""
        return self._request(
            "GET",
            "/api/v2/monitor/system/status",
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "FortiGateClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
