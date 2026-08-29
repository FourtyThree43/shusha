"""
Health probing and liveness checks for the aria2 daemon.
"""

import time
from dataclasses import dataclass
from enum import StrEnum

from shusha.infrastructure.aria2.errors import Aria2RpcError
from shusha.infrastructure.aria2.jsonrpc import JsonRpcTransport


class DaemonHealthStatus(StrEnum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    UNRESPONSIVE = "UNRESPONSIVE"
    DEGRADED = "DEGRADED"
    CRASHED = "CRASHED"


@dataclass(frozen=True, slots=True)
class DaemonHealthReport:
    """Snapshot report of aria2 daemon health and responsiveness."""

    status: DaemonHealthStatus
    version: str | None = None
    latency_ms: float | None = None
    error_message: str | None = None


def probe_daemon_health(
    host: str = "127.0.0.1",
    port: int = 6800,
    secret: str | None = None,
    timeout: float = 2.0,
) -> DaemonHealthReport:
    """Probe the aria2 daemon over JSON-RPC to measure health and latency."""
    endpoint = f"http://{host}:{port}/jsonrpc"
    transport = JsonRpcTransport(endpoint=endpoint, secret=secret, timeout=timeout)

    start_time = time.perf_counter()
    try:
        res = transport.call("aria2.getVersion")
        latency = (time.perf_counter() - start_time) * 1000.0
        version = "unknown"
        if isinstance(res, dict):
            version = str(res.get("version", "unknown"))

        return DaemonHealthReport(
            status=DaemonHealthStatus.HEALTHY,
            version=version,
            latency_ms=round(latency, 2),
        )
    except Aria2RpcError as e:
        return DaemonHealthReport(
            status=DaemonHealthStatus.DEGRADED,
            error_message=str(e),
        )
    except Exception as e:
        return DaemonHealthReport(
            status=DaemonHealthStatus.UNRESPONSIVE,
            error_message=str(e),
        )
