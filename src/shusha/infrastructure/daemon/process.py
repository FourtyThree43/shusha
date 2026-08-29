"""
Low-level process supervisor for aria2c subprocess execution.
Enforces strict security rules: shell=False, argument array validation, graceful termination.
"""

import contextlib
import logging
import subprocess
import time
from pathlib import Path

from shusha.infrastructure.daemon.config import DaemonConfig
from shusha.infrastructure.daemon.discovery import validate_executable

logger = logging.getLogger(__name__)


class DaemonProcess:
    """Controls a single running aria2c process instance."""

    def __init__(
        self,
        executable_path: Path,
        config: DaemonConfig,
        working_dir: Path | None = None,
    ) -> None:
        if not validate_executable(executable_path):
            raise FileNotFoundError(
                f"Executable not found or not executable: {executable_path}"
            )

        self.executable_path = executable_path
        self.config = config
        self.working_dir = working_dir
        self._process: subprocess.Popen[str] | None = None

    @property
    def is_running(self) -> bool:
        """Check whether the child process is currently alive."""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def pid(self) -> int | None:
        """Child process ID if running."""
        return self._process.pid if self.is_running and self._process else None

    def start(self) -> bool:
        """Spawn the aria2c process with explicit argument arrays."""
        if self.is_running:
            return True

        args = [str(self.executable_path), *self.config.build_cli_arguments()]
        redacted_args = [
            str(self.executable_path),
            *self.config.build_redacted_arguments(),
        ]
        logger.info("Spawning aria2c process: %s", " ".join(redacted_args))

        try:
            self._process = subprocess.Popen(
                args,
                cwd=str(self.working_dir) if self.working_dir else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            time.sleep(0.2)
            if self._process.poll() is not None:
                _, stderr = self._process.communicate()
                logger.error("aria2c failed to start immediately: %s", stderr)
                return False
            return True
        except Exception as e:
            logger.error("Failed to spawn aria2c subprocess: %s", e)
            return False

    def terminate(self, timeout: float = 3.0) -> bool:
        """Gracefully terminate the aria2c process (SIGTERM with SIGKILL fallback)."""
        if not self.is_running or not self._process:
            return True

        logger.info("Terminating aria2c process (PID: %s)...", self._process.pid)
        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
                return True
            except subprocess.TimeoutExpired:
                logger.warning("aria2c did not exit gracefully; sending SIGKILL...")
                self._process.kill()
                self._process.wait(timeout=2.0)
                return True
        except Exception as e:
            logger.error("Error during aria2c termination: %s", e)
            return False
        finally:
            with contextlib.suppress(Exception):
                if self._process:
                    if self._process.stdout:
                        self._process.stdout.close()
                    if self._process.stderr:
                        self._process.stderr.close()
            self._process = None
