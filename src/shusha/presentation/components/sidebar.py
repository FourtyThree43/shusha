"""
Sidebar navigation and category filter component for Shusha 2.
"""

import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as tb

from shusha.domain.category import Category
from shusha.presentation.components.base import BaseFrame


class AppSidebar(BaseFrame):
    """Sidebar navigation displaying download status groups and user categories."""

    def __init__(
        self,
        parent: tk.Misc,
        on_filter_selected: Callable[[str, str | None], None] | None = None,
    ) -> None:
        super().__init__(parent, padding=6)
        self.on_filter_selected = on_filter_selected
        self._categories: list[Category] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        lbl_header = tb.Label(self, text="FILTERS", font=("TkDefaultFont", 9, "bold"))
        lbl_header.grid(row=0, column=0, sticky="w", padx=4, pady=(2, 4))

        self.tree = tb.Treeview(
            self,
            show="tree",
            selectmode="browse",
            bootstyle="secondary",
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Top-level status filters
        self._root_status = self.tree.insert(
            "", "end", iid="status_root", text="Status", open=True
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:all", text="📥 All Downloads"
        )
        self.tree.insert(
            self._root_status, "end", iid="filter:active", text="⚡ Downloading"
        )
        self.tree.insert(self._root_status, "end", iid="filter:paused", text="⏸ Paused")
        self.tree.insert(
            self._root_status, "end", iid="filter:completed", text="✔ Completed"
        )
        self.tree.insert(self._root_status, "end", iid="filter:failed", text="❌ Error")

        # Categories branch
        self._root_cats = self.tree.insert(
            "", "end", iid="cats_root", text="Categories", open=True
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.selection_set("filter:all")

    def _on_select(self, _event: tk.Event[tk.Misc]) -> None:
        selected = self.tree.selection()
        if not selected or not self.on_filter_selected:
            return

        item_id = selected[0]
        if item_id.startswith("filter:"):
            filter_val = item_id.split("filter:")[-1]
            self.on_filter_selected(
                "state", None if filter_val == "all" else filter_val
            )
        elif item_id.startswith("category:"):
            cat_val = item_id.split("category:")[-1]
            self.on_filter_selected("category", cat_val)

    def update_categories(self, categories: list[Category]) -> None:
        """Refresh category items in the sidebar."""
        self._categories = categories
        # Clear existing category leaves
        for child in self.tree.get_children(self._root_cats):
            self.tree.delete(child)

        for cat in categories:
            iid = f"category:{cat.id}"
            self.tree.insert(self._root_cats, "end", iid=iid, text=f"📁 {cat.name}")
