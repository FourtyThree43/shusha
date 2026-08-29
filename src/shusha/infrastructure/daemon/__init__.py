"""
aria2 daemon management, process supervision, and discovery for Shusha 2.
"""

from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.discovery import (
    find_aria2_executable,
    inspect_aria2_version,
    validate_executable,
)
from shusha.infrastructure.daemon.health import (
    DaemonHealthReport,
    DaemonHealthStatus,
    probe_daemon_health,
)
from shusha.infrastructure.daemon.manager import DaemonSupervisor, is_port_in_use
from shusha.infrastructure.daemon.process import DaemonProcess

__all__ = [
    "DaemonConfig",
    "DaemonHealthReport",
    "DaemonHealthStatus",
    "DaemonProcess",
    "DaemonSupervisor",
    "find_aria2_executable",
    "inspect_aria2_version",
    "is_port_in_use",
    "probe_daemon_health",
    "validate_executable",
]
