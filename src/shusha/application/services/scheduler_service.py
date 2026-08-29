"""
Download scheduler service for Shusha 2.
Enforces bandwidth throttles and time-window based downloading.
"""

import logging
import threading
import time
from datetime import UTC, datetime

from shusha.domain.scheduler import ScheduleWindow
from shusha.infrastructure.aria2.client import Aria2Client

logger = logging.getLogger(__name__)


class SchedulerService:
    """Monitors scheduled time windows and adjusts aria2 speed limits dynamically."""

    def __init__(
        self,
        client: Aria2Client,
        windows: list[ScheduleWindow] | None = None,
        check_interval: float = 10.0,
    ) -> None:
        self.client = client
        self.windows = windows or []
        self.check_interval = check_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._current_limit_applied: str | None = None

    def evaluate_at(self, dt: datetime) -> None:
        """Check all windows for the given datetime and apply limits if matched."""
        matching_window: ScheduleWindow | None = None
        for w in self.windows:
            if w.is_active_at(dt):
                matching_window = w
                break

        if matching_window and matching_window.speed_limit:
            speed_str = f"{matching_window.speed_limit.bytes_per_sec}"
            if self._current_limit_applied != speed_str:
                logger.info("Applying scheduler speed limit: %s B/s", speed_str)
                self.client.change_global_option(
                    {
                        "max-overall-download-limit": speed_str,
                        "max-overall-upload-limit": speed_str,
                    }
                )
                self._current_limit_applied = speed_str
        elif self._current_limit_applied is not None:
            logger.info("Clearing scheduler speed limit (outside active windows)")
            self.client.change_global_option(
                {
                    "max-overall-download-limit": "0",
                    "max-overall-upload-limit": "0",
                }
            )
            self._current_limit_applied = None

    def _loop(self) -> None:
        while self._running:
            try:
                now = datetime.now(UTC)
                self.evaluate_at(now)
            except Exception as e:
                logger.error("Error in scheduler loop: %s", e)
            time.sleep(self.check_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="SchedulerServiceThread"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
