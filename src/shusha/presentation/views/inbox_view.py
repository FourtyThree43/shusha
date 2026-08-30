"""Acquisition Inbox View for reviewing detected capture candidates (E11-I07)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shusha.domain.acquisition import AcquisitionRequest
from shusha.presentation.app_context import AppContext
from shusha.presentation.theme import SpacingTokens


class AcquisitionInboxView(ttk.Frame):
    """View allowing users to inspect, accept, or ignore detected items from clipboard/browser/drag-drop."""

    def __init__(self, parent: tk.Misc, context: AppContext, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.context = context
        self.spacing = SpacingTokens()
        self._items: dict[str, AcquisitionRequest] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ttk.Frame(self, padding=self.spacing.sm)
        toolbar.grid(row=0, column=0, sticky="ew")

        self.btn_accept = ttk.Button(
            toolbar, text="Accept & Download", command=self._on_accept
        )
        self.btn_accept.pack(side="left", padx=self.spacing.xs)

        self.btn_ignore = ttk.Button(
            toolbar, text="Ignore Item", command=self._on_ignore
        )
        self.btn_ignore.pack(side="left", padx=self.spacing.xs)

        self.btn_refresh = ttk.Button(
            toolbar, text="Refresh Inbox", command=self.refresh
        )
        self.btn_refresh.pack(side="right", padx=self.spacing.xs)

        # Table
        table_frame = ttk.Frame(self, padding=self.spacing.sm)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "source", "kind", "input", "backend", "status")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("source", text="Source")
        self.tree.heading("kind", text="Detected Type")
        self.tree.heading("input", text="Payload / URL")
        self.tree.heading("backend", text="Recommended Backend")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("source", width=100, anchor="center")
        self.tree.column("kind", width=120, anchor="center")
        self.tree.column("input", width=300, anchor="w")
        self.tree.column("backend", width=100, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def refresh(self) -> None:
        """Fetch items from AcquisitionInbox."""
        self.tree.delete(*self.tree.get_children())
        self._items.clear()

        if self.context.acquisition_inbox is None:
            return

        items = self.context.acquisition_inbox.list_active()
        for item in items:
            self._items[str(item.id)] = item
            self.tree.insert(
                "",
                "end",
                iid=str(item.id),
                values=(
                    str(item.id),
                    item.source_kind.value,
                    item.detected_kind.value,
                    item.raw_input,
                    str(item.preferred_backend or "auto"),
                    item.status.value,
                ),
            )

    def _on_accept(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        if self.context.acquisition_inbox:
            self.context.acquisition_inbox.accept(item_id)
        self.refresh()

    def _on_ignore(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        if self.context.acquisition_inbox:
            self.context.acquisition_inbox.ignore(item_id)
        self.refresh()
