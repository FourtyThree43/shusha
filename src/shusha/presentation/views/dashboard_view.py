"""Modern backend-neutral Dashboard View (E11-I04)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shusha.presentation.app_context import AppContext
from shusha.presentation.theme import SpacingTokens, TypographyTokens


class DashboardView(ttk.Frame):
    """Overview dashboard displaying statistics cards, active jobs, and event stream."""

    def __init__(self, parent: tk.Misc, context: AppContext, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.context = context
        self.spacing = SpacingTokens()
        self.typography = TypographyTokens()

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header Cards Bar
        cards_frame = ttk.Frame(self, padding=self.spacing.md)
        cards_frame.grid(row=0, column=0, sticky="ew")
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_active = self._create_card(cards_frame, 0, "Active Downloads", "0")
        self.lbl_speed_down = self._create_card(
            cards_frame, 1, "Download Speed", "0.0 B/s"
        )
        self.lbl_speed_up = self._create_card(cards_frame, 2, "Upload Speed", "0.0 B/s")
        self.lbl_completed = self._create_card(cards_frame, 3, "Completed Today", "0")

        # Active Jobs Overview Area
        content_frame = ttk.LabelFrame(
            self, text="Active Transfers", padding=self.spacing.md
        )
        content_frame.grid(
            row=1, column=0, sticky="nsew", padx=self.spacing.md, pady=self.spacing.sm
        )
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        cols = ("name", "backend", "progress", "speed", "eta")
        self.tree = ttk.Treeview(
            content_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("name", text="Name")
        self.tree.heading("backend", text="Backend")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("speed", text="Speed")
        self.tree.heading("eta", text="ETA")

        self.tree.column("name", width=250, anchor="w")
        self.tree.column("backend", width=80, anchor="center")
        self.tree.column("progress", width=100, anchor="center")
        self.tree.column("speed", width=100, anchor="e")
        self.tree.column("eta", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(
            content_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _create_card(
        self, parent: ttk.Frame, col: int, title: str, value: str
    ) -> ttk.Label:
        card = ttk.Frame(parent, relief="groove", padding=self.spacing.sm)
        card.grid(row=0, column=col, padx=self.spacing.xs, sticky="nsew")

        lbl_title = ttk.Label(
            card, text=title, font=(self.typography.ui_font, self.typography.small_size)
        )
        lbl_title.pack(anchor="w")

        lbl_val = ttk.Label(
            card,
            text=value,
            font=(self.typography.ui_font, self.typography.h2_size, "bold"),
        )
        lbl_val.pack(anchor="w", pady=(self.spacing.xs, 0))
        return lbl_val

    def update_metrics(
        self,
        active_count: int,
        download_speed_str: str,
        upload_speed_str: str,
        completed_count: int,
    ) -> None:
        """Update metric card counters."""
        self.lbl_active.config(text=str(active_count))
        self.lbl_speed_down.config(text=download_speed_str)
        self.lbl_speed_up.config(text=upload_speed_str)
        self.lbl_completed.config(text=str(completed_count))
