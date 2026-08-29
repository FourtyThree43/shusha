"""Piece Map bitfield visualization canvas widget.

This widget renders a 2D chunk grid representing the bitfield pieces of an active
or completed download (inspired by Motrix, Persepolis, and aria2 web clients).
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

import ttkbootstrap as ttk

from shusha.models.structs_downloads import Download


class PieceMapWidget(ttk.Frame):
    """Canvas widget rendering the piece completion state in a scalable grid."""

    def __init__(
        self,
        master: Any,
        download: Download | None = None,
        block_size: int = 10,
        gap: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self.download = download
        self.block_size = block_size
        self.gap = gap

        self.colors = ttk.Style().colors

        # Info Header
        self.info_label = ttk.Label(
            self,
            text="Pieces: 0 / 0 (0%) | Piece Length: 0 B",
            font=("TkDefaultFont", 9),
        )
        self.info_label.pack(side=tk.TOP, anchor="w", pady=(0, 4))

        # Canvas with Scrollbar
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=self.colors.bg,
            highlightthickness=0,
        )
        self.v_scroll = ttk.Scrollbar(
            self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind("<Configure>", lambda e: self.redraw())

        if self.download:
            self.update_download(self.download)

    def update_download(self, download: Download) -> None:
        """Update piece completion data and redraw grid."""
        self.download = download
        if not download:
            self.info_label.config(text="No download selected")
            self.canvas.delete("all")
            return

        try:
            total_pieces = int(getattr(download, "num_pieces", 0) or 0)
            completed_pieces = int(getattr(download, "num_completed_pieces", 0) or 0)
            piece_len = int(getattr(download, "piece_length", 0) or 0)
        except TypeError, ValueError:
            total_pieces, completed_pieces, piece_len = 0, 0, 0

        pct = (completed_pieces / total_pieces * 100) if total_pieces > 0 else 0.0

        length_str = f"{piece_len} B"
        if piece_len >= 1048576:
            length_str = f"{piece_len / 1048576:.1f} MB"
        elif piece_len >= 1024:
            length_str = f"{piece_len / 1024:.1f} KB"

        self.info_label.config(
            text=f"Pieces: {completed_pieces} / {total_pieces} ({pct:.1f}%) | Piece Size: {length_str}"
        )
        self.redraw()

    def redraw(self) -> None:
        """Redraw all piece blocks on the canvas."""
        self.canvas.delete("all")
        if not self.download:
            return

        pieces = self.download.pieces_bool_array
        if not pieces:
            return

        canvas_width = max(100, self.canvas.winfo_width())
        item_step = self.block_size + self.gap
        cols = max(1, canvas_width // item_step)

        completed_color = self.colors.success
        pending_color = self.colors.secondary

        for idx, is_done in enumerate(pieces):
            row = idx // cols
            col = idx % cols
            x1 = col * item_step + 4
            y1 = row * item_step + 4
            x2 = x1 + self.block_size
            y2 = y1 + self.block_size

            fill_color = completed_color if is_done else pending_color
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=fill_color, outline="", width=0
            )

        total_rows = (len(pieces) + cols - 1) // cols
        scroll_height = total_rows * item_step + 10
        self.canvas.configure(scrollregion=(0, 0, canvas_width, scroll_height))
