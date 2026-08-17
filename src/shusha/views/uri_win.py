"""
Dynamic Mirror & URI Management Dialog for Shusha.
Allows viewing, adding new mirror URLs, or deleting dead mirror links for an active download.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService

if TYPE_CHECKING:
    from shusha.controller.api import ShushaAPI as Api

logger = LoggerService(__name__)


class UriManagerWindow(ttk.Toplevel):
    """Dialog to dynamically manage mirror URIs for an aria2 download task."""

    def __init__(
        self, master=None, api: Api | None = None, gid: str = "", **kwargs: Any
    ):
        super().__init__(
            title=f"Manage Mirrors & URIs (GID: {gid[:8]}...)",
            master=master,
            size=(640, 420),
            resizable=(True, True),
            **kwargs,
        )
        self.config(padx=12, pady=12)
        self.api = api
        self.gid = gid

        self._build_ui()
        self._load_uris()

    def _build_ui(self):
        # Description
        ttk.Label(
            self,
            text="Active Download Mirrors & Alternative URIs",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        # URIs Treeview
        cols = ("uri", "status")
        self.tree = ttk.Treeview(
            self, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("uri", text="Mirror / Source URI")
        self.tree.heading("status", text="Status")
        self.tree.column("uri", width=460)
        self.tree.column("status", width=120, anchor=tk.CENTER)

        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=tree_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y, in_=tree_frame)

        # Add New URI Frame
        add_frame = ttk.Labelframe(self, text="Add New Mirror URI", padding=8)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        self.new_uri_var = tk.StringVar()
        entry = ttk.Entry(add_frame, textvariable=self.new_uri_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        add_btn = ttk.Button(
            add_frame,
            text="Add Mirror",
            bootstyle="success",
            command=self._on_add_uri,
        )
        add_btn.pack(side=tk.RIGHT)

        # Bottom Button Bar
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X)

        remove_btn = ttk.Button(
            btn_bar,
            text="Delete Selected URI",
            bootstyle="danger",
            command=self._on_delete_uri,
        )
        remove_btn.pack(side=tk.LEFT)

        close_btn = ttk.Button(
            btn_bar,
            text="Close",
            bootstyle="secondary",
            command=self.destroy,
        )
        close_btn.pack(side=tk.RIGHT)

    def _load_uris(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.api or not self.gid:
            return

        try:
            uris = self.api.client.get_uris(self.gid)
            if isinstance(uris, list):
                for u in uris:
                    uri_val = u.get("uri", "")
                    status_val = u.get("status", "unknown")
                    self.tree.insert("", "end", values=(uri_val, status_val))
        except Exception as e:
            logger.log(f"Error loading URIs for {self.gid}: {e}", level="error")

    def _on_add_uri(self):
        new_uri = self.new_uri_var.get().strip()
        if not new_uri or not self.api or not self.gid:
            return

        res = self.api.change_uri(self.gid, file_index=1, add_uris=[new_uri])
        logger.log(f"Added URI {new_uri} to {self.gid}: result {res}")
        self.new_uri_var.set("")
        self._load_uris()

    def _on_delete_uri(self):
        selected = self.tree.selection()
        if not selected or not self.api or not self.gid:
            return
        item_values = self.tree.item(selected[0], "values")
        if not item_values:
            return
        del_uri = item_values[0]

        res = self.api.change_uri(self.gid, file_index=1, del_uris=[del_uri])
        logger.log(f"Deleted URI {del_uri} from {self.gid}: result {res}")
        self._load_uris()
