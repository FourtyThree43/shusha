"""BitTorrent public tracker aggregator and updater service.

This module provides automated discovery and fetching of high-availability public
BitTorrent trackers (inspired by Motrix), allowing users to optimize peer connectivity
and download speed for magnet links and torrents.
"""

from __future__ import annotations

import threading
import time
import urllib.request
from typing import Any, ClassVar

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)

# Default top reliable public tracker sources
DEFAULT_TRACKER_SOURCES = [
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
    "https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/best.txt",
]

DEFAULT_FALLBACK_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.tracker.cl:1337/announce",
    "udp://opentracker.i2p.rocks:6969/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://explodie.org:6969/announce",
    "udp://open.stealth.si:80/announce",
]


class TrackerService:
    """Manages fetching, caching, and formatting public BitTorrent trackers."""

    _cached_trackers: ClassVar[list[str]] = list(DEFAULT_FALLBACK_TRACKERS)
    _last_fetched: ClassVar[float] = 0.0
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def get_trackers(cls, force_refresh: bool = False) -> list[str]:
        """Retrieve current cached tracker list.

        Args:
            force_refresh: If True, fetches live list synchronously.

        Returns:
            List of clean tracker announce URLs.
        """
        if force_refresh or (time.time() - cls._last_fetched > 86400 and not cls._cached_trackers):
            cls.fetch_latest_trackers_sync()
        return list(cls._cached_trackers)

    @classmethod
    def get_trackers_csv(cls) -> str:
        """Return comma-separated string of trackers for aria2 `bt-tracker` option."""
        return ",".join(cls.get_trackers())

    @classmethod
    def fetch_latest_trackers_sync(
        cls, sources: list[str] | None = None, timeout: float = 5.0
    ) -> list[str]:
        """Fetch trackers synchronously from remote source lists.

        Args:
            sources: List of URLs pointing to plain text tracker lists.
            timeout: Network request timeout in seconds.

        Returns:
            Aggregated list of valid tracker URLs.
        """
        urls = sources or DEFAULT_TRACKER_SOURCES
        fetched: set[str] = set(DEFAULT_FALLBACK_TRACKERS)

        for source_url in urls:
            try:
                req = urllib.request.Request(
                    source_url,
                    headers={"User-Agent": "Shusha-Download-Manager/1.0"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    text = resp.read().decode("utf-8", errors="ignore")
                    for line in text.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "://" in line:
                            fetched.add(line)
            except Exception as e:
                logger.log(f"Notice: Failed to fetch trackers from {source_url}: {e}", level="debug")

        with cls._lock:
            if fetched:
                cls._cached_trackers = sorted(fetched)
                cls._last_fetched = time.time()
            return list(cls._cached_trackers)

    @classmethod
    def fetch_latest_trackers_async(
        cls, on_complete: Any = None
    ) -> threading.Thread:
        """Fetch trackers in a background thread."""
        def _bg():
            trackers = cls.fetch_latest_trackers_sync()
            if callable(on_complete):
                on_complete(trackers)

        t = threading.Thread(target=_bg, daemon=True, name="TrackerFetcher")
        t.start()
        return t
