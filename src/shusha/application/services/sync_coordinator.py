"""
State Synchronization Coordinator for Shusha 2.
Reconciles live polling and real-time WebSocket events into a unified, thread-safe state stream.
"""

import contextlib
import logging
import threading
import time
from collections.abc import Callable

from shusha.domain.download import Download
from shusha.domain.identifiers import DownloadId, Gid
from shusha.domain.statistics import GlobalStatistics
from shusha.infrastructure.aria2.client import Aria2Client
from shusha.infrastructure.aria2.ws_client import Aria2WebSocketClient
from shusha.infrastructure.persistence.repositories.download_repository import (
    DownloadRepository,
)

logger = logging.getLogger(__name__)

type StateUpdateCallback = Callable[[list[Download]], None]
type StatsUpdateCallback = Callable[[GlobalStatistics], None]


class SyncCoordinator:
    """Coordinates polling, WebSocket events, and persistence synchronization."""

    def __init__(
        self,
        client: Aria2Client,
        download_repo: DownloadRepository,
        ws_client: Aria2WebSocketClient | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.client = client
        self.download_repo = download_repo
        self.ws_client = ws_client
        self.poll_interval = poll_interval

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._downloads_cache: dict[DownloadId, Download] = {}
        self._state_observers: list[StateUpdateCallback] = []
        self._stats_observers: list[StatsUpdateCallback] = []

    def subscribe_downloads(self, callback: StateUpdateCallback) -> None:
        """Register an observer for download state changes."""
        with self._lock:
            if callback not in self._state_observers:
                self._state_observers.append(callback)

    def subscribe_stats(self, callback: StatsUpdateCallback) -> None:
        """Register an observer for global throughput metrics."""
        with self._lock:
            if callback not in self._stats_observers:
                self._stats_observers.append(callback)

    def _notify_state_observers(self, downloads: list[Download]) -> None:
        with self._lock:
            callbacks = list(self._state_observers)
        for cb in callbacks:
            with contextlib.suppress(Exception):
                cb(downloads)

    def _notify_stats_observers(self, stats: GlobalStatistics) -> None:
        with self._lock:
            callbacks = list(self._stats_observers)
        for cb in callbacks:
            with contextlib.suppress(Exception):
                cb(stats)

    def poll_once(self) -> None:
        """Perform a single round of synchronization."""
        try:
            active = self.client.tell_active()
            waiting = self.client.tell_waiting(0, 100)
            stopped = self.client.tell_stopped(0, 50)
            all_live = active + waiting + stopped

            # Update cache and persist changes
            with self._lock:
                for dl in all_live:
                    self._downloads_cache[dl.download_id] = dl
                    self.download_repo.save(dl)
                cached_list = list(self._downloads_cache.values())

            self._notify_state_observers(cached_list)

            # Global stats
            stats = self.client.get_global_stat()
            self._notify_stats_observers(stats)

        except Exception as e:
            logger.debug("Sync cycle skipped: %s", e)

    def _on_ws_event(self, event_name: str, params: dict[str, str]) -> None:
        """Handle real-time notification push from WebSocket."""
        gid_str = params.get("gid")
        if not gid_str:
            return

        with contextlib.suppress(Exception):
            live_dl = self.client.tell_status(Gid(gid_str))
            with self._lock:
                self._downloads_cache[live_dl.download_id] = live_dl
                self.download_repo.save(live_dl)
                cached_list = list(self._downloads_cache.values())
            self._notify_state_observers(cached_list)

    def _sync_loop(self) -> None:
        while self._running:
            self.poll_once()
            time.sleep(self.poll_interval)

    def start(self) -> None:
        """Start synchronization loop and WebSocket listeners."""
        if self._running:
            return
        self._running = True

        if self.ws_client:
            self.ws_client.on("aria2.onDownloadStart", self._on_ws_event)
            self.ws_client.on("aria2.onDownloadPause", self._on_ws_event)
            self.ws_client.on("aria2.onDownloadStop", self._on_ws_event)
            self.ws_client.on("aria2.onDownloadComplete", self._on_ws_event)
            self.ws_client.on("aria2.onDownloadError", self._on_ws_event)
            self.ws_client.on("aria2.onBtDownloadComplete", self._on_ws_event)
            self.ws_client.start()

        self._thread = threading.Thread(
            target=self._sync_loop, daemon=True, name="SyncCoordinatorThread"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop synchronization."""
        self._running = False
        if self.ws_client:
            self.ws_client.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
