"""
Add Download Dialog with progressive disclosure (Basic, Advanced, Expert) for Shusha 2.
"""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import ttkbootstrap as tb

from shusha.application.use_cases.download_use_cases import AddDownloadRequest
from shusha.domain.identifiers import CategoryId
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.base import BaseDialog, BaseFrame


class AddDownloadDialog(BaseDialog):
    """Modal dialog for submitting new downloads (URIs, torrents, or metalinks)."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        ctx: AppContext,
        initial_url: str = "",
        on_added: Callable[[], None] | None = None,
    ) -> None:
        self.ctx = ctx
        self.on_added = on_added
        self.torrent_bytes: bytes | None = None
        self.metalink_bytes: bytes | None = None

        super().__init__(
            parent=parent,
            title="Add New Download",
            min_width=600,
            min_height=450,
        )

        self._setup_form(initial_url)

    def _setup_form(self, initial_url: str) -> None:
        main_frame = BaseFrame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        # 1. URL / Source
        lbl_url = tb.Label(
            main_frame, text="URL / Magnet Link:", font=("TkDefaultFont", 9, "bold")
        )
        lbl_url.pack(anchor="w", pady=(0, 2))

        url_frame = BaseFrame(main_frame)
        url_frame.pack(fill="x", pady=(0, 8))

        self.txt_url = tb.Entry(url_frame)
        self.txt_url.insert(0, initial_url)
        self.txt_url.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_browse_torrent = tb.Button(
            url_frame,
            text="Open Torrent/Metalink...",
            bootstyle="secondary-outline",
            command=self._on_browse_file,
        )
        btn_browse_torrent.pack(side="right")

        # 2. Destination & Category
        dest_frame = BaseFrame(main_frame)
        dest_frame.pack(fill="x", pady=(0, 8))

        lbl_dir = tb.Label(dest_frame, text="Download Folder:")
        lbl_dir.grid(row=0, column=0, sticky="w", pady=2)

        self.txt_dir = tb.Entry(dest_frame)
        settings = self.ctx.settings_store.load_settings()
        self.txt_dir.insert(0, settings.download_dir)
        self.txt_dir.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        btn_browse_dir = tb.Button(
            dest_frame,
            text="Browse...",
            bootstyle="secondary",
            command=self._on_browse_dir,
        )
        btn_browse_dir.grid(row=0, column=2, padx=(2, 0), pady=2)

        lbl_cat = tb.Label(dest_frame, text="Category:")
        lbl_cat.grid(row=1, column=0, sticky="w", pady=2)

        self.categories = self.ctx.category_repo.list_all()
        cat_names = ["(Auto-Detect)", "(None)"] + [c.name for c in self.categories]
        self.cmb_category = tb.Combobox(dest_frame, values=cat_names, state="readonly")
        self.cmb_category.current(0)
        self.cmb_category.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        dest_frame.columnconfigure(1, weight=1)

        # 3. Progressive Disclosure Notebook
        self.notebook = tb.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, pady=8)

        # Tab: Basic Options
        tab_basic = BaseFrame(self.notebook, padding=8)
        self.notebook.add(tab_basic, text="Basic Options")
        self._setup_basic_tab(tab_basic)

        # Tab: Advanced Options
        tab_adv = BaseFrame(self.notebook, padding=8)
        self.notebook.add(tab_adv, text="Advanced Options")
        self._setup_adv_tab(tab_adv)

        # 4. Action Buttons
        btn_frame = BaseFrame(main_frame)
        btn_frame.pack(fill="x", pady=(4, 0))

        btn_cancel = tb.Button(
            btn_frame, text="Cancel", bootstyle="secondary", command=self.cancel
        )
        btn_cancel.pack(side="right", padx=(4, 0))

        btn_submit = tb.Button(
            btn_frame, text="Start Download", bootstyle="primary", command=self.submit
        )
        btn_submit.pack(side="right")

    def _setup_basic_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        tb.Label(parent, text="Max Connections:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.spn_connections = tb.Spinbox(parent, from_=1, to=16)
        self.spn_connections.set("16")
        self.spn_connections.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        tb.Label(parent, text="Split Parts:").grid(row=1, column=0, sticky="w", pady=4)
        self.spn_split = tb.Spinbox(parent, from_=1, to=16)
        self.spn_split.set("8")
        self.spn_split.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        self.chk_integrity = tb.Checkbutton(
            parent, text="Verify file integrity before starting"
        )
        self.chk_integrity.grid(row=2, column=0, columnspan=2, sticky="w", pady=4)
        self.chk_integrity.invoke()

    def _setup_adv_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        tb.Label(parent, text="Custom Referer:").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.txt_referer = tb.Entry(parent)
        self.txt_referer.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        tb.Label(parent, text="Custom User-Agent:").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.txt_user_agent = tb.Entry(parent)
        self.txt_user_agent.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        tb.Label(parent, text="Speed Limit (e.g. 2M):").grid(
            row=2, column=0, sticky="w", pady=4
        )
        self.txt_speed_limit = tb.Entry(parent)
        self.txt_speed_limit.grid(row=2, column=1, sticky="ew", padx=4, pady=4)

    def _on_browse_file(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Select Torrent or Metalink File",
            filetypes=[
                ("Torrent / Metalink", "*.torrent *.metalink *.meta4"),
                ("Torrent Files", "*.torrent"),
                ("Metalink Files", "*.metalink *.meta4"),
                ("All Files", "*.*"),
            ],
            parent=self,
        )
        if filepath:
            p = Path(filepath)
            if p.suffix.lower() == ".torrent":
                self.torrent_bytes = p.read_bytes()
                self.txt_url.delete(0, "end")
                self.txt_url.insert(0, f"[Torrent] {p.name}")
            else:
                self.metalink_bytes = p.read_bytes()
                self.txt_url.delete(0, "end")
                self.txt_url.insert(0, f"[Metalink] {p.name}")

    def _on_browse_dir(self) -> None:
        selected_dir = filedialog.askdirectory(
            title="Select Download Directory",
            initialdir=self.txt_dir.get(),
            parent=self,
        )
        if selected_dir:
            self.txt_dir.delete(0, "end")
            self.txt_dir.insert(0, selected_dir)

    def submit(self) -> None:
        url_input = self.txt_url.get().strip()
        custom_dir = (
            Path(self.txt_dir.get().strip()) if self.txt_dir.get().strip() else None
        )

        # Resolve selected category
        cat_choice = self.cmb_category.get()
        selected_cat_id: CategoryId | None = None
        if cat_choice not in ("(Auto-Detect)", "(None)"):
            for c in self.categories:
                if c.name == cat_choice:
                    selected_cat_id = c.id
                    break

        options: dict[str, str] = {}
        if self.spn_connections.get():
            options["max-connection-per-server"] = str(self.spn_connections.get())
        if self.spn_split.get():
            options["split"] = str(self.spn_split.get())
        if self.txt_referer.get().strip():
            options["referer"] = self.txt_referer.get().strip()
        if self.txt_user_agent.get().strip():
            options["user-agent"] = self.txt_user_agent.get().strip()
        if self.txt_speed_limit.get().strip():
            options["max-download-limit"] = self.txt_speed_limit.get().strip()

        try:
            req = AddDownloadRequest(
                uris=[url_input]
                if url_input and not url_input.startswith("[")
                else None,
                torrent_bytes=self.torrent_bytes,
                metalink_bytes=self.metalink_bytes,
                category_id=selected_cat_id,
                custom_dir=custom_dir,
                options=options,
            )
            self.ctx.add_download_uc.execute(req)
            if self.on_added:
                self.on_added()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error Adding Download", str(e), parent=self)
