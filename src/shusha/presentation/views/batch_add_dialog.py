"""
Batch URL Ingestion Dialog with range expansion pattern support for Shusha 2.
"""

import re
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as tb

from shusha.application.use_cases.download_use_cases import AddDownloadRequest
from shusha.domain.identifiers import CategoryId
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.base import BaseDialog, BaseFrame


def expand_batch_pattern(pattern: str) -> list[str]:
    """
    Expand numerical and alphabetic range patterns in URLs.
    Example: 'http://example.com/file[01-03].zip' -> ['...01.zip', '...02.zip', '...03.zip']
    """
    match = re.search(r"\[([0-9]+)-([0-9]+)\]", pattern)
    if match:
        start_str, end_str = match.groups()
        start, end = int(start_str), int(end_str)
        width = len(start_str) if start_str.startswith("0") else 0
        step = 1 if start <= end else -1

        urls: list[str] = []
        for num in range(start, end + step, step):
            formatted_num = f"{num:0{width}d}" if width else str(num)
            urls.append(
                pattern[: match.start()] + formatted_num + pattern[match.end() :]
            )
        return urls

    char_match = re.search(r"\[([a-zA-Z])-([a-zA-Z])\]", pattern)
    if char_match:
        c1, c2 = char_match.groups()
        s_ord, e_ord = ord(c1), ord(c2)
        step = 1 if s_ord <= e_ord else -1

        urls = []
        for ch_code in range(s_ord, e_ord + step, step):
            urls.append(
                pattern[: char_match.start()]
                + chr(ch_code)
                + pattern[char_match.end() :]
            )
        return urls

    return [pattern]


class BatchAddDialog(BaseDialog):
    """Modal dialog for pasting multiple URLs and expanding range expressions."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        ctx: AppContext,
        on_added: Callable[[], None] | None = None,
    ) -> None:
        self.ctx = ctx
        self.on_added = on_added

        super().__init__(
            parent=parent,
            title="Batch Add URLs — Shusha",
            min_width=650,
            min_height=500,
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_frame = BaseFrame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        lbl_desc = tb.Label(
            main_frame,
            text="Enter one URL per line. Range patterns like [01-10] and [a-z] are supported:",
            font=("TkDefaultFont", 9),
        )
        lbl_desc.pack(anchor="w", pady=(0, 4))

        # Text area
        text_frame = BaseFrame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.txt_urls = tk.Text(text_frame, wrap="none", font=("TkFixedFont", 9))
        scroll_v = tb.Scrollbar(
            text_frame, orient="vertical", command=self.txt_urls.yview
        )
        self.txt_urls.configure(yscrollcommand=scroll_v.set)

        self.txt_urls.pack(side="left", fill="both", expand=True)
        scroll_v.pack(side="right", fill="y")

        # Destination & Category
        dest_frame = BaseFrame(main_frame)
        dest_frame.pack(fill="x", pady=(0, 8))
        dest_frame.columnconfigure(1, weight=1)

        lbl_dir = tb.Label(dest_frame, text="Download Folder:")
        lbl_dir.grid(row=0, column=0, sticky="w", pady=2)

        self.txt_dir = tb.Entry(dest_frame)
        settings = self.ctx.settings_store.load_settings()
        self.txt_dir.insert(0, settings.download_dir)
        self.txt_dir.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        btn_browse = tb.Button(
            dest_frame,
            text="Browse...",
            bootstyle="secondary",
            command=self._on_browse_dir,
        )
        btn_browse.grid(row=0, column=2, pady=2)

        lbl_cat = tb.Label(dest_frame, text="Category:")
        lbl_cat.grid(row=1, column=0, sticky="w", pady=2)

        self.categories = self.ctx.category_repo.list_all()
        cat_names = ["(Auto-Detect)", "(None)"] + [c.name for c in self.categories]
        self.cmb_category = tb.Combobox(dest_frame, values=cat_names, state="readonly")
        self.cmb_category.current(0)
        self.cmb_category.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        # Action Buttons
        btn_box = BaseFrame(main_frame)
        btn_box.pack(fill="x")

        btn_start = tb.Button(
            btn_box,
            text="Start Downloads",
            bootstyle="primary",
            command=self._on_submit_batch,
        )
        btn_start.pack(side="right", padx=(4, 0))

        btn_cancel = tb.Button(
            btn_box,
            text="Cancel",
            bootstyle="secondary-outline",
            command=self.destroy,
        )
        btn_cancel.pack(side="right")

    def _on_browse_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Download Folder", parent=self)
        if path:
            self.txt_dir.delete(0, "end")
            self.txt_dir.insert(0, path)

    def _on_submit_batch(self) -> None:
        raw_text = self.txt_urls.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showwarning(
                "Empty Input", "Please enter at least one URL", parent=self
            )
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        expanded_urls: list[str] = []
        for line in lines:
            expanded_urls.extend(expand_batch_pattern(line))

        if not expanded_urls:
            messagebox.showwarning(
                "No Valid URLs", "No valid URLs found in input", parent=self
            )
            return

        target_dir = Path(self.txt_dir.get().strip())
        cat_sel = self.cmb_category.current()
        selected_category_id: CategoryId | None = None
        if cat_sel >= 2:
            selected_category_id = self.categories[cat_sel - 2].id

        # Submit individual downloads
        for url in expanded_urls:
            self.ctx.add_download_uc.execute(
                AddDownloadRequest(
                    uris=[url],
                    custom_dir=target_dir,
                    category_id=selected_category_id,
                )
            )

        if self.on_added:
            self.on_added()

        self.destroy()
