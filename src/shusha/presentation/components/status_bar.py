"""
Bottom Status Bar Component for Shusha 2.
"""

import tkinter as tk

import ttkbootstrap as tb

from shusha.domain.statistics import GlobalStatistics
from shusha.presentation.components.base import BaseFrame


class AppStatusBar(BaseFrame):
    """Application bottom status bar."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, padding=(8, 2))
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.lbl_stats = tb.Label(
            self,
            text="↓ 0 B/s   ↑ 0 B/s",
            font=("TkDefaultFont", 9),
        )
        self.lbl_stats.pack(side="left", padx=4)

        self.lbl_counts = tb.Label(
            self,
            text="0 active, 0 queued",
            font=("TkDefaultFont", 9),
        )
        self.lbl_counts.pack(side="left", padx=12)

        self.lbl_daemon = tb.Label(
            self,
            text="● Daemon: Connecting...",
            bootstyle="secondary",
            font=("TkDefaultFont", 9),
        )
        self.lbl_daemon.pack(side="right", padx=4)

    def update_statistics(self, stats: GlobalStatistics) -> None:
        """Update live throughput and queue numbers."""
        dl_spd = stats.download_speed.human_readable()
        ul_spd = stats.upload_speed.human_readable()
        self.lbl_stats.config(text=f"↓ {dl_spd}   ↑ {ul_spd}")
        self.lbl_counts.config(
            text=f"{stats.num_active} active, {stats.num_waiting} queued, {stats.num_stopped} stopped"
        )

    def update_daemon_status(self, is_online: bool, version: str | None = None) -> None:
        """Update daemon connectivity badge."""
        if is_online:
            ver_text = f" (v{version})" if version else ""
            self.lbl_daemon.config(
                text=f"● Daemon: Online{ver_text}", bootstyle="success"
            )
        else:
            self.lbl_daemon.config(text="● Daemon: Offline", bootstyle="danger")
