"""Modern Action Toolbar Component with Lucide Icons for Shusha Desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

import ttkbootstrap as tb

from shusha.presentation.components.base import BaseFrame
from shusha.presentation.icons import get_lucide_icon
from shusha.presentation.theme import SpacingTokens


class AppToolbar(BaseFrame):
    """Main application action toolbar equipped with modern Lucide icons."""

    def __init__(
        self,
        parent: tk.Misc,
        on_add_url: Callable[[], None] | None = None,
        on_add_torrent: Callable[[], None] | None = None,
        on_media_grabber: Callable[[], None] | None = None,
        on_inbox: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
        on_pause: Callable[[], None] | None = None,
        on_remove: Callable[[], None] | None = None,
        on_settings: Callable[[], None] | None = None,
        on_theme_toggle: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, padding=SpacingTokens().sm)
        self.on_add_url = on_add_url
        self.on_add_torrent = on_add_torrent
        self.on_media_grabber = on_media_grabber
        self.on_inbox = on_inbox
        self.on_resume = on_resume
        self.on_pause = on_pause
        self.on_remove = on_remove
        self.on_settings = on_settings
        self.on_theme_toggle = on_theme_toggle
        self._icon_refs: list[Any] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        icon_plus = get_lucide_icon("plus", 16, "#ffffff")
        if icon_plus:
            self._icon_refs.append(icon_plus)
            btn_add_url = tb.Button(
                self,
                text=" Add URL",
                image=icon_plus,
                compound="left",
                bootstyle="primary",
                command=lambda: self.on_add_url() if self.on_add_url else None,
            )
        else:
            btn_add_url = tb.Button(
                self,
                text="+ Add URL",
                bootstyle="primary",
                command=lambda: self.on_add_url() if self.on_add_url else None,
            )
        btn_add_url.pack(side="left", padx=2)

        icon_folder = get_lucide_icon("folder", 16, "#ffffff")
        if icon_folder:
            self._icon_refs.append(icon_folder)
            btn_add_torrent = tb.Button(
                self,
                text=" Add File/Torrent",
                image=icon_folder,
                compound="left",
                bootstyle="secondary",
                command=lambda: self.on_add_torrent() if self.on_add_torrent else None,
            )
        else:
            btn_add_torrent = tb.Button(
                self,
                text="+ File/Torrent",
                bootstyle="secondary",
                command=lambda: self.on_add_torrent() if self.on_add_torrent else None,
            )
        btn_add_torrent.pack(side="left", padx=2)

        icon_video = get_lucide_icon("video", 16, "#ffffff")
        if icon_video:
            self._icon_refs.append(icon_video)
            btn_media = tb.Button(
                self,
                text=" Media Grabber",
                image=icon_video,
                compound="left",
                bootstyle="info-outline",
                command=lambda: (
                    self.on_media_grabber() if self.on_media_grabber else None
                ),
            )
        else:
            btn_media = tb.Button(
                self,
                text="🎬 Media Grabber",
                bootstyle="info-outline",
                command=lambda: (
                    self.on_media_grabber() if self.on_media_grabber else None
                ),
            )
        btn_media.pack(side="left", padx=2)

        icon_inbox = get_lucide_icon("inbox", 16, "#ffffff")
        if icon_inbox:
            self._icon_refs.append(icon_inbox)
            btn_inbox = tb.Button(
                self,
                text=" Inbox",
                image=icon_inbox,
                compound="left",
                bootstyle="secondary-outline",
                command=lambda: self.on_inbox() if self.on_inbox else None,
            )
        else:
            btn_inbox = tb.Button(
                self,
                text="📥 Inbox",
                bootstyle="secondary-outline",
                command=lambda: self.on_inbox() if self.on_inbox else None,
            )
        btn_inbox.pack(side="left", padx=2)

        sep1 = tb.Separator(self, orient="vertical")
        sep1.pack(side="left", fill="y", padx=8, pady=2)

        icon_play = get_lucide_icon("play", 16, "#00bc8c")
        if icon_play:
            self._icon_refs.append(icon_play)
            btn_resume = tb.Button(
                self,
                text=" Resume",
                image=icon_play,
                compound="left",
                bootstyle="success-outline",
                command=lambda: self.on_resume() if self.on_resume else None,
            )
        else:
            btn_resume = tb.Button(
                self,
                text="▶ Resume",
                bootstyle="success-outline",
                command=lambda: self.on_resume() if self.on_resume else None,
            )
        btn_resume.pack(side="left", padx=2)

        icon_pause = get_lucide_icon("pause", 16, "#f39c12")
        if icon_pause:
            self._icon_refs.append(icon_pause)
            btn_pause = tb.Button(
                self,
                text=" Pause",
                image=icon_pause,
                compound="left",
                bootstyle="warning-outline",
                command=lambda: self.on_pause() if self.on_pause else None,
            )
        else:
            btn_pause = tb.Button(
                self,
                text="⏸ Pause",
                bootstyle="warning-outline",
                command=lambda: self.on_pause() if self.on_pause else None,
            )
        btn_pause.pack(side="left", padx=2)

        icon_trash = get_lucide_icon("trash", 16, "#e74c3c")
        if icon_trash:
            self._icon_refs.append(icon_trash)
            btn_remove = tb.Button(
                self,
                text=" Remove",
                image=icon_trash,
                compound="left",
                bootstyle="danger-outline",
                command=lambda: self.on_remove() if self.on_remove else None,
            )
        else:
            btn_remove = tb.Button(
                self,
                text="✕ Remove",
                bootstyle="danger-outline",
                command=lambda: self.on_remove() if self.on_remove else None,
            )
        btn_remove.pack(side="left", padx=2)

        # Right-aligned tools
        icon_settings = get_lucide_icon("settings", 16, "#ffffff")
        if icon_settings:
            self._icon_refs.append(icon_settings)
            btn_settings = tb.Button(
                self,
                text=" Settings",
                image=icon_settings,
                compound="left",
                bootstyle="secondary-outline",
                command=lambda: self.on_settings() if self.on_settings else None,
            )
        else:
            btn_settings = tb.Button(
                self,
                text="⚙ Settings",
                bootstyle="secondary-outline",
                command=lambda: self.on_settings() if self.on_settings else None,
            )
        btn_settings.pack(side="right", padx=4)

        icon_moon = get_lucide_icon("moon", 16, "#ffffff")
        if icon_moon:
            self._icon_refs.append(icon_moon)
            btn_theme = tb.Button(
                self,
                text=" Theme",
                image=icon_moon,
                compound="left",
                bootstyle="link",
                command=lambda: (
                    self.on_theme_toggle() if self.on_theme_toggle else None
                ),
            )
        else:
            btn_theme = tb.Button(
                self,
                text="🌗 Theme",
                bootstyle="link",
                command=lambda: (
                    self.on_theme_toggle() if self.on_theme_toggle else None
                ),
            )
        btn_theme.pack(side="right", padx=2)
