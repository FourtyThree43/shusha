"""Dialog for creating new .torrent files and Magnet URIs from local targets."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import Any

import ttkbootstrap as ttk

from shusha.models.logger import LoggerService
from shusha.models.torrent_creator import TorrentCreator
from shusha.models.tracker_service import TrackerService

logger = LoggerService(__name__)

PIECE_SIZES = [
    ("256 KiB", 256 * 1024),
    ("512 KiB", 512 * 1024),
    ("1 MiB", 1024 * 1024),
    ("2 MiB", 2 * 1024 * 1024),
    ("4 MiB", 4 * 1024 * 1024),
    ("8 MiB", 8 * 1024 * 1024),
]


class CreateTorrentWindow(ttk.Toplevel):
    """Modal window for creating .torrent files and copying magnet links."""

    def __init__(self, master: Any = None, on_created: Any = None) -> None:
        super().__init__(
            title="Create Torrent / Magnet - Shusha",
            master=master,
            size=(640, 520),
            resizable=(True, True),
        )
        self.minsize(580, 440)
        self.config(padx=12, pady=12)
        self.on_created = on_created

        self.source_path_var = tk.StringVar(value="")
        self.piece_size_var = tk.StringVar(value="512 KiB")
        self.comment_var = tk.StringVar(value="Created with Shusha Download Manager")
        self.is_private_var = tk.BooleanVar(value=False)
        self.magnet_output_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # Source Selection
        src_lf = ttk.Labelframe(container, text="Source Target (File or Directory)", padding=10)
        src_lf.pack(fill=tk.X, pady=(0, 10))

        s_row = ttk.Frame(src_lf)
        s_row.pack(fill=tk.X)
        ttk.Entry(s_row, textvariable=self.source_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(s_row, text="Select File...", command=self._browse_file, bootstyle="info-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(s_row, text="Select Folder...", command=self._browse_folder, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=2)

        # Parameters
        param_lf = ttk.Labelframe(container, text="Torrent Properties", padding=10)
        param_lf.pack(fill=tk.X, pady=(0, 10))

        p_grid = ttk.Frame(param_lf)
        p_grid.pack(fill=tk.X)

        ttk.Label(p_grid, text="Piece Size:").grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Combobox(
            p_grid,
            textvariable=self.piece_size_var,
            values=[name for name, _ in PIECE_SIZES],
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky=tk.W, pady=3, padx=5)

        ttk.Label(p_grid, text="Comment:").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(p_grid, textvariable=self.comment_var, width=35).grid(row=1, column=1, sticky=tk.EW, pady=3, padx=5)

        ttk.Checkbutton(
            p_grid,
            text="Private Torrent (Disable DHT / Peer Exchange)",
            variable=self.is_private_var,
            bootstyle="round-toggle",
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=4)

        # Trackers
        tr_lf = ttk.Labelframe(container, text="Trackers (One per line)", padding=10)
        tr_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.trackers_text = tk.Text(tr_lf, height=4, wrap=tk.NONE)
        self.trackers_text.pack(fill=tk.BOTH, expand=True)
        self.trackers_text.insert("1.0", "\n".join(TrackerService.get_trackers()[:8]))

        # Magnet Result
        mag_row = ttk.Frame(container)
        mag_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(mag_row, text="Magnet Link:").pack(anchor=tk.W)
        m_entry_row = ttk.Frame(mag_row)
        m_entry_row.pack(fill=tk.X, pady=(2, 0))
        ttk.Entry(m_entry_row, textvariable=self.magnet_output_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(m_entry_row, text="Copy Link", command=self._copy_magnet, bootstyle="secondary-outline").pack(side=tk.RIGHT)

        # Bottom Button Bar
        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_bar, text="Close", command=self.destroy, bootstyle="secondary", width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_bar, text="Generate .torrent", command=self._create_torrent, bootstyle="success", width=16).pack(side=tk.RIGHT)

    def _browse_file(self) -> None:
        selected = filedialog.askopenfilename(title="Select File to Package", parent=self)
        if selected:
            self.source_path_var.set(selected)

    def _browse_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select Directory to Package", parent=self)
        if selected:
            self.source_path_var.set(selected)

    def _copy_magnet(self) -> None:
        mag = self.magnet_output_var.get().strip()
        if mag:
            self.clipboard_clear()
            self.clipboard_append(mag)

    def _create_torrent(self) -> None:
        src = self.source_path_var.get().strip()
        if not src:
            return

        # Find piece size
        chosen_size = 512 * 1024
        for name, size in PIECE_SIZES:
            if name == self.piece_size_var.get():
                chosen_size = size
                break

        trackers = [t.strip() for t in self.trackers_text.get("1.0", tk.END).split("\n") if t.strip()]

        out_file = filedialog.asksaveasfilename(
            title="Save .torrent File As",
            defaultextension=".torrent",
            filetypes=[("Torrent files", "*.torrent")],
            parent=self,
        )
        if not out_file:
            return

        try:
            torrent_path, magnet_uri = TorrentCreator.create_torrent_file(
                target_path=src,
                output_file=out_file,
                piece_length=chosen_size,
                trackers=trackers,
                comment=self.comment_var.get().strip(),
                is_private=self.is_private_var.get(),
            )
            self.magnet_output_var.set(magnet_uri)
            if callable(self.on_created):
                self.on_created(torrent_path, magnet_uri)
        except Exception as e:
            logger.log(f"Failed to create torrent: {e}", level="error")
