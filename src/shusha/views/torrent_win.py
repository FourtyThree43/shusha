"""
Torrent and Multi-File Selective Download Inspector Window.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService
from shusha.models.utilities import format_size

if TYPE_CHECKING:
    from shusha.controller.api import ShushaAPI as Api
    from shusha.models.structs_downloads import Download

logger = LoggerService(__name__)


class TorrentFilesWindow(ttk.Toplevel):
    """Dialog allowing users to inspect and selectively enable/disable files in a multi-file download."""

    def __init__(
        self,
        master: Any = None,
        api: Api | None = None,
        download: Download | None = None,
        on_applied: Any = None,
    ):
        super().__init__(
            title=f"Files - {download.name if download else 'Torrent'}",
            master=master,
            size=(700, 450),
            resizable=(True, True),
        )
        self.config(padx=12, pady=12)

        self.api = api
        self.download = download
        self.on_applied = on_applied
        self.file_vars: dict[int, tk.BooleanVar] = {}

        # Top label
        hdr_frame = ttk.Frame(self)
        hdr_frame.pack(fill=tk.X, pady=(0, 8))
        dl_name = download.name if download else "Unknown"
        ttk.Label(
            hdr_frame,
            text=f"Selective Download for: {dl_name}",
            font=("Helvetica", 11, "bold"),
        ).pack(side=tk.LEFT)

        # Table container
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ("selected", "index", "name", "size", "progress")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="extended"
        )
        self.tree.heading("selected", text="Download?")
        self.tree.heading("index", text="#")
        self.tree.heading("name", text="File Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("progress", text="Completed")

        self.tree.column("selected", width=90, anchor=tk.CENTER)
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=350, anchor=tk.W)
        self.tree.column("size", width=90, anchor=tk.E)
        self.tree.column("progress", width=90, anchor=tk.E)

        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self._toggle_selected_item)

        # Action Buttons
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_bar,
            text="Select All",
            bootstyle="secondary-outline",
            command=self._select_all,
            width=12,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_bar,
            text="Deselect All",
            bootstyle="secondary-outline",
            command=self._deselect_all,
            width=12,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_bar,
            text="Toggle",
            bootstyle="info-outline",
            command=self._toggle_selected_row,
            width=10,
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_bar,
            text="Apply Selection",
            bootstyle="success",
            command=self._apply_selection,
            width=14,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        ttk.Button(
            btn_bar,
            text="Close",
            bootstyle="secondary",
            command=self.destroy,
            width=10,
        ).pack(side=tk.RIGHT)

        self._populate_files()

    def _populate_files(self):
        """Populate table with files from download."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.download or not self.download.files:
            return

        for f in self.download.files:
            idx = int(f.index)
            is_selected = bool(f.selected)
            self.file_vars[idx] = tk.BooleanVar(value=is_selected)

            file_name = f.path.name if f.path else f"File #{idx}"
            size_str = format_size(f.length) if f.length else "Unknown"
            comp_str = format_size(f.completed_length) if f.completed_length else "0 B"
            status_text = "[X] YES" if is_selected else "[ ] NO"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(status_text, str(idx), file_name, size_str, comp_str),
            )

    def _toggle_selected_item(self, event=None):
        """Toggle checked state on double-click."""
        item = self.tree.focus()
        if item and item.isdigit():
            idx = int(item)
            current = self.file_vars[idx].get()
            self.file_vars[idx].set(not current)
            self._refresh_row(idx)

    def _toggle_selected_row(self):
        """Toggle selected rows."""
        selected = self.tree.selection()
        for item in selected:
            if item.isdigit():
                idx = int(item)
                current = self.file_vars[idx].get()
                self.file_vars[idx].set(not current)
                self._refresh_row(idx)

    def _select_all(self):
        for idx, var in self.file_vars.items():
            var.set(True)
            self._refresh_row(idx)

    def _deselect_all(self):
        for idx, var in self.file_vars.items():
            var.set(False)
            self._refresh_row(idx)

    def _refresh_row(self, idx: int):
        val = self.file_vars[idx].get()
        status_text = "[X] YES" if val else "[ ] NO"
        if self.tree.exists(str(idx)):
            curr = list(self.tree.item(str(idx), "values"))
            if curr:
                curr[0] = status_text
                self.tree.item(str(idx), values=curr)

    def _apply_selection(self):
        """Send select-file option to aria2 daemon."""
        selected_indices = [
            str(idx) for idx, var in self.file_vars.items() if var.get()
        ]
        if not selected_indices:
            return

        select_file_str = ",".join(selected_indices)
        if self.api and self.download and self.download.gid:
            try:
                self.api.client.change_option(
                    self.download.gid, {"select-file": select_file_str}
                )
                logger.log(
                    f"Updated selective download for {self.download.gid}: {select_file_str}"
                )
            except Exception as e:
                logger.log(f"Error applying selective download: {e}", level="error")

        if callable(self.on_applied):
            self.on_applied()
        self.destroy()
