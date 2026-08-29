"""
Modern Action Toolbar Component for Shusha 2.
"""

import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as tb

from shusha.presentation.components.base import BaseFrame


class AppToolbar(BaseFrame):
    """Main application action toolbar."""

    def __init__(
        self,
        parent: tk.Misc,
        on_add_url: Callable[[], None] | None = None,
        on_add_torrent: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
        on_pause: Callable[[], None] | None = None,
        on_remove: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, padding=4)
        self.on_add_url = on_add_url
        self.on_add_torrent = on_add_torrent
        self.on_resume = on_resume
        self.on_pause = on_pause
        self.on_remove = on_remove
        self.on_settings = on_settings

        self._setup_ui()

    def _setup_ui(self) -> None:
        btn_add_url = tb.Button(
            self,
            text="+ Add URL",
            bootstyle="primary",
            command=lambda: self.on_add_url() if self.on_add_url else None,
        )
        btn_add_url.pack(side="left", padx=2)

        btn_add_torrent = tb.Button(
            self,
            text="+ Add Torrent",
            bootstyle="secondary",
            command=lambda: self.on_add_torrent() if self.on_add_torrent else None,
        )
        btn_add_torrent.pack(side="left", padx=2)

        sep1 = tb.Separator(self, orient="vertical")
        sep1.pack(side="left", fill="y", padx=6, pady=2)

        btn_resume = tb.Button(
            self,
            text="▶ Resume",
            bootstyle="success-outline",
            command=lambda: self.on_resume() if self.on_resume else None,
        )
        btn_resume.pack(side="left", padx=2)

        btn_pause = tb.Button(
            self,
            text="⏸ Pause",
            bootstyle="warning-outline",
            command=lambda: self.on_pause() if self.on_pause else None,
        )
        btn_pause.pack(side="left", padx=2)

        btn_remove = tb.Button(
            self,
            text="✕ Remove",
            bootstyle="danger-outline",
            command=lambda: self.on_remove() if self.on_remove else None,
        )
        btn_remove.pack(side="left", padx=2)

        # Right-aligned settings button
        btn_settings = tb.Button(
            self,
            text="⚙ Settings",
            bootstyle="secondary-outline",
            command=lambda: self.on_settings() if self.on_settings else None,
        )
        btn_settings.pack(side="right", padx=4)
