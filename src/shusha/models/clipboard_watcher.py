"""Clipboard monitor service for automatically detecting downloadable URLs.

Watches the system clipboard in a background thread and invokes callbacks when
a new valid HTTP/HTTPS/FTP, magnet, or torrent link is copied.
"""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Callable
from typing import Any

from shusha.models.logger import LoggerService

logger = LoggerService(__name__)

URL_REGEX = re.compile(
    r"^(https?://|ftp://|magnet:\?|sftp://|thunder://|flashget://|qqdl://).+",
    re.IGNORECASE,
)

DOWNLOADABLE_EXTENSIONS = (
    ".zip",
    ".rar",
    ".7z",
    ".tar.gz",
    ".tar.xz",
    ".iso",
    ".exe",
    ".msi",
    ".dmg",
    ".pkg",
    ".deb",
    ".rpm",
    ".AppImage",
    ".apk",
    ".mp4",
    ".mkv",
    ".avi",
    ".mp3",
    ".flac",
    ".pdf",
    ".epub",
    ".torrent",
    ".metalink",
)


class ClipboardWatcher:
    """Monitors system clipboard for downloadable URLs."""

    def __init__(
        self,
        on_url_detected: Callable[[str], Any] | None = None,
        poll_interval: float = 1.0,
        clipboard_getter: Callable[[], str] | None = None,
    ) -> None:
        self.on_url_detected = on_url_detected
        self.poll_interval = poll_interval
        self.clipboard_getter = clipboard_getter
        self._running = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._last_content = ""
        self._seen_urls: set[str] = set()

    def start(self) -> None:
        """Start clipboard monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.log("Clipboard watcher started.", level="info")

    def stop(self) -> None:
        """Stop clipboard monitoring thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.log("Clipboard watcher stopped.", level="info")

    def pause(self) -> None:
        """Pause notification dispatch."""
        self._paused = True

    def resume(self) -> None:
        """Resume notification dispatch."""
        self._paused = False

    def is_running(self) -> bool:
        """Check if clipboard watcher is active."""
        return self._running

    def _get_clipboard_text(self) -> str:
        """Fetch current clipboard text using provided getter or tkinter fallback."""
        if self.clipboard_getter is not None:
            try:
                return str(self.clipboard_getter() or "").strip()
            except Exception:
                return ""

        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            content = root.clipboard_get()
            root.destroy()
            return str(content or "").strip()
        except Exception:
            return ""

    def _run_loop(self) -> None:
        """Background polling loop."""
        while self._running:
            try:
                if not self._paused:
                    content = self._get_clipboard_text()
                    if content and content != self._last_content:
                        self._last_content = content
                        if (
                            self.is_downloadable_url(content)
                            and content not in self._seen_urls
                        ):
                            self._seen_urls.add(content)
                            if len(self._seen_urls) > 500:
                                self._seen_urls.clear()
                            if self.on_url_detected:
                                self.on_url_detected(content)
            except Exception as e:
                logger.log(f"Clipboard watcher notice: {e}", level="debug")

            time.sleep(self.poll_interval)

    @classmethod
    def is_downloadable_url(cls, text: str) -> bool:
        """Verify whether text contains a valid downloadable URL pattern."""
        if not text or len(text) > 4096:
            return False

        stripped = text.strip()

        # Direct magnet link
        if stripped.lower().startswith("magnet:?xt="):
            return True

        if not URL_REGEX.match(stripped):
            return False

        # If it has spaces, likely not a single URL
        return not (" " in stripped and not stripped.startswith("magnet:"))
