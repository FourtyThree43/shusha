"""Batch Download Addition Dialog for Shusha-DM.

This modal dialog allows users to enter multi-line URLs, auto-expand sequence range patterns
like `http://example.com/item[01-20].zip`, paste links from clipboard, and attach custom
HTTP headers, cookies, Referer, and save directories.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

import ttkbootstrap as ttk

from shusha.models.batch_parser import extract_urls
from shusha.models.utilities import user_downloads_dir


class BatchAddWindow(ttk.Toplevel):
    """Modal dialog for smart batch URL parsing and download dispatch."""

    def __init__(
        self,
        master: Any = None,
        callback: Callable[[list[str], dict[str, Any]], None] | None = None,
        initial_text: str = "",
    ) -> None:
        super().__init__(master=master)
        self.callback = callback
        self.title("Batch Add Downloads - Shusha")
        self.geometry("640x520")
        self.minsize(500, 400)

        self._build_ui(initial_text)

    def _build_ui(self, initial_text: str) -> None:
        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=tk.YES)

        # Instructions / Help
        ttk.Label(
            main_frame,
            text="Enter one or more URLs (supports range patterns like [01-10] and magnet links):",
            font=("TkDefaultFont", 9),
        ).pack(anchor="w", pady=(0, 4))

        # Text Area
        self.text_box = tk.Text(main_frame, height=10, wrap=tk.NONE)
        self.text_box.pack(fill=tk.BOTH, expand=tk.YES)
        if initial_text:
            self.text_box.insert("1.0", initial_text)

        # Action bar under text box
        bar = ttk.Frame(main_frame)
        bar.pack(fill=tk.X, pady=(4, 8))

        ttk.Button(
            bar,
            text="Paste from Clipboard",
            command=self._paste_clipboard,
            bootstyle="outline-secondary",
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            bar,
            text="Preview / Parse URLs",
            command=self._parse_preview,
            bootstyle="outline-info",
        ).pack(side=tk.LEFT, padx=4)

        self.count_label = ttk.Label(
            bar, text="0 links detected", foreground="gray", font=("TkDefaultFont", 8)
        )
        self.count_label.pack(side=tk.RIGHT, padx=4)

        # Options Frame
        opts_lf = ttk.Labelframe(main_frame, text="Download Options", padding=8)
        opts_lf.pack(fill=tk.X, pady=(0, 10))

        # Save Dir
        dir_row = ttk.Frame(opts_lf)
        dir_row.pack(fill=tk.X, pady=2)
        ttk.Label(dir_row, text="Save Folder:", width=14).pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value=str(user_downloads_dir()))
        ttk.Entry(dir_row, textvariable=self.dir_var).pack(
            side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=4
        )

        # Referer & User-Agent
        ref_row = ttk.Frame(opts_lf)
        ref_row.pack(fill=tk.X, pady=2)
        ttk.Label(ref_row, text="Referer URL:", width=14).pack(side=tk.LEFT)
        self.referer_var = tk.StringVar()
        ttk.Entry(ref_row, textvariable=self.referer_var).pack(
            side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=4
        )

        # Connections & Split
        conn_row = ttk.Frame(opts_lf)
        conn_row.pack(fill=tk.X, pady=2)
        ttk.Label(conn_row, text="Split Chunks:", width=14).pack(side=tk.LEFT)
        self.split_var = tk.StringVar(value="8")
        ttk.Spinbox(conn_row, from_=1, to=16, textvariable=self.split_var, width=5).pack(
            side=tk.LEFT, padx=4
        )

        # Buttons
        btn_box = ttk.Frame(main_frame)
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            btn_box,
            text="Cancel",
            command=self.destroy,
            bootstyle="secondary",
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Button(
            btn_box,
            text="Start Downloads",
            command=self._on_submit,
            bootstyle="success",
        ).pack(side=tk.RIGHT, padx=4)

        self._parse_preview()

    def _paste_clipboard(self) -> None:
        try:
            clip = self.clipboard_get()
            if clip:
                self.text_box.insert(tk.END, ("\n" if self.text_box.get("1.0", tk.END).strip() else "") + clip.strip())
                self._parse_preview()
        except Exception:
            pass

    def _parse_preview(self) -> list[str]:
        raw = self.text_box.get("1.0", tk.END)
        urls = extract_urls(raw)
        self.count_label.config(text=f"{len(urls)} links ready to download")
        return urls

    def _on_submit(self) -> None:
        urls = self._parse_preview()
        if not urls:
            return

        options: dict[str, Any] = {}
        if self.dir_var.get().strip():
            options["dir"] = self.dir_var.get().strip()
        if self.referer_var.get().strip():
            options["referer"] = self.referer_var.get().strip()
        if self.split_var.get().strip():
            options["split"] = self.split_var.get().strip()

        if self.callback:
            self.callback(urls, options)

        self.destroy()
