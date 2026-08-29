"""
Clipboard monitor service for detecting downloadable URLs and magnet links.
"""

import contextlib
import logging
import re
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"^(https?|ftp|sftp)://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
MAGNET_PATTERN = re.compile(
    r"^magnet:\?xt=urn:[a-z0-9]+:[a-z0-9]{32,40}", re.IGNORECASE
)


def is_downloadable_link(text: str) -> bool:
    """Validate whether clipboard text contains a valid downloadable URI."""
    clean = text.strip()
    return bool(URL_PATTERN.match(clean) or MAGNET_PATTERN.match(clean))


class ClipboardWatcherService:
    """Background service polling system clipboard for downloadable links."""

    def __init__(
        self,
        on_link_detected: Callable[[str], None],
        get_clipboard_text: Callable[[], str | None],
        poll_interval: float = 1.0,
    ) -> None:
        self.on_link_detected = on_link_detected
        self.get_clipboard_text = get_clipboard_text
        self.poll_interval = poll_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_seen: str | None = None

    def _loop(self) -> None:
        while self._running:
            with contextlib.suppress(Exception):
                text = self.get_clipboard_text()
                if text and text != self._last_seen:
                    self._last_seen = text
                    if is_downloadable_link(text):
                        logger.info("Detected new downloadable link in clipboard")
                        self.on_link_detected(text.strip())
            time.sleep(self.poll_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="ClipboardWatcherThread"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
