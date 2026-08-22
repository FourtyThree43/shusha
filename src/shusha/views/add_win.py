"""Add Download Dialog for URLs, Torrents, and Metalinks.

Supports:
- Multi-line URL entry with live category auto-detection.
- Category folder routing (Videos, Audio, Archives, Documents, Programs, Images).
- Checksum verification (sha-256, md5).
- Advanced connection splits, renaming, custom User-Agent, Referer, Cookies, and Proxy.
"""

from __future__ import annotations

import pathlib
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import askdirectory
from typing import Any

import ttkbootstrap as ttk

from shusha.models.category_manager import CategoryManager
from shusha.models.utilities import download_dir

DEFAULT_DIR = download_dir()
CATEGORIES = ["Auto-Detect", "Video", "Audio", "Archive", "Document", "Software", "Image", "Other"]


class AddWindow(ttk.Toplevel):
    """Modern modal dialog for adding new single or multi-URL downloads."""

    def __init__(self, callback: Any) -> None:
        super().__init__(
            title="Add Download - Shusha",
            size=(760, 520),
            resizable=(True, True),
        )
        self.minsize(640, 440)
        self.config(padx=15, pady=15)
        self.callback = callback

        # Form variables
        self.path_var = ttk.StringVar(value=str(DEFAULT_DIR))
        self.torrent_file_var = ttk.StringVar(value="")
        self.category_var = ttk.StringVar(value="Auto-Detect")
        self.rename_var = ttk.StringVar(value="")
        self.split_var = ttk.IntVar(value=8)
        self.checksum_var = ttk.StringVar(value="")
        self.user_agent_var = ttk.StringVar(value="")
        self.referer_var = ttk.StringVar(value="")
        self.header_var = ttk.StringVar(value="")
        self.proxy_var = ttk.StringVar(value="")

        # Notebook container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._build_url_page()
        self._build_torrent_page()
        self._build_advanced_page()

    def _build_url_page(self) -> None:
        """Create URL download page."""
        page = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(page, text="URL Download")

        # URLs text input
        url_row = ttk.Frame(page)
        url_row.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        ttk.Label(url_row, text="Download URLs (one per line):").pack(anchor=tk.W, pady=(0, 2))
        self.urls = ttk.ScrolledText(url_row, wrap=tk.WORD, height=4)
        self.urls.pack(fill=tk.BOTH, expand=True)
        self.urls.bind("<KeyRelease>", self._on_url_text_change)

        # Options Container
        opt_lf = ttk.Labelframe(page, text="Download Options & Category", padding=10)
        opt_lf.pack(fill=tk.X, pady=(0, 10))

        grid = ttk.Frame(opt_lf)
        grid.pack(fill=tk.X)

        # Category
        ttk.Label(grid, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=3)
        cat_combo = ttk.Combobox(grid, textvariable=self.category_var, values=CATEGORIES, width=14, state="readonly")
        cat_combo.grid(row=0, column=1, sticky=tk.W, pady=3, padx=(5, 15))
        cat_combo.bind("<<ComboboxSelected>>", self._on_category_selected)

        # Splits
        ttk.Label(grid, text="Splits:").grid(row=0, column=2, sticky=tk.W, pady=3)
        ttk.Spinbox(grid, textvariable=self.split_var, from_=1, to=64, width=5).grid(row=0, column=3, sticky=tk.W, pady=3, padx=5)

        # Rename
        ttk.Label(grid, text="Rename File:").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(grid, textvariable=self.rename_var, width=30).grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=3, padx=5)

        # Checksum
        ttk.Label(grid, text="Checksum (sha-256=...):").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(grid, textvariable=self.checksum_var, width=30).grid(row=2, column=1, columnspan=3, sticky=tk.EW, pady=3, padx=5)

        # Destination folder
        path_row = ttk.Frame(opt_lf)
        path_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(path_row, text="Save to:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(path_row, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(path_row, text="Browse...", command=self._on_browse, bootstyle="secondary-outline").pack(side=tk.RIGHT)

        # Bottom buttons
        btn_bar = ttk.Frame(page)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_bar, text="Cancel", command=self.destroy, bootstyle="secondary", width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_bar, text="Download", command=self._submit_urls, bootstyle="success", width=12).pack(side=tk.RIGHT)

    def _build_torrent_page(self) -> None:
        """Create Torrent / Metalink page."""
        page = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(page, text="Torrent / Metalink")

        t_row = ttk.Frame(page)
        t_row.pack(fill=tk.X, pady=(10, 15))

        ttk.Label(t_row, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(t_row, textvariable=self.torrent_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(t_row, text="Browse...", command=self._on_browse_torrent, bootstyle="info-outline").pack(side=tk.RIGHT)

        opt_lf = ttk.Labelframe(page, text="Save Location", padding=10)
        opt_lf.pack(fill=tk.X, pady=(0, 15))

        path_row = ttk.Frame(opt_lf)
        path_row.pack(fill=tk.X)
        ttk.Label(path_row, text="Save to:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(path_row, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(path_row, text="Browse...", command=self._on_browse, bootstyle="secondary-outline").pack(side=tk.RIGHT)

        btn_bar = ttk.Frame(page)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_bar, text="Cancel", command=self.destroy, bootstyle="secondary", width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_bar, text="Start Torrent", command=self._submit_torrent, bootstyle="success", width=14).pack(side=tk.RIGHT)

    def _build_advanced_page(self) -> None:
        """Create Advanced HTTP / Network options page."""
        page = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(page, text="Advanced Network")

        lf = ttk.Labelframe(page, text="HTTP Headers & Proxies", padding=10)
        lf.pack(fill=tk.BOTH, expand=True)

        grid = ttk.Frame(lf)
        grid.pack(fill=tk.X)

        fields = [
            ("User-Agent:", self.user_agent_var),
            ("Referer:", self.referer_var),
            ("Custom Header (Key: Value):", self.header_var),
            ("Proxy (e.g. http://127.0.0.1:8080):", self.proxy_var),
        ]

        for idx, (lbl_text, var) in enumerate(fields):
            ttk.Label(grid, text=lbl_text).grid(row=idx, column=0, sticky=tk.W, pady=4)
            ttk.Entry(grid, textvariable=var, width=40).grid(row=idx, column=1, sticky=tk.EW, pady=4, padx=5)

        grid.columnconfigure(1, weight=1)

    def _on_url_text_change(self, event: Any = None) -> None:
        """Auto-detect category from first URL in text area."""
        if self.category_var.get() != "Auto-Detect":
            return

        lines = self.urls.get("1.0", tk.END).strip().split("\n")
        first_url = lines[0].strip() if lines else ""
        if first_url:
            detected_cat = CategoryManager.get_category(first_url)
            if detected_cat != "Other":
                target_dir = CategoryManager.get_category_directory(DEFAULT_DIR, detected_cat, auto_subfolder=True)
                self.path_var.set(str(target_dir))

    def _on_category_selected(self, event: Any = None) -> None:
        """Update destination path when category is manually selected."""
        cat = self.category_var.get()
        if cat != "Auto-Detect":
            target_dir = CategoryManager.get_category_directory(DEFAULT_DIR, cat, auto_subfolder=True)
            self.path_var.set(str(target_dir))

    def _on_browse(self) -> None:
        path = askdirectory(title="Select Download Directory", initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)

    def _on_browse_torrent(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Torrent or Metalink file",
            filetypes=[
                ("Torrent / Metalink files", "*.torrent;*.metalink"),
                ("All files", "*.*"),
            ],
            parent=self,
        )
        if file_path:
            self.torrent_file_var.set(file_path)

    def _submit_urls(self) -> None:
        content = self.urls.get("1.0", tk.END).strip()
        if not content:
            self.destroy()
            return

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        var_list = [ttk.StringVar(value=line) for line in lines]
        dpath = pathlib.Path(self.path_var.get())
        split = self.split_var.get()
        rename = self.rename_var.get().strip()
        checksum = self.checksum_var.get().strip()

        opts: dict[str, Any] = {
            "dir": str(dpath),
            "split": split,
        }
        if rename:
            opts["out"] = rename
        if checksum:
            opts["checksum"] = checksum
        if self.user_agent_var.get().strip():
            opts["user-agent"] = self.user_agent_var.get().strip()
        if self.referer_var.get().strip():
            opts["referer"] = self.referer_var.get().strip()
        if self.header_var.get().strip():
            opts["header"] = self.header_var.get().strip()
        if self.proxy_var.get().strip():
            opts["all-proxy"] = self.proxy_var.get().strip()

        if var_list:
            self.callback(var_list, opts)

        self.destroy()

    def _submit_torrent(self) -> None:
        t_path = self.torrent_file_var.get().strip()
        dpath = pathlib.Path(self.path_var.get())
        opts = {"dir": str(dpath)}
        if t_path:
            self.callback([ttk.StringVar(value=t_path)], opts)
        self.destroy()

    def submit(self) -> None:
        """Alias for submit_urls."""
        self._submit_urls()

    def submit_torrent(self) -> None:
        """Alias for submit_torrent."""
        self._submit_torrent()
