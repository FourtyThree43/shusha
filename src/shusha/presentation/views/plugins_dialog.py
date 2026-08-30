"""Plugin Management and Permissions Dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from shusha.presentation.app_context import AppContext
from shusha.presentation.theme import SpacingTokens


class PluginsDialog(tk.Toplevel):
    """View and manage loaded plugins, capabilities, and sandboxed permissions."""

    def __init__(
        self,
        parent: tk.Misc | None = None,
        context: AppContext | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.context = context
        self.spacing = SpacingTokens()
        self.title("Plugin Architecture & Permissions")
        self.geometry("640x440")
        if parent and isinstance(parent, tk.Wm):
            self.transient(parent)

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Table
        table_frame = ttk.Frame(self, padding=self.spacing.md)
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "name", "version", "permissions", "status")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("id", text="Plugin ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("version", text="Version")
        self.tree.heading("permissions", text="Declared Permissions")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=120, anchor="w")
        self.tree.column("name", width=140, anchor="w")
        self.tree.column("version", width=60, anchor="center")
        self.tree.column("permissions", width=180, anchor="w")
        self.tree.column("status", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bottom Bar
        bottom = ttk.Frame(self, padding=self.spacing.sm)
        bottom.grid(row=1, column=0, sticky="ew")

        self.btn_close = ttk.Button(bottom, text="Close", command=self.destroy)
        self.btn_close.pack(side="right")

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        if not self.context or not self.context.plugin_loader:
            return

        active_plugins = self.context.plugin_loader.get_active_plugins()
        for p in active_plugins:
            perms = (
                ", ".join(p.manifest.permissions) if p.manifest.permissions else "None"
            )
            self.tree.insert(
                "",
                "end",
                iid=p.manifest.id,
                values=(
                    p.manifest.id,
                    p.manifest.name,
                    p.manifest.version,
                    perms,
                    "Active",
                ),
            )
