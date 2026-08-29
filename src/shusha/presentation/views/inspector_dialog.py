"""
Download Inspector Dialog with multi-tab inspection (General, Files, Piece Map, Peers, Servers, Options).
"""

import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from shusha.domain.identifiers import DownloadId
from shusha.presentation.app_context import AppContext
from shusha.presentation.components.base import BaseDialog, BaseFrame


class InspectorDialog(BaseDialog):
    """Deep inspection inspector for active and completed downloads."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        ctx: AppContext,
        download_id: DownloadId,
    ) -> None:
        self.ctx = ctx
        self.download_id = download_id

        # Fetch inspection DTO
        self.inspection = self.ctx.inspect_download_uc.execute(download_id)
        dl = self.inspection.download

        super().__init__(
            parent=parent,
            title=f"Inspector — {dl.name}",
            min_width=750,
            min_height=520,
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_frame = BaseFrame(self, padding=8)
        main_frame.pack(fill="both", expand=True)

        self.notebook = tb.Notebook(main_frame, bootstyle="primary")
        self.notebook.pack(fill="both", expand=True, pady=(0, 8))

        # 1. General Tab
        tab_gen = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_gen, text="General")
        self._setup_general_tab(tab_gen)

        # 2. Files Tab
        tab_files = BaseFrame(self.notebook, padding=6)
        self.notebook.add(tab_files, text=f"Files ({len(self.inspection.files)})")
        self._setup_files_tab(tab_files)

        # 3. Piece Map Tab
        tab_pieces = BaseFrame(self.notebook, padding=6)
        self.notebook.add(tab_pieces, text="Piece Map")
        self._setup_piece_map_tab(tab_pieces)

        # 4. Peers Tab
        tab_peers = BaseFrame(self.notebook, padding=6)
        self.notebook.add(tab_peers, text=f"Peers ({len(self.inspection.peers)})")
        self._setup_peers_tab(tab_peers)

        # 5. Servers Tab
        tab_servers = BaseFrame(self.notebook, padding=6)
        self.notebook.add(tab_servers, text=f"Servers ({len(self.inspection.servers)})")
        self._setup_servers_tab(tab_servers)

        # 6. Options Tab
        tab_options = BaseFrame(self.notebook, padding=12)
        self.notebook.add(tab_options, text="Options")
        self._setup_options_tab(tab_options)

        # Close button
        btn_close = tb.Button(
            main_frame, text="Close", bootstyle="secondary", command=self.destroy
        )
        btn_close.pack(side="right")

    def _setup_general_tab(self, parent: BaseFrame) -> None:
        dl = self.inspection.download
        parent.columnconfigure(1, weight=1)

        fields = [
            ("Name:", dl.name),
            ("GID:", str(dl.gid)),
            ("Status:", dl.state.value),
            ("Progress:", dl.progress.human_readable()),
            (
                "Size:",
                f"{dl.completed_length.human_readable()} of {dl.total_length.human_readable() if dl.total_length else 'Unknown'}",
            ),
            ("Download Speed:", dl.download_speed.human_readable()),
            ("Upload Speed:", dl.upload_speed.human_readable()),
            ("ETA:", dl.eta.human_readable() if dl.eta else "N/A"),
            ("Connections:", str(dl.connections)),
            ("Save Directory:", dl.dir_path or "Default"),
        ]

        if dl.error_message:
            fields.append(("Error:", f"[{dl.error_code}] {dl.error_message}"))

        for row, (label, val) in enumerate(fields):
            lbl = tb.Label(parent, text=label, font=("TkDefaultFont", 9, "bold"))
            lbl.grid(row=row, column=0, sticky="w", pady=3)
            val_lbl = tb.Label(parent, text=val)
            val_lbl.grid(row=row, column=1, sticky="w", padx=8, pady=3)

    def _setup_files_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        cols = ("index", "path", "length", "completed", "selected")
        tree = tb.Treeview(parent, columns=cols, show="headings", bootstyle="primary")
        tree.heading("index", text="#")
        tree.heading("path", text="File Path")
        tree.heading("length", text="Total Size")
        tree.heading("completed", text="Completed")
        tree.heading("selected", text="Selected")

        tree.column("index", width=40, anchor="center")
        tree.column("path", width=340, stretch=True)
        tree.column("length", width=90, anchor="e")
        tree.column("completed", width=90, anchor="e")
        tree.column("selected", width=70, anchor="center")

        v_scroll = tb.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=v_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        for f in self.inspection.files:
            tree.insert(
                "",
                "end",
                values=(
                    f.index,
                    f.path or f"file_{f.index}",
                    f.length.human_readable(),
                    f.completed_length.human_readable(),
                    "✔" if f.selected else "✕",
                ),
            )

    def _setup_piece_map_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        canvas = tk.Canvas(parent, bg="#2b2b2b", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        bf = self.inspection.download.bitfield
        if not bf or bf.total_pieces == 0:
            lbl_no_pieces = tb.Label(
                parent, text="Piece map information is not available for this download."
            )
            lbl_no_pieces.grid(row=0, column=0)
            return

        def draw_pieces(_event: tk.Event[tk.Misc] | None = None) -> None:
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 1:
                return

            block_size = 12
            gap = 2
            cols = max(1, (w - 10) // (block_size + gap))

            for i in range(bf.total_pieces):
                r = i // cols
                c = i % cols
                x1 = 6 + c * (block_size + gap)
                y1 = 6 + r * (block_size + gap)
                x2 = x1 + block_size
                y2 = y1 + block_size

                color = "#28a745" if bf.is_piece_complete(i) else "#6c757d"
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        canvas.bind("<Configure>", draw_pieces)

    def _setup_peers_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        cols = ("ip", "client", "dl_speed", "ul_speed", "seeder")
        tree = tb.Treeview(parent, columns=cols, show="headings", bootstyle="primary")
        tree.heading("ip", text="IP:Port")
        tree.heading("client", text="Peer ID")
        tree.heading("dl_speed", text="DL Speed")
        tree.heading("ul_speed", text="UL Speed")
        tree.heading("seeder", text="Seeder")

        tree.column("ip", width=140)
        tree.column("client", width=200, stretch=True)
        tree.column("dl_speed", width=90, anchor="e")
        tree.column("ul_speed", width=90, anchor="e")
        tree.column("seeder", width=60, anchor="center")

        tree.grid(row=0, column=0, sticky="nsew")

        for p in self.inspection.peers:
            tree.insert(
                "",
                "end",
                values=(
                    f"{p.ip}:{p.port.number}",
                    str(p.peer_id),
                    p.download_speed.human_readable(),
                    p.upload_speed.human_readable(),
                    "✔" if p.seeder else "✕",
                ),
            )

    def _setup_servers_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        cols = ("uri", "current_uri", "speed")
        tree = tb.Treeview(parent, columns=cols, show="headings", bootstyle="primary")
        tree.heading("uri", text="Original URI")
        tree.heading("current_uri", text="Current Mirror URI")
        tree.heading("speed", text="Download Speed")

        tree.column("uri", width=250, stretch=True)
        tree.column("current_uri", width=250, stretch=True)
        tree.column("speed", width=100, anchor="e")

        tree.grid(row=0, column=0, sticky="nsew")

        for s in self.inspection.servers:
            tree.insert(
                "",
                "end",
                values=(
                    s.uri.raw_uri,
                    s.current_uri.raw_uri,
                    s.download_speed.human_readable(),
                ),
            )

    def _setup_options_tab(self, parent: BaseFrame) -> None:
        parent.columnconfigure(1, weight=1)

        opts = self.inspection.options

        tb.Label(parent, text="Max Download Limit (e.g. 500K):").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.txt_dl_limit = tb.Entry(parent)
        self.txt_dl_limit.insert(0, opts.get("max-download-limit", "0"))
        self.txt_dl_limit.grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        tb.Label(parent, text="Max Upload Limit (e.g. 100K):").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.txt_ul_limit = tb.Entry(parent)
        self.txt_ul_limit.insert(0, opts.get("max-upload-limit", "0"))
        self.txt_ul_limit.grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        btn_apply = tb.Button(
            parent,
            text="Apply Changes",
            bootstyle="success",
            command=self._on_apply_options,
        )
        btn_apply.grid(row=2, column=1, sticky="e", pady=8)

    def _on_apply_options(self) -> None:
        new_opts = {
            "max-download-limit": self.txt_dl_limit.get().strip() or "0",
            "max-upload-limit": self.txt_ul_limit.get().strip() or "0",
        }
        try:
            self.ctx.change_options_uc.execute(self.download_id, new_opts)
            messagebox.showinfo(
                "Options Updated", "Download options updated successfully.", parent=self
            )
        except Exception as e:
            messagebox.showerror("Failed to Update Options", str(e), parent=self)
