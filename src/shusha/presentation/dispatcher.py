"""
Thread-safe UI Dispatcher for Tkinter / ttkbootstrap.
Marshals background worker results and asynchronous events back onto the UI thread.
"""

import contextlib
import logging
import threading
import tkinter as tk
from collections.abc import Callable

logger = logging.getLogger(__name__)


class UiDispatcher:
    """Thread-safe scheduler routing background callbacks into Tk mainloop."""

    def __init__(self, root: tk.Misc) -> None:
        self.root = root

    def dispatch(self, callback: Callable[[], None]) -> None:
        """Schedule a callable on the Tkinter main thread safely."""
        with contextlib.suppress(Exception):
            self.root.after(0, callback)

    def run_in_background[T](
        self,
        task: Callable[[], T],
        on_success: Callable[[T], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Execute a blocking task in a background worker thread and return result to UI."""

        def worker() -> None:
            try:
                result = task()
                if on_success:
                    self.dispatch(lambda: on_success(result))
            except Exception as e:
                err = e
                logger.error("Background task error: %s", err, exc_info=True)
                if on_error:
                    self.dispatch(lambda: on_error(err))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
