"""Local aria2 daemon lifecycle management and supervision (E07-I03)."""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Any

from shusha.backends.errors import BackendConnectionError

logger = logging.getLogger(__name__)


class Aria2Supervisor:
    """Manages the lifecycle of a local aria2c daemon process."""

    def __init__(
        self,
        executable_path: str | None = None,
        port: int = 6800,
        secret: str = "",
    ) -> None:
        self.executable_path = executable_path or self.discover_executable()
        self.port = port
        self.secret = secret
        self._process: subprocess.Popen[Any] | None = None

    @classmethod
    def discover_executable(cls) -> str | None:
        """Find the aria2c binary in system PATH."""
        return shutil.which("aria2c")

    def is_running(self) -> bool:
        """Check if the child daemon process is alive."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(
        self,
        port: int | None = None,
        secret: str | None = None,
        extra_args: list[str] | None = None,
    ) -> None:
        """Start the local aria2 daemon process."""
        if self.is_running():
            logger.info(
                "aria2 daemon is already running (PID %s)",
                self._process.pid if self._process else "unknown",
            )
            return

        if not self.executable_path:
            raise BackendConnectionError(
                "aria2c executable not found on system PATH. Please install aria2."
            )

        if port is not None:
            self.port = port
        if secret is not None:
            self.secret = secret

        cmd: list[str] = [
            self.executable_path,
            "--enable-rpc",
            f"--rpc-listen-port={self.port}",
            "--rpc-listen-all=false",
            "--rpc-allow-origin-all=false",
            "--quiet=true",
        ]

        if self.secret:
            cmd.append(f"--rpc-secret={self.secret}")

        if extra_args:
            cmd.extend(extra_args)

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            logger.info(
                "Started aria2c daemon on port %s (PID %s)",
                self.port,
                self._process.pid,
            )
        except Exception as e:
            raise BackendConnectionError(f"Failed to start aria2 process: {e}") from e

    def stop(self, timeout_seconds: float = 5.0) -> None:
        """Gracefully terminate the aria2 daemon process."""
        if not self.is_running() or self._process is None:
            return

        logger.info("Stopping aria2c daemon (PID %s)", self._process.pid)
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.warning(
                "aria2c did not terminate in %ss, killing...", timeout_seconds
            )
            self._process.kill()
            self._process.wait()
        finally:
            self._process = None
