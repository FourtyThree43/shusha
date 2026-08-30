"""Modern System Doctor & Diagnostics view for Desktop (E11, E12)."""

from __future__ import annotations

import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any

from shusha.presentation.app_context import AppContext
from shusha.presentation.theme import SpacingTokens, TypographyTokens


class DoctorView(ttk.Frame):
    """System health inspection and backend diagnostics overview."""

    def __init__(self, parent: tk.Misc, context: AppContext, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.context = context
        self.spacing = SpacingTokens()
        self.typography = TypographyTokens()

        self._build_ui()
        self.run_checks()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header
        header = ttk.Frame(self, padding=self.spacing.md)
        header.grid(row=0, column=0, sticky="ew")

        lbl_title = ttk.Label(
            header,
            text="System Doctor & Backend Diagnostics",
            font=(self.typography.ui_font, self.typography.h1_size, "bold"),
        )
        lbl_title.pack(side="left")

        self.btn_refresh = ttk.Button(
            header, text="Re-run Probes", command=self.run_checks
        )
        self.btn_refresh.pack(side="right")

        # Probes Table / List
        content = ttk.Frame(self, padding=self.spacing.md)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        cols = ("status", "subsystem", "detail", "recommendation")
        self.tree = ttk.Treeview(
            content, columns=cols, show="headings", selectmode="browse"
        )
        self.tree.heading("status", text="Status")
        self.tree.heading("subsystem", text="Subsystem")
        self.tree.heading("detail", text="Diagnostic Information")
        self.tree.heading("recommendation", text="Remediation Advice")

        self.tree.column("status", width=90, anchor="center")
        self.tree.column("subsystem", width=160, anchor="w")
        self.tree.column("detail", width=320, anchor="w")
        self.tree.column("recommendation", width=250, anchor="w")

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def run_checks(self) -> None:
        """Run all environment and subsystem health probes."""
        self.tree.delete(*self.tree.get_children())

        # 1. Python Runtime
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self._add_row(
            "✔ PASS", "Python Runtime", f"Python {py_ver}", "Target runtime satisfied."
        )

        # 2. aria2 Binary
        aria2_path = shutil.which("aria2c")
        if aria2_path:
            self._add_row(
                "✔ PASS",
                "aria2c Binary",
                f"Found at {aria2_path}",
                "Reference engine available.",
            )
        else:
            self._add_row(
                "▲ WARN",
                "aria2c Binary",
                "Not found on system PATH",
                "Install aria2 for multi-source BitTorrent/HTTP.",
            )

        # 3. yt-dlp Binary
        ytdlp_path = shutil.which("yt-dlp")
        if ytdlp_path:
            self._add_row(
                "✔ PASS",
                "yt-dlp Binary",
                f"Found at {ytdlp_path}",
                "Media extraction engine available.",
            )
        else:
            self._add_row(
                "▲ WARN",
                "yt-dlp Binary",
                "Not found on system PATH",
                "Install yt-dlp for video stream extraction.",
            )

        # 4. Storage Write Access
        download_dir = os.path.expanduser("~/Downloads")
        if os.path.isdir(download_dir) and os.access(download_dir, os.W_OK):
            self._add_row(
                "✔ PASS",
                "Download Directory",
                f"Writable: {download_dir}",
                "Storage ready.",
            )
        else:
            self._add_row(
                "✖ FAIL",
                "Download Directory",
                f"Cannot write to {download_dir}",
                "Check filesystem permissions.",
            )

        # 5. Network Proxy Environment
        proxies = [
            k for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY") if os.environ.get(k)
        ]
        if proxies:
            self._add_row(
                "✔ PASS",
                "Network Proxies",
                f"Active: {', '.join(proxies)}",
                "Proxy routing detected.",
            )
        else:
            self._add_row(
                "✔ PASS",
                "Network Proxies",
                "Direct connection (no proxy)",
                "Direct network access.",
            )

        # 6. Backend Registry & Plugins
        if self.context.backend_registry:
            backends = self.context.backend_registry.list_backends()
            names = ", ".join(b.identity.id for b in backends)
            self._add_row(
                "✔ PASS",
                "Backend Registry",
                f"{len(backends)} backends registered ({names})",
                "Orchestration operational.",
            )

    def _add_row(
        self, status: str, subsystem: str, detail: str, recommendation: str
    ) -> None:
        self.tree.insert("", "end", values=(status, subsystem, detail, recommendation))
