"""
High-Level aria2 Daemon Supervisor for Shusha 2.
Coordinates discovery, configuration, process lifecycle, PID tracking, and health checks.
"""

import contextlib
import logging
import socket
import time
from pathlib import Path

from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.discovery import find_aria2_executable
from shusha.infrastructure.daemon.health import (
    DaemonHealthReport,
    DaemonHealthStatus,
    probe_daemon_health,
)
from shusha.infrastructure.daemon.process import DaemonProcess

logger = logging.getLogger(__name__)


def is_port_in_use(host: str, port: int) -> bool:
    """Check if a TCP port is currently open and listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


class DaemonSupervisor:
    """Manages the full lifecycle of local and remote aria2 instances."""

    def __init__(
        self,
        config: DaemonConfig | None = None,
        custom_executable: Path | None = None,
        pid_file: Path | None = None,
    ) -> None:
        self.config = config or DaemonConfig()
        self.custom_executable = custom_executable
        self.pid_file = pid_file
        self._process: DaemonProcess | None = None
        self._is_external = False

    @property
    def is_running(self) -> bool:
        """Check if local process is running or external port is listening."""
        if self._process and self._process.is_running:
            return True
        return is_port_in_use(self.config.host, self.config.port)

    def _write_pid(self, pid: int) -> None:
        if self.pid_file:
            with contextlib.suppress(Exception):
                self.pid_file.parent.mkdir(parents=True, exist_ok=True)
                self.pid_file.write_text(str(pid), encoding="utf-8")

    def _remove_pid(self) -> None:
        if self.pid_file and self.pid_file.exists():
            with contextlib.suppress(Exception):
                self.pid_file.unlink()

    def start(self) -> bool:
        """
        Start the aria2 daemon instance.
        If an instance is already listening on the configured port, adopts it as external.
        """
        if is_port_in_use(self.config.host, self.config.port):
            logger.info(
                "Found existing aria2 instance listening on %s:%d",
                self.config.host,
                self.config.port,
            )
            self._is_external = True
            return True

        executable = find_aria2_executable(self.custom_executable)
        if not executable:
            logger.error("Could not find aria2c executable on system")
            return False

        self._process = DaemonProcess(
            executable_path=executable,
            config=self.config,
            working_dir=self.config.download_dir,
        )

        success = self._process.start()
        if success and self._process.pid:
            self._write_pid(self._process.pid)
            self._is_external = False

            # Wait briefly for RPC socket to become ready
            for _ in range(10):
                if is_port_in_use(self.config.host, self.config.port):
                    return True
                time.sleep(0.1)

        return success

    def stop(self) -> bool:
        """Stop the managed local aria2 process."""
        if self._is_external:
            logger.info(
                "Cannot stop external aria2 instance on %s:%d",
                self.config.host,
                self.config.port,
            )
            return True

        success = True
        if self._process:
            success = self._process.terminate()
            self._process = None

        self._remove_pid()
        return success

    def restart(self) -> bool:
        """Restart the daemon process."""
        self.stop()
        time.sleep(0.5)
        return self.start()

    def get_health(self) -> DaemonHealthReport:
        """Probe the daemon health status."""
        if not self.is_running:
            return DaemonHealthReport(status=DaemonHealthStatus.STOPPED)

        return probe_daemon_health(
            host=self.config.host,
            port=self.config.port,
            secret=self.config.secret,
        )
