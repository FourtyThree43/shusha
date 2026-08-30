"""Modern Navigation Sidebar for Shusha Desktop (E11 Modern UI)."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as tb

from shusha.domain.category import Category
from shusha.presentation.components.base import BaseFrame
from shusha.presentation.theme import SpacingTokens, TypographyTokens


class AppSidebar(BaseFrame):
    """Sidebar navigation rail displaying primary application views and categories."""

    def __init__(
        self,
        parent: tk.Misc,
        on_nav_selected: Callable[[str], None] | None = None,
        on_filter_selected: Callable[[str, str | None], None] | None = None,
    ) -> None:
        super().__init__(parent, padding=SpacingTokens().sm)
        self.on_nav_selected = on_nav_selected
        self.on_filter_selected = on_filter_selected
        self.spacing = SpacingTokens()
        self.typography = TypographyTokens()
        self._categories: list[Category] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        lbl_header = tb.Label(
            self,
            text="NAVIGATION",
            font=(self.typography.ui_font, 8, "bold"),
            bootstyle="secondary",
        )
        lbl_header.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 6))

        self.tree = tb.Treeview(
            self,
            show="tree",
            selectmode="browse",
            bootstyle="secondary",
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        # 1. Primary Views
        self._root_views = self.tree.insert(
            "", "end", iid="nav_root", text="Views", open=True
        )
        self.tree.insert(
            self._root_views, "end", iid="nav:dashboard", text="📊 Dashboard"
        )
        self.tree.insert(
            self._root_views, "end", iid="nav:transfers", text="⚡ Downloads"
        )
        self.tree.insert(
            self._root_views, "end", iid="nav:inbox", text="📥 Acquisition Inbox"
        )
        self.tree.insert(
            self._root_views, "end", iid="nav:media", text="🎬 Media Grabber"
        )
        self.tree.insert(self._root_views, "end", iid="nav:plugins", text="🧩 Plugins")
        self.tree.insert(
            self._root_views, "end", iid="nav:doctor", text="🩺 Doctor & Health"
        )

        # 2. State Filters (under Transfers)
        self._root_status = self.tree.insert(
            "", "end", iid="status_root", text="Download Filters", open=True
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:all", text="  ● All Transfers"
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:active", text="  ⚡ Active"
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:paused", text="  ⏸ Paused"
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:completed", text="  ✔ Completed"
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:failed", text="  ✖ Failed"
        )

        # 3. Categories branch
        self._root_cats = self.tree.insert(
            "", "end", iid="cats_root", text="Categories", open=True
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.selection_set("nav:transfers")

    def _on_select(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        if item_id.startswith("nav:"):
            nav_view = item_id.split("nav:")[-1]
            if self.on_nav_selected:
                self.on_nav_selected(nav_view)
        elif item_id.startswith("filter:"):
            filter_val = item_id.split("filter:")[-1]
            # Ensure we're viewing transfers
            if self.on_nav_selected:
                self.on_nav_selected("transfers")
            if self.on_filter_selected:
                self.on_filter_selected(
                    "state", None if filter_val == "all" else filter_val
                )
        elif item_id.startswith("category:"):
            cat_val = item_id.split("category:")[-1]
            if self.on_nav_selected:
                self.on_nav_selected("transfers")
            if self.on_filter_selected:
                self.on_filter_selected("category", cat_val)

    def update_categories(self, categories: list[Category]) -> None:
        """Refresh category items in the sidebar."""
        self._categories = categories
        for child in self.tree.get_children(self._root_cats):
            self.tree.delete(child)

        for cat in categories:
            iid = f"category:{cat.id}"
            self.tree.insert(self._root_cats, "end", iid=iid, text=f"  📁 {cat.name}")
